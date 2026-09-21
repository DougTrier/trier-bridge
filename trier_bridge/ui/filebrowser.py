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
"""In-app file browser (DEC-025, DOC-02): navigate, list, sort, open, and —
Phase 2 — rename/cut/copy/paste/delete/new folder through the already-proven
typed operations in ``operations/files.py``: the same ``plan_file``/
``execute_file`` pair the Bridge Terminal's ``del``/``move``/``copy``/``ren``/
``mkdir`` already use, with the same confirmation dialog, the same
never-overwrite and Trash-first behavior, and the same TOCTOU-safe identity
revalidation (TB-INV-050). Nothing here calls a shell or writes through any
other path.

A double-click or Enter on a folder navigates into it; on a file, it opens
with the desktop's default app via ``Launcher.open_uri`` — never a custom
parser or opener (TB-INV-239). Special files (devices, sockets, FIFOs) and
broken symlinks are named honestly and never opened (TB-INV-243, TB-INV-244).
After any mutation the current folder is re-listed from disk, never assumed
(TB-INV-006).

"This PC" is a virtual root, not a real path: it lists the drive letters from
``driveletters.py`` the same way Explorer's This PC lists drives, then hands
off to ``filelisting.list_directory`` for every real folder under them. Going
up from a drive's own mount point returns to This PC rather than walking past
it, mirroring how going up from ``C:\\`` in Explorer reaches This PC and no
further — the real filesystem does not end there, but the familiar picture
does (TB-INV-242: labeling only, never a claim about what is reachable).
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..core.operations import OperationResult  # noqa: E402
from ..desktop.launch import Launcher  # noqa: E402
from ..operations.files import FilePlan, execute_file, plan_file  # noqa: E402
from ..state.journal import OperationJournal  # noqa: E402
from ..system.driveletters import DriveLetter, letters  # noqa: E402
from ..system.filelisting import FileEntry, ListResult, list_directory  # noqa: E402

log = logging.getLogger("trier_bridge.ui.filebrowser")

VISIBLE_CAP = 500  # matches the _ProcessList convention: cap widgets, offer search to narrow

KIND_LABEL = {
    "dir": "File folder",
    "file": "File",
    "symlink_dir": "Shortcut to a folder",
    "symlink_file": "Shortcut to a file",
    "symlink_broken": "Broken shortcut",
    "device": "Device",
    "socket": "Socket",
    "fifo": "Named pipe",
    "unknown": "Unknown item",
}


def _fmt_size(n: int | None) -> str:
    if n is None:
        return ""
    for unit, size in (("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if n >= size:
            return f"{n / size:.1f} {unit}"
    return f"{n} bytes"


def _fmt_date(ts: float | None) -> str:
    if ts is None:
        return ""
    try:
        return datetime.fromtimestamp(ts).strftime("%m/%d/%Y %I:%M %p")
    except (OSError, OverflowError, ValueError):
        return ""


@dataclass(frozen=True)
class _Row:
    """One line the list view renders, whether it came from a folder or This PC."""

    name: str
    subtitle: str
    hidden: bool
    activate: Callable[[], None]
    entry: FileEntry | None = None  # None for This PC's drive rows: no file actions there


class FileBrowserPage(Gtk.Box):  # type: ignore[misc]
    """A real, in-app, Explorer-shaped view over a real Linux path."""

    def __init__(
        self,
        launcher: Launcher,
        notify: Callable[[str], None],
        journal: OperationJournal | None = None,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._launcher = launcher
        self._notify = notify
        self._journal = journal
        self._current: Path | None = None  # None = This PC
        self._back: list[Path | None] = []
        self._forward: list[Path | None] = []
        self._show_hidden = False
        self._letters: list[DriveLetter] = []
        self._rows_data: list[_Row] = []
        self._generation = 0  # discards a stale worker result from a superseded navigation
        self._clipboard: tuple[Path, str] | None = None  # (source, "copy" | "move")

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        toolbar.set_margin_top(12)
        self._back_btn = self._nav_button("go-previous-symbolic", "Back", self._go_back)
        self._fwd_btn = self._nav_button("go-next-symbolic", "Forward", self._go_forward)
        self._up_btn = self._nav_button("go-up-symbolic", "Up", self._go_up)
        toolbar.append(self._back_btn)
        toolbar.append(self._fwd_btn)
        toolbar.append(self._up_btn)
        self._crumb_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self._crumb_box.set_hexpand(True)
        crumb_scroll = Gtk.ScrolledWindow(
            child=self._crumb_box, vscrollbar_policy=Gtk.PolicyType.NEVER
        )
        crumb_scroll.set_hexpand(True)
        toolbar.append(crumb_scroll)
        self._hidden_toggle = Gtk.ToggleButton(label="Hidden items")
        self._hidden_toggle.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Show files and folders whose name starts with a dot. Nothing is changed."],
        )
        self._hidden_toggle.connect("toggled", self._on_hidden_toggled)
        toolbar.append(self._hidden_toggle)
        self.append(toolbar)

        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        search_row.set_margin_start(12)
        search_row.set_margin_end(12)
        self._search = Gtk.SearchEntry(placeholder_text="Search this folder…")
        self._search.update_property(
            [Gtk.AccessibleProperty.LABEL], ["Search the current folder by name"]
        )
        self._search.set_hexpand(True)
        self._search.connect("search-changed", lambda *_: self._render())
        search_row.append(self._search)
        self._new_folder_btn = Gtk.Button(label="New folder")
        self._new_folder_btn.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Create a new, empty folder here. You will be asked to confirm."],
        )
        self._new_folder_btn.connect("clicked", lambda *_: self._start_new_folder())
        search_row.append(self._new_folder_btn)
        self._paste_btn = Gtk.Button(label="Paste")
        self._paste_btn.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Paste the cut or copied item here. You will be asked to confirm."],
        )
        self._paste_btn.connect("clicked", lambda *_: self._do_paste())
        search_row.append(self._paste_btn)
        self.append(search_row)

        self._status = Adw.ActionRow(use_markup=False)
        self._status.set_margin_start(12)
        self._status.set_margin_end(12)
        self._status.set_visible(False)
        self.append(self._status)

        self._list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self._list.add_css_class("boxed-list")
        self._list.set_margin_start(12)
        self._list.set_margin_end(12)
        self._list.set_margin_bottom(12)
        self._list.connect("row-activated", self._on_row_activated)
        scroller = Gtk.ScrolledWindow(child=self._list, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroller.set_vexpand(True)
        self.append(scroller)

        self._summary = Gtk.Label(xalign=0.0, margin_start=12, margin_bottom=6)
        self._summary.add_css_class("dim-label")
        self.append(self._summary)

        self._show_this_pc(record_history=False)

    # ---- small widget builders -------------------------------------------------
    def _nav_button(self, icon: str, description: str, on_click: Callable[[], None]) -> Gtk.Button:
        b = Gtk.Button(icon_name=icon)
        b.update_property([Gtk.AccessibleProperty.LABEL], [description])
        b.connect("clicked", lambda *_: on_click())
        return b

    # ---- navigation --------------------------------------------------------
    def navigate_to(self, path: Path) -> None:
        """Public entry point: jump straight to a real folder (e.g. from a drive row)."""
        self._load(path)

    def _push_history(self) -> None:
        self._back.append(self._current)
        self._forward.clear()

    def _go_back(self) -> None:
        if not self._back:
            return
        self._forward.append(self._current)
        target = self._back.pop()
        self._load(target, record_history=False)

    def _go_forward(self) -> None:
        if not self._forward:
            return
        self._back.append(self._current)
        target = self._forward.pop()
        self._load(target, record_history=False)

    def _go_up(self) -> None:
        if self._current is None:
            return
        if self._is_drive_root(self._current):
            self._load(None)
            return
        self._load(self._current.parent)

    def _is_drive_root(self, path: Path) -> bool:
        return any(Path(d.mount_point) == path for d in self._letters)

    def _load(self, path: Path | None, record_history: bool = True) -> None:
        if record_history and path != self._current:
            self._push_history()
        if path is None:
            self._show_this_pc(record_history=False)
            return
        self._generation += 1
        gen = self._generation
        show_hidden = self._show_hidden
        threading.Thread(
            target=self._worker, args=(path, show_hidden, gen), name="tb-filebrowser", daemon=True
        ).start()

    def _worker(self, path: Path, show_hidden: bool, gen: int) -> None:
        try:
            result = list_directory(path, show_hidden)
        except Exception as exc:  # a real, unexpected fault: report it, never crash the page
            log.exception("directory listing failed for %s", path)
            GLib.idle_add(self._apply_error, path, str(exc), gen)
            return
        GLib.idle_add(self._apply, path, result, gen)

    # ---- rendering -----------------------------------------------------------
    def _show_this_pc(self, record_history: bool) -> None:
        if record_history and self._current is not None:
            self._push_history()
        self._current = None
        self._letters = list(letters())
        self._rows_data = [
            _Row(
                name=f"{d.display}  {d.label}",
                subtitle=d.mount_point,
                hidden=False,
                activate=partial(self.navigate_to, Path(d.mount_point)),
            )
            for d in self._letters
        ]
        self._status.set_visible(False)
        self._render()
        self._update_breadcrumb()
        self._update_nav_buttons()
        self._update_action_buttons()

    def _apply(self, path: Path, result: ListResult, gen: int) -> bool:
        if gen != self._generation:
            return False  # a later navigation already superseded this
        self._current = path
        if not self._letters:
            self._letters = list(letters())
        if result.error or result.denied:
            self._rows_data = []
            self._status.set_title("This folder could not be opened")
            self._status.set_subtitle(f"{result.error or 'Access is denied.'} Nothing was changed.")
            self._status.set_visible(True)
        else:
            self._status.set_visible(False)
            self._rows_data = [
                _Row(
                    name=e.name,
                    subtitle=self._entry_subtitle(e),
                    hidden=e.hidden,
                    activate=partial(self._activate_entry, e),
                    entry=e,
                )
                for e in result.entries
            ]
            if result.truncated_count:
                self._status.set_title("This folder is large")
                self._status.set_subtitle(
                    f"Showing the first {len(result.entries)} items; "
                    f"{result.truncated_count} more were left out. Nothing was changed."
                )
                self._status.set_visible(True)
        self._render()
        self._update_breadcrumb()
        self._update_nav_buttons()
        self._update_action_buttons()
        return False

    def _apply_error(self, path: Path, text: str, gen: int) -> bool:
        if gen != self._generation:
            return False
        self._current = path
        self._rows_data = []
        self._status.set_title("This folder could not be read")
        self._status.set_subtitle(f"Nothing was changed. Technical detail: {text}")
        self._status.set_visible(True)
        self._render()
        self._update_breadcrumb()
        self._update_nav_buttons()
        self._update_action_buttons()
        return False

    @staticmethod
    def _entry_subtitle(e: FileEntry) -> str:
        parts = [KIND_LABEL.get(e.kind, e.kind)]
        size = _fmt_size(e.size_bytes)
        if size:
            parts.append(size)
        date = _fmt_date(e.modified)
        if date:
            parts.append(date)
        return " · ".join(parts)

    def _activate_entry(self, e: FileEntry) -> None:
        if e.is_navigable:
            self.navigate_to(e.path)
            return
        if e.kind in ("file", "symlink_file"):
            uri = GLib.filename_to_uri(str(e.path), None)
            res = self._launcher.open_uri(uri)
            self._notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")
            return
        # devices, sockets, FIFOs, broken symlinks, unknown: named honestly, never opened blindly
        self._notify(
            f"{e.name} is a {KIND_LABEL.get(e.kind, e.kind).lower()}; "
            "Trier Bridge does not open that kind of item."
        )

    def _on_row_activated(self, _box: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        activate = getattr(row, "tb_activate", None)
        if activate is not None:
            activate()

    def _on_hidden_toggled(self, toggle: Gtk.ToggleButton) -> None:
        self._show_hidden = toggle.get_active()
        if self._current is not None:
            self._load(self._current, record_history=False)

    def _render(self) -> None:
        q = self._search.get_text().strip().casefold()
        shown = [
            r
            for r in self._rows_data
            if (not r.hidden or self._show_hidden) and (not q or q in r.name.casefold())
        ]
        while (child := self._list.get_row_at_index(0)) is not None:
            self._list.remove(child)
        for r in shown[:VISIBLE_CAP]:
            row = Adw.ActionRow(use_markup=False, title=r.name, subtitle=r.subtitle)
            row.tb_activate = r.activate
            row.update_property([Gtk.AccessibleProperty.LABEL], [f"{r.name}, {r.subtitle}"])
            if r.entry is not None:
                menu_btn = Gtk.MenuButton(icon_name="view-more-symbolic")
                menu_btn.set_valign(Gtk.Align.CENTER)
                menu_btn.add_css_class("flat")
                menu_btn.update_property([Gtk.AccessibleProperty.LABEL], [f"Actions for {r.name}"])
                menu_btn.set_popover(self._build_entry_popover(r.entry))
                row.add_suffix(menu_btn)
            self._list.append(row)
        if len(shown) > VISIBLE_CAP:
            more = Adw.ActionRow(use_markup=False)
            more.set_title(f"{len(shown) - VISIBLE_CAP} more; search narrows the list")
            self._list.append(more)
        label = "This PC" if self._current is None else str(self._current)
        count = len(shown)
        noun = "drive" if self._current is None else "item"
        self._summary.set_text(f"{label} · {count} {noun}{'s' if count != 1 else ''}")

    def _update_nav_buttons(self) -> None:
        self._back_btn.set_sensitive(bool(self._back))
        self._fwd_btn.set_sensitive(bool(self._forward))
        self._up_btn.set_sensitive(self._current is not None)

    def _update_breadcrumb(self) -> None:
        while (child := self._crumb_box.get_first_child()) is not None:
            self._crumb_box.remove(child)
        self._crumb_box.append(
            self._crumb_button("This PC", None, is_current=self._current is None)
        )
        if self._current is None:
            return
        owner = max(
            (d for d in self._letters if str(self._current).startswith(d.mount_point)),
            key=lambda d: len(d.mount_point),
            default=None,
        )
        if owner is None:
            for i, part in enumerate(self._current.parts):
                cumulative = Path(*self._current.parts[: i + 1])
                self._crumb_box.append(
                    self._crumb_button(part, cumulative, is_current=cumulative == self._current)
                )
            return
        drive_root = Path(owner.mount_point)
        self._crumb_box.append(
            self._crumb_button(owner.display, drive_root, is_current=self._current == drive_root)
        )
        try:
            rel = self._current.relative_to(drive_root)
        except ValueError:
            return
        cumulative = drive_root
        for part in rel.parts:
            cumulative = cumulative / part
            self._crumb_box.append(
                self._crumb_button(part, cumulative, is_current=cumulative == self._current)
            )

    def _crumb_button(self, label: str, target: Path | None, is_current: bool) -> Gtk.Widget:
        if is_current:
            lbl = Gtk.Label(label=label)
            lbl.add_css_class("heading")
            lbl.set_margin_start(4)
            lbl.set_margin_end(4)
            return lbl
        b = Gtk.Button(label=label)
        b.add_css_class("flat")
        b.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION], [f"Go to {label}. Nothing changes."]
        )
        if target is None:
            b.connect("clicked", lambda *_: self._nav_to(None))
        else:
            b.connect("clicked", lambda *_, t=target: self._nav_to(t))
        sep = Gtk.Label(label="›")
        sep.add_css_class("dim-label")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        box.append(b)
        box.append(sep)
        return box

    def _nav_to(self, target: Path | None) -> None:
        self._load(target)

    # ---- Phase 2: rename/cut/copy/paste/delete/new folder -------------------
    def _update_action_buttons(self) -> None:
        self._new_folder_btn.set_sensitive(self._current is not None)
        self._paste_btn.set_sensitive(self._current is not None and self._clipboard is not None)

    def _build_entry_popover(self, e: FileEntry) -> Gtk.Popover:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        popover = Gtk.Popover()
        popover.set_child(box)

        def item(label: str, action: Callable[[], None]) -> None:
            b = Gtk.Button()
            lbl = Gtk.Label(label=label, xalign=0.0)
            b.set_child(lbl)
            b.add_css_class("flat")

            def on_click(*_a: object) -> None:
                popover.popdown()
                action()

            b.connect("clicked", on_click)
            box.append(b)

        item("Rename…", partial(self._start_rename, e))
        item("Cut", partial(self._start_cut, e))
        item("Copy", partial(self._start_copy, e))
        item("Move to Trash", partial(self._start_trash, e))
        return popover

    def _start_cut(self, e: FileEntry) -> None:
        self._clipboard = (e.path, "move")
        self._update_action_buttons()
        self._notify(f"{e.name} will move here when you Paste. Nothing has changed yet.")

    def _start_copy(self, e: FileEntry) -> None:
        self._clipboard = (e.path, "copy")
        self._update_action_buttons()
        self._notify(f"{e.name} will copy here when you Paste. Nothing has changed yet.")

    def _do_paste(self) -> None:
        if self._current is None or self._clipboard is None:
            return
        src, verb = self._clipboard
        self._run_plan(plan_file(verb, str(src), str(self._current), self._current))

    def _start_new_folder(self) -> None:
        folder = self._current
        if folder is None:
            return
        self._prompt_name(
            heading="New folder",
            initial="New folder",
            on_confirmed=lambda name: self._run_plan(
                plan_file("mkdir", str(folder / name), None, folder)
            ),
        )

    def _start_rename(self, e: FileEntry) -> None:
        cwd = self._current or e.path.parent
        self._prompt_name(
            heading=f"Rename {e.name}",
            initial=e.name,
            on_confirmed=lambda name: self._run_plan(plan_file("rename", str(e.path), name, cwd)),
        )

    def _start_trash(self, e: FileEntry) -> None:
        cwd = self._current or e.path.parent
        self._run_plan(plan_file("trash", str(e.path), None, cwd))

    def _prompt_name(self, heading: str, initial: str, on_confirmed: Callable[[str], None]) -> None:
        entry = Gtk.Entry(text=initial)
        entry.update_property([Gtk.AccessibleProperty.LABEL], ["New name"])
        dialog = Adw.AlertDialog(heading=heading, extra_child=entry)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("go", "OK")
        dialog.set_response_appearance("go", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("go")
        dialog.set_close_response("cancel")

        def on_response(_d: Adw.AlertDialog, response: str) -> None:
            if response != "go":
                return
            name = entry.get_text().strip()
            if not name:
                self._notify("A name is needed. Nothing was changed.")
                return
            on_confirmed(name)

        dialog.connect("response", on_response)
        dialog.present(self.get_root())
        entry.grab_focus()

    def _run_plan(self, plan_or_result: FilePlan | OperationResult | None) -> None:
        if plan_or_result is None:
            return
        if isinstance(plan_or_result, OperationResult):
            self._notify(f"{plan_or_result.plain} Nothing was changed.")
            return
        plan = plan_or_result
        dialog = Adw.AlertDialog(heading=f"{plan.heading}?", body=plan.preview)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("go", plan.heading)
        dialog.set_response_appearance(
            "go",
            (
                Adw.ResponseAppearance.DESTRUCTIVE
                if plan.destructive
                else Adw.ResponseAppearance.SUGGESTED
            ),
        )
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_plan_response, plan)
        dialog.present(self.get_root())

    def _on_plan_response(self, _d: Adw.AlertDialog, response: str, plan: FilePlan) -> None:
        if response != "go":
            self._notify(f"Cancelled. {plan.label} was left as it is.")
            return
        folder = self._current

        def work() -> None:
            result = execute_file(plan, self._journal)
            GLib.idle_add(self._after_execute, result, folder, plan)

        threading.Thread(target=work, name="tb-filebrowser-op", daemon=True).start()

    def _after_execute(self, result: OperationResult, folder: Path | None, plan: FilePlan) -> bool:
        self._notify(f"{result.plain} {result.three_answers()['Did anything change?']}")
        if plan.verb in ("move", "trash") and self._clipboard is not None:
            if self._clipboard[0] == plan.source:
                self._clipboard = None
                self._update_action_buttons()
        if folder is not None and folder == self._current:
            self._load(self._current, record_history=False)
        return False
