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
"""Open routes through public desktop interfaces (no shell, no privilege).

  GNOME Settings panel  org.gnome.Settings: org.freedesktop.Application.ActivateAction
                        with the "launch-panel" action
  folder                org.freedesktop.FileManager1.ShowFolders (Nautilus; verified 2026-09-21)
  application           Gio.DesktopAppInfo.launch

Everything is user-scoped (class A/B): opening a window changes nothing on the
system. Results are structured and plain (TB-INV-040, TB-INV-078).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from ..catalog.model import Route, RouteKind  # noqa: E402

CALL_TIMEOUT_MS = 5000

SPECIAL_DIRS: dict[str, Any] = {
    "desktop": GLib.UserDirectory.DIRECTORY_DESKTOP,
    "documents": GLib.UserDirectory.DIRECTORY_DOCUMENTS,
    "download": GLib.UserDirectory.DIRECTORY_DOWNLOAD,
    "music": GLib.UserDirectory.DIRECTORY_MUSIC,
    "pictures": GLib.UserDirectory.DIRECTORY_PICTURES,
    "publicshare": GLib.UserDirectory.DIRECTORY_PUBLIC_SHARE,
    "templates": GLib.UserDirectory.DIRECTORY_TEMPLATES,
    "videos": GLib.UserDirectory.DIRECTORY_VIDEOS,
}


@dataclass(frozen=True)
class LaunchResult:
    ok: bool
    plain: str
    technical: str = ""

    @property
    def three_answers(self) -> dict[str, str]:
        return {
            "Did anything change?": (
                "Nothing on this computer was changed; a window was opened."
                if self.ok
                else "Nothing was changed."
            ),
            "What stopped it?": "Nothing." if self.ok else self.plain,
            "What is the safest next step?": (
                "No action is needed." if self.ok else "Open it from the desktop's own menu."
            ),
        }


def folder_path(key: str) -> str | None:
    """Real Linux path for a familiar folder key, or None when the key is a URI/unknown."""
    if key == "home":
        return str(GLib.get_home_dir())
    kind = SPECIAL_DIRS.get(key)
    if kind is None:
        return None
    path = GLib.get_user_special_dir(kind)
    return str(path) if path else None


def folder_uri(key_or_uri: str) -> str | None:
    if "://" in key_or_uri:
        return key_or_uri
    path = folder_path(key_or_uri)
    return GLib.filename_to_uri(path, None) if path else None


class Launcher:
    def __init__(self) -> None:
        self.error = ""
        try:
            self.bus: Any = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error as exc:
            self.bus = None
            self.error = f"{exc.domain}: {exc.message}"

    def _call(self, name: str, path: str, iface: str, method: str, args: Any) -> str:
        if self.bus is None:
            return self.error or "no session bus"
        try:
            self.bus.call_sync(
                name, path, iface, method, args, None, Gio.DBusCallFlags.NONE, CALL_TIMEOUT_MS, None
            )
            return ""
        except GLib.Error as exc:
            return f"{exc.domain}: {exc.message}"

    def open_settings_panel(self, panel: str) -> LaunchResult:
        params = GLib.Variant("(sav)", (panel, []))
        err = self._call(
            "org.gnome.Settings",
            "/org/gnome/Settings",
            "org.freedesktop.Application",
            "ActivateAction",
            GLib.Variant("(sava{sv})", ("launch-panel", [params], {})),
        )
        if err:
            return LaunchResult(False, "Settings could not be opened on this desktop.", err)
        return LaunchResult(True, f"Opened Settings ({panel}).")

    def show_folder(self, key_or_uri: str) -> LaunchResult:
        uri = folder_uri(key_or_uri)
        if uri is None:
            return LaunchResult(
                False, "That folder is not set up on this computer.", f"no XDG dir for {key_or_uri}"
            )
        err = self._call(
            "org.freedesktop.FileManager1",
            "/org/freedesktop/FileManager1",
            "org.freedesktop.FileManager1",
            "ShowFolders",
            GLib.Variant("(ass)", ([uri], "")),
        )
        if err:
            return LaunchResult(False, "The file manager could not be opened.", err)
        return LaunchResult(True, "Opened in Files.")

    def open_uri(self, uri: str) -> LaunchResult:
        """Open a web address or file with whatever the desktop associates with it."""
        try:
            ok = Gio.AppInfo.launch_default_for_uri(uri, None)
        except GLib.Error as exc:
            return LaunchResult(False, "Nothing on this computer opens that.", exc.message)
        return LaunchResult(
            bool(ok), f"Opened {uri}." if ok else "Nothing on this computer opens that."
        )

    def launch_app(self, desktop_id: str) -> LaunchResult:
        info = Gio.DesktopAppInfo.new(desktop_id)
        if info is None:
            return LaunchResult(
                False, "That program is not installed on this computer.", f"no {desktop_id}"
            )
        try:
            info.launch([], None)
        except GLib.Error as exc:
            return LaunchResult(False, "The program could not be started.", exc.message)
        return LaunchResult(True, f"Started {info.get_display_name()}.")

    def open(self, route: Route) -> LaunchResult:
        if route.kind is RouteKind.GNOME_SETTINGS:
            return self.open_settings_panel(route.target)
        if route.kind is RouteKind.FOLDER:
            return self.show_folder(route.target)
        if route.kind is RouteKind.APP:
            return self.launch_app(route.target)
        return LaunchResult(False, "There is nothing to open for this item.", route.kind.value)
