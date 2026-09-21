# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T049/TB-T050/TB-T051/TB-T052/TB-T158/TB-T165: stable identities detect replaced targets."""
from trier_bridge.core.identity import (
    BlockDeviceIdentity,
    ConnectionIdentity,
    PackageIdentity,
    ProcessIdentity,
    StableIdentity,
    UnitIdentity,
)


def test_process_pid_reuse_is_a_different_target() -> None:
    before = ProcessIdentity(pid=4271, start_ticks=1000, uid=1000, comm="firefox")
    reused = ProcessIdentity(pid=4271, start_ticks=2000, uid=1000, comm="bash")
    assert not before.same_target(reused)
    assert before.same_target(ProcessIdentity(pid=4271, start_ticks=1000, uid=1000))
    assert isinstance(before, StableIdentity)
    assert "4271" in before.label()


def test_unit_replaced_fragment_is_a_different_target() -> None:
    a = UnitIdentity(
        "ssh.service",
        "/org/freedesktop/systemd1/unit/ssh_2eservice",
        "loaded",
        "/usr/lib/systemd/system/ssh.service",
    )
    b = UnitIdentity(
        "ssh.service",
        "/org/freedesktop/systemd1/unit/ssh_2eservice",
        "loaded",
        "/etc/systemd/system/ssh.service",
    )
    assert not a.same_target(b)
    assert a.same_target(UnitIdentity(a.name, a.object_path, "loaded", a.fragment_path))


def test_connection_version_change_requires_reconfirmation() -> None:
    a = ConnectionIdentity(uuid="abc-123", interface="eth0", version=3)
    assert not a.same_target(ConnectionIdentity(uuid="abc-123", interface="eth0", version=4))
    assert a.same_target(ConnectionIdentity(uuid="abc-123", interface="eth0", version=3))


def test_block_device_never_matches_on_device_node_alone() -> None:
    weak = BlockDeviceIdentity(
        object_path="/org/freedesktop/UDisks2/block_devices/sdb", device_node="/dev/sdb"
    )
    assert not weak.same_target(
        weak
    )  # no strong identifier -> refuse to claim sameness (TB-INV-158)
    strong = BlockDeviceIdentity(
        "/org/freedesktop/UDisks2/block_devices/sdb",
        drive_id="Msft-Virtual-Disk-6002",
        serial="6002",
        size=64 << 20,
    )
    assert strong.same_target(
        BlockDeviceIdentity(
            "/org/freedesktop/UDisks2/block_devices/sdb",
            drive_id="Msft-Virtual-Disk-6002",
            serial="6002",
            size=64 << 20,
        )
    )
    swapped = BlockDeviceIdentity(
        "/org/freedesktop/UDisks2/block_devices/sdb",
        drive_id="Other-Disk-9999",
        serial="9999",
        size=64 << 20,
    )
    assert not strong.same_target(swapped)


def test_same_package_name_across_systems_is_not_the_same_package() -> None:
    apt = PackageIdentity(
        system="apt", name="firefox", version="1.0", arch="amd64", source="ubuntu"
    )
    snap = PackageIdentity(
        system="snap", name="firefox", version="1.0", arch="amd64", source="snapstore"
    )
    assert not apt.same_target(snap)
    assert apt.label() == "firefox (apt)"
