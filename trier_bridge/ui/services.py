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
"""Services (Foundation 06, IMP-06.05): list; start/stop/restart/enable/disable with confirmation.

Running and Startup are two columns, never one (TB-INV-067). System services say
that administrator permission will be requested; the prompt itself is polkit's.
"""
from __future__ import annotations

import logging
import threading
from functools import partial
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..operations.service import (  # noqa: E402
    ServicePlan,
    execute_service,
    is_session_critical_user_unit,
    plan_service,
)
from ..state.journal import OperationJournal  # noqa: E402
from ..system.services import Scope, ServiceInfo, list_services  # noqa: E402

log = logging.getLogger("trier_bridge.ui.services")
MAX_ROWS = 250


class ServicesPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self, journal: OperationJournal | None, notify: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._journal = journal
        self._notify = notify
        self._services: list[ServiceInfo] = []
        self._rows: list[Gtk.Widget] = []
        self.append(
            Adw.Banner(
                title=(
                    "Running and Start at boot are separate. Changing a system service asks for "
                    "administrator permission through Linux; your own services need none."
                ),
                revealed=True,
            )
        )
        bar = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=8, margin_bottom=4)
        self._scope = Gtk.DropDown.new_from_strings(["System services", "My services"])
        self._scope.update_property([Gtk.AccessibleProperty.LABEL], ["Service scope"])
        self._scope.connect("notify::selected", lambda *_: self.refresh())
        bar.append(self._scope)
        self._entry = Gtk.SearchEntry(placeholder_text="Find a service…", hexpand=True)
        self._entry.update_property([Gtk.AccessibleProperty.LABEL], ["Find a service"])
        self._entry.connect("search-changed", lambda *_: self._render())
        bar.append(self._entry)
        refresh = Gtk.Button(label="Refresh")
        refresh.update_property([Gtk.AccessibleProperty.DESCRIPTION], ["Reads the services again."])
        refresh.connect("clicked", lambda *_: self.refresh())
        bar.append(refresh)
        self.append(bar)
        self._summary = Gtk.Label(xalign=0.0, margin_start=12)
        self._summary.add_css_class("dim-label")
        self.append(self._summary)
        self._list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self._list.add_css_class("boxed-list")
        self._list.set_margin_start(12)
        self._list.set_margin_end(12)
        self._list.set_margin_bottom(12)
        scroller = Gtk.ScrolledWindow(child=self._list, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroller.set_vexpand(True)
        self.append(scroller)
        self._started = False

    @property
    def scope(self) -> Scope:
        return Scope.SYSTEM if self._scope.get_selected() == 0 else Scope.USER

    def start(self) -> None:
        if not self._started:
            self._started = True
            self.refresh()

    def refresh(self) -> None:
        self._summary.set_text("Reading services…")
        scope = self.scope
        threading.Thread(
            target=self._worker, args=(scope,), name="tb-services", daemon=True
        ).start()

    def _worker(self, scope: Scope) -> None:
        try:
            services, err = list_services(scope)
        except Exception as exc:
            log.exception("service listing failed")
            GLib.idle_add(self._loaded, [], str(exc))
            return
        GLib.idle_add(self._loaded, services, err)

    def _loaded(self, services: list[ServiceInfo], err: str) -> bool:
        self._services = services
        if err:
            self._summary.set_text(f"Services could not be read. Nothing was changed. {err}")
        self._render()
        return False

    def _render(self) -> None:
        for w in self._rows:
            self._list.remove(w)
        self._rows = []
        q = self._entry.get_text().strip().casefold()
        shown = [
            s
            for s in self._services
            if not q or q in s.identity.name.casefold() or q in s.description.casefold()
        ]
        if self._services:
            self._summary.set_text(f"{len(shown)} of {len(self._services)} services")
        for s in shown[:MAX_ROWS]:
            critical = s.scope is Scope.USER and is_session_critical_user_unit(s.identity.name)
            row = Adw.ActionRow(use_markup=False)
            row.set_title(s.identity.name)
            subtitle = f"{s.description} · Start at boot: {s.plain_startup}"
            if critical:
                subtitle += " · Critical: runs your desktop session, stopping it signs you out"
            row.set_subtitle(subtitle)
            state = Gtk.Label(label=s.plain_running, valign=Gtk.Align.CENTER, width_chars=8)
            state.add_css_class("tb-pill")
            state.add_css_class(
                {
                    "Running": "tb-pill-ok",
                    "Active": "tb-pill-ok",
                    "Failed": "tb-pill-error",
                    "Starting": "tb-pill-warn",
                    "Stopping": "tb-pill-warn",
                }.get(s.plain_running, "tb-pill-off")
            )
            row.add_prefix(state)
            row.set_tooltip_text(s.identity.fragment_path or s.identity.object_path)
            row.update_property(
                [Gtk.AccessibleProperty.LABEL],
                [
                    f"{s.identity.name}, {s.plain_running}, start at boot {s.plain_startup}"
                    + (", critical: runs your desktop session" if critical else "")
                ],
            )
            menu = Gtk.MenuButton(icon_name="view-more-symbolic")
            menu.set_valign(Gtk.Align.CENTER)
            menu.update_property([Gtk.AccessibleProperty.LABEL], [f"Actions for {s.identity.name}"])
            # Real, reported lag on first opening this page: with ~190 system services on a
            # typical desktop, building a Popover + 5 buttons for every row eagerly meant
            # ~1,300 extra widgets constructed synchronously on the main thread before anything
            # painted. set_create_popup_func defers that to the moment a row's menu is actually
            # opened, so a page with 190 services builds 0 popovers up front instead of 190.
            menu.set_create_popup_func(self._build_service_popup, s)
            row.add_suffix(menu)
            self._list.append(row)
            self._rows.append(row)
        if len(shown) > MAX_ROWS:
            more = Adw.ActionRow(use_markup=False)
            more.set_title(f"{len(shown) - MAX_ROWS} more; narrow the search to see them")
            self._list.append(more)
            self._rows.append(more)

    def _build_service_popup(self, menu: Gtk.MenuButton, service: ServiceInfo) -> None:
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4,
            margin_top=6,
            margin_bottom=6,
            margin_start=6,
            margin_end=6,
        )
        for verb, label in (
            ("start", "Start"),
            ("stop", "Stop"),
            ("restart", "Restart"),
            ("enable", "Start at boot"),
            ("disable", "Do not start at boot"),
        ):
            b = Gtk.Button(label=label)
            b.add_css_class("flat")
            b.update_property(
                [Gtk.AccessibleProperty.DESCRIPTION],
                [f"{label} {service.identity.name}. You will be asked to confirm."],
            )
            b.connect("clicked", partial(self._ask, service, verb))
            box.append(b)
        menu.set_popover(Gtk.Popover(child=box))

    def _ask(self, service: ServiceInfo, verb: str, *_: object) -> None:
        plan = plan_service(service, verb)
        if not isinstance(plan, ServicePlan):
            self._notify(plan.plain)
            return
        dialog = Adw.AlertDialog(
            heading=f"{verb.capitalize()} {service.identity.name}?", body=plan.preview
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("go", "Continue")
        if verb in ("stop", "disable", "restart"):
            dialog.set_response_appearance("go", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_confirm, plan)
        dialog.present(self.get_root())

    def _on_confirm(self, _d: Adw.AlertDialog, response: str, plan: ServicePlan) -> None:
        if response != "go":
            self._notify(f"Cancelled. {plan.service.identity.name} was not changed.")
            return
        threading.Thread(target=self._run, args=(plan,), name="tb-service-op", daemon=True).start()

    def _run(self, plan: ServicePlan) -> None:
        try:
            result = execute_service(plan, self._journal)
        except Exception as exc:
            log.exception("service operation failed")
            GLib.idle_add(self._notify, f"The change failed unexpectedly: {exc}")
            return
        answers = result.three_answers()
        text = f"{result.plain} {answers['Did anything change?']}"
        if result.safest_next_step and not result.state.is_success:
            text += f" Next: {result.safest_next_step}"
        GLib.idle_add(self._notify, text)
        GLib.idle_add(self.refresh)
