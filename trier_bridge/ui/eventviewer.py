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
"""Event Viewer (Foundation 04, IMP-04.03): familiar views over the systemd journal.

Reads the newest entries on a worker thread; the view drop-down filters in
place. Restricted access is stated, not hidden (TB-INV-145). Messages are
plain text: nothing is a link and nothing is executed (TB-INV-148).
"""
from __future__ import annotations

import datetime as dt
import logging
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..system.journal import Entry, JournalReader, Level, View, journal_access  # noqa: E402

log = logging.getLogger("trier_bridge.ui.eventviewer")

MAX_ROWS = 300
LEVEL_CSS = {
    Level.ERROR: "tb-pill-error",
    Level.WARNING: "tb-pill-warn",
    Level.INFORMATION: "tb-pill-neutral",
    Level.DEBUG: "tb-pill-off",
    Level.UNKNOWN: "tb-pill-off",
}


class EventViewerPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._reader = JournalReader()
        self._entries: list[Entry] = []
        self._boot_entries: list[Entry] = []
        self._rows: list[Gtk.Widget] = []
        self._loading = False
        access = journal_access()
        self._banner = Adw.Banner(title=access.detail, revealed=True)
        self.append(self._banner)
        bar = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=8, margin_bottom=4)
        self._view = Gtk.DropDown.new_from_strings([v.value for v in View])
        self._view.update_property([Gtk.AccessibleProperty.LABEL], ["Event view"])
        self._view.connect("notify::selected", lambda *_: self._render())
        bar.append(self._view)
        self._entry = Gtk.SearchEntry(placeholder_text="Find in messages…", hexpand=True)
        self._entry.update_property([Gtk.AccessibleProperty.LABEL], ["Find in messages"])
        self._entry.connect("search-changed", lambda *_: self._render())
        bar.append(self._entry)
        self._refresh = Gtk.Button(label="Refresh")
        self._refresh.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Reads the newest entries again. Nothing is changed."],
        )
        self._refresh.connect("clicked", lambda *_: self.refresh())
        bar.append(self._refresh)
        self.append(bar)
        self._summary = Gtk.Label(xalign=0.0, margin_start=12)
        self._summary.add_css_class("dim-label")
        self.append(self._summary)
        self._list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self._list.add_css_class("boxed-list")
        self._list.set_margin_start(12)
        self._list.set_margin_end(12)
        self._list.set_margin_bottom(12)
        scroller = Gtk.ScrolledWindow(child=self._list, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroller.set_vexpand(True)
        self.append(scroller)
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._started = True
            self.refresh()

    def refresh(self) -> None:
        if self._loading:
            return
        self._loading = True
        self._refresh.set_sensitive(False)
        self._summary.set_text("Reading the newest entries…")
        threading.Thread(target=self._worker, name="tb-journal", daemon=True).start()

    def _worker(self) -> None:
        try:
            entries = self._reader.newest()
            boot = self._reader.newest(boot_only=True)
        except Exception as exc:
            log.exception("journal read failed")
            GLib.idle_add(self._fail, str(exc))
            return
        GLib.idle_add(self._loaded, entries, boot)

    def _fail(self, text: str) -> bool:
        self._summary.set_text(
            f"The log could not be read. Nothing was changed. Technical detail: {text}"
        )
        self._loading = False
        self._refresh.set_sensitive(True)
        return False

    def _loaded(self, entries: list[Entry], boot: list[Entry]) -> bool:
        self._entries = entries
        self._boot_entries = boot
        self._loading = False
        self._refresh.set_sensitive(True)
        self._render()
        return False

    def _render(self) -> None:
        for w in self._rows:
            self._list.remove(w)
        self._rows = []
        view = list(View)[self._view.get_selected()]
        q = self._entry.get_text().strip().casefold()
        pool = self._boot_entries if view is View.BOOT else self._entries
        shown = [
            e
            for e in pool
            if e.matches(view) and (not q or q in e.message.casefold() or q in e.source.casefold())
        ]
        if not pool:
            self._summary.set_text("No entries were read." if not self._loading else "Reading…")
        elif view is View.BOOT:
            self._summary.set_text(
                f"{len(shown)} of the newest {len(pool)} kernel and audit entries from this boot"
            )
        else:
            self._summary.set_text(
                f"{len(shown)} of the newest {len(pool)} entries in “{view.value}”"
            )
        for e in shown[:MAX_ROWS]:
            when = dt.datetime.fromtimestamp(e.realtime_usec / 1_000_000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            row = Adw.ActionRow(use_markup=False)
            row.set_title(e.message or "(no message)")
            row.set_title_lines(2)
            row.set_subtitle(f"{when} · {e.source}")
            badge = Gtk.Label(label=e.level.value, width_chars=11)
            badge.add_css_class("tb-pill")
            badge.add_css_class(LEVEL_CSS[e.level])
            badge.set_valign(Gtk.Align.CENTER)
            row.add_prefix(badge)
            tech = ", ".join(f"{k}={v}" for k, v in e.fields.items() if k not in ("MESSAGE",))
            row.set_tooltip_text(tech[:400])
            row.update_property(
                [Gtk.AccessibleProperty.LABEL],
                [f"{e.level.value}, {when}, {e.source}: {e.message[:200]}"],
            )
            self._list.append(row)
            self._rows.append(row)
        if len(shown) > MAX_ROWS:
            more = Adw.ActionRow(use_markup=False)
            more.set_title(f"{len(shown) - MAX_ROWS} more; narrow the search to see them")
            self._list.append(more)
            self._rows.append(more)
