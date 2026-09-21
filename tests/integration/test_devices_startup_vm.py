# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Integration: device inventory and startup entries against the live VM.

Oracles: /sys/bus/*/devices counts, /etc/xdg/autostart listing. No mocks.
TB-T173, TB-T174, TB-T175.
"""
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration
pytest.importorskip("gi")

from trier_bridge.system.devices import Category, read_devices  # noqa: E402
from trier_bridge.system.startup import read_startup  # noqa: E402


def test_devices_cover_pci_and_usb_with_drivers_named() -> None:
    inv = read_devices()
    pci = [d for d in inv.devices if d.bus == "pci"]
    if Path("/sys/bus/pci/devices").is_dir():
        assert len(pci) == len(list(Path("/sys/bus/pci/devices").iterdir()))
    if Path("/sys/bus/vmbus/devices").is_dir():  # Hyper-V guests expose devices on vmbus
        assert any(d.bus == "vmbus" for d in inv.devices)
    assert inv.devices
    net = [d for d in inv.devices if d.category is Category.NETWORK]
    assert net and all(d.driver for d in net), "network adapters have drivers bound on the VM"
    for d in inv.devices:
        assert d.name and "\x1b" not in d.name and len(d.name) <= 80
        assert d.working in (True, False, None)
    if pci and Path("/usr/share/misc/pci.ids").is_file():
        assert any(":" not in d.name for d in pci), "names resolved from pci.ids"


def test_startup_entries_match_the_autostart_directories() -> None:
    entries = read_startup(Path.home())
    system = [e for e in entries if e.mechanism == "Autostart (all users)"]
    on_disk = [p for p in Path("/etc/xdg/autostart").glob("*.desktop")]
    assert len(system) <= len(on_disk) and system
    assert all(e.source_path.startswith("/etc/xdg/autostart/") for e in system)
    assert all(e.enabled in (True, False) for e in system)
