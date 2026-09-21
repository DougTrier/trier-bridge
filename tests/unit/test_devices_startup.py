# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T173/TB-T175 (devices) and startup parsing, on real files in a temp tree."""
from pathlib import Path

import pytest

from trier_bridge.system.startup import parse_autostart, read_startup

gi = pytest.importorskip("gi")

from trier_bridge.system.devices import (  # noqa: E402
    Category,
    IdDatabase,
    clean,
    pci_category,
    usb_category,
)


def test_clean_truncates_and_strips_control_chars() -> None:
    assert clean("Evil\x1b[31m Device\x00 name") == "Evil[31m Device name"
    assert len(clean("x" * 500)) == 80


def test_pci_and_usb_categories() -> None:
    assert pci_category("030000") is Category.DISPLAY
    assert pci_category("020000") is Category.NETWORK
    assert pci_category("0c0330") is Category.USB_CONTROLLER
    assert pci_category("060400") is Category.SYSTEM
    assert pci_category("zz") is Category.OTHER
    assert usb_category("09", "hub") is Category.USB_CONTROLLER
    assert usb_category("00", "Gaming Mouse") is Category.INPUT
    assert usb_category("e0", "") is Category.BLUETOOTH
    assert usb_category("00", "Widget") is Category.USB_DEVICE


def test_id_database_parses_hwdata_format(tmp_path: Path) -> None:
    ids = tmp_path / "pci.ids"
    ids.write_text(
        "# comment\n1234  Acme Corp\n\t5678  Acme Widget\n\t\t0001 0002  subsystem\n8086  Intel Corporation\n",
        encoding="utf-8",
    )
    db = IdDatabase((str(tmp_path / "missing"), str(ids)))
    assert db.source == str(ids)
    assert db.name("1234", "5678") == ("Acme Corp", "Acme Widget")
    assert db.name("8086", "ffff") == ("Intel Corporation", "")
    assert IdDatabase(("/nonexistent/pci.ids",)).name("1234", "5678") == ("", "")


def test_autostart_entries_and_overrides(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".config" / "autostart").mkdir(parents=True)
    (tmp_path / "etc-xdg" / "autostart").mkdir(parents=True)
    (tmp_path / "etc-xdg" / "autostart" / "update-notifier.desktop").write_text(
        "[Desktop Entry]\nName=Update Notifier\nExec=update-notifier\nComment=Checks for updates\n",
        encoding="utf-8",
    )
    (tmp_path / "etc-xdg" / "autostart" / "broken.desktop").write_text(
        "not a desktop file", encoding="utf-8"
    )
    (home / ".config" / "autostart" / "update-notifier.desktop").write_text(
        "[Desktop Entry]\nName=Update Notifier\nExec=update-notifier\nX-GNOME-Autostart-enabled=false\n",
        encoding="utf-8",
    )
    (home / ".config" / "autostart" / "mine.desktop").write_text(
        "[Desktop Entry]\nName=My Tool\nExec=/home/tb/tool\nHidden=true\n", encoding="utf-8"
    )
    entries = read_startup(home, (tmp_path / "etc-xdg",))
    by = {(e.name, e.mechanism): e for e in entries}
    assert by[("Update Notifier", "Autostart (this user)")].enabled is False
    assert by[("Update Notifier", "Autostart (all users)")].overridden_by_user is True
    assert by[("My Tool", "Autostart (this user)")].enabled is False  # Hidden=true
    assert ("broken", "Autostart (all users)") not in by
    assert parse_autostart(tmp_path / "etc-xdg" / "autostart" / "broken.desktop") is None
