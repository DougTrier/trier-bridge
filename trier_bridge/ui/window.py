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
"""Main window: sidebar of familiar places and tools, content on the right.

Foundation 01 ships the shell only. Every view that is not implemented says
so in plain words and states that nothing on the computer is read or changed
(TB-INV-004: never display availability without evidence). Every sidebar row
carries an accessible label and description (TB-INV-209).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from .. import APP_NAME, __version__  # noqa: E402
from ..capability.model import CapabilityRecord, EnvironmentProfile  # noqa: E402


@dataclass(frozen=True)
class Section:
    key: str
    title: str
    icon: str
    familiar: str  # the Windows concept the user already knows
    group: str
    available: bool = False


SECTIONS: tuple[Section, ...] = (
    Section("home", "Home", "go-home-symbolic", "Start", "Everyday", available=True),
    Section("files", "Files", "folder-symbolic", "File Explorer", "Everyday"),
    Section("apps", "Apps", "view-grid-symbolic", "Start menu, Installed Apps", "Everyday"),
    Section(
        "settings", "Settings", "preferences-system-symbolic", "Settings, Control Panel", "Everyday"
    ),
    Section("printers", "Printers", "printer-symbolic", "Printers & scanners", "Everyday"),
    Section("network", "Network", "network-wired-symbolic", "Network Connections", "Everyday"),
    Section(
        "taskmanager",
        "Task Manager",
        "utilities-system-monitor-symbolic",
        "Task Manager",
        "Troubleshooting",
    ),
    Section(
        "events", "Event Viewer", "document-open-recent-symbolic", "Event Viewer", "Troubleshooting"
    ),
    Section("devices", "Device Manager", "computer-symbolic", "Device Manager", "Troubleshooting"),
    Section(
        "disks", "Disk Management", "drive-harddisk-symbolic", "Disk Management", "Troubleshooting"
    ),
    Section("services", "Services", "system-run-symbolic", "Services", "Advanced"),
    Section(
        "terminal", "Command Prompt", "utilities-terminal-symbolic", "Command Prompt", "Advanced"
    ),
    Section(
        "sysinfo",
        "System Information",
        "dialog-information-symbolic",
        "System Information (msinfo32)",
        "Advanced",
        available=True,
    ),
    Section(
        "integrations",
        "Integrations",
        "emblem-system-symbolic",
        "Setup choices",
        "Trier Bridge",
        available=True,
    ),
    Section("help", "Help", "help-browser-symbolic", "Help", "Trier Bridge", available=True),
)

NOT_YET = (
    "This view is not available in this build. Nothing on this computer is read or changed "
    "from here yet. It will appear in a later Trier Bridge foundation."
)


class MainWindow(Adw.ApplicationWindow):  # type: ignore[misc]
    def __init__(self, application: Adw.Application) -> None:
        super().__init__(application=application, title=APP_NAME)
        self.set_default_size(960, 640)
        self.set_size_request(360, 400)
        self._pages: dict[str, Gtk.Widget] = {}

        self._split = Adw.NavigationSplitView()
        self._split.set_sidebar(self._build_sidebar())
        self._content_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        for section in SECTIONS:
            page = self._build_page(section)
            self._pages[section.key] = page
            self._content_stack.add_named(page, section.key)
        content_toolbar = Adw.ToolbarView()
        content_toolbar.add_top_bar(self._build_content_header())
        content_toolbar.set_content(self._content_stack)
        self._split.set_content(Adw.NavigationPage.new(content_toolbar, APP_NAME))
        self.set_content(self._split)
        self._select("home")

    # ---- sidebar ------------------------------------------------------------
    def _build_sidebar(self) -> Adw.NavigationPage:
        self._list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self._list.add_css_class("navigation-sidebar")
        self._list.update_property([Gtk.AccessibleProperty.LABEL], ["Trier Bridge sections"])
        self._list.set_header_func(self._group_header)
        for section in SECTIONS:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(spacing=12, margin_top=6, margin_bottom=6, margin_start=6, margin_end=6)
            box.append(Gtk.Image.new_from_icon_name(section.icon))
            label = Gtk.Label(label=section.title, xalign=0.0)
            box.append(label)
            row.set_child(box)
            desc = f"Windows: {section.familiar}."
            if not section.available:
                desc += " Not available in this build."
            row.update_property(
                [Gtk.AccessibleProperty.LABEL, Gtk.AccessibleProperty.DESCRIPTION],
                [section.title, desc],
            )
            self._list.append(row)
        self._list.connect("row-selected", self._on_row_selected)
        scroller = Gtk.ScrolledWindow(child=self._list, hscrollbar_policy=Gtk.PolicyType.NEVER)
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=APP_NAME, subtitle="Everything you know"))
        toolbar.add_top_bar(header)
        toolbar.set_content(scroller)
        return Adw.NavigationPage.new(toolbar, "Sections")

    def _group_header(self, row: Gtk.ListBoxRow, before: Gtk.ListBoxRow | None) -> None:
        section = SECTIONS[row.get_index()]
        prev = SECTIONS[before.get_index()] if before is not None else None
        if prev is None or prev.group != section.group:
            label = Gtk.Label(
                label=section.group, xalign=0.0, margin_start=12, margin_top=8, margin_bottom=2
            )
            label.add_css_class("dim-label")
            label.add_css_class("caption-heading")
            row.set_header(label)
        else:
            row.set_header(None)

    def _on_row_selected(self, _list: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        if row is not None:
            section = SECTIONS[row.get_index()]
            self._content_stack.set_visible_child_name(section.key)
            if section.key == "sysinfo":
                self._sysinfo.start()
            self._title.set_title(section.title)
            self._title.set_subtitle(f"Windows: {section.familiar}")

    def select_section(self, key: str) -> None:
        """Public for tests and development aids: select a sidebar section by key."""
        self._select(key)

    def _select(self, key: str) -> None:
        for index, section in enumerate(SECTIONS):
            if section.key == key:
                self._list.select_row(self._list.get_row_at_index(index))
                return

    # ---- content -------------------------------------------------------------
    def _build_content_header(self) -> Adw.HeaderBar:
        header = Adw.HeaderBar()
        self._title = Adw.WindowTitle(title="Home", subtitle="")
        header.set_title_widget(self._title)
        menu = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu.update_property([Gtk.AccessibleProperty.LABEL], ["Main menu"])
        model = Gio_menu()
        menu.set_menu_model(model)
        header.pack_end(menu)
        return header

    def _build_page(self, section: Section) -> Gtk.Widget:
        if section.key == "home":
            return self._home_page()
        if section.key == "sysinfo":
            from ..capability.discovery import Discovery
            from .sysinfo import SystemInfoPage

            def discover() -> tuple[EnvironmentProfile, list[CapabilityRecord]]:
                d = Discovery()
                return d.environment(), d.capabilities()

            self._sysinfo = SystemInfoPage(discover)
            return self._sysinfo
        if section.key == "help":
            return self._status(
                "Help",
                "The Manual is optional. A normal user should be productive without it. "
                "Help content arrives with the features it explains.",
                "help-browser-symbolic",
            )
        if section.key == "integrations":
            return self._status(
                "Integrations",
                "Nothing has been integrated into your desktop. The setup screen that lets you "
                "choose integrations in groups arrives in a later foundation. Until then Trier "
                "Bridge is only this window.",
                "emblem-system-symbolic",
            )
        return self._status(section.title, NOT_YET, section.icon)

    def _status(self, title: str, description: str, icon: str) -> Gtk.Widget:
        page = Adw.StatusPage(title=title, description=description, icon_name=icon)
        page.update_property([Gtk.AccessibleProperty.DESCRIPTION], [description])
        return page

    def _home_page(self) -> Gtk.Widget:
        text = (
            f"Trier Bridge {__version__} (Foundation 02).\n\n"
            "This build shows where familiar things will live. The only thing it reads on this "
            "computer is the read-only check under System Information; it changes nothing."
        )
        return self._status("Everything you know. Linux underneath.", text, "go-home-symbolic")


def Gio_menu() -> Any:
    from gi.repository import Gio

    model = Gio.Menu()
    model.append("About Trier Bridge", "app.about")
    model.append("Quit", "app.quit")
    return model
