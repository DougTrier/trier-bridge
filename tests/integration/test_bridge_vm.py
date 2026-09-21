# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Bridge Terminal read-only commands against the live VM (SECURITY.md section 45, tests A and C).

Each command's output is checked against an independent read of the same fact.
No mocks. TB-T084, TB-T093, TB-T096, TB-T099, TB-T104.
"""
import os
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("gi")

from trier_bridge.bridge.commands import Exit, Session, run_line  # noqa: E402
from trier_bridge.operations.process import TerminatePlan  # noqa: E402

pytestmark = pytest.mark.integration


def test_north_star_a_windows_commands_without_root() -> None:
    s = Session()
    ip = run_line("ipconfig /all", s)
    assert ip.exit is Exit.OK and ip.performed
    text = "\n".join(ip.lines)
    eth = Path("/sys/class/net/eth0/address").read_text().strip().upper()
    assert "eth0" in text and eth in text.upper() and "Connectivity check" in text
    tl = run_line("tasklist", s)
    assert tl.exit in (Exit.OK, Exit.TRUNCATED) and any(
        f"{os.getpid():>8}" in ln for ln in tl.lines
    )
    sc = run_line("sc query ssh", s)
    assert sc.exit is Exit.OK and "SERVICE_NAME: ssh.service" in sc.lines[0]
    assert "Running" in sc.lines[1]
    host = run_line("hostname", s)
    assert host.lines == (socket.gethostname(),)
    who = run_line("whoami", s)
    assert who.lines[0].endswith("\\tb")
    info = run_line("systeminfo", s)
    assert any("Ubuntu" in ln for ln in info.lines) and any("Processors" in ln for ln in info.lines)
    mac = run_line("getmac", s)
    assert any("eth0" in ln for ln in mac.lines)
    ns = run_line("netstat", s)
    assert any(":22 " in ln or ":22" in ln for ln in ns.lines), ns.lines[:5]
    # nothing above needed root: our process is still an ordinary user
    assert os.geteuid() != 0


def test_north_star_c_injection_is_rejected_and_nothing_runs(tmp_path: Path) -> None:
    marker = tmp_path / "pwned"
    s = Session(tmp_path)
    for line in (
        f"echo hi > {marker}",
        f"dir; touch {marker}",
        f"tasklist && touch {marker}",
        f"type `touch {marker}`",
        f"echo $(touch {marker})",
    ):
        out = run_line(line, s)
        assert out.exit is Exit.PARSE_ERROR and not out.performed, line
    assert not marker.exists()


def test_taskkill_returns_a_plan_and_does_not_kill_by_itself() -> None:
    child = subprocess.Popen(["sleep", "60"])
    try:
        out = run_line(f"taskkill /PID {child.pid}", Session())
        assert out.exit is Exit.NEEDS_CONFIRMATION and isinstance(
            out.pending_operation, TerminatePlan
        )
        assert not out.performed and child.poll() is None  # still running: no confirmation yet
        bad = run_line("taskkill /IM sleep", Session())  # unknown switch: parse error, nothing runs
        assert bad.exit is Exit.PARSE_ERROR and not bad.performed and child.poll() is None
        one = run_line("taskkill /PID 1", Session())
        assert one.exit is Exit.UNSUPPORTED and "core system process" in one.lines[0]
    finally:
        child.kill()
        child.wait()


def test_type_and_dir_stay_inside_real_paths(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("secret-free text\n", encoding="utf-8")
    s = Session(tmp_path)
    assert run_line("type a.txt", s).lines == ("secret-free text",)
    assert run_line("dir", s).exit is Exit.OK
    out = run_line("type /etc/shadow", s)
    assert out.exit is Exit.DENIED and "Access is denied" in out.lines[0]
