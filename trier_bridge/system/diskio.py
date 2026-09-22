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
"""Per-disk throughput from /proc/diskstats (Task Manager Performance tab, read-only).

Whole physical disks only (sda, nvme0n1, ...), never partitions -- matches how
real Windows Task Manager graphs "Disk 0" as the whole device, not each
partition separately. Loop devices (snap squashfs mounts), RAM disks, and
device-mapper nodes are excluded, the same kind of filter `storage.py`
already applies to its own inventory (TB-INV-250). Rates come from the delta
between two samples, the same pattern `ProcessSampler` already uses for CPU%
(TB-INV-246); a first sample has no rate yet and reports Unknown, never a
fabricated 0 (TB-INV-247).

Drive-letter labeling ("Disk 0 (C:)") is a display convenience built from the
existing `storage.py`/`driveletters.py` data, resolved from a real device path
-- never the other way around (TB-INV-249).
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

SECTOR_BYTES = 512
_EXCLUDED_PREFIXES = ("loop", "ram", "zram", "dm-")
_TRAILING_PART_NUM = re.compile(r"\d+$")
_TRAILING_NVME_PART = re.compile(r"p\d+$")


@dataclass(frozen=True)
class DiskStat:
    name: str  # "sda", "nvme0n1", "sr0", ...
    read_sectors: int
    write_sectors: int


@dataclass(frozen=True)
class DiskRate:
    name: str
    read_bytes_per_sec: float | None  # None = Unknown (first sample, or read failed)
    write_bytes_per_sec: float | None


def is_whole_disk(name: str) -> bool:
    """True for a whole physical disk name; false for a partition or pseudo-device."""
    if name.startswith(_EXCLUDED_PREFIXES):
        return False
    if name.startswith("nvme"):
        return not _TRAILING_NVME_PART.search(name)
    if name.startswith("mmcblk"):
        return not _TRAILING_NVME_PART.search(name)
    if name.startswith(("sd", "hd", "vd")):
        return not _TRAILING_PART_NUM.search(name)
    return True  # sr0 (optical), fd0 (floppy): no partitions, keep as-is


def parse_diskstats(text: str) -> list[DiskStat]:
    """/proc/diskstats: field 3 is the device name, field 6 read sectors, field 10 write
    sectors (kernel Documentation/admin-guide/iostats.rst), 1-indexed."""
    out: list[DiskStat] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 14:
            continue
        name = parts[2]
        if not is_whole_disk(name):
            continue
        try:
            out.append(DiskStat(name, int(parts[5]), int(parts[9])))
        except (ValueError, IndexError):
            continue
    return out


def read_diskstats(proc: Path = Path("/proc")) -> list[DiskStat]:
    try:
        text = (proc / "diskstats").read_text(encoding="utf-8")
    except OSError:
        return []
    return parse_diskstats(text)


def whole_disk_name(device_node: str) -> str:
    """/dev/sda2 -> sda; /dev/nvme0n1p2 -> nvme0n1; /dev/mmcblk0p1 -> mmcblk0."""
    name = device_node.removeprefix("/dev/")
    if name.startswith("nvme") or name.startswith("mmcblk"):
        return _TRAILING_NVME_PART.sub("", name)
    return _TRAILING_PART_NUM.sub("", name)


def disk_drive_letters() -> dict[str, list[str]]:
    """Real drive-letter aliases (TB-INV-249) per whole-disk name, resolved from the same
    live udisks2 + mount data the Disk Management page already reads -- not re-derived
    from /proc/mounts by hand, so there is exactly one source of truth for the mapping."""
    from .driveletters import letters
    from .storage import read_storage

    by_mount = {d.mount_point: d.display for d in letters()}
    result: dict[str, list[str]] = {}
    overview = read_storage()
    if not overview.available:
        return result
    for drive in overview.drives:
        for vol in drive.volumes:
            for mp in vol.mount_points:
                display = by_mount.get(mp)
                if display:
                    result.setdefault(whole_disk_name(vol.device_node), []).append(display)
    return result


class DiskIoSampler:
    """Stateful: each call to sample() needs the previous one to compute a rate."""

    def __init__(self, proc: Path = Path("/proc")) -> None:
        self._proc = proc
        self._prev: dict[str, DiskStat] = {}
        self._prev_time: float | None = None

    def sample(self) -> list[DiskRate]:
        now = time.monotonic()
        stats = read_diskstats(self._proc)
        dt = now - self._prev_time if self._prev_time is not None else None
        rates = []
        for s in stats:
            prev = self._prev.get(s.name)
            if prev is not None and dt is not None and dt > 0:
                read_bps: float | None = max(
                    0.0, (s.read_sectors - prev.read_sectors) * SECTOR_BYTES / dt
                )
                write_bps: float | None = max(
                    0.0, (s.write_sectors - prev.write_sectors) * SECTOR_BYTES / dt
                )
            else:
                read_bps = None
                write_bps = None
            rates.append(DiskRate(s.name, read_bps, write_bps))
        self._prev = {s.name: s for s in stats}
        self._prev_time = now
        return rates
