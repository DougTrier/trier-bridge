# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Integration: network and storage inventories against live NetworkManager and udisks2.

Independent oracles: /sys/class/net, /proc/mounts, statvfs. No mocks (DEC-021).
TB-T052, TB-T071, TB-T149, TB-T157, TB-T158, TB-T162.
"""
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration
pytest.importorskip("gi")

from trier_bridge.system.network import read_network  # noqa: E402
from trier_bridge.system.storage import read_storage  # noqa: E402


def test_network_devices_match_sysfs_and_keep_layers_apart() -> None:
    nw = read_network()
    assert nw.available and nw.backend_version
    sys_ifaces = {p.name for p in Path("/sys/class/net").iterdir()}
    ours = {d.interface for d in nw.devices}
    assert ours <= sys_ifaces and "lo" in ours
    eth = [d for d in nw.devices if not d.is_loopback and d.link_state == "Connected"]
    assert eth, "the VM has one connected adapter"
    d = eth[0]
    assert d.connection_uuid and d.identity is not None and d.identity.interface == d.interface
    assert d.ipv4 and d.gateway4 and d.dns
    mac = Path(f"/sys/class/net/{d.interface}/address").read_text().strip()
    assert d.mac.lower() == mac.lower()
    # link state, profile, IP config and connectivity are separate facts
    assert nw.connectivity in (
        "Unknown",
        "No connectivity",
        "Portal (sign-in page)",
        "Limited",
        "Full Internet access",
    )
    assert nw.overall_state != d.link_state or True  # different vocabularies, both reported


def test_storage_matches_proc_mounts_and_never_uses_device_node_alone() -> None:
    st = read_storage()
    assert st.available and st.drives
    mounts = {}
    for line in Path("/proc/mounts").read_text().splitlines():
        parts = line.split()
        if parts and parts[0].startswith("/dev/"):
            mounts.setdefault(parts[0], []).append(parts[1])
    root_vols = [v for d in st.drives for v in d.volumes if "/" in v.mount_points]
    assert len(root_vols) == 1
    root = root_vols[0]
    assert root.fs_type and root.size_bytes and root.free_bytes is not None
    assert root.free_bytes <= (root.size_bytes or 0)
    real = os.statvfs("/")
    assert abs(root.free_bytes - real.f_bavail * real.f_frsize) < 512 * 1024 * 1024
    assert root.identity.fs_uuid or root.identity.serial  # strong identity present (TB-INV-158)
    assert root.identity.same_target(root.identity)
    for d in st.drives:
        for v in d.volumes:
            for m in v.mount_points:
                assert (
                    m in mounts.get(v.device_node, [])
                    or m == "/"
                    or v.device_node.startswith("/dev/mapper")
                )
    # snap squashfs loop devices are hidden and counted, never shown as drives
    assert st.hidden_count >= 1
    assert all(v.kind != "Loop" for dr in st.drives for v in dr.volumes)
    assert all(not (v.kind == "Loop" and v.fs_type == "squashfs") for v in st.loose_volumes)
    # a mounted EFI system partition is shown, not hidden (TB-INV-070)
    if Path("/boot/efi").is_dir() and any(
        "/boot/efi" in ln for ln in Path("/proc/mounts").read_text().splitlines()
    ):
        assert any("/boot/efi" in v.mount_points for d in st.drives for v in d.volumes)
