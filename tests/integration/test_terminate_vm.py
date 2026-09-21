# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""End task against real child processes (docs/TEST-STRATEGY.md 3.3). Linux only, no mocks.

TB-T050 (PID reuse), TB-T134 (TERM vs KILL), TB-T136 (protected), TB-T006 (verified, not dispatched).
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from trier_bridge.core.identity import ProcessIdentity
from trier_bridge.core.state import OperationState
from trier_bridge.operations.process import TerminatePlan, execute_terminate, plan_terminate
from trier_bridge.state.journal import OperationJournal
from trier_bridge.system.processes import ProcessKind, ProcessSampler

pytestmark = pytest.mark.integration
if sys.platform != "linux":
    pytest.skip("procfs and POSIX signals", allow_module_level=True)


def _identity(pid: int) -> ProcessIdentity:
    rows, _ = ProcessSampler().sample()
    return next(r.identity for r in rows if r.identity.pid == pid)


def _child(ignore_term: bool = False) -> subprocess.Popen:
    code = (
        "import signal, time; "
        + ("signal.signal(signal.SIGTERM, signal.SIG_IGN); " if ignore_term else "")
        + "time.sleep(60)"
    )
    p = subprocess.Popen([sys.executable, "-c", code])
    time.sleep(0.3)
    return p


def test_end_verifies_the_process_is_gone(tmp_path: Path) -> None:
    child = _child()
    plan = plan_terminate(_identity(child.pid), ProcessKind.USER)
    assert isinstance(plan, TerminatePlan) and "asked to close" in plan.preview
    j = OperationJournal(tmp_path / "j")
    res = execute_terminate(plan, j)
    assert res.state is OperationState.VERIFIED, res
    assert child.wait(timeout=2) == -15
    rec = j.load(plan.operation.operation_id)
    assert rec is not None and rec.operation_state is OperationState.VERIFIED
    assert [h["state"] for h in rec.history][-3:] == ["committed", "verifying", "verified"]


def test_term_ignored_reports_partial_then_force_end_works(tmp_path: Path) -> None:
    child = _child(ignore_term=True)
    j = OperationJournal(tmp_path / "j")
    plan = plan_terminate(_identity(child.pid), ProcessKind.USER)
    assert isinstance(plan, TerminatePlan)
    res = execute_terminate(plan, j)
    assert res.state is OperationState.PARTIAL and "Force end" in res.safest_next_step
    force = plan_terminate(_identity(child.pid), ProcessKind.USER, force=True)
    assert isinstance(force, TerminatePlan) and force.operation.kind == "process.force_end"
    res2 = execute_terminate(force, j)
    assert res2.state is OperationState.VERIFIED
    assert child.wait(timeout=2) == -9


def test_stale_identity_cancels_instead_of_killing_a_replacement(tmp_path: Path) -> None:
    child = _child()
    ident = _identity(child.pid)
    stale = ProcessIdentity(
        pid=ident.pid, start_ticks=ident.start_ticks - 1, uid=ident.uid, comm=ident.comm
    )
    plan = plan_terminate(stale, ProcessKind.USER)
    assert isinstance(plan, TerminatePlan)
    res = execute_terminate(plan, OperationJournal(tmp_path / "j"))
    assert res.state is OperationState.CANCELLED and "no longer the same" in res.plain
    assert child.poll() is None  # untouched
    child.kill()
    child.wait()


def test_protected_and_foreign_processes_are_refused_without_a_signal() -> None:
    rows, _ = ProcessSampler().sample()
    pid1 = next(r for r in rows if r.identity.pid == 1)
    res = plan_terminate(pid1.identity, pid1.kind)
    assert isinstance(res, type(plan_terminate(pid1.identity, ProcessKind.CRITICAL)))
    assert res.state is OperationState.UNSUPPORTED and "core system process" in res.plain
    me = next(r for r in rows if r.identity.pid == os.getpid())
    self_res = plan_terminate(me.identity, ProcessKind.USER)
    assert self_res.state is OperationState.UNSUPPORTED
    other = next((r for r in rows if r.kind is ProcessKind.SYSTEM), None)
    if other is not None:
        assert plan_terminate(other.identity, other.kind).state is OperationState.UNSUPPORTED
