# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T006/TB-T050/TB-T164: file operations on real files, Trash-first, never overwriting."""
from pathlib import Path

import pytest

gi = pytest.importorskip("gi")
gi.require_version("Gio", "2.0")
from gi.repository import Gio  # noqa: E402

from trier_bridge.bridge.commands import Exit, Session, run_line  # noqa: E402
from trier_bridge.core.state import OperationState  # noqa: E402
from trier_bridge.operations.files import FilePlan, execute_file, plan_file  # noqa: E402
from trier_bridge.state.journal import OperationJournal  # noqa: E402


def _plan(verb: str, src: str, dest: str | None, cwd: Path) -> FilePlan:
    plan = plan_file(verb, src, dest, cwd)
    assert isinstance(plan, FilePlan), plan
    return plan


def test_copy_move_rename_are_verified_and_never_overwrite(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    journal = OperationJournal(tmp_path / "j")
    res = execute_file(_plan("copy", "a.txt", "b.txt", tmp_path), journal)
    assert res.state is OperationState.VERIFIED, res
    assert (tmp_path / "b.txt").read_text(encoding="utf-8") == "hello"
    assert (tmp_path / "a.txt").exists()
    refused = plan_file("copy", "a.txt", "b.txt", tmp_path)
    assert not isinstance(refused, FilePlan) and refused.state is OperationState.UNSUPPORTED
    assert "already exists" in refused.plain
    (tmp_path / "sub").mkdir()
    res = execute_file(_plan("move", "b.txt", "sub", tmp_path), journal)
    assert res.state is OperationState.VERIFIED and (tmp_path / "sub" / "b.txt").exists()
    assert not (tmp_path / "b.txt").exists()
    res = execute_file(_plan("rename", "sub\\b.txt", "c.txt", tmp_path), journal)
    assert res.state is OperationState.VERIFIED and (tmp_path / "sub" / "c.txt").exists()
    assert journal.unresolved() == []


def test_delete_means_trash_and_is_restorable(tmp_path: Path) -> None:
    victim = tmp_path / "gone.txt"
    victim.write_text("keep me", encoding="utf-8")
    plan = _plan("trash", "gone.txt", None, tmp_path)
    assert "Trash" in plan.preview and plan.destructive
    res = execute_file(plan, OperationJournal(tmp_path / "j"))
    assert res.state is OperationState.VERIFIED and not victim.exists()
    assert "restore" in res.plain
    trash = Gio.File.new_for_uri("trash:///")
    originals = []
    for info in trash.enumerate_children("trash::orig-path", Gio.FileQueryInfoFlags.NONE, None):
        originals.append(info.get_attribute_byte_string("trash::orig-path") or "")
    assert str(victim) in originals, originals[:5]


def test_folders_create_and_remove_only_when_empty(tmp_path: Path) -> None:
    journal = OperationJournal(tmp_path / "j")
    res = execute_file(_plan("mkdir", "new folder", None, tmp_path), journal)
    assert res.state is OperationState.VERIFIED and (tmp_path / "new folder").is_dir()
    (tmp_path / "new folder" / "x").write_text("", encoding="utf-8")
    refused = plan_file("rmdir", "new folder", None, tmp_path)
    assert not isinstance(refused, FilePlan) and "not empty" in refused.plain
    (tmp_path / "new folder" / "x").unlink()
    res = execute_file(_plan("rmdir", "new folder", None, tmp_path), journal)
    assert res.state is OperationState.VERIFIED and not (tmp_path / "new folder").exists()
    refused = plan_file("copy", "j", "j2", tmp_path)
    assert not isinstance(refused, FilePlan) and "Folders are copied in Files" in refused.plain


def test_identity_change_between_plan_and_execute_cancels(tmp_path: Path) -> None:
    f = tmp_path / "same-name.txt"
    f.write_text("first", encoding="utf-8")
    plan = _plan("trash", "same-name.txt", None, tmp_path)
    f.unlink()
    f.write_text("second, a different file", encoding="utf-8")  # same path, new inode
    res = execute_file(plan, OperationJournal(tmp_path / "j"))
    assert res.state is OperationState.CANCELLED and f.exists()
    assert "Nothing was changed" in res.plain


def test_bridge_commands_plan_but_do_not_act(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    session = Session(tmp_path)
    out = run_line("copy a.txt b.txt", session)
    assert out.exit is Exit.NEEDS_CONFIRMATION and isinstance(out.pending_operation, FilePlan)
    assert not (tmp_path / "b.txt").exists()
    out = run_line("Remove-Item -Path a.txt", session)
    assert out.exit is Exit.NEEDS_CONFIRMATION and out.lines[0] == "PowerShell Remove-Item → del"
    assert (tmp_path / "a.txt").exists()
    out = run_line("Remove-Item a.txt -Recurse", session)
    assert out.exit is Exit.PARSE_ERROR and "-Recurse" in out.lines[0]
    out = run_line("del missing.txt", session)
    assert out.exit is Exit.FAILED and "cannot find" in out.lines[0]
    out = run_line("copy a.txt /tmp", session)  # a Linux path is an argument, not a switch
    assert out.exit is Exit.NEEDS_CONFIRMATION


def test_hostile_filenames_are_data_not_syntax(tmp_path: Path) -> None:
    """SECURITY 37.3: names with spaces, quotes, dashes, unicode, and shell characters are
    plain data through the typed path; the terminal refuses shell characters whole."""
    names = ["with space.txt", "-leading-dash.txt", "quote'mark.txt", "über straße.txt", "a;b.txt"]
    journal = OperationJournal(tmp_path / "j")
    for n in names:
        (tmp_path / n).write_text("x", encoding="utf-8")
        res = execute_file(_plan("copy", n, n + ".copy", tmp_path), journal)
        assert res.state is OperationState.VERIFIED, (n, res)
        assert (tmp_path / (n + ".copy")).read_text(encoding="utf-8") == "x"
    session = Session(tmp_path)
    assert run_line('copy "with space.txt" spaced.txt', session).exit is Exit.NEEDS_CONFIRMATION
    assert run_line("copy a;b.txt c.txt", session).exit is Exit.PARSE_ERROR  # ; is shell syntax
    assert run_line("del ../../etc/passwd", session).exit is Exit.FAILED  # not found here
    assert journal.unresolved() == []
