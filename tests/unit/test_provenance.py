# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T024/TB-T072: package provenance is decided from the real entry path and never merged."""
from trier_bridge.apps.provenance import Provenance, provenance_for

HOME = "/home/tb"


def test_paths_map_to_distinct_provenance() -> None:
    assert (
        provenance_for("/usr/share/applications/org.gnome.Nautilus.desktop", HOME)
        is Provenance.SYSTEM
    )
    assert (
        provenance_for("/var/lib/snapd/desktop/applications/firefox_firefox.desktop", HOME)
        is Provenance.SNAP
    )
    assert (
        provenance_for("/var/lib/flatpak/exports/share/applications/org.x.App.desktop", HOME)
        is Provenance.FLATPAK
    )
    assert (
        provenance_for("/home/tb/.local/share/flatpak/exports/share/applications/a.desktop", HOME)
        is Provenance.FLATPAK
    )
    assert (
        provenance_for("/home/tb/.local/share/applications/tb-pad.desktop", HOME) is Provenance.USER
    )
    assert provenance_for("/opt/thing/thing.desktop", HOME) is Provenance.OTHER


def test_same_name_different_system_is_different_provenance() -> None:
    a = provenance_for("/usr/share/applications/firefox.desktop", HOME)
    b = provenance_for("/var/lib/snapd/desktop/applications/firefox_firefox.desktop", HOME)
    assert a is not b
    assert {p.label for p in Provenance} == {
        "System package",
        "Snap",
        "Flatpak",
        "Installed for this user",
        "Other",
    }
