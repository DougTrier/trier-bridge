# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T006/TB-T077: a default-app change is verified and undone by choosing the previous one."""
from pathlib import Path

import pytest

gi = pytest.importorskip("gi")

from trier_bridge.bridge.commands import Exit, Session, run_line  # noqa: E402
from trier_bridge.core.state import OperationState  # noqa: E402
from trier_bridge.operations.defaults import (  # noqa: E402
    DefaultAppPlan,
    candidates,
    current_default,
    execute_default,
    plan_default,
)
from trier_bridge.state.journal import OperationJournal  # noqa: E402

MIME = "text/plain"


def test_set_and_revert_default_for_text_files(tmp_path: Path) -> None:
    options = candidates(MIME)
    if len(options) < 2:
        pytest.skip("fewer than two programs registered for text/plain on this system")
    before = current_default(MIME)
    other = next((c for c in options if before is None or c.desktop_id != before.desktop_id), None)
    assert other is not None
    journal = OperationJournal(tmp_path / "j")
    plan = plan_default(MIME, "Text files", other.desktop_id)
    assert isinstance(plan, DefaultAppPlan) and other.name in plan.preview
    res = execute_default(plan, journal)
    assert res.state is OperationState.VERIFIED, res
    now = current_default(MIME)
    assert now is not None and now.desktop_id == other.desktop_id
    # the same choice again is refused as a no-op
    again = plan_default(MIME, "Text files", other.desktop_id)
    assert not isinstance(again, DefaultAppPlan) and "already" in again.plain
    # undo: choose the previous program again (or leave it if nothing was set before)
    if before is not None:
        back = plan_default(MIME, "Text files", before.desktop_id)
        assert isinstance(back, DefaultAppPlan)
        res2 = execute_default(back, journal)
        assert res2.state is OperationState.VERIFIED, res2
        restored = current_default(MIME)
        assert restored is not None and restored.desktop_id == before.desktop_id
    assert journal.unresolved() == []


def test_unlisted_program_is_refused_and_stale_default_cancels(tmp_path: Path) -> None:
    refused = plan_default(MIME, "Text files", "not-a-real-app.desktop")
    assert not isinstance(refused, DefaultAppPlan)
    assert (
        refused.state is OperationState.UNSUPPORTED and "not one the desktop lists" in refused.plain
    )
    # any common kind of file with three registered programs will do
    mime = next(
        (
            m
            for m in ("text/plain", "image/png", "image/jpeg", "application/pdf")
            if len(candidates(m)) >= 3
        ),
        None,
    )
    if mime is None:
        pytest.skip("no common kind of file has three registered programs here")
    options = candidates(mime)
    before = current_default(mime)
    before_id = before.desktop_id if before else ""
    target = next(c for c in options if c.desktop_id != before_id)
    other = next((c for c in options if c.desktop_id not in (before_id, target.desktop_id)), None)
    if other is None:
        pytest.skip("need three programs for text/plain to stage a concurrent change")
    plan = plan_default(mime, "Files of that kind", target.desktop_id)
    assert isinstance(plan, DefaultAppPlan)
    # someone else changes the default between plan and execute: the plan must cancel
    elsewhere = plan_default(mime, "Files of that kind", other.desktop_id)
    assert isinstance(elsewhere, DefaultAppPlan)
    assert execute_default(elsewhere).state is OperationState.VERIFIED
    res = execute_default(plan, OperationJournal(tmp_path / "j"))
    assert res.state is OperationState.CANCELLED and "changed elsewhere" in res.plain
    if before is not None:
        back = plan_default(mime, "Files of that kind", before.desktop_id)
        assert isinstance(back, DefaultAppPlan)
        assert execute_default(back).state is OperationState.VERIFIED


def test_assoc_lists_defaults_read_only(tmp_path: Path) -> None:
    out = run_line("assoc", Session(tmp_path))
    assert out.exit is Exit.OK and out.performed
    assert any(line.startswith("Text files") for line in out.lines)
    assert out.pending_operation is None
