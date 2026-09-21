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
"""Disk Management (Foundation 04, IMP-04.05): drives, volumes, mounts, free space, read-only.

Mount points are shown as the real Linux folders they are (TB-INV-070). No
format, resize, or mount action exists here; the GNOME Disks app is offered
for changes.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..desktop.launch import Launcher  # noqa: E402
from ..system.storage import StorageOverview, Volume, read_storage  # noqa: E402

log = logging.getLogger("trier_bridge.ui.disks")


def _fmt(n: int | None) -> str:
    if n is None:
        return "Unknown"
    for unit, size in (("TB", 1 << 40), ("GB", 1 << 30), ("MB", 1 << 20)):
        if n >= size:
            return f"{n / size:.1f} {unit}"
    return f"{n / 1024:.0f} KB"


def _row(title: str, subtitle: str = "") -> Adw.ActionRow:
    r = Adw.ActionRow(use_markup=False)
    r.set_title(title)
    r.set_subtitle(subtitle)
    return r


class DisksPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self, launcher: Launcher, notify: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._launcher = launcher
        self._notify = notify
        self._page = Adw.PreferencesPage()
        self._top = Adw.PreferencesGroup(
            title="Disk Management",
            description=(
                "Read from udisks2. Linux attaches drives to folders instead of drive letters; "
                "the folder is shown for every mounted volume. Formatting, partitioning, and "
                "mounting stay in the Disks app."
            ),
        )
        refresh = Gtk.Button(label="Refresh")
        refresh.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION], ["Reads the disks again. Nothing is changed."]
        )
        refresh.connect("clicked", lambda *_: self.refresh())
        self._top.set_header_suffix(refresh)
        self._status = _row("Reading…")
        self._top.add(self._status)
        disks_row = _row("Disks app", "Linux: GNOME Disks, for changes that need care")
        b = Gtk.Button(label="Open")
        b.set_valign(Gtk.Align.CENTER)
        b.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Open the Disks app. Nothing is changed by opening it."],
        )
        b.connect("clicked", lambda *_: self._open_disks())
        disks_row.add_suffix(b)
        self._top.add(disks_row)
        self._page.add(self._top)
        self._groups: list[Adw.PreferencesGroup] = []
        scroller = Gtk.ScrolledWindow(child=self._page, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroller.set_vexpand(True)
        self.append(scroller)
        self._started = False

    def _open_disks(self) -> None:
        res = self._launcher.launch_app("org.gnome.DiskUtility.desktop")
        self._notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")

    def start(self) -> None:
        if not self._started:
            self._started = True
            self.refresh()

    def refresh(self) -> None:
        threading.Thread(target=self._worker, name="tb-storage", daemon=True).start()

    def _worker(self) -> None:
        try:
            st = read_storage()
        except Exception as exc:
            log.exception("storage read failed")
            GLib.idle_add(self._fail, str(exc))
            return
        GLib.idle_add(self._show, st)

    def _fail(self, text: str) -> bool:
        self._status.set_title("The disks could not be read")
        self._status.set_subtitle(f"Nothing was changed. Technical detail: {text}")
        return False

    def _volume_row(self, v: Volume) -> Adw.ActionRow:
        name = v.label or v.device_node
        parts = [v.kind, v.fs_type or "no filesystem", _fmt(v.size_bytes)]
        if v.is_mounted:
            parts.append("mounted at " + ", ".join(v.mount_points))
            parts.append(f"{_fmt(v.free_bytes)} free")
        else:
            parts.append("not mounted")
        if v.hint_system:
            parts.append("system")
        r = _row(name, " · ".join(parts))
        r.set_tooltip_text(f"{v.device_node} uuid={v.identity.fs_uuid or 'none'}")
        r.update_property([Gtk.AccessibleProperty.LABEL], [f"{name}: {' , '.join(parts)}"])
        return r

    def _show(self, st: StorageOverview) -> bool:
        for g in self._groups:
            self._page.remove(g)
        self._groups = []
        if not st.available:
            self._status.set_title("Not available on this computer")
            self._status.set_subtitle(st.detail)
            return False
        n_vol = sum(len(d.volumes) for d in st.drives) + len(st.loose_volumes)
        hidden = (
            f"; {st.hidden_count} internal volumes hidden (app packages)" if st.hidden_count else ""
        )
        self._status.set_title(f"{len(st.drives)} drives, {n_vol} volumes")
        self._status.set_subtitle(f"Read from udisks2{hidden}")
        for d in st.drives:
            kind = "Removable" if d.removable else "Fixed"
            title = f"{d.display_name} ({kind}, {_fmt(d.size_bytes)})"
            g = Adw.PreferencesGroup(
                title=title,
                description=f"{d.connection_bus or 'internal'} · serial {d.serial or 'Unknown'}",
            )
            for v in d.volumes:
                g.add(self._volume_row(v))
            if not d.volumes:
                g.add(_row("No volumes", "No partitions or filesystems were reported"))
            self._page.add(g)
            self._groups.append(g)
        if st.loose_volumes:
            g = Adw.PreferencesGroup(
                title="Other volumes", description="Not attached to a physical drive"
            )
            for v in st.loose_volumes:
                g.add(self._volume_row(v))
            self._page.add(g)
            self._groups.append(g)
        return False
