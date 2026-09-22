# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T246/TB-T247/TB-T250: /proc/diskstats parsing, whole-disk filtering, real rate deltas."""
import time
from pathlib import Path

from trier_bridge.system.diskio import (
    DiskIoSampler,
    is_whole_disk,
    parse_diskstats,
    whole_disk_name,
)

# Real line shape from tb-ubuntu-desktop-2404's /proc/diskstats (kernel iostats.rst fields).
SDA_LINE = "   8       0 sda 35887 9651 5493202 386767 46226 79211 1629602 148983 0 141070 611038 0 0 0 0 13315 75287"
SDA1_LINE = "   8       1 sda1 100 0 2000 10 0 0 0 0 0 10 10 0 0 0 0 0 0"
LOOP_LINE = "   7       0 loop0 500 0 4000 20 0 0 0 0 0 20 20 0 0 0 0 0 0"
NVME_LINE = "259       0 nvme0n1 9999 0 200000 500 8888 0 300000 600 0 900 1100 0 0 0 0 0 0"
NVME_PART_LINE = "259       1 nvme0n1p1 10 0 20 1 0 0 0 0 0 1 1 0 0 0 0 0 0"


def test_is_whole_disk_matches_the_real_device_naming_rules() -> None:
    assert is_whole_disk("sda") and not is_whole_disk("sda1") and not is_whole_disk("sda15")
    assert is_whole_disk("nvme0n1") and not is_whole_disk("nvme0n1p1")
    assert is_whole_disk("mmcblk0") and not is_whole_disk("mmcblk0p1")
    assert is_whole_disk("sr0")  # optical: no partitions, kept as-is
    assert not is_whole_disk("loop0") and not is_whole_disk("dm-0") and not is_whole_disk("ram0")


def test_parse_diskstats_keeps_only_whole_disks() -> None:
    text = "\n".join([SDA_LINE, SDA1_LINE, LOOP_LINE, NVME_LINE, NVME_PART_LINE])
    stats = parse_diskstats(text)
    names = {s.name for s in stats}
    assert names == {"sda", "nvme0n1"}
    sda = next(s for s in stats if s.name == "sda")
    assert sda.read_sectors == 5493202 and sda.write_sectors == 1629602


def test_whole_disk_name_strips_the_right_partition_suffix() -> None:
    assert whole_disk_name("/dev/sda2") == "sda"
    assert whole_disk_name("/dev/nvme0n1p2") == "nvme0n1"
    assert whole_disk_name("/dev/mmcblk0p1") == "mmcblk0"


def test_disk_io_sampler_real_deltas_on_real_files(tmp_path: Path) -> None:
    proc = tmp_path / "proc"
    proc.mkdir()
    (proc / "diskstats").write_text(SDA_LINE + "\n", encoding="utf-8")
    sampler = DiskIoSampler(proc)

    first = sampler.sample()
    assert len(first) == 1 and first[0].name == "sda"
    assert first[0].read_bytes_per_sec is None and first[0].write_bytes_per_sec is None

    # a real, if brief, delay -- DiskIoSampler needs a measurable dt to compute a rate at all
    time.sleep(0.05)
    grown_line = (
        "   8       0 sda 35900 9651 5495202 386800 46240 79211 "
        "1629702 148990 0 141080 611040 0 0 0 0 13315 75287"
    )
    (proc / "diskstats").write_text(grown_line + "\n", encoding="utf-8")
    second = sampler.sample()
    assert len(second) == 1
    rate = second[0]
    assert rate.read_bytes_per_sec is not None and rate.read_bytes_per_sec > 0
    assert rate.write_bytes_per_sec is not None and rate.write_bytes_per_sec > 0
    # sectors grew by 2000 (read) and 100 (write) * 512 bytes; rate must be proportional
    assert rate.read_bytes_per_sec > rate.write_bytes_per_sec


def test_disk_io_sampler_missing_file_is_unknown_not_zero(tmp_path: Path) -> None:
    sampler = DiskIoSampler(tmp_path / "proc")  # no diskstats file at all
    assert sampler.sample() == []
