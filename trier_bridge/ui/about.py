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
_BIO = (
    "Bridging {years} years of industrial grit and enterprise technology. Doug's journey began "
    "on the front lines — driving delivery routes, working the floor, and operating "
    "production equipment — before evolving into architecting enterprise digital "
    "infrastructure. Trier Bridge is one piece of that same throughline: taking hard-won "
    "operational knowledge and building a tool that makes Linux make sense to people who "
    "already know how to get work done on Windows."
)
_TITLES = (
    "Platform Architect",
    "Systems Administrator",
    "Enterprise Operations Technologist",
    "Mobile Infrastructure Specialist",
)
_LINKS = (
    ("Sponsor on GitHub", "https://github.com/sponsors/dougtrier"),
    ("Open Collective", "https://opencollective.com/trier-os"),
    ("Buy Me a Coffee", "https://www.buymeacoffee.com/dougtrier"),
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

        app_group = Adw.PreferencesGroup()
        header = Adw.ActionRow(title=APP_NAME, subtitle="Everything you know. Linux underneath.")
        icon = Gtk.Image.new_from_icon_name(APP_ID)
        icon.set_pixel_size(48)
        header.add_prefix(icon)
        app_group.add(header)
        app_group.add(Adw.ActionRow(title="Version", subtitle=__version__))
        license_row = Adw.ActionRow(title="License", subtitle="Apache License 2.0")
        license_row.add_suffix(self._link_button("https://www.apache.org/licenses/LICENSE-2.0"))
        app_group.add(license_row)
        app_group.add(Adw.ActionRow(title="Copyright", subtitle="Copyright 2026 Doug Trier"))
        page.add(app_group)

        creator_group = Adw.PreferencesGroup(title="Built by")
        creator_row = Adw.ActionRow(
            title="Doug Trier", subtitle=" · ".join(_TITLES), subtitle_lines=2
        )
        creator_row.add_prefix(Adw.Avatar(text="Doug Trier", show_initials=True, size=48))
        creator_group.add(creator_row)
        bio_row = Adw.ActionRow(use_markup=False)
        bio_row.set_subtitle(_BIO.format(years=_years_experience()))
        bio_row.set_subtitle_lines(6)
        creator_group.add(bio_row)
        page.add(creator_group)

        support_group = Adw.PreferencesGroup(
            title="Support this project",
            description="Trier Bridge is independent work. If it's useful to you, these are the "
            "real ways to say so.",
        )
        for title, url in _LINKS:
            row = Adw.ActionRow(title=title, subtitle=url)
            row.add_suffix(self._link_button(url))
            row.set_activatable(True)
            row.connect("activated", lambda *_r, u=url: self._open(u))
            support_group.add(row)
        page.add(support_group)

        self.append(page)

    def _link_button(self, url: str) -> Gtk.Button:
        button = Gtk.Button(icon_name="web-browser-symbolic", valign=Gtk.Align.CENTER)
        button.update_property([Gtk.AccessibleProperty.DESCRIPTION], [f"Open {url}"])
        button.connect("clicked", lambda *_b, u=url: self._open(u))
        return button

    def _open(self, url: str) -> None:
        res = self._launcher.open_uri(url)
        self._notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")
