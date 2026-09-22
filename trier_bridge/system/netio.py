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
"""Per-adapter throughput from /proc/net/dev (Task Manager Performance tab, read-only).

Loopback is excluded (TB-INV-250) -- never a real adapter a user would
recognize as "Ethernet" or "Wi-Fi". Rates come from the delta between two
samples, the same pattern `DiskIoSampler` uses (TB-INV-246); a first sample
or an interface that disappeared mid-run reports Unknown, never a fabricated
0 (TB-INV-247).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NetStat:
    name: str
    rx_bytes: int
    tx_bytes: int


@dataclass(frozen=True)
class NetRate:
    name: str
    rx_bytes_per_sec: float | None
    tx_bytes_per_sec: float | None


def parse_net_dev(text: str) -> list[NetStat]:
    """/proc/net/dev: "iface: rx_bytes ... (8 fields) tx_bytes ...". Column 1 after the
    colon is rx bytes, column 9 is tx bytes (kernel Documentation/filesystems/proc.rst)."""
    out: list[NetStat] = []
    for line in text.splitlines():
        if ":" not in line:
            continue
        name, _, rest = line.partition(":")
        name = name.strip()
        if not name or name == "lo":
            continue
        fields = rest.split()
        if len(fields) < 9:
            continue
        try:
            out.append(NetStat(name, int(fields[0]), int(fields[8])))
        except (ValueError, IndexError):
            continue
    return out


def read_net_dev(proc: Path = Path("/proc")) -> list[NetStat]:
    try:
        text = (proc / "net" / "dev").read_text(encoding="utf-8")
    except OSError:
        return []
    return parse_net_dev(text)


class NetIoSampler:
    """Stateful: each call to sample() needs the previous one to compute a rate."""

    def __init__(self, proc: Path = Path("/proc")) -> None:
        self._proc = proc
        self._prev: dict[str, NetStat] = {}
        self._prev_time: float | None = None

    def sample(self) -> list[NetRate]:
        now = time.monotonic()
        stats = read_net_dev(self._proc)
        dt = now - self._prev_time if self._prev_time is not None else None
        rates = []
        for s in stats:
            prev = self._prev.get(s.name)
            if prev is not None and dt is not None and dt > 0:
                rx: float | None = max(0.0, (s.rx_bytes - prev.rx_bytes) / dt)
                tx: float | None = max(0.0, (s.tx_bytes - prev.tx_bytes) / dt)
            else:
                rx = None
                tx = None
            rates.append(NetRate(s.name, rx, tx))
        self._prev = {s.name: s for s in stats}
        self._prev_time = now
        return rates
