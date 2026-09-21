# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T031/TB-T073: drive letters are a stable label over real mounts; the Linux path stays true."""
from pathlib import Path

from trier_bridge.system.driveletters import (
    DriveLetter,
    assign,
    read_mounts,
    to_linux_path,
    to_windows_path,
)

# a real mount table shape (the VM's, plus a USB stick and a second data disk)
MOUNTS = [
    ("/", "ext4"),
    ("/boot/efi", "vfat"),
    ("/snap/core22/1380", "squashfs"),
    ("/run/user/1000", "tmpfs"),
    ("/media/tb/CIDATA", "vfat"),
    ("/data", "xfs"),
    ("/media/tb/USB STICK", "exfat"),
]


def test_letters_are_c_then_fixed_then_removable_in_path_order() -> None:
    drives = assign(MOUNTS)
    assert [(d.letter, d.mount_point) for d in drives] == [
        ("C", "/"),
        ("D", "/data"),
        ("E", "/media/tb/CIDATA"),
        ("F", "/media/tb/USB STICK"),
    ]
    assert drives[0].label == "System drive" and drives[3].removable and not drives[1].removable
    # plumbing gets no letter: the EFI partition, snaps, tmpfs
    assert all(d.mount_point not in ("/boot/efi", "/snap/core22/1380") for d in drives)
    assert assign(MOUNTS) == drives  # stable


def test_windows_spellings_resolve_to_real_paths(tmp_path: Path) -> None:
    drives = assign(MOUNTS)
    cwd = Path("/home/tb")
    assert to_linux_path("C:\\", cwd, drives) == Path("/")
    assert to_linux_path("C:\\Users\\tb\\Documents", cwd, drives) == Path("/home/tb/Documents")
    assert to_linux_path("c:/users", cwd, drives) == Path("/home")
    assert to_linux_path("D:\\reports\\q3.txt", cwd, drives) == Path("/data/reports/q3.txt")
    assert to_linux_path("E:", cwd, drives) == Path("/media/tb/CIDATA")
    assert to_linux_path("Documents\\a.txt", cwd, drives) == Path("/home/tb/Documents/a.txt")
    assert to_linux_path("/etc/hostname", cwd, drives) == Path("/etc/hostname")
    assert to_linux_path("..", cwd, drives) == Path("/home")
    try:
        to_linux_path("Q:\\x", cwd, drives)
    except ValueError as exc:
        assert "no drive Q:" in str(exc)
    else:
        raise AssertionError("an unknown letter must be refused")


def test_linux_paths_get_their_familiar_spelling() -> None:
    drives = assign(MOUNTS)
    assert to_windows_path(Path("/home/tb/Documents"), drives) == "C:\\Users\\tb\\Documents"
    assert to_windows_path(Path("/home"), drives) == "C:\\Users"
    assert to_windows_path(Path("/data/reports"), drives) == "D:\\reports"
    assert to_windows_path(Path("/media/tb/USB STICK"), drives) == "F:\\"
    assert to_windows_path(Path("/etc/hostname"), drives) == "C:\\etc\\hostname"
    assert to_windows_path(Path("/"), drives) == "C:\\"


def test_mount_table_parsing_unescapes_spaces(tmp_path: Path) -> None:
    table = tmp_path / "mounts"
    table.write_text(
        "/dev/sda2 / ext4 rw 0 0\n/dev/sdb1 /media/tb/USB\\040STICK exfat rw 0 0\nbad\n",
        encoding="utf-8",
    )
    assert read_mounts(table) == [("/", "ext4"), ("/media/tb/USB STICK", "exfat")]
    assert isinstance(assign(read_mounts(table))[1], DriveLetter)
