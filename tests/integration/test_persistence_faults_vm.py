# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Fault injection for durable state on a real loopback filesystem (IMP-05.06).

Runs only in the project VM (TB-INV-230). The filesystem is a real ext4 image
mounted through the kernel; no mock. sudo is used with a fixed argv only to
mount/unmount the test image, never by the product. TB-T182, TB-T181, TB-T059.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

from trier_bridge.config import StateWriteError, atomic_write_text
from trier_bridge.core.state import OperationState
from trier_bridge.state.journal import OperationJournal
from trier_bridge.state.preferences import Preferences

pytestmark = pytest.mark.integration


def _sudo(*argv: str) -> None:
    subprocess.run(["sudo", "-n", *argv], check=True, capture_output=True)


@pytest.fixture()
def tiny_fs(tmp_path: Path):
    if subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode != 0:
        pytest.skip("needs passwordless sudo in the test VM to mount a loopback image")
    image = tmp_path / "tiny.img"
    with image.open("wb") as fh:
        fh.truncate(4 * 1024 * 1024)
    subprocess.run(["mkfs.ext4", "-q", "-F", str(image)], check=True, capture_output=True)
    mount = tmp_path / "mnt"
    mount.mkdir()
    _sudo("mount", "-o", "loop", str(image), str(mount))
    _sudo("chown", f"{os.getuid()}:{os.getgid()}", str(mount))
    try:
        yield mount
    finally:
        subprocess.run(["sudo", "-n", "umount", str(mount)], capture_output=True)


def test_disk_full_keeps_the_last_known_good_state(tiny_fs: Path) -> None:
    state = tiny_fs / "state"
    state.mkdir()
    prefs = Preferences(state / "prefs.json")
    assert prefs.set("mode", "bridge").durable
    filler = tiny_fs / "filler"
    with filler.open("wb") as fh:  # consume everything the filesystem will give
        for chunk in (65536, 4096, 512, 64, 1):
            try:
                while True:
                    fh.write(b"\0" * chunk)
                    fh.flush()
            except OSError:
                continue
    extra = []
    for i in range(64):  # and every remaining inode/block a new temp file might use
        try:
            f = tiny_fs / f"fill{i}"
            f.write_bytes(b"x" * 4096)
            extra.append(f)
        except OSError:
            break
    res = prefs.set("mode", "native")
    assert not res.durable and "not changed" in res.plain
    assert json.loads((state / "prefs.json").read_text())["mode"] == "bridge"
    assert prefs.get("mode") == "bridge"
    assert [p.name for p in state.iterdir()] == ["prefs.json"]  # no temp file left behind
    filler.unlink()
    for f in extra:
        f.unlink()
    assert prefs.set("mode", "native").durable  # recovers once space returns


def test_read_only_filesystem_is_reported_not_hidden(tiny_fs: Path) -> None:
    j = OperationJournal(tiny_fs / "journal")
    rec = j.open("op", "service.restart", "service", "cups.service", {"name": "cups.service"})
    _sudo("mount", "-o", "remount,ro", str(tiny_fs))
    try:
        with pytest.raises(StateWriteError):
            j.advance(rec, OperationState.PREVIEWED)
        with pytest.raises(StateWriteError):
            atomic_write_text(tiny_fs / "journal" / "x.txt", "x")
    finally:
        _sudo("mount", "-o", "remount,rw", str(tiny_fs))
    again = j.load("op")
    assert again is not None and again.operation_state is OperationState.DRAFT


def test_permission_loss_mid_session(tiny_fs: Path) -> None:
    d = tiny_fs / "journal"
    j = OperationJournal(d)
    rec = j.open("op", "process.terminate", "process", "firefox", {"pid": "1", "start": "2"})
    os.chmod(d, 0o500)
    try:
        with pytest.raises(StateWriteError):
            j.advance(rec, OperationState.PREVIEWED)
    finally:
        os.chmod(d, 0o700)
    assert j.load("op").operation_state is OperationState.DRAFT


def test_process_killed_mid_operation_is_flagged_on_restart(tmp_path: Path) -> None:
    # A real child process opens an operation, advances it to EXECUTING, then dies with SIGKILL.
    code = (
        "import os, sys; sys.path.insert(0, %r)\n"
        "from trier_bridge.state.journal import OperationJournal\n"
        "from trier_bridge.core.state import OperationState\n"
        "from pathlib import Path\n"
        "j = OperationJournal(Path(%r))\n"
        "r = j.open('killed', 'service.restart', 'service', 'ssh.service', {'name': 'ssh.service'})\n"
        "j.advance(r, OperationState.PREVIEWED); j.advance(r, OperationState.AUTHORIZED)\n"
        "j.advance(r, OperationState.EXECUTING)\n"
        "os.kill(os.getpid(), 9)\n"
    ) % (str(Path(__file__).resolve().parents[2]), str(tmp_path / "journal"))
    proc = subprocess.run(["python3", "-c", code], capture_output=True)
    assert proc.returncode == -9
    j = OperationJournal(tmp_path / "journal")
    flagged = j.reconcile_on_start()
    assert [r.operation_id for r in flagged] == ["killed"]
    assert flagged[0].operation_state is OperationState.OUTCOME_UNKNOWN
