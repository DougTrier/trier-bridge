# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T083/TB-T096/TB-T099/TB-T098: pure Bridge commands on real files; parse failures do nothing."""
from pathlib import Path

from trier_bridge.bridge.commands import Exit, Session, is_sensitive, run_line


def test_parse_failure_performs_nothing() -> None:
    out = run_line("tasklist; rm -rf /", Session())
    assert out.exit is Exit.PARSE_ERROR and not out.performed and "Nothing was run" in out.lines[0]
    out = run_line("nonsense", Session())
    assert out.exit is Exit.PARSE_ERROR and not out.performed


def test_help_lists_commands_with_classes() -> None:
    out = run_line("help", Session())
    assert out.exit is Exit.OK
    text = "\n".join(out.lines)
    assert (
        "ipconfig" in text
        and "taskkill" in text
        and "[asks first]" in text
        and "[no equivalent]" in text
    )
    one = run_line("help ipconfig", Session())
    assert "/all" in "\n".join(one.lines) and "NetworkManager" in one.linux_equivalent


def test_dir_type_cd_on_a_real_tree(tmp_path: Path) -> None:
    (tmp_path / "Documents").mkdir()
    (tmp_path / "notes.txt").write_text("hello\nworld\n", encoding="utf-8")
    (tmp_path / ".hidden").write_text("x", encoding="utf-8")
    (tmp_path / "bin.dat").write_bytes(b"\x00\x01\x02")
    s = Session(tmp_path)
    out = run_line("dir", s)
    assert out.exit is Exit.OK and out.performed
    text = "\n".join(out.lines)
    assert "<DIR>          Documents" in text and "notes.txt" in text and ".hidden" not in text
    assert ".hidden" in "\n".join(run_line("dir /a", s).lines)
    assert run_line("type notes.txt", s).lines == ("hello", "world")
    assert run_line("type bin.dat", s).exit is Exit.UNSUPPORTED
    assert run_line("type missing.txt", s).exit is Exit.FAILED
    assert (
        run_line("cd Documents", s).exit is Exit.OK and s.cwd == (tmp_path / "Documents").resolve()
    )
    assert run_line("cd nope", s).exit is Exit.FAILED
    assert run_line("cd", s).lines[0].startswith(str(s.cwd))  # plus the familiar spelling
    assert run_line("echo hi there", s).lines == ("hi there",)


def test_output_is_bounded(tmp_path: Path) -> None:
    big = tmp_path / "big.txt"
    big.write_text("\n".join(f"line {i}" for i in range(1000)), encoding="utf-8")
    out = run_line("type big.txt", Session(tmp_path))
    assert out.exit is Exit.TRUNCATED and out.truncated and len(out.lines) <= 402


def test_history_excludes_sensitive_lines() -> None:
    assert is_sensitive("echo password=hunter2")
    assert not is_sensitive("ipconfig /all")
