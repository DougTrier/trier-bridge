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
positioned directly above Help. Donation links are the owner's real ones,
reused from another of his public projects (github.com/DougTrier/trier-os,
its .github/FUNDING.yml and AboutView.jsx) with his personal photo left out
per his instruction -- the source page itself uses initials only, which is
exactly what Adw.Avatar renders here too, so nothing needed to be stripped.
Every link opens only on click, through the same Launcher.open_uri every
other outbound link in this codebase already uses (TB-INV-255).
"""
from __future__ import annotations

from datetime import date
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from .. import APP_ID, APP_NAME, __version__  # noqa: E402
from ..desktop.launch import Launcher  # noqa: E402

_CAREER_START = date(1992, 9, 21)
_GOAL = (
    "Trier Bridge doesn't ask you to relearn Linux from scratch. Type what you already know "
    "how to look for — Task Manager, Control Panel, Command Prompt — and it shows you "
    "the real Linux place for it, honestly, including the times it isn't the same. Every "
    "action it takes is a typed, reviewable operation, never a hidden shell command, and it "
    "never claims something works when it doesn't."
)
_BIO = (
    "{years} years bridging industrial operations and enterprise technology — from driving "
    "routes and running the floor to architecting digital infrastructure. Trier Bridge is the "
    "same idea applied here: hard-won operational knowledge, built into a tool."
)
_TITLES = ("Platform Architect", "Systems Administrator")
_LINKS = (
    ("Sponsor on GitHub", "https://github.com/sponsors/dougtrier", "tb-support-sponsors"),
    ("Open Collective", "https://opencollective.com/trier-os", "tb-support-collective"),
    ("Buy Me a Coffee", "https://www.buymeacoffee.com/dougtrier", "tb-support-coffee"),
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
        page.set_margin_top(4)

        page.add(self._hero_group())

        goal_group = Adw.PreferencesGroup(title="Our goal")
        goal_row = Adw.ActionRow(use_markup=False)
        goal_row.set_subtitle(_GOAL)
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
        for title, url, accent_class in _LINKS:
            row = Adw.ActionRow(title=title, subtitle=url)
            row.add_prefix(self._support_icon(accent_class))
            row.add_suffix(self._link_button(url))
            row.set_activatable(True)
            row.connect("activated", lambda *_r, u=url: self._open(u))
            support_group.add(row)
        page.add(support_group)

        self.append(page)

    def _hero_group(self) -> Adw.PreferencesGroup:
        hero = Gtk.Box(spacing=16, valign=Gtk.Align.CENTER)
        hero.add_css_class("tb-about-hero")
        icon = Gtk.Image.new_from_icon_name(APP_ID)
        icon.set_pixel_size(56)
        hero.append(icon)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, valign=Gtk.Align.CENTER)
        title = Gtk.Label(label=APP_NAME, xalign=0.0)
        title.add_css_class("title-1")
        title.add_css_class("tb-about-hero-title")
        text.append(title)
        subtitle = Gtk.Label(label="Everything you know. Linux underneath.", xalign=0.0)
        subtitle.add_css_class("tb-about-hero-subtitle")
        text.append(subtitle)
        hero.append(text)
        group = Adw.PreferencesGroup()
        group.add(hero)
        return group

    def _support_icon(self, accent_class: str) -> Gtk.Image:
        icon = Gtk.Image.new_from_icon_name("emblem-favorite-symbolic")
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
