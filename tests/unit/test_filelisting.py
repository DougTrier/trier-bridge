# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T234/TB-T243: real files, real symlinks, real special files -- no mocks."""
import os
import sys
from pathlib import Path

import pytest

from trier_bridge.system.filelisting import MAX_ENTRIES, list_directory


def _tree(tmp_path: Path) -> Path:
    (tmp_path / "Documents").mkdir()
    (tmp_path / "report.txt").write_text("hello", encoding="utf-8")
    (tmp_path / ".hidden_file").write_text("shh", encoding="utf-8")
    return tmp_path


def test_lists_real_files_and_folders_sorted_dirs_first(tmp_path: Path) -> None:
    _tree(tmp_path)
    res = list_directory(tmp_path)
    assert not res.denied and not res.error and res.truncated_count == 0
    names = [e.name for e in res.entries]
    assert names == ["Documents", "report.txt"]  # dirs first, then casefold order
    doc = res.entries[0]
    assert doc.kind == "dir" and doc.is_navigable and doc.size_bytes is None
    report = res.entries[1]
    assert report.kind == "file" and not report.is_navigable and report.size_bytes == 5


def test_hidden_files_excluded_by_default_shown_with_flag(tmp_path: Path) -> None:
    _tree(tmp_path)
    default = list_directory(tmp_path)
    assert all(not e.hidden for e in default.entries)
    with_hidden = list_directory(tmp_path, show_hidden=True)
    hidden_names = [e.name for e in with_hidden.entries if e.hidden]
    assert hidden_names == [".hidden_file"]


def test_missing_folder_reports_plainly_not_an_exception(tmp_path: Path) -> None:
    res = list_directory(tmp_path / "does-not-exist")
    assert res.entries == () and not res.denied and "no longer exists" in res.error


def test_permission_denied_reports_plainly(tmp_path: Path) -> None:
    if sys.platform != "linux" or os.geteuid() == 0:
        pytest.skip("POSIX permission bits, and root ignores them")
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "secret.txt").write_text("x", encoding="utf-8")
    locked.chmod(0o000)
    try:
        res = list_directory(locked)
        assert res.denied and res.entries == ()
    finally:
        locked.chmod(0o755)  # so tmp_path cleanup can remove it


def test_symlinks_are_classified_as_links_never_silently_as_their_target(tmp_path: Path) -> None:
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    real_file = tmp_path / "real_file.txt"
    real_file.write_text("x", encoding="utf-8")
    try:
        (tmp_path / "link_to_dir").symlink_to(real_dir, target_is_directory=True)
        (tmp_path / "link_to_file").symlink_to(real_file)
        (tmp_path / "link_broken").symlink_to(tmp_path / "nope")
    except OSError:
        pytest.skip("creating symlinks needs admin/Developer Mode on this Windows host")

    res = list_directory(tmp_path)
    by_name = {e.name: e for e in res.entries}
    assert by_name["link_to_dir"].kind == "symlink_dir" and by_name["link_to_dir"].is_navigable
    assert by_name["link_to_file"].kind == "symlink_file"
    assert not by_name["link_to_file"].is_navigable
    assert by_name["link_broken"].kind == "symlink_broken"
    # the symlink itself must never be reported as a plain "dir" or "file" (TB-INV-234)
    assert by_name["link_to_dir"].kind != "dir"
    assert by_name["link_to_file"].kind != "file"


def test_special_files_identified_by_type_not_opened(tmp_path: Path) -> None:
    if sys.platform != "linux":
        pytest.skip("FIFOs and sockets are POSIX-only")
    import socket as socket_module

    fifo_path = tmp_path / "a_fifo"
    os.mkfifo(fifo_path)
    sock_path = tmp_path / "a_socket"
    s = socket_module.socket(socket_module.AF_UNIX, socket_module.SOCK_STREAM)
    try:
        s.bind(str(sock_path))
        res = list_directory(tmp_path)
        by_name = {e.name: e for e in res.entries}
        assert by_name["a_fifo"].kind == "fifo"
        assert by_name["a_socket"].kind == "socket"
        # a FIFO with no writer would block a plain open() forever -- the point of
        # TB-INV-243 is that list_directory never does that; it only stats.
    finally:
        s.close()


def test_bounded_to_max_entries_with_an_honest_truncation_count(tmp_path: Path) -> None:
    for i in range(MAX_ENTRIES + 37):
        (tmp_path / f"f{i:05d}.txt").write_text("", encoding="utf-8")
    res = list_directory(tmp_path)
    assert len(res.entries) == MAX_ENTRIES
    assert res.truncated_count == 37
