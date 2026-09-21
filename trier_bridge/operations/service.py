# Copyright 2026 Doug Trier
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Service control (IMP-06.05): start, stop, restart, enable, disable.

Each verb is its own typed operation; none implies another (TB-INV-067,
TB-INV-139). System-scope calls go to systemd over the system bus with
ALLOW_INTERACTIVE_AUTHORIZATION so polkit prompts the user through the
desktop's agent; Trier Bridge never elevates itself (docs/PRIVILEGE-MODEL.md).
The unit is revalidated by name, object path, and fragment path right before
the call (TB-INV-053); a replaced unit cancels. Success is the observed
postcondition, not the returned job (TB-INV-006). A restart that stops but
does not start is PARTIAL (TB-INV-143). Denial is a result, never routed
around (TB-SEC-007).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from ..core.operations import Operation, OperationResult  # noqa: E402
from ..core.state import OperationState, PrivilegeClass  # noqa: E402
from ..state.journal import OperationJournal  # noqa: E402
from ..system.bus import Bus  # noqa: E402
from ..system.services import MANAGER, SD, SD_PATH, Scope  # noqa: E402
from ..system.services import ServiceInfo, bus_for, read_unit  # noqa: E402

VERIFY_TIMEOUT_S = 15.0
CALL_TIMEOUT_MS = 30000


@dataclass(frozen=True)
class ServicePlan:
    operation: Operation
    service: ServiceInfo
    verb: str  # start, stop, restart, enable, disable
    preview: str
    needs_admin: bool


VERB_TEXT = {
    "start": ("Start", "starts it now; it will not start at boot unless it is already set to"),
    "stop": ("Stop", "stops it now; it may start again at the next boot if it is set to"),
    "restart": ("Restart", "stops and starts it now"),
    "enable": ("Set to start at boot", "does not start it now"),
    "disable": ("Stop starting at boot", "does not stop it now"),
}


def plan_service(service: ServiceInfo, verb: str) -> ServicePlan | OperationResult:
    if verb not in VERB_TEXT:
        raise ValueError(f"unknown verb {verb}")
    needs_admin = service.scope is Scope.SYSTEM
    op = Operation(
        kind=f"service.{verb}",
        target=service.identity,
        privilege=(
            PrivilegeClass.C_ADMIN_MUTATION if needs_admin else PrivilegeClass.B_USER_MUTATION
        ),
        parameters={"unit": service.identity.name, "scope": service.scope.value},
    )
    name = service.identity.name
    if verb == "start" and not service.can_start:
        return OperationResult(
            op.operation_id,
            OperationState.UNSUPPORTED,
            f"{name} cannot be started this way. Nothing was changed.",
        )
    if verb == "stop" and not service.can_stop:
        return OperationResult(
            op.operation_id,
            OperationState.UNSUPPORTED,
            f"{name} cannot be stopped this way. Nothing was changed.",
        )
    if verb in ("enable", "disable") and service.unit_file_state in (
        "static",
        "masked",
        "transient",
        "generated",
    ):
        return OperationResult(
            op.operation_id,
            OperationState.UNSUPPORTED,
            f"{name} is '{service.unit_file_state}': its startup is not set by enabling "
            "or disabling. Nothing was changed.",
        )
    label, effect = VERB_TEXT[verb]
    who = (
        "Administrator permission will be requested."
        if needs_admin
        else "No administrator permission is needed."
    )
    preview = f"{label} {name}? This {effect}. {who}"
    return ServicePlan(op.with_preview(preview), service, verb, preview, needs_admin)


def _manager_call(bus: Bus, method: str, args: Any) -> tuple[Any, str]:
    """Call the systemd manager, letting polkit prompt interactively for system scope."""
    if bus.conn is None:
        return None, bus.error or "bus unavailable"
    try:
        res = bus.conn.call_sync(
            SD,
            SD_PATH,
            MANAGER,
            method,
            args,
            None,
            Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION,
            CALL_TIMEOUT_MS,
            None,
        )
        return res.unpack(), ""
    except GLib.Error as exc:
        return None, f"{exc.domain}: {exc.message}"


def _classify_error(err: str) -> tuple[OperationState, str]:
    low = err.lower()
    if (
        "accessdenied" in low
        or "not authorized" in low
        or "interactive authentication required" in low
    ):
        return OperationState.DENIED, "Linux did not grant permission for this change."
    if "cancel" in low or "dismissed" in low:
        return OperationState.CANCELLED, "The permission request was cancelled."
    if "nosuchunit" in low or "not loaded" in low:
        return OperationState.CANCELLED, "The service is no longer there."
    if "timeout" in low or "timed out" in low:
        return OperationState.OUTCOME_UNKNOWN, "The service manager did not answer in time."
    return OperationState.FAILED, "The service manager refused the request."


def execute_service(
    plan: ServicePlan, journal: OperationJournal | None = None, bus: Bus | None = None
) -> OperationResult:
    scope = plan.service.scope
    bus = bus or bus_for(scope)
    op = plan.operation
    name = plan.service.identity.name
    rec = None
    if journal is not None:
        rec = journal.open(
            op.operation_id,
            op.kind,
            "service",
            name,
            {
                "name": name,
                "object_path": plan.service.identity.object_path,
                "fragment": plan.service.identity.fragment_path,
                "scope": scope.value,
            },
            plan.preview,
        )
        journal.advance(rec, OperationState.PREVIEWED)

    def finish(
        state: OperationState,
        plain: str,
        technical: str = "",
        next_step: str = "",
        succeeded: tuple[str, ...] = (),
        failed: tuple[str, ...] = (),
    ) -> OperationResult:
        if journal is not None and rec is not None:
            journal.advance(rec, state, plain, technical)
        return OperationResult(
            op.operation_id, state, plain, technical, next_step, succeeded, failed
        )

    # Revalidate the exact unit right before acting (TB-INV-053, TB-INV-121).
    fresh, err = read_unit(scope, name, bus)
    if fresh is None:
        return finish(
            OperationState.CANCELLED,
            f"{name} could not be found any more. Nothing was changed.",
            err,
        )
    if not fresh.identity.same_target(plan.service.identity):
        return finish(
            OperationState.CANCELLED,
            f"{name} was replaced or reloaded since it was shown. Nothing was changed.",
            f"fragment {plan.service.identity.fragment_path!r} -> {fresh.identity.fragment_path!r}",
            "Refresh Services and try again.",
        )
    if journal is not None and rec is not None:
        journal.advance(
            rec, OperationState.AUTHORIZED if not plan.needs_admin else OperationState.PREVIEWED
        )
    verb = plan.verb
    if verb in ("start", "stop", "restart"):
        method = {"start": "StartUnit", "stop": "StopUnit", "restart": "RestartUnit"}[verb]
        args = GLib.Variant("(ss)", (name, "replace"))
    elif verb == "enable":
        method, args = "EnableUnitFiles", GLib.Variant("(asbb)", ([name], False, False))
    else:
        method, args = "DisableUnitFiles", GLib.Variant("(asb)", ([name], False))
    if journal is not None and rec is not None:
        journal.advance(rec, OperationState.EXECUTING)
    res, err = _manager_call(bus, method, args)
    if err:
        state, plain = _classify_error(err)
        return finish(
            state,
            f"{plain} {name} was not changed.",
            err,
            "Nothing to do." if state is OperationState.CANCELLED else "",
        )
    if journal is not None and rec is not None:
        journal.advance(rec, OperationState.COMMITTED)
        journal.advance(rec, OperationState.VERIFYING)
    if verb in ("enable", "disable"):
        _manager_call(bus, "Reload", None)
        after, err = read_unit(scope, name, bus)
        want = "enabled" if verb == "enable" else "disabled"
        if after is not None and after.unit_file_state == want:
            return finish(
                OperationState.VERIFIED,
                f"{name} is now set to {after.plain_startup.lower()} start.",
                f"{method} ok; UnitFileState={after.unit_file_state}",
            )
        return finish(
            OperationState.OUTCOME_UNKNOWN,
            f"The change was sent but {name} still reports "
            f"'{(after.unit_file_state if after else 'unknown')}'.",
            err or f"UnitFileState={(after.unit_file_state if after else '?')}",
            "Refresh Services in a moment.",
        )
    want = {"start": "active", "stop": "inactive", "restart": "active"}[verb]
    deadline = time.monotonic() + VERIFY_TIMEOUT_S
    last = ""
    while time.monotonic() < deadline:
        after, err = read_unit(scope, name, bus)
        last = after.active_state if after else err
        if after is not None and after.active_state == want:
            return finish(
                OperationState.VERIFIED,
                f"{name} is now {after.plain_running.lower()}.",
                f"{method} ok; ActiveState={after.active_state}/{after.sub_state}",
            )
        if after is not None and after.active_state == "failed":
            if verb == "restart":
                return finish(
                    OperationState.PARTIAL,
                    f"{name} stopped but did not start again.",
                    f"ActiveState=failed after {method}",
                    "Check Event Viewer for the reason.",
                    succeeded=("stopped",),
                    failed=("started",),
                )
            return finish(
                OperationState.FAILED,
                f"{name} failed to {verb}.",
                f"ActiveState=failed after {method}",
                "Check Event Viewer for the reason.",
            )
        time.sleep(0.3)
    return finish(
        OperationState.OUTCOME_UNKNOWN,
        f"{name} was asked to {verb} but reports '{last}' after {int(VERIFY_TIMEOUT_S)} seconds.",
        f"{method} ok; verify timeout",
        "Refresh Services in a moment.",
    )
