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
"""Printers page: live queues from CUPS, changes through GNOME Settings."""
from __future__ import annotations

import logging
import threading
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..desktop.launch import Launcher  # noqa: E402
from ..system.printers import PrinterOverview, read_printers  # noqa: E402

log = logging.getLogger("trier_bridge.ui.printers")


class PrintersPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self, launcher: Launcher, notify: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._launcher = launcher
        self._notify = notify
        page = Adw.PreferencesPage()
        page.set_vexpand(True)
        top = Adw.PreferencesGroup(
            title="Printers",
            description=(
                "What Printers and scanners shows on Windows: each printer, whether it is ready, "
                "and what is waiting to print. Adding a printer or changing the default happens "
                "in Settings."
            ),
        )
        settings = Gtk.Button(label="Printers settings")
        settings.set_valign(Gtk.Align.CENTER)
        settings.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Open the Printers panel of GNOME Settings (add, remove, set default)."],
        )
        settings.connect("clicked", lambda *_: self._open_settings())
        top.set_header_suffix(settings)
        self._status = Adw.ActionRow(use_markup=False)
        self._status.set_title("Reading printers…")
        top.add(self._status)
        page.add(top)
        self._list = Adw.PreferencesGroup(title="Printers on this computer")
        page.add(self._list)
        self._rows: list[Gtk.Widget] = []
        self.append(page)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        threading.Thread(target=self._worker, name="tb-printers", daemon=True).start()

    def _worker(self) -> None:
        try:
            overview = read_printers()
        except Exception as exc:  # report, never hide (TB-INV-004)
            log.exception("printer read failed")
            overview = PrinterOverview(False, f"Printers could not be read: {exc}")
        GLib.idle_add(self._show, overview)

    def _show(self, o: PrinterOverview) -> bool:
        for w in self._rows:
            self._list.remove(w)
        self._rows = []
        if not o.available:
            self._status.set_title("Printer status is not available")
            self._status.set_subtitle(f"{o.detail} Nothing was changed.")
            return False
        n = len(o.printers)
        self._status.set_title(f"{n} printer{'s' if n != 1 else ''} known to the print service")
        self._status.set_subtitle(
            f"Default: {o.default_name}" if o.default_name else "No default printer is set"
        )
        if not o.printers:
            row = Adw.ActionRow(use_markup=False)
            row.set_title("No printers yet")
            row.set_subtitle("Use Printers settings to add one; the print service is running.")
            self._list.add(row)
            self._rows.append(row)
            return False
        for p in o.printers:
            row = Adw.ActionRow(use_markup=False)
            row.set_title(f"{p.description or p.name}{' (default)' if p.is_default else ''}")
            parts = [p.state]
            if p.reason:
                parts.append(p.reason.replace("-", " "))
            if not p.accepting:
                parts.append("not accepting jobs")
            if p.location:
                parts.append(p.location)
            if p.make_model:
                parts.append(p.make_model)
            parts.append(f"{len(p.jobs)} job{'s' if len(p.jobs) != 1 else ''} waiting")
            row.set_subtitle(" · ".join(parts))
            row.set_subtitle_lines(3)
            row.update_property(
                [Gtk.AccessibleProperty.DESCRIPTION],
                [f"Printer {p.name}: {p.state}. {len(p.jobs)} jobs waiting."],
            )
            self._list.add(row)
            self._rows.append(row)
            for job in p.jobs:
                jr = Adw.ActionRow(use_markup=False)
                jr.set_title(f"    {job.title}")
                jr.set_subtitle(f"{job.state} · {job.user} · job {job.job_id}")
                self._list.add(jr)
                self._rows.append(jr)
        return False

    def _open_settings(self) -> None:
        res = self._launcher.open_settings_panel("printers")
        self._notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")
