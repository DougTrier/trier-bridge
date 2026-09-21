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
"""Default-app changes as typed, reversible operations (IMP-03.05).

"Which program opens PDFs" is the user's own per-user association
(``~/.config/mimeapps.list``), written through GIO exactly as GNOME Settings
writes it. Only an application the desktop already lists for that kind of file
can be chosen (no arbitrary commands, TB-INV-119). The previous default is
recorded so the change can be undone by choosing it again (TB-INV-077).
Success is the observed new default (TB-INV-006).
"""
from __future__ import annotations

from dataclasses import dataclass

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from ..core.operations import Operation, OperationResult  # noqa: E402
from ..core.state import AuthorizationState, OperationState, PrivilegeClass  # noqa: E402
from ..state.journal import OperationJournal  # noqa: E402


@dataclass(frozen=True)
class Candidate:
    desktop_id: str
    name: str


@dataclass(frozen=True)
class MimeIdentity:
    """The association being changed: the kind of file plus what opens it right now."""

    mime: str
    current_id: str  # "" when nothing is set

    @property
    def kind(self) -> str:
        return "default-app"

    def same_target(self, other: object) -> bool:
        return (
            isinstance(other, MimeIdentity)
            and other.mime == self.mime
            and other.current_id == self.current_id
        )

    def label(self) -> str:
        return self.mime


@dataclass(frozen=True)
class DefaultAppPlan:
    operation: Operation
    identity: MimeIdentity
    label: str  # "PDF documents"
    candidate: Candidate
    previous: Candidate | None
    preview: str


def current_default(mime: str) -> Candidate | None:
    info = Gio.AppInfo.get_default_for_type(mime, False)
    if info is None:
        return None
    return Candidate(info.get_id() or "", info.get_display_name() or info.get_id() or "")


def candidates(mime: str) -> list[Candidate]:
    """Applications the desktop lists for this kind of file, recommended ones first."""
    out: list[Candidate] = []
    seen: set[str] = set()
    for info in list(Gio.AppInfo.get_recommended_for_type(mime)) + list(
        Gio.AppInfo.get_all_for_type(mime)
    ):
        ident = info.get_id() or ""
        if not ident or ident in seen:
            continue
        seen.add(ident)
        out.append(Candidate(ident, info.get_display_name() or ident))
    return out


def plan_default(mime: str, label: str, desktop_id: str) -> DefaultAppPlan | OperationResult:
    previous = current_default(mime)
    identity = MimeIdentity(mime, previous.desktop_id if previous else "")
    op = Operation(
        kind="default-app.set",
        target=identity,
        privilege=PrivilegeClass.B_USER_MUTATION,
        parameters={"mime": mime, "desktop_id": desktop_id},
    )
    chosen = next((c for c in candidates(mime) if c.desktop_id == desktop_id), None)
    if chosen is None:
        return OperationResult(
            op.operation_id,
            OperationState.UNSUPPORTED,
            f"That program is not one the desktop lists for {label}. Nothing was changed.",
            safest_next_step="Pick one of the listed programs.",
        )
    if previous is not None and previous.desktop_id == desktop_id:
        return OperationResult(
            op.operation_id,
            OperationState.UNSUPPORTED,
            f"{chosen.name} already opens {label}. Nothing was changed.",
        )
    was = f" (was {previous.name})" if previous else " (nothing was set)"
    preview = (
        f"Open {label} with {chosen.name} from now on{was}? "
        "This is your own setting; choosing the previous program again undoes it."
    )
    return DefaultAppPlan(op.with_preview(preview), identity, label, chosen, previous, preview)


def execute_default(
    plan: DefaultAppPlan, journal: OperationJournal | None = None
) -> OperationResult:
    op = plan.operation.with_authorization(AuthorizationState.NOT_REQUIRED)
    rec = None
    if journal is not None:
        rec = journal.open(
            op.operation_id,
            op.kind,
            "default-app",
            plan.label,
            {
                "mime": plan.identity.mime,
                "desktop_id": plan.candidate.desktop_id,
                "previous_id": plan.previous.desktop_id if plan.previous else "",
            },
            plan.preview,
        )
        journal.advance(rec, OperationState.PREVIEWED)
        journal.advance(rec, OperationState.AUTHORIZED)

    def finish(
        state: OperationState, plain: str, technical: str = "", next_step: str = ""
    ) -> OperationResult:
        if journal is not None and rec is not None:
            journal.advance(rec, state, plain, technical)
        return OperationResult(op.operation_id, state, plain, technical, next_step)

    now = current_default(plan.identity.mime)
    if not plan.identity.same_target(
        MimeIdentity(plan.identity.mime, now.desktop_id if now else "")
    ):
        return finish(
            OperationState.CANCELLED,
            f"The program for {plan.label} was changed elsewhere in the meantime. "
            "Nothing was changed.",
            next_step="Look at the current setting and choose again.",
        )
    info = next(
        (
            i
            for i in Gio.AppInfo.get_all_for_type(plan.identity.mime)
            if (i.get_id() or "") == plan.candidate.desktop_id
        ),
        None,
    )
    if info is None:
        return finish(
            OperationState.CANCELLED,
            f"{plan.candidate.name} is no longer available for {plan.label}. Nothing was changed.",
        )
    if journal is not None and rec is not None:
        journal.advance(rec, OperationState.EXECUTING)
    try:
        info.set_as_default_for_type(plan.identity.mime)
    except GLib.Error as exc:
        state = (
            OperationState.DENIED
            if exc.domain == "g-io-error-quark" and exc.code == Gio.IOErrorEnum.PERMISSION_DENIED
            else OperationState.FAILED
        )
        return finish(
            state,
            f"The setting for {plan.label} could not be written. Nothing was changed.",
            technical=f"{exc.domain} {exc.code}: {exc.message}",
        )
    if journal is not None and rec is not None:
        journal.advance(rec, OperationState.COMMITTED)
        journal.advance(rec, OperationState.VERIFYING)
    after = current_default(plan.identity.mime)
    if after is not None and after.desktop_id == plan.candidate.desktop_id:
        undo = f" Choose {plan.previous.name} again to undo." if plan.previous else ""
        return finish(
            OperationState.VERIFIED,
            f"{plan.label} now open with {plan.candidate.name}.{undo}",
            technical="mimeapps.list updated through GIO; default re-read",
        )
    return finish(
        OperationState.OUTCOME_UNKNOWN,
        f"The setting for {plan.label} was written but reads back differently.",
        technical=f"expected {plan.candidate.desktop_id}, read "
        f"{after.desktop_id if after else 'none'}",
        next_step="Check Default Apps in Settings.",
    )
