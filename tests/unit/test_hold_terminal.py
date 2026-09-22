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
"""The shipped terminal helper, run for real as a child process (no mocks).

It is what ping/tracert run inside the terminal window instead of a shell
(TB-SEC-003, TB-INV-088; entry IMP-07.14). These tests feed it a real
program and a real Enter on stdin, on the host and in the VM alike.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from trier_bridge.resources import terminal_runner_path


def _run(marker: Path, *program: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(terminal_runner_path()), str(marker), "--", *program],
        input="\n",
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_helper_is_shipped_beside_the_catalog() -> None:
    assert terminal_runner_path().is_file()


def test_helper_records_its_pid_runs_the_program_and_holds_for_enter(tmp_path: Path) -> None:
    marker = tmp_path / "terminal.pid"
    proc = _run(marker, sys.executable, "-c", "print('64 bytes from a real child')")
    assert proc.returncode == 0, proc.stderr
    assert "64 bytes from a real child" in proc.stdout
    assert "Press Enter to close" in proc.stdout
    assert marker.read_text().strip().isdigit()


def test_helper_passes_arguments_through_untouched(tmp_path: Path) -> None:
    marker = tmp_path / "terminal.pid"
    tricky = "10.1.70.1; echo INJECTED"  # would be two commands to a shell; here it is one argument
    proc = _run(marker, sys.executable, "-c", "import sys; print(repr(sys.argv[1]))", tricky)
    assert proc.returncode == 0, proc.stderr
    assert repr(tricky) in proc.stdout
    assert "INJECTED\n" not in proc.stdout.replace(repr(tricky), "")


def test_helper_reports_a_missing_program_and_still_holds(tmp_path: Path) -> None:
    marker = tmp_path / "terminal.pid"
    proc = _run(marker, "definitely-not-a-program-on-this-computer")
    assert proc.returncode == 127
    assert "definitely-not-a-program-on-this-computer" in proc.stderr
    assert "Press Enter to close" in proc.stdout


def test_helper_refuses_a_malformed_call(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(terminal_runner_path()), str(tmp_path / "m"), "nope"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 2
    assert "usage" in proc.stderr
