# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Integration: the journal reader against the live journal, cross-checked with journalctl.

journalctl is invoked here only as an independent oracle for the test
(fixed argv, no shell); the product never runs it. TB-T145, TB-T146.
"""
import json
import subprocess

import pytest

from trier_bridge.system.journal import JournalReader, journal_access

pytestmark = pytest.mark.integration


def test_access_matches_group_membership() -> None:
    acc = journal_access()
    assert acc.available
    groups = subprocess.run(
        ["id", "-Gn"], capture_output=True, text=True, check=True
    ).stdout.split()
    assert acc.system_readable == bool({"adm", "systemd-journal"} & set(groups))


def test_newest_entries_agree_with_journalctl() -> None:
    reader = JournalReader()
    assert reader.available
    ours = reader.newest(limit=50)
    assert 0 < len(ours) <= 50
    assert ours[0].realtime_usec >= ours[-1].realtime_usec  # newest first
    theirs = subprocess.run(
        ["journalctl", "-o", "json", "-n", "50", "--no-pager", "-q"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    their_msgs = {json.loads(ln).get("MESSAGE", "") for ln in theirs if ln.strip()}
    their_msgs = {m if isinstance(m, str) else "" for m in their_msgs}
    overlap = sum(1 for e in ours if e.message in their_msgs)
    assert overlap >= 25, f"only {overlap} of 50 messages matched journalctl"
    for e in ours:
        assert "\x1b" not in e.message and "\n" not in e.message
        assert e.source and e.level


def test_cancellation_stops_early() -> None:
    reader = JournalReader()
    reader.cancel.set()
    assert reader.newest(limit=100) == []
