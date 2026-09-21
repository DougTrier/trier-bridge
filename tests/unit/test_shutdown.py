# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T094/TB-T110: shutdown /s and /r plan a logind power action and never act on their own."""
from pathlib import Path

import pytest

from trier_bridge.bridge.grammar import ParseFailure, parse
from trier_bridge.core.state import PrivilegeClass

gi = pytest.importorskip("gi")

from trier_bridge.bridge.commands import (  # noqa: E402
    ActionPlan,
    Exit,
    Session,
    cancel_scheduled_power,
    run_line,
    scheduled_power,
)


def test_shutdown_forms() -> None:
    cmd = parse("shutdown /r /t 30")
    assert not isinstance(cmd, ParseFailure)
    assert cmd.spec.privilege is PrivilegeClass.C_ADMIN_MUTATION and cmd.switches == ("r", "t")
    assert isinstance(parse("shutdown /x"), ParseFailure)


def test_shutdown_plans_only(tmp_path: Path) -> None:
    s = Session(tmp_path)
    assert run_line("shutdown", s).exit is Exit.PARSE_ERROR
    assert run_line("shutdown /s /r", s).exit is Exit.PARSE_ERROR
    assert run_line("shutdown /r /t abc", s).exit is Exit.PARSE_ERROR
    assert run_line("shutdown /a", s).exit is Exit.FAILED  # nothing scheduled
    out = run_line("shutdown /r /t 5", s)
    # on a Linux box logind answers; the plan exists and nothing has run
    assert out.exit in (Exit.NEEDS_CONFIRMATION, Exit.DENIED), out
    if out.exit is Exit.NEEDS_CONFIRMATION:
        assert isinstance(out.pending_operation, ActionPlan)
        assert "after 5 seconds" in out.pending_operation.preview
        assert "shutdown /a cancels it" in out.pending_operation.preview
        assert out.pending_operation.heading == "Restart the computer"


def test_delayed_shutdown_is_a_cancellable_timer(tmp_path: Path) -> None:
    """Confirming a delayed shutdown arms a main-loop timer; /a removes it. No loop runs
    here, so nothing can fire; the timer is an hour away in any case."""
    s = Session(tmp_path)
    out = run_line("shutdown /s /t 3600", s)
    if out.exit is Exit.DENIED:
        pytest.skip("logind refuses power actions for this account")
    assert isinstance(out.pending_operation, ActionPlan)
    try:
        ok, text = out.pending_operation.run()
        assert ok and text.startswith("The computer will shut down in 3600 seconds")
        pending = scheduled_power()
        assert pending is not None and pending.action == "poweroff"
        assert 3590 <= pending.remaining <= 3600
        again = run_line("shutdown /r /t 10", s)
        assert again.exit is Exit.FAILED and "already scheduled" in again.lines[0]
        cancelled = run_line("shutdown /a", s)
        assert cancelled.exit is Exit.OK and cancelled.lines[0].endswith("has been cancelled.")
        assert scheduled_power() is None
        assert run_line("shutdown /a", s).exit is Exit.FAILED
    finally:
        cancel_scheduled_power()
