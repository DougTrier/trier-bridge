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
"""Process observation from procfs (Task Manager data, read-only).

SECURITY: reads /proc only; respects native visibility (a process whose files
cannot be read is reported with what is readable and Unknown elsewhere,
TB-INV-132). Command lines are read but the UI decides how much to show
(TB-INV-133). No signals are sent from this module.
IDENTITY: every row carries PID plus start time so a reused PID is a different
target (TB-INV-050). Kernel threads and PID 1 are classified as system-critical
(TB-INV-136).
RESOURCES: CPU percentages need two samples; the sampler keeps the previous
tick table and computes deltas, so cost is one pass per refresh (TB-INV-199).
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from enum import Enum, unique
from pathlib import Path

from ..capability.facts import parse_proc_stat_starttime
from ..core.identity import ProcessIdentity


@unique
class ProcessKind(Enum):
    APP = "app"  # has a graphical window or a desktop entry (best effort)
    USER = "user"  # this user's ordinary process
    OTHER_USER = "other-user"
    SYSTEM = "system"  # root-owned service or daemon
    KERNEL = "kernel"  # kernel thread; never actionable
    CRITICAL = "critical"  # PID 1 and the init family; never actionable

    @property
    def actionable_by_user(self) -> bool:
        return self in (ProcessKind.APP, ProcessKind.USER)


@dataclass(frozen=True)
class ProcessSample:
    identity: ProcessIdentity
    name: str
    state: str
    ppid: int
    uid: int
    user: str
    cmdline: str  # possibly empty (kernel threads) or unreadable (empty, with readable=False)
    rss_bytes: int | None  # None = Unknown, never 0 (TB-INV-131)
    cpu_ticks: int  # utime + stime at sample time
    threads: int | None
    kind: ProcessKind
    readable: bool  # False when /proc/PID/status could not be read (native visibility)
    cpu_percent: float | None = None  # None until two samples exist


@dataclass
class SystemTotals:
    cpu_ticks_total: int | None
    cpu_count: int
    mem_total_bytes: int | None
    mem_available_bytes: int | None
    load1: float | None
    uptime_seconds: float | None


def parse_stat_fields(stat_text: str) -> dict[str, int | str] | None:
    """Parse /proc/PID/stat robustly (comm may contain spaces and parentheses)."""
    try:
        head, _, tail = stat_text.rpartition(")")
        pid_str, _, comm = head.partition("(")
        f = tail.split()
        return {
            "pid": int(pid_str),
            "comm": comm,
            "state": f[0],
            "ppid": int(f[1]),
            "utime": int(f[11]),
            "stime": int(f[12]),
            "num_threads": int(f[17]),
            "starttime": int(f[19]),
            "rss_pages": int(f[21]),
        }
    except (ValueError, IndexError):
        return None


def parse_status_uid(status_text: str) -> int | None:
    for line in status_text.splitlines():
        if line.startswith("Uid:"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except ValueError:
                    return None
    return None


def parse_meminfo(text: str) -> tuple[int | None, int | None]:
    total = avail = None
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            total = _kb(line)
        elif line.startswith("MemAvailable:"):
            avail = _kb(line)
    return total, avail


def _kb(line: str) -> int | None:
    parts = line.split()
    try:
        return int(parts[1]) * 1024
    except (IndexError, ValueError):
        return None


def parse_cpu_total(stat_text: str) -> int | None:
    for line in stat_text.splitlines():
        if line.startswith("cpu "):
            try:
                return sum(int(x) for x in line.split()[1:])
            except ValueError:
                return None
    return None


def classify(pid: int, ppid: int, uid: int, my_uid: int, cmdline: str, comm: str) -> ProcessKind:
    if pid in (1, 2) or ppid == 2 or (cmdline == "" and uid == 0):
        return ProcessKind.CRITICAL if pid == 1 else ProcessKind.KERNEL
    if uid == my_uid:
        return ProcessKind.USER
    if uid == 0:
        return ProcessKind.SYSTEM
    return ProcessKind.OTHER_USER


class ProcessSampler:
    """Takes successive samples; CPU percent is computed from the previous sample."""

    def __init__(self, proc: Path = Path("/proc")) -> None:
        self.proc = proc
        self._prev_ticks: dict[tuple[int, int], int] = {}
        self._prev_total: int | None = None
        self._prev_time = 0.0
        self.cpu_count = os.cpu_count() or 1
        self._users: dict[int, str] = {}

    def _user_name(self, uid: int) -> str:
        if uid not in self._users:
            try:
                import pwd

                self._users[uid] = pwd.getpwuid(uid).pw_name
            except (KeyError, ImportError):
                self._users[uid] = str(uid)
        return self._users[uid]

    def totals(self) -> SystemTotals:
        cpu_total = mem_total = mem_avail = None
        load1 = uptime = None
        try:
            cpu_total = parse_cpu_total((self.proc / "stat").read_text(encoding="utf-8"))
        except OSError:
            pass
        try:
            mem_total, mem_avail = parse_meminfo(
                (self.proc / "meminfo").read_text(encoding="utf-8")
            )
        except OSError:
            pass
        try:
            load1 = float((self.proc / "loadavg").read_text(encoding="utf-8").split()[0])
        except (OSError, ValueError, IndexError):
            pass
        try:
            uptime = float((self.proc / "uptime").read_text(encoding="utf-8").split()[0])
        except (OSError, ValueError, IndexError):
            pass
        return SystemTotals(cpu_total, self.cpu_count, mem_total, mem_avail, load1, uptime)

    def sample(self) -> tuple[list[ProcessSample], SystemTotals]:
        my_uid = os.getuid() if hasattr(os, "getuid") else -1
        page = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096
        totals = self.totals()
        now = time.monotonic()
        rows: list[ProcessSample] = []
        new_ticks: dict[tuple[int, int], int] = {}
        try:
            entries = [e for e in os.listdir(self.proc) if e.isdigit()]
        except OSError:
            return [], totals
        for entry in entries:
            pid = int(entry)
            pdir = self.proc / entry
            try:
                stat = parse_stat_fields(
                    (pdir / "stat").read_text(encoding="utf-8", errors="replace")
                )
            except OSError:
                continue  # exited between listdir and read; not an error
            if stat is None:
                continue
            readable = True
            uid: int | None = None
            try:
                uid = parse_status_uid(
                    (pdir / "status").read_text(encoding="utf-8", errors="replace")
                )
            except OSError:
                readable = False
            if uid is None:
                try:
                    uid = pdir.stat().st_uid
                except OSError:
                    uid = -1
            cmdline = ""
            try:
                raw = (pdir / "cmdline").read_bytes()
                cmdline = raw.replace(b"\x00", b" ").decode("utf-8", "replace").strip()
            except OSError:
                readable = False
            comm = str(stat["comm"])
            ppid = int(stat["ppid"])
            ticks = int(stat["utime"]) + int(stat["stime"])
            start = int(stat["starttime"])
            key = (pid, start)
            new_ticks[key] = ticks
            cpu_pct: float | None = None
            if (
                self._prev_total is not None
                and totals.cpu_ticks_total is not None
                and key in self._prev_ticks
            ):
                dt = totals.cpu_ticks_total - self._prev_total
                if dt > 0:
                    cpu_pct = 100.0 * (ticks - self._prev_ticks[key]) / dt * self.cpu_count
            rss_pages = int(stat["rss_pages"])
            rows.append(
                ProcessSample(
                    identity=ProcessIdentity(pid=pid, start_ticks=start, uid=uid, comm=comm),
                    name=comm,
                    state=str(stat["state"]),
                    ppid=ppid,
                    uid=uid,
                    user=self._user_name(uid) if uid >= 0 else "Unknown",
                    cmdline=cmdline,
                    rss_bytes=rss_pages * page if readable else None,
                    cpu_ticks=ticks,
                    threads=int(stat["num_threads"]) if readable else None,
                    kind=classify(pid, ppid, uid, my_uid, cmdline, comm),
                    readable=readable,
                    cpu_percent=cpu_pct,
                )
            )
        self._prev_ticks = new_ticks
        self._prev_total = totals.cpu_ticks_total
        self._prev_time = now
        return rows, totals


def has_ended(identity: ProcessIdentity, proc: Path = Path("/proc")) -> bool:
    """True when the process is gone or is a zombie (exited, not yet reaped by its parent)."""
    try:
        text = (proc / str(identity.pid) / "stat").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return True
    fields = parse_stat_fields(text)
    if fields is None or int(fields["starttime"]) != identity.start_ticks:
        return True
    return str(fields["state"]) in ("Z", "X")


def is_still_same(identity: ProcessIdentity, proc: Path = Path("/proc")) -> bool:
    """Revalidate immediately before any action: same PID and same start time (TB-INV-050)."""
    try:
        text = (proc / str(identity.pid) / "stat").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    start = parse_proc_stat_starttime(text)
    return start is not None and start == identity.start_ticks
