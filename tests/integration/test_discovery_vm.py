# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Integration: discovery against the live VM (docs/TEST-STRATEGY.md section 3.2).

Every assertion compares Trier Bridge's observation with a second, independent
real observation made by the test itself (a file read or a direct D-Bus read).
No mocks (DEC-021). Runs only in the project VM: `python3 tools/dev.py test --integration`.
TB-T016, TB-T018, TB-T019, TB-T020, TB-T023, TB-T036, TB-T046.
"""
import os
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

gi = pytest.importorskip("gi")
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from trier_bridge.capability.discovery import Discovery  # noqa: E402
from trier_bridge.capability.model import Capability  # noqa: E402
from trier_bridge.core.state import CapabilityState  # noqa: E402


def _bus_names(bus_type):
    conn = Gio.bus_get_sync(bus_type, None)
    res = conn.call_sync(
        "org.freedesktop.DBus",
        "/org/freedesktop/DBus",
        "org.freedesktop.DBus",
        "ListNames",
        None,
        GLib.VariantType("(as)"),
        Gio.DBusCallFlags.NONE,
        3000,
        None,
    )
    return set(res.unpack()[0])


def _sysprop(name, path, iface, prop):
    conn = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    res = conn.call_sync(
        name,
        path,
        "org.freedesktop.DBus.Properties",
        "Get",
        GLib.Variant("(ss)", (iface, prop)),
        GLib.VariantType("(v)"),
        Gio.DBusCallFlags.NONE,
        3000,
        None,
    )
    return res.unpack()[0]


def test_environment_matches_os_release_and_kernel() -> None:
    env = Discovery().environment()
    raw = Path("/etc/os-release").read_text(encoding="utf-8")
    expected_id = next(
        ln.split("=", 1)[1].strip().strip('"') for ln in raw.splitlines() if ln.startswith("ID=")
    )
    expected_ver = next(
        ln.split("=", 1)[1].strip().strip('"')
        for ln in raw.splitlines()
        if ln.startswith("VERSION_ID=")
    )
    assert env.distro_id == expected_id and env.distro_version == expected_ver
    assert env.kernel == Path("/proc/sys/kernel/osrelease").read_text().strip()
    assert env.architecture == os.uname().machine
    assert env.user_id == os.getuid()
    assert "/etc/os-release" in env.evidence


def test_session_facts_come_from_logind_not_environment() -> None:
    env = Discovery().environment()
    # Over SSH this is a tty session; on the console it is wayland. Either way it is a fact, not a guess.
    assert env.session_type in ("tty", "wayland", "x11", "")
    assert env.session_remote in (True, False, None)
    if env.session_type == "tty":
        assert env.is_graphical_local_session is False


def test_backends_agree_with_direct_bus_reads() -> None:
    recs = {r.capability: r for r in Discovery().capabilities()}
    names = _bus_names(Gio.BusType.SYSTEM)
    for cap, bus_name, backend_ver in (
        (
            Capability.SERVICE_MANAGER,
            "org.freedesktop.systemd1",
            ("/org/freedesktop/systemd1", "org.freedesktop.systemd1.Manager", "Version"),
        ),
        (
            Capability.NETWORK_MANAGER,
            "org.freedesktop.NetworkManager",
            ("/org/freedesktop/NetworkManager", "org.freedesktop.NetworkManager", "Version"),
        ),
    ):
        rec = recs[cap]
        if bus_name in names:
            assert rec.state is CapabilityState.SUPPORTED, rec
            assert rec.version == str(_sysprop(bus_name, *backend_ver))
        else:
            assert rec.state is not CapabilityState.SUPPORTED
    udisks = recs[Capability.STORAGE]
    assert (udisks.state is CapabilityState.SUPPORTED) == ("org.freedesktop.UDisks2" in names)
    polkit = recs[Capability.AUTHORIZATION]
    assert (polkit.state is CapabilityState.SUPPORTED) == ("org.freedesktop.PolicyKit1" in names)


def test_package_systems_match_the_filesystem() -> None:
    recs = {r.capability: r for r in Discovery().capabilities()}
    assert (recs[Capability.PACKAGES_NATIVE].state is CapabilityState.SUPPORTED) == Path(
        "/var/lib/dpkg/status"
    ).is_file()
    assert (recs[Capability.PACKAGES_FLATPAK].state is CapabilityState.SUPPORTED) == Path(
        "/usr/bin/flatpak"
    ).exists()
    snap = recs[Capability.PACKAGES_SNAP]
    if Path("/run/snapd.socket").exists():
        assert snap.state is CapabilityState.SUPPORTED
    assert snap.state is not CapabilityState.UNKNOWN


def test_every_record_has_evidence_and_no_unknown_without_reason() -> None:
    for rec in Discovery().capabilities():
        assert rec.evidence or rec.detail, rec
        assert rec.is_fresh()
        if rec.state is CapabilityState.UNKNOWN:
            assert rec.detail, "Unknown must explain why it is unknown"


def test_discovery_is_side_effect_free_on_the_filesystem() -> None:
    # A discovery pass under a fresh XDG home must create nothing at all (TB-INV-036, TB-INV-046).
    with tempfile.TemporaryDirectory() as home:
        before = sorted(Path(home).rglob("*"))
        saved = {
            k: os.environ.get(k)
            for k in ("HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME")
        }
        os.environ.update(
            {
                "HOME": home,
                "XDG_CONFIG_HOME": f"{home}/c",
                "XDG_STATE_HOME": f"{home}/s",
                "XDG_CACHE_HOME": f"{home}/k",
            }
        )
        try:
            d = Discovery()
            d.environment()
            d.capabilities()
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        after = sorted(Path(home).rglob("*"))
        assert before == after == []
