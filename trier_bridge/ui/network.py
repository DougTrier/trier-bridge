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
from ..system.network import NetworkOverview, read_network  # noqa: E402

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
                "Windows: Network Connections, ipconfig. Read from NetworkManager; "
                "each fact is shown separately. Changes are made in Settings."
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
