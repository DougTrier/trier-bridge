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
"""Bridge Terminal page (Foundation 07): Bridge Mode only in this build.

The mode label is always visible and there is no fall-through to a shell
(TB-INV-082, TB-INV-085, TB-INV-102). Output is plain text in a bounded
buffer (TB-INV-099); the ANSI-free rendering is a text view, so no escape
sequence is ever interpreted (TB-INV-100). History lives in memory for the
session and skips sensitive-looking lines (TB-INV-098). taskkill produces a
typed plan that goes through the same confirmation as Task Manager.
"""
from __future__ import annotations

from pathlib import Path

import logging
import threading
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..bridge.commands import CommandOutput, Exit, Session, is_sensitive, run_line  # noqa: E402
from ..operations.files import FilePlan, execute_file  # noqa: E402
from ..operations.process import TerminatePlan, execute_terminate  # noqa: E402
from ..operations.service import VERB_TEXT, ServicePlan, execute_service  # noqa: E402
from ..state.journal import OperationJournal  # noqa: E402

log = logging.getLogger("trier_bridge.ui.terminal")
MAX_BUFFER_LINES = 5000
MAX_HISTORY = 200


class TerminalPage(Gtk.Box):  # type: ignore[misc]
    def __init__(
        self,
        journal: OperationJournal | None,
        notify: Callable[[str], None],
        cwd: Path | None = None,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._journal = journal
        self._notify = notify
        self._session = Session(cwd if cwd is not None and cwd.is_dir() else None)
        self._history: list[str] = []
        self._hist_pos = 0
        self._busy = False
        self.append(
            Adw.Banner(
                title=(
                    "Bridge Mode: Windows commands become typed Linux operations. Nothing is "
                    "passed to a shell. Unknown commands do nothing. Type help."
                ),
                revealed=True,
            )
        )
        self._view = Gtk.TextView(editable=False, cursor_visible=False, monospace=True)
        self._view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._view.update_property([Gtk.AccessibleProperty.LABEL], ["Bridge Terminal output"])
        self._buffer = self._view.get_buffer()
        scroller = Gtk.ScrolledWindow(child=self._view)
        scroller.set_vexpand(True)
        self.append(scroller)
        bar = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=6, margin_bottom=8)
        self._mode = Gtk.Label(label="Bridge>")
        self._mode.add_css_class("heading")
        self._mode.update_property([Gtk.AccessibleProperty.LABEL], ["Mode: Bridge"])
        bar.append(self._mode)
        self._entry = Gtk.Entry(
            hexpand=True, placeholder_text="ipconfig /all, tasklist, dir, sc query, help"
        )
        self._entry.update_property([Gtk.AccessibleProperty.LABEL], ["Bridge command"])
        self._entry.connect("activate", lambda *_: self._submit())
        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._on_key)
        self._entry.add_controller(key)
        bar.append(self._entry)
        run = Gtk.Button(label="Run")
        run.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Run the Bridge command. Read-only commands change nothing."],
        )
        run.connect("clicked", lambda *_: self._submit())
        bar.append(run)
        pwsh = Gtk.Button(label="PowerShell")
        pwsh.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Open real PowerShell in a terminal window, if it is installed."],
        )
        pwsh.connect("clicked", lambda *_: self._submit_text("powershell"))
        bar.append(pwsh)
        self.append(bar)
        self._append(f"Trier Bridge Terminal, Bridge Mode. Current folder: {self._session.cwd}\n")

    def change_folder(self, folder: Path) -> None:
        """Start at a folder chosen in Files (integration); nothing is run."""
        if folder.is_dir():
            self._session.cwd = folder
            self._append(f"Current folder: {folder}\n")
        else:
            self._append(f"Folder not found: {folder}\n")

    # ---- output buffer, bounded --------------------------------------------------
    def _append(self, text: str) -> None:
        end = self._buffer.get_end_iter()
        self._buffer.insert(end, text)
        n = self._buffer.get_line_count()
        if n > MAX_BUFFER_LINES:
            start = self._buffer.get_start_iter()
            cut = self._buffer.get_iter_at_line(n - MAX_BUFFER_LINES)[1]
            self._buffer.delete(start, cut)
        self._view.scroll_to_iter(self._buffer.get_end_iter(), 0.0, False, 0.0, 1.0)

    def _on_key(self, _c: Gtk.EventControllerKey, keyval: int, _code: int, _state: object) -> bool:
        from gi.repository import Gdk

        if keyval == Gdk.KEY_Up and self._history:
            self._hist_pos = max(0, self._hist_pos - 1)
            self._entry.set_text(self._history[self._hist_pos])
            self._entry.set_position(-1)
            return True
        if keyval == Gdk.KEY_Down and self._history:
            self._hist_pos = min(len(self._history), self._hist_pos + 1)
            self._entry.set_text(
                self._history[self._hist_pos] if self._hist_pos < len(self._history) else ""
            )
            self._entry.set_position(-1)
            return True
        return False

    def _submit(self) -> None:
        if self._busy:
            return
        line = self._entry.get_text()
        self._entry.set_text("")
        if not line.strip():
            return
        if not is_sensitive(line):
            self._history.append(line)
            self._history = self._history[-MAX_HISTORY:]
        self._hist_pos = len(self._history)
        self._append(f"{self._session.cwd}> {line}\n")
        self._busy = True
        threading.Thread(target=self._run, args=(line,), name="tb-bridge", daemon=True).start()

    def _submit_text(self, text: str) -> None:
        self._entry.set_text(text)
        self._submit()

    def _run(self, line: str) -> None:
        try:
            out = run_line(line, self._session)
        except Exception as exc:
            out = CommandOutput(Exit.FAILED, (f"The command could not complete: {exc}",))
            log.exception("bridge command failed")
        GLib.idle_add(self._show, out)

    def _show(self, out: CommandOutput) -> bool:
        self._busy = False
        if out.lines == ("\x0c",):
            self._buffer.set_text("")
            return False
        text = "\n".join(out.lines)
        if text:
            self._append(text + "\n")
        if out.linux_equivalent:
            self._append(f"  [Linux: {out.linux_equivalent}]\n")
        if out.exit not in (Exit.OK, Exit.NEEDS_CONFIRMATION):
            self._append(
                f"  (exit: {out.exit.name.lower().replace('_', ' ')}; nothing was changed)\n"
            )
        self._append("\n")
        if isinstance(out.pending_operation, TerminatePlan):
            self._confirm(out.pending_operation)
        elif isinstance(out.pending_operation, FilePlan):
            self._confirm_file(out.pending_operation)
        elif isinstance(out.pending_operation, ServicePlan):
            self._confirm_service(out.pending_operation)
        return False

    def _confirm(self, plan: TerminatePlan) -> None:
        dialog = Adw.AlertDialog(
            heading="Force end task?" if plan.force else "End task?", body=plan.preview
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("end", "Force end" if plan.force else "End task")
        dialog.set_response_appearance("end", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_confirm, plan)
        dialog.present(self.get_root())

    def _confirm_file(self, plan: FilePlan) -> None:
        dialog = Adw.AlertDialog(heading=f"{plan.heading}?", body=plan.preview)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("go", plan.heading)
        if plan.destructive:
            dialog.set_response_appearance("go", Adw.ResponseAppearance.DESTRUCTIVE)
        else:
            dialog.set_response_appearance("go", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_confirm_file, plan)
        dialog.present(self.get_root())

    def _confirm_service(self, plan: ServicePlan) -> None:
        verb = VERB_TEXT[plan.verb][0]
        dialog = Adw.AlertDialog(heading=f"{verb} {plan.service.identity.name}?", body=plan.preview)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("go", verb)
        dialog.set_response_appearance(
            "go",
            (
                Adw.ResponseAppearance.DESTRUCTIVE
                if plan.verb in ("stop", "disable")
                else Adw.ResponseAppearance.SUGGESTED
            ),
        )
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_confirm_service, plan)
        dialog.present(self.get_root())

    def _on_confirm_service(self, _d: Adw.AlertDialog, response: str, plan: ServicePlan) -> None:
        if response != "go":
            self._append(f"Cancelled. {plan.service.identity.name} was left as it is.\n\n")
            return

        def work() -> None:
            result = execute_service(plan, self._journal)
            GLib.idle_add(
                self._append,
                f"{result.plain} {result.three_answers()['Did anything change?']}\n\n",
            )

        threading.Thread(target=work, name="tb-service", daemon=True).start()

    def _on_confirm_file(self, _d: Adw.AlertDialog, response: str, plan: FilePlan) -> None:
        if response != "go":
            self._append(f"Cancelled. {plan.label} was left as it is.\n\n")
            return

        def work() -> None:
            result = execute_file(plan, self._journal)
            GLib.idle_add(
                self._append,
                f"{result.plain} {result.three_answers()['Did anything change?']}\n\n",
            )

        threading.Thread(target=work, name="tb-file", daemon=True).start()

    def _on_confirm(self, _d: Adw.AlertDialog, response: str, plan: TerminatePlan) -> None:
        if response != "end":
            self._append(f"Cancelled. {plan.label} was left running.\n\n")
            return

        def work() -> None:
            result = execute_terminate(plan, self._journal)
            GLib.idle_add(
                self._append, f"{result.plain} {result.three_answers()['Did anything change?']}\n\n"
            )

        threading.Thread(target=work, name="tb-bridge-endtask", daemon=True).start()
