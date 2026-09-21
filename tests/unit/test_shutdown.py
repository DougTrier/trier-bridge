# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T094/TB-T110: shutdown /s and /r plan a logind power action and never act on their own."""
from pathlib import Path

import pytest

from trier_bridge.bridge.grammar import ParseFailure, parse
from trier_bridge.core.state import PrivilegeClass

gi = pytest.importorskip("gi")

from trier_bridge.bridge.commands import ActionPlan, Exit, Session, run_line  # noqa: E402


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
    assert run_line("shutdown /a", s).exit is Exit.UNSUPPORTED
    out = run_line("shutdown /r /t 5", s)
    # on a Linux box logind answers; the plan exists and nothing has run
    assert out.exit in (Exit.NEEDS_CONFIRMATION, Exit.DENIED), out
    if out.exit is Exit.NEEDS_CONFIRMATION:
        assert isinstance(out.pending_operation, ActionPlan)
        assert "after 5 seconds" in out.pending_operation.preview
        assert out.pending_operation.heading == "Restart the computer"
