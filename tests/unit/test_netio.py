# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T246/TB-T247/TB-T250: /proc/net/dev parsing, loopback excluded, real rate deltas."""
import time
from pathlib import Path

from trier_bridge.system.netio import NetIoSampler, parse_net_dev

HEADER = (
    "Inter-|   Receive                                                |  Transmit\n"
    " face |bytes    packets errs drop fifo frame compressed multicast|"
    "bytes    packets errs drop fifo colls carrier compressed\n"
)
# Real shape from tb-ubuntu-desktop-2404's /proc/net/dev (rx bytes field 1, tx bytes field 9).
LO_LINE = "    lo: 1234567      10    0    0    0     0          0         0  1234567      10    0    0    0     0       0          0\n"
ETH0_LINE = "  eth0: 62640445  19286    0    0    0     0          0         0  1660606    9497    0    0    0     0       0          0\n"


def test_parse_net_dev_excludes_loopback() -> None:
    stats = parse_net_dev(HEADER + LO_LINE + ETH0_LINE)
    names = {s.name for s in stats}
    assert names == {"eth0"}
    eth0 = stats[0]
    assert eth0.rx_bytes == 62640445 and eth0.tx_bytes == 1660606


def test_net_io_sampler_real_deltas_on_real_files(tmp_path: Path) -> None:
    proc = tmp_path / "proc"
    (proc / "net").mkdir(parents=True)
    (proc / "net" / "dev").write_text(HEADER + LO_LINE + ETH0_LINE, encoding="utf-8")
    sampler = NetIoSampler(proc)

    first = sampler.sample()
    assert len(first) == 1 and first[0].name == "eth0"
    assert first[0].rx_bytes_per_sec is None and first[0].tx_bytes_per_sec is None

    # a real, if brief, delay -- NetIoSampler needs a measurable dt to compute a rate at all
    time.sleep(0.05)
    grown = (
        "  eth0: 62650445  19300    0    0    0     0          0         0"
        "  1662606    9500    0    0    0     0       0          0\n"
    )
    (proc / "net" / "dev").write_text(HEADER + LO_LINE + grown, encoding="utf-8")
    second = sampler.sample()
    rate = second[0]
    assert rate.rx_bytes_per_sec is not None and rate.rx_bytes_per_sec > 0
    assert rate.tx_bytes_per_sec is not None and rate.tx_bytes_per_sec > 0
    assert rate.rx_bytes_per_sec > rate.tx_bytes_per_sec  # 10000 bytes rx growth vs 2000 tx


def test_net_io_sampler_missing_file_is_unknown_not_zero(tmp_path: Path) -> None:
    sampler = NetIoSampler(tmp_path / "proc")  # no net/dev file at all
    assert sampler.sample() == []
