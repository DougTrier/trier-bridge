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


def installed_apps() -> list[InstalledApp]:
    apps: list[InstalledApp] = []
    for info in Gio.AppInfo.get_all():
        if not info.should_show():
            continue
        filename = info.get_filename() if isinstance(info, Gio.DesktopAppInfo) else None
        path = filename or ""
        icon = info.get_icon()
        icon_name = icon.to_string() if icon is not None else ""
        apps.append(
            InstalledApp(
                name=info.get_display_name() or info.get_name() or "",
                desktop_id=info.get_id() or "",
                comment=info.get_description() or "",
                provenance=(
                    provenance_for(path, str(GLib.get_home_dir())) if path else Provenance.OTHER
                ),
                source_path=path,
                icon=icon_name,
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
