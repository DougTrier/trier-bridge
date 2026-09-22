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
"""Everyday pages (Foundation 03): Home search, Files, Apps, Settings, Printers, Network.

Each page collects intent and shows structured results; opening anything goes
through the Router, which either switches a Trier Bridge section or asks the
desktop launcher. Every result is reported in plain words with the three
answers (docs/EXPERIENCE.md section 5).
"""
from __future__ import annotations

import logging
import threading
from functools import partial
from pathlib import Path
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from ..apps.inventory import DefaultApp, InstalledApp, default_apps, installed_apps  # noqa: E402
from ..catalog.model import Catalog, Concept, Equivalence, RouteKind  # noqa: E402
from ..desktop.launch import LaunchResult, Launcher, folder_path  # noqa: E402
from ..state.journal import OperationJournal  # noqa: E402
from ..system.driveletters import letters  # noqa: E402
from . import theme  # noqa: E402
from .filebrowser import FileBrowserPage  # noqa: E402
from ..operations.defaults import (  # noqa: E402
    Candidate,
    DefaultAppPlan,
    candidates,
    current_default,
    execute_default,
    plan_default,
)

log = logging.getLogger("trier_bridge.ui.pages")


class Router:
    """Opens a concept: Trier Bridge sections in-window, everything else via the desktop."""

    def __init__(
        self,
        select_section: Callable[[str], None],
        launcher: Launcher,
        actions: dict[str, Callable[[], LaunchResult]] | None = None,
    ) -> None:
        self._select = select_section
        self._launcher = launcher
        self._actions = actions or {}

    def show(self, section_key: str) -> None:
        """Switch to a Trier Bridge section by key; nothing on the computer is touched."""
        self._select(section_key)

    def open(self, concept: Concept) -> LaunchResult:
        if not concept.can_open:
            return LaunchResult(False, concept.mapping_note(), "teach-only")
        if concept.route.kind is RouteKind.SECTION:
            self._select(concept.route.target)
            return LaunchResult(True, f"Showing {concept.title}.")
        if concept.route.kind is RouteKind.ACTION:
            action = self._actions.get(concept.route.target)
            if action is None:
                return LaunchResult(False, "That action is not available in this build.")
            return action()
        return self._launcher.open(concept.route)


def _row(title: str = "", subtitle: str = "") -> Adw.ActionRow:
    """ActionRow with markup off: titles come from data and the system, not from us."""
    row = Adw.ActionRow(use_markup=False)
    row.set_title(title)
    row.set_subtitle(subtitle)
    return row


def _scrolled(child: Gtk.Widget) -> Gtk.ScrolledWindow:
    s = Gtk.ScrolledWindow(child=child, hscrollbar_policy=Gtk.PolicyType.NEVER)
    s.set_vexpand(True)
    return s


def _open_button(label: str, description: str, on_click: Callable[[], None]) -> Gtk.Button:
    b = Gtk.Button(label=label)
    b.set_valign(Gtk.Align.CENTER)
    b.update_property([Gtk.AccessibleProperty.DESCRIPTION], [description])
    b.connect("clicked", lambda *_: on_click())
    return b


def _app_icon(icon: str) -> Gtk.Image:
    """The program's own icon, as the desktop file names it; a generic one if it has none."""
    image = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
    if icon:
        try:
            image = Gtk.Image.new_from_gicon(Gio.Icon.new_for_string(icon))
        except GLib.Error:
            pass
    image.set_pixel_size(28)
    image.set_valign(Gtk.Align.CENTER)
    image.add_css_class("tb-app-icon")
    return image


def _report(notify: Callable[[str], None], action: Callable[[], LaunchResult]) -> None:
    """Run an open action and tell the user the plain result; a failure says nothing changed."""
    res = action()
    notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")


class HomePage(Gtk.Box):  # type: ignore[misc]
    """Search for anything you know from Windows, plus a card for each place people start."""

    # (section key, title, one line, icon, sidebar group) -- every card is a section
    # switch inside Trier Bridge; none of them reads or changes anything on its own.
    CARDS = (
        ("files", "Files", "Browse your folders and drives", "folder-symbolic", "Everyday"),
        (
            "taskmanager",
            "Task Manager",
            "What is running and how the system is doing",
            "utilities-system-monitor-symbolic",
            "Troubleshooting",
        ),
        (
            "network",
            "Network",
            "Adapters, addresses, and connections",
            "network-wired-symbolic",
            "Everyday",
        ),
        (
            "settings",
            "Settings",
            "The Linux equivalent of Control Panel",
            "preferences-system-symbolic",
            "Everyday",
        ),
        (
            "printers",
            "Printers",
            "Printers and scanners on this computer",
            "printer-symbolic",
            "Everyday",
        ),
        (
            "help",
            "Help",
            "Every translation this build knows",
            "help-browser-symbolic",
            "Trier Bridge",
        ),
    )

    def __init__(self, catalog: Catalog, router: Router, notify: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._catalog = catalog
        self._router = router
        self._notify = notify
        page = Adw.PreferencesPage()
        intro = Adw.PreferencesGroup(
            description=(
                "Type what you would look for on Windows: Task Manager, Add or Remove Programs, "
                "Downloads, Printers, Control Panel. Trier Bridge shows the Linux place for it "
                "and tells you when it is not the same."
            ),
        )
        self._entry = Gtk.SearchEntry(placeholder_text="Search Windows words…")
        self._entry.update_property(
            [Gtk.AccessibleProperty.LABEL], ["Search for anything you know from Windows"]
        )
        self._entry.connect("search-changed", self._on_search)
        intro.add(self._entry)
        page.add(intro)
        self._cards = Adw.PreferencesGroup(title="Start here")
        self._cards.add(self._build_cards())
        page.add(self._cards)
        self._results = Adw.PreferencesGroup(title="Results")
        self._rows: list[Gtk.Widget] = []
        page.add(self._results)
        self.append(_scrolled(page))
        self._show_groups()

    def _build_cards(self) -> Gtk.FlowBox:
        grid = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=True,
            min_children_per_line=2,
            max_children_per_line=3,
            column_spacing=12,
            row_spacing=12,
        )
        grid.set_can_focus(False)
        for key, title, line, icon, group in self.CARDS:
            card = Gtk.Button()
            card.add_css_class("flat")
            card.add_css_class("tb-card")
            card.update_property([Gtk.AccessibleProperty.LABEL], [f"{title}. {line}"])
            body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            chip = Gtk.Image.new_from_icon_name(icon)
            chip.set_pixel_size(20)
            chip.set_halign(Gtk.Align.START)
            chip.add_css_class("tb-card-icon")
            chip.add_css_class(theme.group_css_class(group))
            body.append(chip)
            name = Gtk.Label(label=title, xalign=0.0)
            name.add_css_class("tb-card-title")
            body.append(name)
            text = Gtk.Label(label=line, xalign=0.0, wrap=True)
            text.add_css_class("tb-card-text")
            body.append(text)
            card.set_child(body)
            card.connect("clicked", lambda *_b, k=key: self._router.show(k))
            child = Gtk.FlowBoxChild(child=card)
            child.set_can_focus(False)
            grid.append(child)
        return grid

    def _clear(self) -> None:
        for w in self._rows:
            self._results.remove(w)
        self._rows = []

    def _show_groups(self) -> None:
        self._clear()
        self._results.set_title("Familiar places")
        for concepts in self._catalog.by_group().values():
            for c in concepts[:4]:
                self._add_concept(c)

    def _on_search(self, entry: Gtk.SearchEntry) -> None:
        query = entry.get_text().strip()
        if not query:
            self._show_groups()
            return
        self._clear()
        matches = self._catalog.search(query)
        self._results.set_title(f"Results for “{query}”" if matches else "No matches")
        if not matches:
            row = _row(
                title="Nothing matched those words",
                subtitle="Try another Windows term, or look under Help. Nothing was changed.",
            )
            self._results.add(row)
            self._rows.append(row)
            return
        for m in matches:
            self._add_concept(m.concept)

    def _add_concept(self, c: Concept) -> None:
        row = _row(title=c.title, subtitle=f"{c.linux}\n{c.mapping_note()}")
        row.set_subtitle_lines(3)
        if c.equivalence is Equivalence.NONE:
            badge = Gtk.Label(label="No equivalent")
            badge.add_css_class("dim-label")
            badge.set_valign(Gtk.Align.CENTER)
            row.add_suffix(badge)
        elif c.can_open:
            label = {RouteKind.SECTION: "Show", RouteKind.ACTION: "Take"}.get(c.route.kind, "Open")
            row.add_suffix(
                _open_button(
                    label, f"{label} {c.title}. {c.mapping_note()}", partial(self._open, c)
                )
            )
        self._results.add(row)
        self._rows.append(row)

    def _open(self, c: Concept) -> None:
        res = self._router.open(c)
        self._notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")
        if not res.ok:
            log.info("open %s failed: %s", c.id, res.technical)


class FilesPage(Gtk.Box):  # type: ignore[misc]
    """Familiar places. Real local folders browse in-app (DEC-025); the three
    GVfs-virtual locations (Recycle Bin, Removable drives, Network) still hand off to
    Files, the Linux file manager, since they are not real paths ``filelisting`` can read.
    """

    PLACES = (
        ("This Computer", "home", "Your home folder"),
        ("Desktop", "desktop", ""),
        ("Documents", "documents", ""),
        ("Downloads", "download", ""),
        ("Pictures", "pictures", ""),
        ("Music", "music", ""),
        ("Videos", "videos", ""),
        ("Recycle Bin", "trash:///", "Deleted files you can restore"),
        ("Removable drives", "computer:///", "USB drives and discs"),
        ("Network", "network:///", "Shared folders on the network"),
    )

    def __init__(
        self,
        launcher: Launcher,
        notify: Callable[[str], None],
        journal: OperationJournal | None = None,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_vexpand(True)
        self._stack.add_named(self._build_overview(launcher, notify), "overview")

        browser_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        back_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        back_bar.set_margin_start(12)
        back_bar.set_margin_top(6)
        back = Gtk.Button(label="◀ Familiar places")
        back.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Return to the familiar places list. Nothing changes."],
        )
        back.connect("clicked", lambda *_: self._stack.set_visible_child_name("overview"))
        back_bar.append(back)
        browser_box.append(back_bar)
        self._browser = FileBrowserPage(launcher, notify, journal)
        browser_box.append(self._browser)
        self._stack.add_named(browser_box, "browser")

        self.append(self._stack)

    def _build_overview(self, launcher: Launcher, notify: Callable[[str], None]) -> Gtk.Widget:
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(
            title="Familiar places",
            description=(
                "Browse opens the place right here in Trier Bridge. Open uses Files, the "
                "Linux file manager, instead."
            ),
        )
        for title, key, hint in self.PLACES:
            is_virtual = "://" in key
            path = key if is_virtual else folder_path(key)
            subtitle = path or "Not set up on this computer"
            if hint:
                subtitle = f"{hint} · {subtitle}"
            row = _row(title=title, subtitle=subtitle)
            if path and not is_virtual:
                row.add_suffix(
                    _open_button(
                        "Browse",
                        f"Browse {title} in Trier Bridge. Nothing is changed.",
                        partial(self._browse, Path(path)),
                    )
                )
            if path:
                row.add_suffix(
                    _open_button(
                        "Open",
                        f"Open {title} in Files. Nothing is changed.",
                        partial(self._open, launcher, notify, key, title),
                    )
                )
            group.add(row)
        page.add(group)
        drives = Adw.PreferencesGroup(
            title="Drives",
            description="C: is the Linux system drive; other mounted volumes get the next letters. "
            "The real folder is shown; Browse stays in Trier Bridge, Open uses Files.",
        )
        for d in letters():
            what = "/" if d.mount_point == "/" else d.mount_point
            row = _row(title=f"{d.display}  {d.label}", subtitle=what)
            row.add_suffix(
                _open_button(
                    "Browse",
                    f"Browse {d.display} ({what}) in Trier Bridge. Nothing is changed.",
                    partial(self._browse, Path(what)),
                )
            )
            row.add_suffix(
                _open_button(
                    "Open",
                    f"Open {d.display} ({what}) in Files. Nothing is changed.",
                    partial(self._open, launcher, notify, f"file://{what}", d.display),
                )
            )
            drives.add(row)
        page.add(drives)
        tips = Adw.PreferencesGroup(title="What works the same")
        for t, s in (
            ("Copy, cut, paste", "Ctrl+C, Ctrl+X, Ctrl+V in Files, just like Explorer."),
            ("Right-click", "Open, Open With, Cut, Copy, Rename, Move to Trash, Properties."),
            (
                "Drag and drop",
                "Drag moves within a drive and copies across drives; hold Ctrl to copy.",
            ),
            ("Delete", "Delete moves to the Recycle Bin (Trash); Shift+Delete deletes for good."),
        ):
            tips.add(_row(title=t, subtitle=s))
        page.add(tips)
        return _scrolled(page)

    def _browse(self, path: Path) -> None:
        self._browser.navigate_to(path)
        self._stack.set_visible_child_name("browser")

    @staticmethod
    def _open(launcher: Launcher, notify: Callable[[str], None], key: str, title: str) -> None:
        res = launcher.show_folder(key)
        notify(f"{title}: {res.plain}" if res.ok else f"{res.plain} Nothing was changed.")


class AppsPage(Gtk.Box):  # type: ignore[misc]
    """Installed Apps with provenance, and current default apps. Read-only in this foundation."""

    def __init__(self, launcher: Launcher, notify: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._launcher = launcher
        self._notify = notify
        self._apps: list[InstalledApp] = []
        page = Adw.PreferencesPage()
        self._entry = Gtk.SearchEntry(placeholder_text="Find an installed program…")
        self._entry.update_property([Gtk.AccessibleProperty.LABEL], ["Find an installed program"])
        self._entry.connect("search-changed", lambda *_: self._render())
        top = Adw.PreferencesGroup(
            title="Installed Apps",
            description=(
                "One list, several package systems. Each program shows where it came from "
                "(system package, Snap, Flatpak, or this user). Uninstalling arrives in a later "
                "foundation; nothing here changes the computer."
            ),
        )
        top.add(self._entry)
        page.add(top)
        self._list_group = Adw.PreferencesGroup()
        page.add(self._list_group)
        self._defaults_group = Adw.PreferencesGroup(
            title="Default apps",
            description=(
                "Which program opens which kind of file. Pick another listed program and "
                "press Set; this is your own setting and choosing the previous program "
                "again undoes it."
            ),
        )
        page.add(self._defaults_group)
        self.append(_scrolled(page))
        self._rows: list[Gtk.Widget] = []
        self._default_rows: list[Gtk.Widget] = []
        self._loading = _row(title="Reading installed programs…")
        self._list_group.add(self._loading)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        threading.Thread(target=self._worker, name="tb-apps", daemon=True).start()

    def _worker(self) -> None:
        try:
            apps = installed_apps()
            defaults = default_apps()
        except Exception as exc:
            log.exception("app inventory failed")
            GLib.idle_add(self._fail, str(exc))
            return
        GLib.idle_add(self._loaded, apps, defaults)

    def _fail(self, text: str) -> bool:
        self._loading.set_title("Installed programs could not be read")
        self._loading.set_subtitle(f"Nothing was changed. Technical detail: {text}")
        return False

    def _loaded(self, apps: list[InstalledApp], defaults: list[DefaultApp]) -> bool:
        self._apps = apps
        self._list_group.remove(self._loading)
        self._render()
        for d in defaults:
            row = _row(title=d.label, subtitle=d.app_name or "Nothing is set")
            self._add_default_chooser(row, d)
            self._defaults_group.add(row)
            self._default_rows.append(row)
        return False

    def _add_default_chooser(self, row: Adw.ActionRow, d: DefaultApp) -> None:
        options = candidates(d.mime_type)
        if not options:
            return
        names = Gtk.StringList.new([c.name for c in options])
        drop = Gtk.DropDown(model=names)
        drop.set_valign(Gtk.Align.CENTER)
        # GTK names a drop-down after its selected item; the purpose goes in the description.
        drop.update_property([Gtk.AccessibleProperty.DESCRIPTION], [f"Program for {d.label}"])
        current = next((i for i, c in enumerate(options) if c.desktop_id == d.desktop_id), 0)
        drop.set_selected(current)
        row.add_suffix(drop)
        row.add_suffix(
            _open_button(
                "Set",
                f"Make the chosen program open {d.label}; asks first.",
                partial(self._set_default, row, d, options, drop),
            )
        )

    def _set_default(
        self, row: Adw.ActionRow, d: DefaultApp, options: list[Candidate], drop: Gtk.DropDown
    ) -> None:
        chosen = options[int(drop.get_selected())]
        plan = plan_default(d.mime_type, d.label, chosen.desktop_id)
        if not isinstance(plan, DefaultAppPlan):
            self._notify(plan.plain)
            return
        dialog = Adw.AlertDialog(heading=f"Open {d.label} with {chosen.name}?", body=plan.preview)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("set", "Set as default")
        dialog.set_response_appearance("set", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", partial(self._on_set_default, row, d, plan))
        dialog.present(self.get_root())

    def _on_set_default(
        self,
        row: Adw.ActionRow,
        d: DefaultApp,
        plan: DefaultAppPlan,
        _dialog: Adw.AlertDialog,
        response: str,
    ) -> None:
        if response != "set":
            self._notify(f"Cancelled. {d.label} still open with {d.app_name or 'nothing'}.")
            return
        app = self.get_root().get_application()
        journal = getattr(app, "journal", None)

        def work() -> None:
            result = execute_default(plan, journal)
            now = current_default(d.mime_type)
            GLib.idle_add(self._default_done, row, result.plain, now.name if now else "")

        threading.Thread(target=work, name="tb-default-app", daemon=True).start()

    def _default_done(self, row: Adw.ActionRow, plain: str, app_name: str) -> bool:
        row.set_subtitle(app_name or "Nothing is set")
        self._notify(plain)
        return False

    def _render(self) -> None:
        for w in self._rows:
            self._list_group.remove(w)
        self._rows = []
        q = self._entry.get_text().strip().casefold()
        shown = [
            a for a in self._apps if not q or q in a.name.casefold() or q in a.comment.casefold()
        ]
        self._list_group.set_title(f"{len(shown)} of {len(self._apps)} programs")
        for a in shown[:200]:
            row = _row(title=a.name, subtitle=a.comment or a.desktop_id)
            row.add_prefix(_app_icon(a.icon))
            badge = Gtk.Label(label=a.provenance.label)
            badge.add_css_class("tb-pill")
            badge.add_css_class("tb-pill-neutral")
            badge.set_valign(Gtk.Align.CENTER)
            row.add_suffix(badge)
            row.set_tooltip_text(a.source_path)
            row.add_suffix(
                _open_button(
                    "Open",
                    f"Start {a.name} ({a.provenance.label}).",
                    partial(self._open, a),
                )
            )
            self._list_group.add(row)
            self._rows.append(row)
        if len(shown) > 200:
            more = _row(title=f"{len(shown) - 200} more; narrow the search to see them")
            self._list_group.add(more)
            self._rows.append(more)

    def _open(self, a: InstalledApp) -> None:
        res = self._launcher.launch_app(a.desktop_id)
        self._notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")


class SettingsPage(Gtk.Box):  # type: ignore[misc]
    """Familiar settings names routed to the desktop's own Settings panels."""

    def __init__(self, catalog: Catalog, router: Router, notify: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(
            title="Settings",
            description=(
                "The names you know, routed to the right place in Linux Settings. "
                "Opening a panel changes nothing until you change something there."
            ),
        )
        for c in catalog.concepts:
            if c.route.kind in (RouteKind.GNOME_SETTINGS, RouteKind.APP) and c.group == "Everyday":
                row = _row(title=c.title, subtitle=f"{c.linux}\n{c.mapping_note()}")
                row.set_subtitle_lines(3)
                row.add_suffix(
                    _open_button(
                        "Open",
                        f"Open {c.title}. {c.mapping_note()}",
                        partial(_report, notify, partial(router.open, c)),
                    )
                )
                group.add(row)
        page.add(group)
        self.append(_scrolled(page))
