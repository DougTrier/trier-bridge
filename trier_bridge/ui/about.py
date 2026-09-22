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
"""About Trier Bridge: version/license (TB-INV-256) and the owner's own support links.

Moved here from the header-bar menu's dialog into a normal sidebar page,
positioned directly above Help. The support links are the author's own
(GitHub Sponsors, Buy Me a Coffee); no photo, initials only, by his
instruction. Every link opens only on click, through the same
Launcher.open_uri every other outbound link in this codebase already uses
(TB-INV-255).
"""
from __future__ import annotations

from datetime import date
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from .. import APP_ID, __version__  # noqa: E402
from ..desktop.launch import Launcher  # noqa: E402

_CAREER_START = date(1992, 9, 21)
# Shared with the top of Home (pages.py): the one paragraph that says what this is for.
GOAL = (
    "Trier Bridge is for people who know Windows and now have Linux in front of them. Type "
    "what you would look for on Windows — Task Manager, Control Panel, Command Prompt "
    "— and it opens the real Linux place for it, and says plainly when there is no "
    "equivalent. Every change it makes is a typed, reviewable operation, never a hidden shell "
    "command, and Linux itself asks for permission each time."
)
_BIO = (
    "{years} years in industrial operations and enterprise IT, from delivery routes and "
    "production equipment to server and mobile infrastructure."
)
_TITLES = ("Platform architect", "Systems administrator")
# (label, address, icon, chip class). The icons are this package's own full-color
# marks, shipped beside the launcher icons: a GitHub-style star and a coffee cup.
_LINKS = (
    (
        "Sponsor on GitHub",
        "https://github.com/sponsors/dougtrier",
        f"{APP_ID}-star",
        "tb-support-sponsors",
    ),
    (
        "Buy Me a Coffee",
        "https://www.buymeacoffee.com/dougtrier",
        f"{APP_ID}-coffee",
        "tb-support-coffee",
    ),
)


def _years_experience() -> int:
    today = date.today()
    years = today.year - _CAREER_START.year
    if (today.month, today.day) < (_CAREER_START.month, _CAREER_START.day):
        years -= 1
    return max(years, 0)


class AboutPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self, launcher: Launcher, notify: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._launcher = launcher
        self._notify = notify
        page = Adw.PreferencesPage()
        page.set_vexpand(True)

        goal_group = Adw.PreferencesGroup(title="What it is for")
        goal_row = Adw.ActionRow(use_markup=False)
        goal_row.set_subtitle(GOAL)
        goal_row.set_subtitle_lines(6)
        goal_group.add(goal_row)
        page.add(goal_group)

        info_group = Adw.PreferencesGroup()
        info_group.add(Adw.ActionRow(title="Version", subtitle=__version__))
        license_row = Adw.ActionRow(title="License", subtitle="Apache License 2.0")
        license_row.add_suffix(self._link_button("https://www.apache.org/licenses/LICENSE-2.0"))
        info_group.add(license_row)
        info_group.add(Adw.ActionRow(title="Copyright", subtitle="Copyright 2026 Doug Trier"))
        page.add(info_group)

        made_group = Adw.PreferencesGroup(title="Made by")
        creator_row = Adw.ActionRow(
            title="Doug Trier", subtitle=" · ".join(_TITLES), subtitle_lines=1
        )
        creator_row.add_prefix(Adw.Avatar(text="Doug Trier", show_initials=True, size=44))
        made_group.add(creator_row)
        bio_row = Adw.ActionRow(use_markup=False)
        bio_row.set_subtitle(_BIO.format(years=_years_experience()))
        bio_row.set_subtitle_lines(3)
        made_group.add(bio_row)
        page.add(made_group)

        support_group = Adw.PreferencesGroup(
            title="Support this project",
            description="Trier Bridge is independent work. If it's useful to you, these are the "
            "real ways to say so.",
        )
        for title, url, icon, accent_class in _LINKS:
            row = Adw.ActionRow(title=title, subtitle=url)
            row.add_prefix(self._support_icon(icon, accent_class))
            row.add_suffix(self._link_button(url))
            row.set_activatable(True)
            row.connect("activated", lambda *_r, u=url: self._open(u))
            support_group.add(row)
        page.add(support_group)

        self.append(page)

    def _support_icon(self, icon_name: str, accent_class: str) -> Gtk.Image:
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.add_css_class("tb-support-icon")
        icon.add_css_class(accent_class)
        icon.set_valign(Gtk.Align.CENTER)
        return icon

    def _link_button(self, url: str) -> Gtk.Button:
        button = Gtk.Button(icon_name="web-browser-symbolic", valign=Gtk.Align.CENTER)
        button.add_css_class("flat")
        button.update_property([Gtk.AccessibleProperty.DESCRIPTION], [f"Open {url}"])
        button.connect("clicked", lambda *_b, u=url: self._open(u))
        return button

    def _open(self, url: str) -> None:
        res = self._launcher.open_uri(url)
        self._notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")
