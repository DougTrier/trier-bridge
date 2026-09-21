# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T080/TB-T105: explorer, start, net, date, time, and the teaching entries parse as intended."""
from pathlib import Path

import pytest

from trier_bridge.bridge.grammar import Failure, ParseFailure, parse
from trier_bridge.core.state import PrivilegeClass

gi = pytest.importorskip("gi")

from trier_bridge.bridge.commands import Exit, Session, run_line  # noqa: E402


def test_specs_and_classes() -> None:
    assert parse("explorer").spec.privilege is PrivilegeClass.A_READ_ONLY  # type: ignore[union-attr]
    assert parse("start www.ubuntu.com").spec.name == "start"  # type: ignore[union-attr]
    assert parse("net stop cups").spec.privilege is PrivilegeClass.C_ADMIN_MUTATION  # type: ignore[union-attr]
    for line in ("sfc /scannow", "chkdsk C: /f", "xcopy a b /e", "gpedit"):
        p = parse(line)
        assert isinstance(p, ParseFailure) and p.failure is Failure.NO_EQUIVALENT, line
    assert parse("taskkill /IM sleep /F").switches == ("im", "f")  # type: ignore[union-attr]


def test_windows_tool_names_open_our_pages(tmp_path: Path) -> None:
    for line in ("taskmgr", "devmgmt.msc", "services.msc", "eventvwr", "MSCONFIG"):
        assert parse(line).spec.name == "taskmgr", line  # type: ignore[union-attr]
    assert isinstance(parse("taskmgr /x"), ParseFailure)
    s = Session(tmp_path)
    # no application object exists under pytest, so the command says where the page lives
    out = run_line("devmgmt.msc", s)
    assert out.exit is Exit.FAILED and out.lines[0].startswith("Device Manager is a page")
    assert out.linux_equivalent == "trier-bridge --section devices"
    out = run_line("start eventvwr", s)
    assert out.exit is Exit.FAILED and "Event Viewer" in out.lines[0]


def test_date_time_and_net_teaching(tmp_path: Path) -> None:
    s = Session(tmp_path)
    d = run_line("date", s)
    assert d.exit is Exit.OK and d.lines[0].startswith("The current date is: ")
    t = run_line("time", s)
    assert t.exit is Exit.OK and d.lines[0] != t.lines[0]
    assert run_line("net use Z: \\\\server\\share", s).exit is Exit.UNSUPPORTED
    assert run_line("net user", s).exit is Exit.UNSUPPORTED
    assert run_line("net start", s).exit is Exit.PARSE_ERROR
    assert run_line("net wibble", s).exit is Exit.UNSUPPORTED


def test_taskkill_by_name_needs_exactly_one_of_your_programs(tmp_path: Path) -> None:
    out = run_line("taskkill /IM no-such-program-xyz", Session(tmp_path))
    assert out.exit is Exit.FAILED and "not found" in out.lines[0]
