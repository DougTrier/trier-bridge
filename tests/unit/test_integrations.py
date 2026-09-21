# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T025/TB-T026/TB-T077: integrations write only under the user's home and reverse exactly."""
import json
from pathlib import Path

import pytest

from trier_bridge.integrations import catalog
from trier_bridge.integrations.ledger import IntegrationLedger


def _paths(tmp_path: Path) -> catalog.UserDirs:
    home = tmp_path / "home"
    return catalog.UserDirs(home, home / ".local/share", home / ".config")


def test_catalog_groups_and_defaults() -> None:
    assert set(i.group for i in catalog.CATALOG) <= set(catalog.GROUPS)
    assert all(not i.recommended for i in catalog.CATALOG if i.individual_only)
    assert catalog.by_id("search-provider") is not None and catalog.by_id("nope") is None
    for i in catalog.CATALOG:
        assert i.changes and i.reversal and i.extension_point


def test_apply_and_remove_launchers_are_exact(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    ledger = IntegrationLedger(tmp_path / "ledger.json", "0.1")
    assert not ledger.exists and not ledger.setup_completed
    res = catalog.apply("familiar-launchers", ledger, paths)
    assert res.ok and len(res.files) == len(catalog.FAMILIAR_LAUNCHERS)
    for f in res.files:
        p = Path(f)
        assert p.is_file() and str(p).startswith(str(paths.home))
        text = p.read_text(encoding="utf-8")
        assert "Exec=trier-bridge --section " in text and "[Desktop Entry]" in text
    assert ledger.is_applied("familiar-launchers")
    doc = json.loads((tmp_path / "ledger.json").read_text())
    assert (
        doc["applied"][0]["integration_id"] == "familiar-launchers"
        and doc["applied"][0]["app_version"] == "0.1"
    )
    # remove deletes exactly what was written and nothing else
    (paths.data / "applications" / "user-own.desktop").write_text(
        "[Desktop Entry]\n", encoding="utf-8"
    )
    res2 = catalog.remove("familiar-launchers", ledger)
    assert res2.ok and not ledger.is_applied("familiar-launchers")
    assert [p.name for p in (paths.data / "applications").iterdir()] == ["user-own.desktop"]
    assert catalog.remove("familiar-launchers", ledger).ok  # idempotent


def test_search_provider_files_point_at_the_service(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    ledger = IntegrationLedger(tmp_path / "ledger.json")
    res = catalog.apply("search-provider", ledger, paths)
    assert res.ok and len(res.files) == 2
    ini = (
        paths.data
        / "gnome-shell/search-providers"
        / "org.triertech.TrierBridge.search-provider.ini"
    ).read_text()
    assert "BusName=org.triertech.TrierBridge.SearchProvider" in ini and "Version=2" in ini
    svc = (
        paths.data / "dbus-1/services" / "org.triertech.TrierBridge.SearchProvider.service"
    ).read_text()
    assert "Exec=" in svc and "search-provider" in svc
    assert catalog.status(ledger)["search-provider"] is True
    assert catalog.remove("search-provider", ledger).ok
    assert not (paths.data / "dbus-1/services").exists() or not list(
        (paths.data / "dbus-1/services").iterdir()
    )


def test_files_menu_needs_the_shipped_extension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _paths(tmp_path)
    ledger = IntegrationLedger(tmp_path / "ledger.json")
    monkeypatch.setenv("TRIER_BRIDGE_DATA_DIR", str(tmp_path / "nodata"))
    res = catalog.apply("files-menu", ledger, paths)
    assert not res.ok and "left off" in res.plain and not ledger.is_applied("files-menu")
    monkeypatch.delenv("TRIER_BRIDGE_DATA_DIR")
    res = catalog.apply("files-menu", ledger, paths)  # source tree ships it
    ext_dir = paths.data / "nautilus-python/extensions"
    assert res.ok and (ext_dir / "tb_nautilus.py").is_file()
    # Files compiles the extension on load; removal takes that copy with it
    (ext_dir / "__pycache__").mkdir()
    (ext_dir / "__pycache__" / "tb_nautilus.cpython-312.pyc").write_bytes(b"\x00")
    assert catalog.remove("files-menu", ledger).ok
    assert not (ext_dir / "tb_nautilus.py").exists() and not (ext_dir / "__pycache__").exists()


def test_tray_autostart_entry_is_per_user_and_hidden(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    ledger = IntegrationLedger(tmp_path / "ledger.json")
    res = catalog.apply("tray-icon", ledger, paths)
    assert res.ok and len(res.files) == 1
    entry = (paths.config / "autostart" / "org.triertech.TrierBridge.Tray.desktop").read_text()
    assert "NoDisplay=true" in entry and "X-GNOME-Autostart-enabled=true" in entry
    assert "Exec=" in entry and "trier-bridge-tray" in entry
    assert catalog.remove("tray-icon", ledger).ok
    assert not (paths.config / "autostart" / "org.triertech.TrierBridge.Tray.desktop").exists()


def test_ledger_follows_changes_made_by_another_process(tmp_path: Path) -> None:
    """The tray process can turn itself off; the window must see that, not a stale copy."""
    paths = _paths(tmp_path)
    window = IntegrationLedger(tmp_path / "ledger.json")
    tray = IntegrationLedger(tmp_path / "ledger.json")
    assert catalog.apply("tray-icon", window, paths).ok
    assert tray.is_applied("tray-icon")
    assert catalog.remove("tray-icon", tray).ok
    assert not window.is_applied("tray-icon")
    assert catalog.apply("familiar-launchers", tray, paths).ok
    window.mark_setup_completed()
    assert IntegrationLedger(tmp_path / "ledger.json").applied_ids() == ["familiar-launchers"]


def test_ledger_survives_reload_and_marks_setup(tmp_path: Path) -> None:
    ledger = IntegrationLedger(tmp_path / "ledger.json")
    ledger.mark_setup_completed()
    again = IntegrationLedger(tmp_path / "ledger.json")
    assert again.setup_completed and again.exists and again.applied_ids() == []
