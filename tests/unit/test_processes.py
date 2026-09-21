# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T050/TB-T131/TB-T136: procfs parsing on real text, identity, and classification."""
from pathlib import Path

from trier_bridge.core.identity import ProcessIdentity
from trier_bridge.system.processes import (
    ProcessKind,
    ProcessSampler,
    classify,
    is_still_same,
    parse_cpu_total,
    parse_meminfo,
    parse_stat_fields,
    parse_status_uid,
)

STAT = "4271 (Web Content) S 1200 4271 4271 0 -1 4194560 100 0 0 0 5 3 0 0 20 0 30 0 296737 123456789 2048 18446744073709551615 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20"


def test_stat_parses_comm_with_spaces_and_parens() -> None:
    f = parse_stat_fields("77 (a (weird) name) R 1 " + " ".join(str(i) for i in range(50)))
    assert f is not None and f["comm"] == "a (weird) name" and f["ppid"] == 1
    f = parse_stat_fields(STAT)
    assert f is not None
    assert f["pid"] == 4271 and f["comm"] == "Web Content" and f["state"] == "S"
    assert f["utime"] == 5 and f["stime"] == 3 and f["num_threads"] == 30
    assert f["starttime"] == 296737 and f["rss_pages"] == 2048
    assert parse_stat_fields("garbage") is None


def test_status_uid_and_meminfo_and_cpu_total() -> None:
    assert parse_status_uid("Name:\tbash\nUid:\t1000\t1000\t1000\t1000\nGid:\t1000\n") == 1000
    assert parse_status_uid("Name:\tx\n") is None
    total, avail = parse_meminfo(
        "MemTotal:        8123456 kB\nMemFree: 1 kB\nMemAvailable:    4000000 kB\n"
    )
    assert total == 8123456 * 1024 and avail == 4000000 * 1024
    assert parse_meminfo("") == (None, None)  # Unknown, not zero (TB-INV-131)
    assert parse_cpu_total("cpu  10 20 30 40 50 0 0 0 0 0\ncpu0 1 2 3\n") == 150
    assert parse_cpu_total("nothing") is None


def test_classification_protects_system_processes() -> None:
    assert classify(1, 0, 0, 1000, "/sbin/init", "systemd") is ProcessKind.CRITICAL
    assert classify(2, 0, 0, 1000, "", "kthreadd") is ProcessKind.KERNEL
    assert classify(300, 2, 0, 1000, "", "kworker/0:1") is ProcessKind.KERNEL
    assert classify(900, 1, 0, 1000, "/usr/sbin/cupsd", "cupsd") is ProcessKind.SYSTEM
    assert classify(4271, 1200, 1000, 1000, "/usr/bin/firefox", "firefox") is ProcessKind.USER
    assert classify(5000, 1, 1001, 1000, "/bin/bash", "bash") is ProcessKind.OTHER_USER
    assert not ProcessKind.KERNEL.actionable_by_user and not ProcessKind.CRITICAL.actionable_by_user
    assert ProcessKind.USER.actionable_by_user


def test_sampler_on_a_synthetic_proc_tree_built_from_real_files(tmp_path: Path) -> None:
    # A real directory tree shaped like procfs; every file is a real file the sampler reads.
    proc = tmp_path / "proc"
    (proc / "4271").mkdir(parents=True)
    (proc / "4271" / "stat").write_text(STAT, encoding="utf-8")
    (proc / "4271" / "status").write_text("Uid:\t1000\t1000\t1000\t1000\n", encoding="utf-8")
    (proc / "4271" / "cmdline").write_bytes(b"/usr/lib/firefox/firefox\x00-contentproc\x00")
    (proc / "stat").write_text("cpu  100 0 100 800 0 0 0 0 0 0\n", encoding="utf-8")
    (proc / "meminfo").write_text("MemTotal: 1000 kB\nMemAvailable: 500 kB\n", encoding="utf-8")
    (proc / "loadavg").write_text("0.50 0.40 0.30 1/200 999\n", encoding="utf-8")
    (proc / "uptime").write_text("1234.5 5000.0\n", encoding="utf-8")
    s = ProcessSampler(proc)
    rows, totals = s.sample()
    assert len(rows) == 1 and rows[0].cpu_percent is None  # first sample: unknown, not zero
    assert rows[0].identity == ProcessIdentity(
        pid=4271, start_ticks=296737, uid=1000, comm="Web Content"
    )
    assert rows[0].cmdline == "/usr/lib/firefox/firefox -contentproc"
    assert totals.mem_total_bytes == 1000 * 1024 and totals.load1 == 0.5
    # second sample: process used 8 more ticks while the system advanced 100
    (proc / "4271" / "stat").write_text(
        STAT.replace(" 5 3 0 0 20", " 10 6 0 0 20"), encoding="utf-8"
    )
    (proc / "stat").write_text("cpu  150 0 150 800 0 0 0 0 0 0\n", encoding="utf-8")
    rows, _ = s.sample()
    assert rows[0].cpu_percent is not None and abs(rows[0].cpu_percent - 8.0 * s.cpu_count) < 1e-6
    # PID reuse: same PID, different start time -> identity differs and revalidation fails
    assert is_still_same(rows[0].identity, proc)
    (proc / "4271" / "stat").write_text(STAT.replace(" 296737 ", " 999999 "), encoding="utf-8")
    assert not is_still_same(rows[0].identity, proc)
    rows, _ = s.sample()
    assert rows[0].cpu_percent is None  # new identity has no previous sample


def test_unreadable_process_reports_unknown_not_zero(tmp_path: Path) -> None:
    proc = tmp_path / "proc"
    (proc / "77").mkdir(parents=True)
    (proc / "77" / "stat").write_text(
        "77 (secret) S 1 " + " ".join(str(i) for i in range(50)), encoding="utf-8"
    )
    # no status, no cmdline: like another user's process under hidepid
    rows, _ = ProcessSampler(proc).sample()
    assert len(rows) == 1
    assert rows[0].readable is False and rows[0].rss_bytes is None and rows[0].threads is None
