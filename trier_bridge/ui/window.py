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

import logging

from pathlib import Path

from dataclasses import dataclass
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk  # noqa: E402

from .. import APP_NAME, __version__  # noqa: E402
from ..capability.model import CapabilityRecord, EnvironmentProfile  # noqa: E402
from ..state.journal import JournalRecord  # noqa: E402
from ..catalog.model import Catalog  # noqa: E402
from ..desktop.launch import Launcher, LaunchResult  # noqa: E402
from ..resources import catalog_path  # noqa: E402
from ..desktop.screenshot import ScreenshotRequest  # noqa: E402
from . import theme  # noqa: E402
from .about import AboutPage  # noqa: E402
from .pages import AppsPage, FilesPage, HomePage, Router, SettingsPage  # noqa: E402
from .devices import DeviceManagerPage, StartupPage  # noqa: E402
from .disks import DisksPage  # noqa: E402
from .eventviewer import EventViewerPage  # noqa: E402
from .help import HelpPage  # noqa: E402
from .printers import PrintersPage  # noqa: E402
from .integrations import IntegrationsPage, SetupDialog  # noqa: E402
from .network import NetworkPage  # noqa: E402
from .services import ServicesPage  # noqa: E402
from .taskmanager import TaskManagerPage  # noqa: E402
from .terminal import TerminalPage  # noqa: E402


log = logging.getLogger("trier_bridge.ui.window")


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
    Section("files", "Files", "folder-symbolic", "File Explorer", "Everyday", available=True),
    Section(
        "apps",
        "Apps",
        "view-grid-symbolic",
        "Start menu, Installed Apps",
        "Everyday",
        available=True,
    ),
    Section(
        "settings",
        "Settings",
        "preferences-system-symbolic",
        "Settings, Control Panel",
        "Everyday",
        available=True,
    ),
    Section(
        "printers",
        "Printers",
        "printer-symbolic",
        "Printers & scanners",
        "Everyday",
        available=True,
    ),
    Section(
        "network",
        "Network",
        "network-wired-symbolic",
        "Network Connections",
        "Everyday",
        available=True,
    ),
    Section(
        "taskmanager",
        "Task Manager",
        "utilities-system-monitor-symbolic",
        "Task Manager",
        "Troubleshooting",
        available=True,
    ),
    Section(
        "events",
        "Event Viewer",
        "document-open-recent-symbolic",
        "Event Viewer",
        "Troubleshooting",
        available=True,
    ),
    Section(
        "devices",
        "Device Manager",
        "computer-symbolic",
        "Device Manager",
        "Troubleshooting",
        available=True,
    ),
    Section(
        "startup",
        "Startup Apps",
        "system-run-symbolic",
        "Startup Apps, msconfig",
        "Troubleshooting",
        available=True,
    ),
    Section(
        "disks",
        "Disk Management",
        "drive-harddisk-symbolic",
        "Disk Management",
        "Troubleshooting",
        available=True,
    ),
    Section("services", "Services", "system-run-symbolic", "Services", "Advanced", available=True),
    Section(
        "terminal",
        "Command Prompt",
        "utilities-terminal-symbolic",
        "Command Prompt",
        "Advanced",
        available=True,
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
    Section(
        "about",
        "About Trier Bridge",
        "help-about-symbolic",
        "About [Program]",
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
        self._catalog = Catalog.load(catalog_path())
        self._launcher = Launcher()
        self._router = Router(
            self.select_section, self._launcher, {"screenshot": self._take_screenshot}
        )
        self._screenshot: ScreenshotRequest | None = None
        self._toasts = Adw.ToastOverlay()

        prefs = getattr(application, "preferences", None)
        self._hue = theme.clamp_hue(
            prefs.get("sidebar_hue") if prefs is not None else theme.DEFAULT_HUE
        )
        self._zoom = theme.clamp_zoom(
            prefs.get("ui_zoom_percent") if prefs is not None else theme.DEFAULT_ZOOM
        )
        self._css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self._css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self._apply_css()

        self._split = Adw.NavigationSplitView()
        self._split.set_sidebar(self._build_sidebar())
        self._content_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self._content_stack.add_css_class("tb-content-zoom")
        for section in SECTIONS:
            page = self._build_page(section)
            self._pages[section.key] = page
            self._content_stack.add_named(page, section.key)
        content_toolbar = Adw.ToolbarView()
        content_toolbar.add_top_bar(self._build_content_header())
        self._review_banner = Adw.Banner(revealed=False)
        self._review_banner.set_button_label("Mark reviewed")
        self._review_banner.connect("button-clicked", self._on_reviewed)
        self._review_records: list[JournalRecord] = []
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.append(self._review_banner)
        content_box.append(self._content_stack)
        self._content_stack.set_vexpand(True)
        content_toolbar.set_content(content_box)
        self._toasts.set_child(content_toolbar)
        self._split.set_content(Adw.NavigationPage.new(self._toasts, APP_NAME))
        outer = Adw.ToolbarView()
        outer.set_content(self._split)
        outer.add_bottom_bar(self._build_zoom_bar())
        self.set_content(outer)
        last = prefs.get("last_section") if prefs is not None else "home"
        self._select(last if any(sec.key == last for sec in SECTIONS) else "home")

    # ---- shell theming (TB-INV-252/253/254) ----------------------------------
    def _apply_css(self) -> None:
        css = theme.generate_css(self._hue, self._zoom)
        self._css_provider.load_from_data(css.encode("utf-8"))

    def _on_hue_changed(self, scale: Gtk.Scale) -> None:
        self._hue = theme.clamp_hue(int(scale.get_value()))
        self._apply_css()
        prefs = getattr(self.get_application(), "preferences", None)
        if prefs is not None:
            prefs.set("sidebar_hue", self._hue)

    def _set_zoom(self, value: int) -> None:
        self._zoom = theme.clamp_zoom(value)
        self._apply_css()
        self._zoom_scale.set_value(self._zoom)
        self._zoom_label.set_label(f"{self._zoom}%")
        prefs = getattr(self.get_application(), "preferences", None)
        if prefs is not None:
            prefs.set("ui_zoom_percent", self._zoom)

    def _on_zoom_changed(self, scale: Gtk.Scale) -> None:
        self._set_zoom(int(scale.get_value()))

    def _build_zoom_bar(self) -> Gtk.Box:
        bar = Gtk.Box(spacing=10, margin_start=16, margin_end=16, margin_top=6, margin_bottom=6)
        bar.add_css_class("tb-zoombar")
        label = Gtk.Label(label=f"{APP_NAME} · {__version__}", xalign=0.0, hexpand=True)
        bar.append(label)
        out_button = Gtk.Button(icon_name="zoom-out-symbolic", valign=Gtk.Align.CENTER)
        out_button.update_property([Gtk.AccessibleProperty.LABEL], ["Zoom out"])
        out_button.connect("clicked", lambda *_: self._set_zoom(self._zoom - 10))
        bar.append(out_button)
        self._zoom_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, theme.MIN_ZOOM, theme.MAX_ZOOM, 10
        )
        self._zoom_scale.set_size_request(120, -1)
        self._zoom_scale.set_draw_value(False)
        self._zoom_scale.set_value(self._zoom)
        self._zoom_scale.set_valign(Gtk.Align.CENTER)
        self._zoom_scale.update_property([Gtk.AccessibleProperty.LABEL], ["Zoom level"])
        self._zoom_scale.connect("value-changed", self._on_zoom_changed)
        bar.append(self._zoom_scale)
        in_button = Gtk.Button(icon_name="zoom-in-symbolic", valign=Gtk.Align.CENTER)
        in_button.update_property([Gtk.AccessibleProperty.LABEL], ["Zoom in"])
        in_button.connect("clicked", lambda *_: self._set_zoom(self._zoom + 10))
        bar.append(in_button)
        self._zoom_label = Gtk.Button(label=f"{self._zoom}%", valign=Gtk.Align.CENTER)
        self._zoom_label.add_css_class("flat")
        self._zoom_label.update_property([Gtk.AccessibleProperty.LABEL], ["Reset zoom to 100%"])
        self._zoom_label.connect("clicked", lambda *_: self._set_zoom(theme.DEFAULT_ZOOM))
        bar.append(self._zoom_label)
        return bar

    def show_unresolved(self, records: list[JournalRecord]) -> None:
        """Interrupted operations are surfaced, never silently repeated (TB-INV-060)."""
        self._review_records = list(records)
        if not records:
            self._review_banner.set_revealed(False)
            return
        first = records[0]
        more = f" and {len(records) - 1} more" if len(records) > 1 else ""
        self._review_banner.set_title(
            f"An earlier action was interrupted: {first.kind} on {first.target_label}{more}. "
            "It is not certain whether it took effect; check the current state before repeating it."
        )
        self._review_banner.set_revealed(True)
        log.info("review banner shown for %d interrupted operation(s)", len(records))

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
        scroller.set_vexpand(True)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        body.add_css_class("tb-sidebar")
        body.append(self._build_wordmark())
        body.append(self._build_hue_control())
        body.append(scroller)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        header.set_show_title(False)
        toolbar.add_top_bar(header)
        toolbar.set_content(body)
        return Adw.NavigationPage.new(toolbar, "Sections")

    def _build_wordmark(self) -> Gtk.Box:
        box = Gtk.Box(spacing=10, margin_start=20, margin_end=20, margin_top=18, margin_bottom=14)
        pill = Gtk.Label(label="T Bridge")
        pill.add_css_class("tb-wordmark-pill")
        box.append(pill)
        sub = Gtk.Label(label="for Linux")
        sub.add_css_class("tb-wordmark-sub")
        box.append(sub)
        return box

    def _build_hue_control(self) -> Gtk.Box:
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            margin_start=20,
            margin_end=20,
            margin_bottom=14,
        )
        label = Gtk.Label(label="SIDEBAR COLOR", xalign=0.0)
        label.add_css_class("caption-heading")
        label.add_css_class("tb-hue-label")
        box.append(label)
        scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, theme.MIN_HUE, theme.MAX_HUE, 1
        )
        scale.set_draw_value(False)
        scale.set_value(self._hue)
        scale.update_property([Gtk.AccessibleProperty.LABEL], ["Sidebar color"])
        scale.connect("value-changed", self._on_hue_changed)
        box.append(scale)
        return box

    def _group_header(self, row: Gtk.ListBoxRow, before: Gtk.ListBoxRow | None) -> None:
        section = SECTIONS[row.get_index()]
        prev = SECTIONS[before.get_index()] if before is not None else None
        if prev is None or prev.group != section.group:
            label = Gtk.Label(
                label=section.group, xalign=0.0, margin_start=12, margin_top=8, margin_bottom=2
            )
            label.add_css_class("caption-heading")
            label.add_css_class("tb-group-label")
            row.set_header(label)
        else:
            row.set_header(None)

    def _on_row_selected(self, _list: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        if row is not None:
            section = SECTIONS[row.get_index()]
            self._content_stack.set_visible_child_name(section.key)
            if section.key == "sysinfo":
                self._sysinfo.start()
            if section.key == "apps":
                self._apps_page.start()
            self._taskmanager.set_active(section.key == "taskmanager")
            if section.key == "events":
                self._events.start()
            if section.key == "network":
                self._network.start()
            if section.key == "disks":
                self._disks.start()
            if section.key == "devices":
                self._devices.start()
            if section.key == "services":
                self._services.start()
            if section.key == "startup":
                self._startup.start()
            if section.key == "printers":
                self._printers.start()
            if section.key == "integrations":
                self._integrations.refresh()
            self._title.set_title(section.title)
            self._title.set_subtitle(f"Windows: {section.familiar}")
            prefs = getattr(self.get_application(), "preferences", None)
            if prefs is not None and prefs.get("last_section") != section.key:
                prefs.set("last_section", section.key)  # durability reported by the result

    def _on_reviewed(self, _banner: Adw.Banner) -> None:
        """The person looked at the current state; the records stop asking (TB-INV-060)."""
        app = self.get_application()
        journal = getattr(app, "journal", None)
        if journal is None:
            return
        for rec in self._review_records:
            journal.resolve(rec, "reviewed by the user in the window")
        count = len(self._review_records)
        log.info("%d interrupted operation(s) marked reviewed", count)
        self.show_unresolved(journal.unresolved())
        self.notify(f"{count} interrupted action{'s' if count != 1 else ''} marked as reviewed.")

    def open_concept(self, concept_id: str) -> None:
        """Open a catalog concept by id (search provider results arrive this way)."""
        concept = self._catalog.get(concept_id)
        if concept is None:
            self.notify("That entry is not in this build of Trier Bridge. Nothing was changed.")
            return
        res = self._router.open(concept)
        self.notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")

    def _take_screenshot(self) -> LaunchResult:
        """Print Screen: the desktop's own screenshot UI through the portal (IMP-03.08)."""
        if self._screenshot is not None:
            return LaunchResult(False, "The screenshot tool is already open.")

        def done(result: LaunchResult) -> None:
            self._screenshot = None
            self.notify(result.plain)

        self._screenshot = ScreenshotRequest(done)
        started = self._screenshot.start()
        if not started.ok:
            self._screenshot = None
        return started

    def cancel_screenshot(self) -> None:
        if self._screenshot is not None:
            self._screenshot.cancel()

    def open_terminal_at(self, folder: str) -> None:
        self._select("terminal")
        self._terminal.change_folder(Path(folder))

    def show_setup(self) -> bool:
        """First-run setup: shown once, never again unless the ledger is reset."""
        app = self.get_application()
        SetupDialog(app.ledger, self.notify, self._after_setup).present(self)
        return False

    def _after_setup(self) -> None:
        self._integrations.refresh()

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

    def notify(self, text: str) -> None:
        """Plain-language result of an action, as a toast (screen readers announce toasts)."""
        self._toasts.add_toast(Adw.Toast(title=text, timeout=4))

    def _build_page(self, section: Section) -> Gtk.Widget:
        if section.key == "home":
            return HomePage(self._catalog, self._router, self.notify)
        if section.key == "files":
            app = self.get_application()
            return FilesPage(self._launcher, self.notify, getattr(app, "journal", None))
        if section.key == "apps":
            self._apps_page = AppsPage(self._launcher, self.notify)
            return self._apps_page
        if section.key == "settings":
            return SettingsPage(self._catalog, self._router, self.notify)
        if section.key == "taskmanager":
            app = self.get_application()
            self._taskmanager = TaskManagerPage(getattr(app, "journal", None), self.notify)
            return self._taskmanager
        if section.key == "events":
            self._events = EventViewerPage()
            return self._events
        if section.key == "printers":
            self._printers = PrintersPage(self._launcher, self.notify)
            return self._printers
        if section.key == "network":
            self._network = NetworkPage(self._launcher, self.notify)
            return self._network
        if section.key == "disks":
            self._disks = DisksPage(self._launcher, self.notify)
            return self._disks
        if section.key == "devices":
            self._devices = DeviceManagerPage()
            return self._devices
        if section.key == "services":
            app = self.get_application()
            self._services = ServicesPage(getattr(app, "journal", None), self.notify)
            return self._services
        if section.key == "terminal":
            app = self.get_application()
            start = str(getattr(app, "options", {}).get("cwd", "")) or None
            self._terminal = TerminalPage(
                getattr(app, "journal", None), self.notify, Path(start) if start else None
            )
            return self._terminal
        if section.key == "startup":
            self._startup = StartupPage()
            return self._startup
        if section.key == "sysinfo":
            from ..capability.discovery import Discovery
            from .sysinfo import SystemInfoPage

            def discover() -> tuple[EnvironmentProfile, list[CapabilityRecord]]:
                d = Discovery()
                return d.environment(), d.capabilities()

            self._sysinfo = SystemInfoPage(discover)
            return self._sysinfo
        if section.key == "help":
            app = self.get_application()
            return HelpPage(self._catalog, app.paths, self._launcher, self.notify)
        if section.key == "integrations":
            app = self.get_application()
            self._integrations = IntegrationsPage(app.ledger, self.notify)
            return self._integrations
        if section.key == "about":
            return AboutPage(self._launcher, self.notify)
        return self._status(section.title, NOT_YET, section.icon)

    def _status(self, title: str, description: str, icon: str) -> Gtk.Widget:
        page = Adw.StatusPage(title=title, description=description, icon_name=icon)
        page.update_property([Gtk.AccessibleProperty.DESCRIPTION], [description])
        return page


def Gio_menu() -> Any:
    from gi.repository import Gio

    model = Gio.Menu()
    model.append("Quit", "app.quit")
    return model
