# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Integration: the process sampler against the live /proc of the VM.

Compares Trier Bridge's sample with independent reads of the same files.
No mocks (DEC-021). TB-T050, TB-T131, TB-T132, TB-T136.
"""
import os
import time
from pathlib import Path

import pytest

from trier_bridge.system.processes import ProcessKind, ProcessSampler, is_still_same

pytestmark = pytest.mark.integration


def test_sampler_sees_this_process_with_the_kernel_identity() -> None:
    s = ProcessSampler()
    rows, totals = s.sample()
    me = next(r for r in rows if r.identity.pid == os.getpid())
    stat = Path("/proc/self/stat").read_text()
    start = int(stat.rsplit(")", 1)[1].split()[19])
    assert me.identity.start_ticks == start and me.identity.uid == os.getuid()
    assert me.kind is ProcessKind.USER and me.readable
    assert me.rss_bytes is not None and me.rss_bytes > 0
    assert is_still_same(me.identity)
    assert totals.cpu_count == os.cpu_count()
    assert totals.mem_total_bytes is not None and totals.mem_total_bytes > 0


def test_pid_one_and_kernel_threads_are_never_actionable() -> None:
    rows, _ = ProcessSampler().sample()
    by_pid = {r.identity.pid: r for r in rows}
    assert by_pid[1].kind is ProcessKind.CRITICAL and not by_pid[1].kind.actionable_by_user
    kernel = [r for r in rows if r.kind is ProcessKind.KERNEL]
    assert kernel, "kernel threads exist on any Linux system"
    assert all(r.cmdline == "" for r in kernel)


def test_cpu_percent_is_unknown_first_then_measured() -> None:
    s = ProcessSampler()
    rows, _ = s.sample()
    assert all(r.cpu_percent is None for r in rows)
    time.sleep(0.5)
    rows, _ = s.sample()
    measured = [r for r in rows if r.cpu_percent is not None]
    assert measured, "processes seen twice get a real percentage"
    assert all(0.0 <= r.cpu_percent <= 100.0 * s.cpu_count for r in measured)


def test_root_processes_report_unknown_where_not_readable() -> None:
    rows, _ = ProcessSampler().sample()
    system = [r for r in rows if r.kind is ProcessKind.SYSTEM]
    assert system
    for r in system:
        # /proc/PID/stat is world-readable, so memory is known; cmdline may or may not be
        assert r.rss_bytes is not None or not r.readable
