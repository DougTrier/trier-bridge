# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""explorer, start, and taskkill /IM against the live desktop and real child processes."""
import os
import subprocess
import time
from pathlib import Path

import pytest

gi = pytest.importorskip("gi")

from trier_bridge.bridge.commands import Exit, Session, run_line  # noqa: E402
from trier_bridge.operations.process import TerminatePlan  # noqa: E402

pytestmark = pytest.mark.integration
needs_session = pytest.mark.skipif(
    not os.environ.get("WAYLAND_DISPLAY"), reason="needs the console session"
)


def test_taskkill_by_name_plans_for_one_child(tmp_path: Path) -> None:
    child = subprocess.Popen(["sleep", "300"])
    try:
        time.sleep(0.3)
        out = run_line("taskkill /IM sleep", Session(tmp_path))
        # other sleep processes may exist on the box; either outcome must name the right thing
        if out.exit is Exit.NEEDS_CONFIRMATION:
            assert isinstance(out.pending_operation, TerminatePlan)
            assert out.pending_operation.identity.pid == child.pid
        else:
            assert out.exit is Exit.UNSUPPORTED and str(child.pid) in out.lines[0]
        assert child.poll() is None  # nothing ran without the dialog
    finally:
        child.kill()
        child.wait()


@needs_session
def test_explorer_opens_files_at_the_folder(tmp_path: Path) -> None:
    out = run_line(f"explorer {tmp_path}", Session(Path.home()))
    assert out.exit is Exit.OK and "Opened in Files" in out.lines[0] and "C:\\" in out.lines[0]
    missing = run_line("explorer C:\\no\\such\\folder", Session(Path.home()))
    assert missing.exit is Exit.FAILED


@needs_session
def test_start_launches_a_familiar_program(tmp_path: Path) -> None:
    out = run_line("start calc", Session(tmp_path))
    assert out.exit is Exit.OK and "Started" in out.lines[0], out
    time.sleep(2)
    subprocess.run(["pkill", "-x", "gnome-calculator"], capture_output=True)
    assert run_line("start cmd", Session(tmp_path)).exit is Exit.OK
    assert run_line("start mspaint", Session(tmp_path)).exit is Exit.UNSUPPORTED
    assert run_line("start nosuchthing.xyz", Session(tmp_path)).exit is Exit.FAILED
