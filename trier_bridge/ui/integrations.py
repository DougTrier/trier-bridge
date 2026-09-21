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
"""Integrations page and first-run setup (DEC-019, SCOPE-14).

The user chooses integrations in groups at first run, changes them any time
on this page, and every switch is individually reversible: off means the
files it added are gone (DEC-018 g). Nothing is applied until the user says
so, and each result is reported in plain words.
"""
from __future__ import annotations

import logging
from functools import partial
from typing import Any, Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from ..config import StateWriteError  # noqa: E402
from ..integrations import catalog, tray  # noqa: E402
from ..integrations.catalog import ApplyResult, Integration  # noqa: E402
from ..integrations.ledger import IntegrationLedger  # noqa: E402

log = logging.getLogger("trier_bridge.ui.integrations")

GROUP_BLURB = {
    "Essentials": "The familiar words, and the tray icon. Recommended for everyone.",
    "Files": "Extra entries in the Files right-click menu. Uses the python3-nautilus package.",
    "Shortcuts": "Keyboard shortcuts you may know from Windows, chosen one at a time.",
}
INTRO = (
    "Trier Bridge is only this window until you say otherwise. Everything here writes only "
    "inside your home folder and can be turned off again, exactly, at any time."
)


def turn_on(integration_id: str, ledger: IntegrationLedger) -> ApplyResult:
    res = catalog.apply(integration_id, ledger)
    if res.ok and integration_id == "tray-icon":
        _ok, plain = tray.start()
        res = ApplyResult(True, f"{res.plain} {plain}", res.files)
    return res


def turn_off(integration_id: str, ledger: IntegrationLedger) -> ApplyResult:
    if integration_id == "tray-icon":
        tray.stop()
    return catalog.remove(integration_id, ledger)


def _switch_row(item: Integration) -> Adw.SwitchRow:
    row = Adw.SwitchRow(use_markup=False)
    row.set_title(item.title)
    row.set_subtitle(f"{item.changes} Off: {item.reversal}")
    row.update_property([Gtk.AccessibleProperty.DESCRIPTION], [f"Uses: {item.extension_point}."])
    return row


def _summary(results: list[tuple[Integration, ApplyResult]]) -> str:
    on = [i.title for i, r in results if r.ok]
    failed = [r.plain for _, r in results if not r.ok]
    parts = []
    if on:
        parts.append(f"On: {', '.join(on)}.")
    if failed:
        parts.append(" ".join(failed))
    return " ".join(parts) or "Nothing changed."


class IntegrationsPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self, ledger: IntegrationLedger, notify: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._ledger = ledger
        self._notify = notify
        self._rows: dict[str, Adw.SwitchRow] = {}
        self._syncing = False
        page = Adw.PreferencesPage()
        page.set_vexpand(True)
        intro = Adw.PreferencesGroup()
        intro.set_description(INTRO)
        off = Gtk.Button(label="Turn everything off")
        off.set_valign(Gtk.Align.CENTER)
        off.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Remove every integration and restore the desktop as it was before setup."],
        )
        off.connect("clicked", self._on_remove_all)
        intro.set_header_suffix(off)
        page.add(intro)
        for group in catalog.GROUPS:
            items = [i for i in catalog.CATALOG if i.group == group]
            box = Adw.PreferencesGroup(title=group, description=GROUP_BLURB.get(group, ""))
            if not any(i.individual_only for i in items):
                button = Gtk.Button(label="Turn on all")
                button.set_valign(Gtk.Align.CENTER)
                button.update_property(
                    [Gtk.AccessibleProperty.DESCRIPTION],
                    [f"Turn on every integration in the {group} group."],
                )
                button.connect("clicked", partial(self._on_group, items))
                box.set_header_suffix(button)
            for item in items:
                row = _switch_row(item)
                row.connect("notify::active", partial(self._on_toggle, item))
                self._rows[item.id] = row
                box.add(row)
            page.add(box)
        self.append(page)
        self.refresh()

    def refresh(self) -> None:
        self._syncing = True
        try:
            for integration_id, row in self._rows.items():
                row.set_active(self._ledger.is_applied(integration_id))
                row.set_sensitive(not self._ledger.read_only)
        finally:
            self._syncing = False

    def _on_toggle(self, item: Integration, row: Adw.SwitchRow, _pspec: Any) -> None:
        if self._syncing:
            return
        res = (
            turn_on(item.id, self._ledger) if row.get_active() else turn_off(item.id, self._ledger)
        )
        self._notify(res.plain)
        if not res.ok:
            self.refresh()  # the switch shows what is true, not what was asked

    def _on_remove_all(self, _button: Gtk.Button) -> None:
        """DELIVERY-MODEL section 2 step 5: restore the pre-setup state exactly."""
        applied = self._ledger.applied_ids()
        if not applied:
            self._notify("Nothing is integrated. The desktop is as it was before setup.")
            return
        results = [turn_off(i, self._ledger) for i in applied]
        failed = [r.plain for r in results if not r.ok]
        self._notify(
            " ".join(failed)
            if failed
            else f"{len(results)} integration(s) turned off; everything they added was removed."
        )
        self.refresh()

    def _on_group(self, items: list[Integration], _button: Gtk.Button) -> None:
        results = [
            (i, turn_on(i.id, self._ledger)) for i in items if not self._ledger.is_applied(i.id)
        ]
        self._notify(_summary(results) if results else "Everything in this group is already on.")
        self.refresh()


class SetupDialog(Adw.Dialog):  # type: ignore[misc]
    """First run: pick groups or single items; nothing happens until Apply."""

    def __init__(
        self, ledger: IntegrationLedger, notify: Callable[[str], None], on_done: Callable[[], None]
    ) -> None:
        super().__init__(title="Set up Trier Bridge", content_width=600, content_height=680)
        self._ledger = ledger
        self._notify = notify
        self._on_done = on_done
        self._rows: dict[str, Adw.SwitchRow] = {}
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        page = Adw.PreferencesPage()
        intro = Adw.PreferencesGroup()
        intro.set_description(
            "Choose how much of Trier Bridge to weave into this desktop: whole groups or single "
            "items. Nothing changes until you press Apply. Everything writes only inside your "
            "home folder, and each item can be turned off again, exactly, any time under "
            "Integrations."
        )
        page.add(intro)
        for group in catalog.GROUPS:
            items = [i for i in catalog.CATALOG if i.group == group]
            box = Adw.PreferencesGroup(title=group, description=GROUP_BLURB.get(group, ""))
            if not any(i.individual_only for i in items):
                check = Gtk.CheckButton(label="Whole group")
                check.set_valign(Gtk.Align.CENTER)
                check.set_active(all(i.recommended for i in items))
                check.connect("toggled", partial(self._on_group_check, items))
                box.set_header_suffix(check)
            for item in items:
                row = _switch_row(item)
                row.set_active(item.recommended)
                self._rows[item.id] = row
                box.add(row)
            page.add(box)
        toolbar.set_content(page)
        actions = Gtk.Box(
            spacing=12, margin_top=8, margin_bottom=12, margin_start=12, margin_end=12
        )
        actions.set_halign(Gtk.Align.END)
        later = Gtk.Button(label="Not now")
        later.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Integrate nothing. You can choose later under Integrations."],
        )
        later.connect("clicked", lambda *_: self._finish([]))
        apply = Gtk.Button(label="Apply")
        apply.add_css_class("suggested-action")
        apply.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION], ["Turn on the integrations switched on above."]
        )
        apply.connect("clicked", lambda *_: self._finish(self._chosen()))
        actions.append(later)
        actions.append(apply)
        toolbar.add_bottom_bar(actions)
        self.set_child(toolbar)

    def _on_group_check(self, items: list[Integration], check: Gtk.CheckButton) -> None:
        for item in items:
            self._rows[item.id].set_active(check.get_active())

    def _chosen(self) -> list[Integration]:
        return [i for i in catalog.CATALOG if self._rows[i.id].get_active()]

    def _finish(self, chosen: list[Integration]) -> None:
        results = [(i, turn_on(i.id, self._ledger)) for i in chosen]
        try:
            self._ledger.mark_setup_completed()
        except StateWriteError as exc:
            log.warning("setup choice not saved: %s", exc)
            self._notify(f"Your choice could not be saved: {exc}")
        if chosen:
            self._notify(_summary(results))
        else:
            self._notify("Nothing was integrated. You can choose any time under Integrations.")
        self.close()
        self._on_done()
