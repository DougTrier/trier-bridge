# Copyright 2026 Doug Trier
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Installed Apps inventory with provenance (docs/PRODUCT-CONCEPT.md section 9).

Provenance comes from where the desktop entry lives, which is a real fact
about how the program was installed. A unified list never erases it
(TB-INV-072). Read-only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from .provenance import Provenance, provenance_for  # noqa: E402

COMMON_TYPES: tuple[tuple[str, str], ...] = (
    ("application/pdf", "PDF documents"),
    ("text/plain", "Text files"),
    ("image/jpeg", "Photos (JPEG)"),
    ("image/png", "Images (PNG)"),
    ("audio/mpeg", "Music (MP3)"),
    ("video/mp4", "Videos (MP4)"),
    ("x-scheme-handler/http", "Web links"),
    ("x-scheme-handler/mailto", "Email links"),
    ("inode/directory", "Folders"),
    # A downloaded installer. On Ubuntu Desktop both App Center and the archive viewer
    # register this type and the archive viewer wins the default, so a double-click opens
    # the .deb as a zip file instead of installing it. Listing the type here lets the
    # person pick App Center once, through the same per-user default-app change as every
    # other row (DEC-028); Trier Bridge itself still never installs anything (DEC-024).
    ("application/vnd.debian.binary-package", "Software installers (.deb)"),
)


@dataclass(frozen=True)
class InstalledApp:
    name: str
    desktop_id: str
    comment: str
    provenance: Provenance
    source_path: str
    icon: str


@dataclass(frozen=True)
class DefaultApp:
    mime_type: str
    label: str
    app_name: str  # empty when nothing is set
    desktop_id: str


def application_dirs() -> list[str]:
    """Directories that hold desktop entries, in XDG precedence order (user first).

    Snap and Flatpak export directories are listed explicitly: they are part of
    XDG_DATA_DIRS only inside a graphical session, and provenance must not
    depend on which session asked (TB-INV-072).
    """
    dirs: list[str] = [str(GLib.get_user_data_dir()) + "/applications"]
    for d in GLib.get_system_data_dirs():
        dirs.append(str(d) + "/applications")
    home = str(GLib.get_home_dir())
    for extra in (
        "/var/lib/snapd/desktop/applications",
        "/var/lib/flatpak/exports/share/applications",
        f"{home}/.local/share/flatpak/exports/share/applications",
    ):
        if extra not in dirs:
            dirs.append(extra)
    return dirs


def installed_apps() -> list[InstalledApp]:
    apps: list[InstalledApp] = []
    seen: set[str] = set()
    home = str(GLib.get_home_dir())
    for directory in application_dirs():
        d = Path(directory)
        if not d.is_dir():
            continue
        for entry in sorted(d.glob("*.desktop")):
            if entry.name in seen:
                continue  # an earlier (higher-precedence) directory already provided this id
            try:
                info = Gio.DesktopAppInfo.new_from_filename(str(entry))
            except TypeError:  # PyGObject raises when the entry cannot be parsed
                info = None
            if info is None:
                continue
            seen.add(entry.name)
            if not info.should_show():
                continue
            icon = info.get_icon()
            apps.append(
                InstalledApp(
                    name=info.get_display_name() or info.get_name() or entry.stem,
                    desktop_id=entry.name,
                    comment=info.get_description() or "",
                    provenance=provenance_for(str(entry), home),
                    source_path=str(entry),
                    icon=icon.to_string() if icon is not None else "",
                )
            )
    apps.sort(key=lambda a: a.name.casefold())
    return apps


def default_apps() -> list[DefaultApp]:
    out: list[DefaultApp] = []
    for mime, label in COMMON_TYPES:
        info = Gio.AppInfo.get_default_for_type(mime, False)
        if info is None:
            out.append(DefaultApp(mime, label, "", ""))
        else:
            out.append(DefaultApp(mime, label, info.get_display_name() or "", info.get_id() or ""))
    return out
