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
"""Network Connections (Foundation 04, IMP-04.06): adapters, IP, DNS, connectivity, read-only.

Each layer is its own row so nothing collapses into one Connected flag
(TB-INV-071). Changes go through the desktop's own Settings panels.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..desktop.launch import LaunchResult, Launcher  # noqa: E402
from ..operations.network import (  # noqa: E402
    IPv4Settings,
    NetworkPlan,
    execute_network,
    ipv4_settings,
    plan_network,
)
from ..system.network import NetworkDevice, NetworkOverview, read_network  # noqa: E402

log = logging.getLogger("trier_bridge.ui.network")


def _row(title: str, subtitle: str = "") -> Adw.ActionRow:
    r = Adw.ActionRow(use_markup=False)
    r.set_title(title)
    r.set_subtitle(subtitle)
    return r


class NetworkPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self, launcher: Launcher, notify: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._launcher = launcher
        self._notify = notify
        self._page = Adw.PreferencesPage()
        self._overview = Adw.PreferencesGroup(
            title="Network",
            description=(
                "Windows: Network Connections, ipconfig. Read from NetworkManager; each "
                "fact is shown separately. Disconnect, connect, or set an IPv4 address "
                "per adapter; Linux asks for permission for each change."
            ),
        )
        self._page.add(self._overview)
        refresh = Gtk.Button(label="Refresh")
        refresh.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Reads the network state again. Nothing is changed."],
        )
        refresh.connect("clicked", lambda *_: self.refresh())
        self._overview.set_header_suffix(refresh)
        self._status = _row("Reading…")
        self._overview.add(self._status)
        self._groups: list[Adw.PreferencesGroup] = []
        self._rows: list[Gtk.Widget] = []
        actions = Adw.PreferencesGroup(title="Change settings")
        for label, sub, panel in (
            ("Wi-Fi settings", "Windows: Wi-Fi · Linux: GNOME Settings (NetworkManager)", "wifi"),
            (
                "Network settings",
                "Windows: Network Connections (ncpa.cpl) · Linux: GNOME Settings",
                "network",
            ),
        ):
            r = _row(label, sub)
            b = Gtk.Button(label="Open")
            b.set_valign(Gtk.Align.CENTER)
            b.update_property(
                [Gtk.AccessibleProperty.DESCRIPTION],
                [f"Open {label}. Nothing is changed by opening it."],
            )
            b.connect("clicked", lambda *_, p=panel: self._open(p))
            r.add_suffix(b)
            actions.add(r)
        self._page.add(actions)
        scroller = Gtk.ScrolledWindow(child=self._page, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroller.set_vexpand(True)
        self.append(scroller)
        self._started = False

    def _actions_for(self, d: NetworkDevice) -> Gtk.Box:
        box = Gtk.Box(spacing=6)
        verb = "disconnect" if d.connection_uuid else "connect"
        b = Gtk.Button(label="Disconnect" if d.connection_uuid else "Connect")
        b.set_valign(Gtk.Align.CENTER)
        b.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            [f"{verb.capitalize()} {d.interface}. Asks first; Linux asks permission."],
        )
        b.connect("clicked", lambda *_, dev=d, v=verb: self._ask(dev, v, None, ()))
        box.append(b)
        if d.connection_uuid:
            ip = Gtk.Button(label="IPv4…")
            ip.set_valign(Gtk.Align.CENTER)
            ip.update_property(
                [Gtk.AccessibleProperty.DESCRIPTION],
                [f"Set a fixed IPv4 address or automatic for {d.interface}. Asks first."],
            )
            ip.connect("clicked", lambda *_, dev=d: self._ipv4_dialog(dev))
            box.append(ip)
        return box

    def _ipv4_dialog(self, d: NetworkDevice) -> None:
        dialog = Adw.Dialog(title=f"IPv4 for {d.interface}", content_width=460)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(
            title="Address",
            description="Windows: adapter Properties, Internet Protocol Version 4. "
            "Automatic means DHCP.",
        )
        auto = Adw.SwitchRow(use_markup=False)
        auto.set_title("Obtain an IP address automatically")
        auto.set_active(True)
        group.add(auto)
        addr = Adw.EntryRow(title="IP address / prefix (e.g. 192.168.1.10/24 or mask)")
        addr.set_text(d.ipv4[0] if d.ipv4 else "")
        gw = Adw.EntryRow(title="Default gateway")
        gw.set_text(d.gateway4)
        dns = Adw.EntryRow(title="DNS servers (comma separated, optional)")
        dns.set_text(", ".join(d.dns))
        for row in (addr, gw, dns):
            group.add(row)
        page.add(group)
        toolbar.set_content(page)
        actions = Gtk.Box(
            spacing=12, margin_top=8, margin_bottom=12, margin_start=12, margin_end=12
        )
        actions.set_halign(Gtk.Align.END)
        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", lambda *_: dialog.close())
        apply = Gtk.Button(label="Apply")
        apply.add_css_class("suggested-action")

        def on_apply(*_: object) -> None:
            dialog.close()
            if auto.get_active():
                self._ask(d, "auto", None, ())
                return
            try:
                text = addr.get_text().strip()
                address, _, mask = text.partition("/")
                settings = ipv4_settings(address, mask, gw.get_text(), dns.get_text())
            except ValueError as exc:
                self._notify(f"{exc} Nothing was changed.")
                return
            self._ask(d, "static", settings, ())

        apply.connect("clicked", on_apply)
        actions.append(cancel)
        actions.append(apply)
        toolbar.add_bottom_bar(actions)
        dialog.set_child(toolbar)
        dialog.present(self.get_root())

    def _ask(
        self, d: NetworkDevice, verb: str, settings: IPv4Settings | None, dns: tuple[str, ...]
    ) -> None:
        plan = plan_network(d, verb, settings, dns)
        if not isinstance(plan, NetworkPlan):
            self._notify(plan.plain)
            return
        dialog = Adw.AlertDialog(heading=f"{plan.heading}: {d.interface}?", body=plan.preview)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("go", plan.heading)
        dialog.set_response_appearance(
            "go",
            (
                Adw.ResponseAppearance.DESTRUCTIVE
                if verb == "disconnect"
                else Adw.ResponseAppearance.SUGGESTED
            ),
        )
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_confirm, plan)
        dialog.present(self.get_root())

    def _on_confirm(self, _d: Adw.AlertDialog, response: str, plan: NetworkPlan) -> None:
        if response != "go":
            self._notify(f"Cancelled. {plan.label} was left as it is.")
            return
        app = self.get_root().get_application()
        journal = getattr(app, "journal", None)

        def work() -> None:
            result = execute_network(plan, journal)
            GLib.idle_add(
                self._notify, f"{result.plain} {result.three_answers()['Did anything change?']}"
            )
            GLib.idle_add(self.refresh)

        threading.Thread(target=work, name="tb-network-change", daemon=True).start()

    def _open(self, panel: str) -> None:
        res: LaunchResult = self._launcher.open_settings_panel(panel)
        self._notify(res.plain if res.ok else f"{res.plain} Nothing was changed.")

    def start(self) -> None:
        if not self._started:
            self._started = True
            self.refresh()

    def refresh(self) -> None:
        threading.Thread(target=self._worker, name="tb-network", daemon=True).start()

    def _worker(self) -> None:
        try:
            nw = read_network()
        except Exception as exc:
            log.exception("network read failed")
            GLib.idle_add(self._fail, str(exc))
            return
        GLib.idle_add(self._show, nw)

    def _clear(self) -> None:
        for w in self._rows:
            parent = w.get_parent()
            if isinstance(parent, Adw.PreferencesGroup):
                parent.remove(w)
        self._rows = []
        for g in self._groups:
            self._page.remove(g)
        self._groups = []

    def _fail(self, text: str) -> bool:
        self._status.set_title("The network state could not be read")
        self._status.set_subtitle(f"Nothing was changed. Technical detail: {text}")
        return False

    def _show(self, nw: NetworkOverview) -> bool:
        self._clear()
        if not nw.available:
            self._status.set_title("Not available on this computer")
            self._status.set_subtitle(nw.detail)
            return False
        self._status.set_title("Overall")
        self._status.set_subtitle(
            f"NetworkManager {nw.backend_version} · state: {nw.overall_state} · "
            f"connectivity check: {nw.connectivity}"
        )
        for d in nw.devices:
            if d.is_loopback:
                continue
            g = Adw.PreferencesGroup(title=f"{d.interface} ({d.kind})")
            g.set_header_suffix(self._actions_for(d))
            facts = [
                ("Link", d.link_state),
                ("Connection profile", d.connection_name or "None active"),
                ("IPv4 address", ", ".join(d.ipv4) or "None"),
                ("IPv6 address", ", ".join(d.ipv6) or "None"),
                ("Default gateway", d.gateway4 or "None"),
                ("DNS servers", ", ".join(d.dns) or "None"),
                ("Physical address (MAC)", d.mac or "Unknown"),
                ("Driver", d.driver or "Unknown"),
                (
                    "Managed by NetworkManager",
                    "Unknown" if d.managed is None else ("Yes" if d.managed else "No"),
                ),
            ]
            for title, value in facts:
                r = _row(title, value)
                r.update_property(
                    [Gtk.AccessibleProperty.LABEL], [f"{d.interface} {title}: {value}"]
                )
                g.add(r)
                self._rows.append(r)
            self._page.add(g)
            self._groups.append(g)
        return False
