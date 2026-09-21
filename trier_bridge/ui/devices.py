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
"""Device Manager (Foundation 04, IMP-04.04) and Startup Apps (IMP-04.02), read-only."""
from __future__ import annotations

import logging
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..system.devices import Category, DeviceInventory, read_devices  # noqa: E402
from ..system.startup import StartupEntry, read_startup  # noqa: E402

log = logging.getLogger("trier_bridge.ui.devices")


def _row(title: str, subtitle: str = "") -> Adw.ActionRow:
    r = Adw.ActionRow(use_markup=False)
    r.set_title(title)
    r.set_subtitle(subtitle)
    return r


class DeviceManagerPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._page = Adw.PreferencesPage()
        self._top = Adw.PreferencesGroup(
            title="Device Manager",
            description=(
                "What each device is, whether a driver is bound, and which one. Most Linux "
                "drivers are part of the kernel; there is no Update Driver button here."
            ),
        )
        refresh = Gtk.Button(label="Refresh")
        refresh.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION], ["Reads the devices again. Nothing is changed."]
        )
        refresh.connect("clicked", lambda *_: self.refresh())
        self._top.set_header_suffix(refresh)
        self._status = _row("Reading…")
        self._top.add(self._status)
        self._page.add(self._top)
        self._groups: list[Adw.PreferencesGroup] = []
        scroller = Gtk.ScrolledWindow(child=self._page, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroller.set_vexpand(True)
        self.append(scroller)
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._started = True
            self.refresh()

    def refresh(self) -> None:
        threading.Thread(target=self._worker, name="tb-devices", daemon=True).start()

    def _worker(self) -> None:
        try:
            inv = read_devices()
        except Exception as exc:
            log.exception("device read failed")
            GLib.idle_add(self._fail, str(exc))
            return
        GLib.idle_add(self._show, inv)

    def _fail(self, text: str) -> bool:
        self._status.set_title("The devices could not be read")
        self._status.set_subtitle(f"Nothing was changed. Technical detail: {text}")
        return False

    def _show(self, inv: DeviceInventory) -> bool:
        for g in self._groups:
            self._page.remove(g)
        self._groups = []
        by_cat = inv.by_category()
        self._status.set_title(f"{len(inv.devices)} devices")
        notes = " ".join(inv.notes)
        self._status.set_subtitle(f"Sources: {', '.join(inv.sources) or 'none'}. {notes}".strip())
        for cat in Category:
            devs = by_cat.get(cat)
            if not devs:
                continue
            g = Adw.PreferencesGroup(title=cat.value)
            for d in devs:
                if d.working is True:
                    state = f"Working (driver: {d.driver})" if d.driver else "Present"
                elif d.working is False:
                    state = "Not present"
                else:
                    state = "No driver bound (may be normal for this device)"
                r = _row(d.name, f"{state} · {d.detail} · ID {d.ids}")
                r.set_tooltip_text(d.sysfs_path)
                r.update_property([Gtk.AccessibleProperty.LABEL], [f"{d.name}: {state}"])
                g.add(r)
            self._page.add(g)
            self._groups.append(g)
        return False


class StartupPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._page = Adw.PreferencesPage()
        self._group = Adw.PreferencesGroup(
            title="Startup Apps",
            description=(
                "What starts when you sign in. Linux has several startup mechanisms; each entry "
                "says which one it is. Turning entries off arrives in a later foundation."
            ),
        )
        self._page.add(self._group)
        self._rows: list[Gtk.Widget] = []
        scroller = Gtk.ScrolledWindow(child=self._page, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroller.set_vexpand(True)
        self.append(scroller)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        try:
            entries = read_startup(Path(GLib.get_home_dir()))
        except Exception as exc:
            log.exception("startup read failed")
            self._group.add(
                _row("Startup entries could not be read", f"Nothing was changed. {exc}")
            )
            return
        self._show(entries)

    def _show(self, entries: list[StartupEntry]) -> None:
        for w in self._rows:
            self._group.remove(w)
        self._rows = []
        if not entries:
            r = _row("No startup entries were found")
            self._group.add(r)
            self._rows.append(r)
            return
        for e in entries:
            if e.enabled is None:
                state = "Unknown"
            else:
                state = "On" if e.enabled else "Off"
            if e.overridden_by_user:
                state += " (changed by your own copy)"
            r = _row(e.name, f"{state} · {e.mechanism} · {e.comment or e.command}")
            r.set_tooltip_text(e.source_path)
            r.update_property([Gtk.AccessibleProperty.LABEL], [f"{e.name}: {state}, {e.mechanism}"])
            self._group.add(r)
            self._rows.append(r)
