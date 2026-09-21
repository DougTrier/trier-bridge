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
"""Help page: the generated sections from trier_bridge.help, searchable."""
from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from ..catalog.model import Catalog  # noqa: E402
from ..config import Paths  # noqa: E402
from ..desktop.launch import Launcher  # noqa: E402
from ..help import HelpSection, sections  # noqa: E402


class HelpPage(Gtk.Box):  # type: ignore[misc]
    def __init__(
        self, catalog: Catalog, paths: Paths, launcher: Launcher, notify: Callable[[str], None]
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._sections = sections(catalog, paths)
        self._launcher = launcher
        self._notify = notify
        self._page = Adw.PreferencesPage()
        self._page.set_vexpand(True)
        top = Adw.PreferencesGroup()
        self._entry = Gtk.SearchEntry(placeholder_text="Search Help…")
        self._entry.update_property([Gtk.AccessibleProperty.LABEL], ["Search Help"])
        self._entry.connect("search-changed", lambda *_: self._render())
        top.add(self._entry)
        self._page.add(top)
        self._groups: list[Adw.PreferencesGroup] = []
        self.append(self._page)
        self._render()

    def _render(self) -> None:
        for g in self._groups:
            self._page.remove(g)
        self._groups = []
        q = self._entry.get_text().strip().casefold()
        for section in self._sections:
            rows = [
                r
                for r in section.rows
                if not q
                or q in r[0].casefold()
                or q in r[1].casefold()
                or q in section.title.casefold()
            ]
            if not rows and q:
                continue
            self._groups.append(self._group(section, rows))
        if not self._groups:
            g = Adw.PreferencesGroup(title="No matches")
            g.set_description("Try another word. Help only lists what this build contains.")
            self._groups.append(g)
        for g in self._groups:
            self._page.add(g)

    def _group(self, section: HelpSection, rows: list[tuple[str, str]]) -> Adw.PreferencesGroup:
        g = Adw.PreferencesGroup(title=section.title, description=section.description)
        for title, subtitle in rows:
            row = Adw.ActionRow(use_markup=False)
            row.set_title(title)
            row.set_subtitle(subtitle)
            row.set_subtitle_lines(4)
            if section.title.startswith("Where Trier Bridge keeps") and title.startswith("/"):
                button = Gtk.Button(label="Open")
                button.set_valign(Gtk.Align.CENTER)
                button.update_property(
                    [Gtk.AccessibleProperty.DESCRIPTION], [f"Show {title} in Files."]
                )
                button.connect("clicked", lambda *_, p=title: self._open(p))
                row.add_suffix(button)
            g.add(row)
        return g

    def _open(self, path: str) -> None:
        res = self._launcher.show_folder(f"file://{path}")
        self._notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")
