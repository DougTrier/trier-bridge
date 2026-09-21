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
"""Drive letters as a familiar label over Linux mounts (DEC-024, IMP-04.07).

Linux attaches volumes to folders. Windows users know letters, so Trier Bridge
gives each mounted volume one: C: is the system drive (the root filesystem),
D:, E:, ... are the other mounted volumes, fixed ones before removable ones,
each in a stable order. The real path is always shown next to the letter and
is the truth (TB-INV-031, TB-INV-073). ``C:\\Users\\<name>`` is the one
familiar alias with a different shape on Linux: it resolves to ``/home/<name>``.
Nothing here mounts, renames, or writes anything.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

REAL_FS = {
    "ext2",
    "ext3",
    "ext4",
    "xfs",
    "btrfs",
    "f2fs",
    "zfs",
    "vfat",
    "exfat",
    "ntfs",
    "ntfs3",
    "fuseblk",
    "hfsplus",
    "iso9660",
    "udf",
}
# Mounts that are plumbing, not places a person keeps files (no letter, like the EFI partition)
NO_LETTER_PREFIXES = (
    "/boot",
    "/snap",
    "/var/snap",
    "/var/lib/snapd",
    "/run",
    "/sys",
    "/proc",
    "/dev",
    "/tmp",
)
REMOVABLE_PREFIXES = ("/media/", "/mnt/", "/run/media/")


@dataclass(frozen=True)
class DriveLetter:
    letter: str  # "C"
    mount_point: str
    fs_type: str
    removable: bool

    @property
    def label(self) -> str:
        if self.mount_point == "/":
            return "System drive"
        return os.path.basename(self.mount_point.rstrip("/")) or self.mount_point

    @property
    def display(self) -> str:
        return f"{self.letter}:"


def read_mounts(path: Path = Path("/proc/self/mounts")) -> list[tuple[str, str]]:
    """(mount point, filesystem type) pairs, mount points unescaped."""
    out: list[tuple[str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        mount = re.sub(r"\\(\d{3})", lambda m: chr(int(m.group(1), 8)), parts[1])
        out.append((mount, parts[2]))
    return out


def assign(mounts: list[tuple[str, str]]) -> list[DriveLetter]:
    """Deterministic letters: C: for /, then fixed volumes, then removable ones, sorted by path."""
    seen: set[str] = set()
    root_fs = next((fs for m, fs in mounts if m == "/"), "")
    out = [DriveLetter("C", "/", root_fs, False)]
    seen.add("/")
    candidates = []
    for mount, fs in mounts:
        if mount in seen or fs not in REAL_FS:
            continue
        if any(mount == p or mount.startswith(p + "/") for p in NO_LETTER_PREFIXES):
            if not mount.startswith("/run/media/"):
                continue
        seen.add(mount)
        removable = mount.startswith(REMOVABLE_PREFIXES)
        candidates.append((removable, mount, fs))
    letter = ord("D")
    for removable, mount, fs in sorted(candidates):
        if letter > ord("Z"):
            break
        out.append(DriveLetter(chr(letter), mount, fs, removable))
        letter += 1
    return out


def letters(mounts_path: Path = Path("/proc/self/mounts")) -> list[DriveLetter]:
    return assign(read_mounts(mounts_path))


_DRIVE = re.compile(r"^([A-Za-z]):(?=[\\/]|$)")


def to_linux_path(text: str, cwd: Path, drives: list[DriveLetter] | None = None) -> Path:
    """A Windows- or Linux-style path as typed, resolved to an absolute Linux path.

    ``C:\\`` is /, ``C:\\Users\\<name>`` is /home/<name>, ``D:\\x`` is under D:'s mount.
    A letter nobody has raises ValueError with a plain reason.
    """
    raw = text.replace("\\", "/")
    m = _DRIVE.match(raw)
    if m:
        letter = m.group(1).upper()
        drives = letters() if drives is None else drives
        drive = next((d for d in drives if d.letter == letter), None)
        if drive is None:
            raise ValueError(f"There is no drive {letter}: on this computer.")
        rest = raw[m.end() :].lstrip("/")
        parts = rest.split("/") if rest else []
        if letter == "C" and parts and parts[0].lower() == "users":
            base = Path("/home")
            parts = parts[1:]
        else:
            base = Path(drive.mount_point)
        p = base.joinpath(*parts) if parts else base
    else:
        p = Path(raw)
        if not p.is_absolute():
            p = cwd / p
    return Path(os.path.normpath(str(p)))


def to_windows_path(path: Path, drives: list[DriveLetter] | None = None) -> str:
    """The familiar spelling of a Linux path: /home/tb/x is C:\\Users\\tb\\x."""
    drives = letters() if drives is None else drives
    s = path.as_posix()
    best: DriveLetter | None = None
    for d in drives:
        if d.mount_point == "/":
            continue
        if s == d.mount_point or s.startswith(d.mount_point.rstrip("/") + "/"):
            if best is None or len(d.mount_point) > len(best.mount_point):
                best = d
    if best is not None:
        rest = s[len(best.mount_point.rstrip("/")) :].strip("/")
        return f"{best.letter}:\\" + rest.replace("/", "\\")
    if s == "/home" or s.startswith("/home/"):
        rest = s[len("/home") :].strip("/")
        return "C:\\Users" + ("\\" + rest.replace("/", "\\") if rest else "")
    return "C:\\" + s.strip("/").replace("/", "\\")
