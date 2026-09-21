# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Integration: installed-app inventory and route resolution against the live VM.

Needs the console session bus for launching; the inventory and folder
resolution parts run in any session. No mocks (DEC-021).
TB-T072, TB-T073, TB-T074.
"""
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration
gi = pytest.importorskip("gi")

from trier_bridge.apps.inventory import default_apps, installed_apps  # noqa: E402
from trier_bridge.apps.provenance import Provenance  # noqa: E402
from trier_bridge.catalog.model import Catalog  # noqa: E402
from trier_bridge.desktop.launch import Launcher, folder_path, folder_uri  # noqa: E402
from trier_bridge.resources import catalog_path  # noqa: E402


def _count_visible(dirpath: str) -> int:
    n = 0
    for p in Path(dirpath).glob("*.desktop"):
        text = p.read_text(encoding="utf-8", errors="replace")
        if "NoDisplay=true" in text or "Hidden=true" in text:
            continue
        n += 1
    return n


def test_inventory_provenance_matches_real_directories() -> None:
    apps = installed_apps()
    assert apps, "the VM has desktop entries"
    by_prov = {}
    for a in apps:
        by_prov[a.provenance] = by_prov.get(a.provenance, 0) + 1
        assert a.name and a.desktop_id and a.source_path
    if Path("/var/lib/snapd/desktop/applications").is_dir():
        assert by_prov.get(Provenance.SNAP, 0) >= 1
        assert by_prov[Provenance.SNAP] <= _count_visible("/var/lib/snapd/desktop/applications")
    assert by_prov.get(Provenance.SYSTEM, 0) >= 10
    # A snap and a system entry never share provenance even when names match (TB-INV-072)
    names = {}
    for a in apps:
        names.setdefault(a.name, set()).add(a.provenance)
    for n, provs in names.items():
        assert len(provs) == len({a.source_path for a in apps if a.name == n})


def test_default_apps_are_real_and_unset_stays_empty() -> None:
    defaults = {d.mime_type: d for d in default_apps()}
    assert defaults["inode/directory"].app_name  # Files
    for d in defaults.values():
        assert isinstance(d.app_name, str)  # empty string when nothing is set, never a guess


def test_folder_keys_resolve_to_real_paths_or_none() -> None:
    home = os.path.expanduser("~")
    assert folder_path("home") == home
    for key in ("desktop", "documents", "download", "pictures", "music", "videos"):
        p = folder_path(key)
        assert p is None or p.startswith(home)
    assert folder_uri("trash:///") == "trash:///"
    assert folder_uri(
        "download",
    ) is None or folder_uri(
        "download"
    ).startswith("file://")


def test_every_catalog_route_is_resolvable_in_principle() -> None:
    cat = Catalog.load(catalog_path())
    for c in cat.concepts:
        if c.route.kind.value == "folder":
            assert folder_uri(c.route.target) is not None, c.id
        if c.route.kind.value == "app":
            assert c.route.target.endswith(".desktop")


@pytest.mark.skipif(not os.environ.get("WAYLAND_DISPLAY"), reason="needs the console session")
def test_launcher_opens_the_downloads_folder_in_files() -> None:
    res = Launcher().show_folder("download")
    assert res.ok, res
    assert "Files" in res.plain
