# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T080/TB-T099: findstr, find, where, set, path, tree, %VAR% expansion on real files."""
import os
from pathlib import Path

import pytest

from trier_bridge.bridge.grammar import Failure, ParseFailure, parse

gi = pytest.importorskip("gi")

from trier_bridge.bridge.commands import Exit, Session, expand_vars, run_line  # noqa: E402


def _tree(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.txt").write_text("Alpha line\nbeta LINE\ngamma\n", encoding="utf-8")
    (tmp_path / "docs" / "b.txt").write_text("nothing here\nBETA again\n", encoding="utf-8")
    (tmp_path / "docs" / "bin.dat").write_bytes(b"\x00\x01beta")
    (tmp_path / "docs" / "sub").mkdir()
    (tmp_path / ".hidden").mkdir()
    return tmp_path


def test_findstr_and_find_search_real_files(tmp_path: Path) -> None:
    s = Session(_tree(tmp_path))
    out = run_line("findstr /I beta docs\\a.txt docs\\b.txt", s)
    assert out.exit is Exit.OK and out.lines == ("a.txt:beta LINE", "b.txt:BETA again")
    out = run_line("findstr /N Alpha docs\\a.txt", s)
    assert out.lines == ("1:Alpha line",)
    out = run_line("findstr /I /C beta docs\\*.txt", s)  # /C counts; the binary file is skipped
    assert out.lines == ("a.txt: 1", "b.txt: 1")
    out = run_line('find "gamma" docs\\a.txt', s)
    assert out.exit is Exit.OK and out.lines == ("gamma",)
    out = run_line("find /V gamma docs\\a.txt", s)
    assert out.lines == ("Alpha line", "beta LINE")
    assert run_line("findstr zzz docs\\a.txt", s).exit is Exit.FAILED
    out = run_line("findstr /R /I al.ha docs\\a.txt", s)  # /R: a pattern
    assert (
        out.exit is Exit.OK and out.lines == ("Alpha line",) and out.linux_equivalent.endswith("-E")
    )
    assert run_line("findstr /R al.ha docs\\a.txt", s).exit is Exit.FAILED  # case matters
    assert run_line("findstr /L al.ha docs\\a.txt", s).exit is Exit.FAILED  # /L: literal dot
    bad = run_line("findstr /R [ docs\\a.txt", s)
    assert bad.exit is Exit.PARSE_ERROR and bad.lines[0].startswith("Not a valid pattern")
    assert run_line("findstr x docs\\missing.txt", s).exit is Exit.FAILED
    assert isinstance(parse("findstr beta"), ParseFailure)  # needs a file


def test_where_set_path_and_variables(tmp_path: Path) -> None:
    s = Session(tmp_path)
    out = run_line("where python", s)
    assert out.exit in (Exit.OK, Exit.FAILED)
    assert run_line("where no-such-program-xyz", s).exit is Exit.FAILED
    out = run_line("set USERPROFILE", s)
    assert out.exit is Exit.OK and out.lines[0] == f"USERPROFILE={Path.home()}"
    assert run_line("set NOPE_NOT_SET_XYZ", s).exit is Exit.FAILED
    assert run_line("path", s).lines[0].startswith("PATH=")
    assert expand_vars("%USERPROFILE%\\Documents") == f"{Path.home()}\\Documents"
    assert expand_vars("%TEMP%") == os.environ.get("TMPDIR", "/tmp")
    assert expand_vars("%UNKNOWN_VAR_XYZ%") == "%UNKNOWN_VAR_XYZ%"
    assert run_line("echo %COMPUTERNAME%", s).lines[0] != "%COMPUTERNAME%"


def test_tree_is_bounded_and_hides_dotfiles_by_default(tmp_path: Path) -> None:
    s = Session(_tree(tmp_path))
    out = run_line("tree", s)
    assert out.exit is Exit.OK and "+---docs" in out.lines and "|   +---sub" in out.lines
    assert not any(".hidden" in ln for ln in out.lines)
    assert any(".hidden" in ln for ln in run_line("tree /A", s).lines)
    assert any("a.txt" in ln for ln in run_line("tree /F docs", s).lines)
    assert run_line("tree nope", s).exit is Exit.FAILED


def test_teaching_and_exit() -> None:
    for line in ("attrib +r x", "icacls x /grant y", "takeown /f x"):
        p = parse(line)
        assert isinstance(p, ParseFailure) and p.failure is Failure.NO_EQUIVALENT, line
    assert parse("exit").spec.name == "exit"  # type: ignore[union-attr]
