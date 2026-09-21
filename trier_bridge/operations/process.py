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
"""End task (IMP-06.04): terminate one of the user's own processes.

Class B (user-scoped mutation, docs/SECURITY.md section 10): no elevation,
ever. Terminate (SIGTERM) and Force end (SIGKILL) are separate operations
(TB-INV-134). The target is revalidated by PID plus start time immediately
before the signal (TB-INV-050, TB-INV-121); a reused PID cancels. Kernel
threads, PID 1, other users' processes, and Trier Bridge itself are refused
(TB-INV-132, TB-INV-136). Success means the process is gone, observed, not
that a signal was sent (TB-INV-006).
"""
from __future__ import annotations

import os
import signal
import time
from dataclasses import dataclass
from pathlib import Path

from ..core.identity import ProcessIdentity
from ..core.operations import Operation, OperationResult
from ..core.state import AuthorizationState, OperationState, PrivilegeClass
from ..state.journal import OperationJournal
from ..system.processes import ProcessKind, has_ended, is_still_same

VERIFY_TIMEOUT_S = 3.0


@dataclass(frozen=True)
class TerminatePlan:
    operation: Operation
    identity: ProcessIdentity
    force: bool
    label: str
    preview: str


def plan_terminate(
    identity: ProcessIdentity, kind: ProcessKind, force: bool = False
) -> TerminatePlan | OperationResult:
    """Build the typed operation, or return a terminal result explaining why not."""
    op_kind = "process.force_end" if force else "process.end"
    op = Operation(
        kind=op_kind,
        target=identity,
        privilege=PrivilegeClass.B_USER_MUTATION,
        parameters={"signal": "KILL" if force else "TERM", "pid": str(identity.pid)},
    )
    label = identity.label()
    if identity.pid == os.getpid():
        return OperationResult(
            op.operation_id,
            OperationState.UNSUPPORTED,
            "Trier Bridge will not end itself from here. Close the window instead.",
            safest_next_step="Use Quit from the menu.",
        )
    if not kind.actionable_by_user:
        why = {
            ProcessKind.KERNEL: "It is part of the Linux kernel, not a program you started.",
            ProcessKind.CRITICAL: (
                "It is the core system process; ending it would stop the computer."
            ),
            ProcessKind.SYSTEM: "It belongs to the system, not to your account.",
            ProcessKind.OTHER_USER: "It belongs to another user.",
        }.get(kind, "It is not a process of yours.")
        return OperationResult(
            op.operation_id,
            OperationState.UNSUPPORTED,
            f"{label} cannot be ended from Task Manager. {why} Nothing was changed.",
            safest_next_step="System services are managed under Services in a later foundation.",
        )
    if identity.uid != os.getuid():
        return OperationResult(
            op.operation_id,
            OperationState.UNSUPPORTED,
            f"{label} belongs to another user account. Nothing was changed.",
        )
    action = "Force end" if force else "End"
    preview = f"{action} {label}? Unsaved work in this program may be lost. " + (
        "This cannot be undone and the program gets no chance to save."
        if force
        else "The program is asked to close."
    )
    op = op.with_preview(preview)
    return TerminatePlan(op, identity, force, label, preview)


def execute_terminate(
    plan: TerminatePlan, journal: OperationJournal | None = None, proc: Path = Path("/proc")
) -> OperationResult:
    op = plan.operation.with_authorization(AuthorizationState.NOT_REQUIRED)
    rec = None
    if journal is not None:
        rec = journal.open(
            op.operation_id,
            op.kind,
            "process",
            plan.label,
            {"pid": str(plan.identity.pid), "start_ticks": str(plan.identity.start_ticks)},
            plan.preview,
        )
        journal.advance(rec, OperationState.PREVIEWED)
        journal.advance(rec, OperationState.AUTHORIZED)

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

    # Revalidate immediately before acting (TB-INV-050, TB-INV-121).
    if not is_still_same(plan.identity, proc):
        return finish(
            OperationState.CANCELLED,
            f"{plan.label} is no longer the same process (it ended, or its number was reused). "
            "Nothing was changed.",
            next_step="Refresh Task Manager and try again if it is still running.",
        )
    if journal is not None and rec is not None:
        journal.advance(rec, OperationState.EXECUTING)
    sig = signal.SIGKILL if plan.force else signal.SIGTERM
    try:
        os.kill(plan.identity.pid, sig)
    except ProcessLookupError:
        return finish(
            OperationState.CANCELLED, f"{plan.label} had already ended. Nothing was changed."
        )
    except PermissionError as exc:
        return finish(
            OperationState.DENIED,
            f"Linux did not allow ending {plan.label}. Nothing was changed.",
            technical=str(exc),
        )
    if journal is not None and rec is not None:
        journal.advance(rec, OperationState.COMMITTED)
        journal.advance(rec, OperationState.VERIFYING)
    deadline = time.monotonic() + VERIFY_TIMEOUT_S
    while time.monotonic() < deadline:
        if has_ended(plan.identity, proc):
            return finish(
                OperationState.VERIFIED,
                f"{plan.label} has ended.",
                technical=f"signal {sig.name} to pid {plan.identity.pid}, process gone",
            )
        time.sleep(0.1)
    if plan.force:
        return finish(
            OperationState.OUTCOME_UNKNOWN,
            f"{plan.label} was told to stop but is still listed. "
            "It may be finishing or stuck in the kernel.",
            technical="SIGKILL sent; process still present after verify timeout",
            next_step="Refresh Task Manager in a moment.",
        )
    return finish(
        OperationState.PARTIAL,
        f"{plan.label} was asked to close but is still running. "
        "It may be waiting to save or ignoring the request.",
        technical="SIGTERM sent; process still present after verify timeout",
        next_step="Wait a moment, then use Force end if it does not close.",
        succeeded=("asked the program to close",),
        failed=("the program has not closed yet",),
    )
