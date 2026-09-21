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
"""Read-only directory listing for the in-app file browser (DEC-025, DOC-02).

A structured counterpart to the Bridge Terminal's ``dir`` (see
``bridge/commands.py:cmd_dir``), which formats the same read to text; this
returns data a GTK list view can bind to directly. Read-only: nothing here
opens a file for writing, follows a symlink into a mutation, or changes
anything on disk (TB-INV-234, TB-INV-242, TB-INV-243).

Every entry is classified from ``lstat`` (never follows the entry itself, so a
symlink is reported as a symlink, not silently as whatever it points to);
non-regular files (block/character devices, sockets, FIFOs) are identified by
type and never opened, matching TB-INV-243. Listings are bounded (TB-INV-237):
a very large folder is truncated with an honest count of what was left out,
never silently or without saying so.
"""
from __future__ import annotations

import os
import stat as stat_module
from dataclasses import dataclass
from pathlib import Path

MAX_ENTRIES = 5000  # bounded per TB-INV-237; same cap style as Event Viewer's 500


@dataclass(frozen=True)
class FileEntry:
    """One row a file-browser list view can bind to directly."""

    name: str
    path: Path
    kind: str  # "dir", "file", "symlink_dir", "symlink_file", "symlink_broken",
    # "device", "socket", "fifo", "unknown"
    size_bytes: int | None  # None for directories and unreadable entries
    modified: float | None  # epoch seconds; None when unavailable
    hidden: bool  # name starts with "."

    @property
    def is_navigable(self) -> bool:
        """Double-click/Enter should descend into this, not try to open it as a file."""
        return self.kind in ("dir", "symlink_dir")


@dataclass(frozen=True)
class ListResult:
    """What ``list_directory`` returns: the entries plus honest bounds/errors."""

    entries: tuple[FileEntry, ...]
    truncated_count: int  # how many more existed beyond MAX_ENTRIES, 0 if none
    denied: bool  # PermissionError reading this folder
    error: str  # empty on success; a plain description otherwise


def _classify(p: Path, entry_stat_result: os.stat_result) -> str:
    mode = entry_stat_result.st_mode
    if stat_module.S_ISLNK(mode):
        try:
            target_mode = p.stat().st_mode  # this one *does* follow, to classify the target
        except OSError:
            return "symlink_broken"
        return "symlink_dir" if stat_module.S_ISDIR(target_mode) else "symlink_file"
    if stat_module.S_ISDIR(mode):
        return "dir"
    if stat_module.S_ISREG(mode):
        return "file"
    if stat_module.S_ISBLK(mode) or stat_module.S_ISCHR(mode):
        return "device"
    if stat_module.S_ISSOCK(mode):
        return "socket"
    if stat_module.S_ISFIFO(mode):
        return "fifo"
    return "unknown"


def list_directory(folder: Path, show_hidden: bool = False) -> ListResult:
    """List one folder's immediate children, non-recursively. Never follows into
    a child symlink's contents; classifies the symlink itself (TB-INV-234)."""
    try:
        raw = list(os.scandir(folder))
    except PermissionError:
        return ListResult((), 0, True, "Access is denied.")
    except FileNotFoundError:
        return ListResult((), 0, False, "This folder no longer exists.")
    except OSError as exc:
        return ListResult((), 0, False, str(exc))

    entries: list[FileEntry] = []
    for de in raw:
        name = de.name
        if name.startswith(".") and not show_hidden:
            continue
        p = Path(de.path)
        try:
            st = de.stat(follow_symlinks=False)
        except OSError:
            entries.append(FileEntry(name, p, "unknown", None, None, name.startswith(".")))
            continue
        kind = _classify(p, st)
        size = st.st_size if kind == "file" else None
        try:
            modified: float | None = st.st_mtime
        except (OSError, ValueError):
            modified = None
        entries.append(FileEntry(name, p, kind, size, modified, name.startswith(".")))

    entries.sort(key=lambda e: (not e.is_navigable, e.name.casefold()))
    truncated = 0
    if len(entries) > MAX_ENTRIES:
        truncated = len(entries) - MAX_ENTRIES
        entries = entries[:MAX_ENTRIES]
    return ListResult(tuple(entries), truncated, False, "")
