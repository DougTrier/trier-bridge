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
"""System Information view (Windows: System Information / msinfo32).

Shows the environment profile and the capability table from a read-only
discovery pass. Discovery runs on a worker thread so a slow bus never
freezes the window; results are handed back to the main loop with
GLib.idle_add. CONCURRENCY: the worker only reads and only posts immutable
records; the view is the single writer of its own widgets.
"""
from __future__ import annotations

import logging
import threading
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..capability.model import CapabilityRecord, EnvironmentProfile  # noqa: E402
from ..core.state import CapabilityState  # noqa: E402

log = logging.getLogger("trier_bridge.ui.sysinfo")

FRIENDLY = {
    "service-manager": ("Services", "Start, stop, and inspect background services"),
    "network-manager": ("Network", "Adapters, Wi-Fi, IP configuration"),
    "storage": ("Disks and drives", "Disks, partitions, removable drives"),
    "packages-native": (
        "Installed programs (system packages)",
        "Programs installed from the distribution",
    ),
    "packages-snap": ("Installed programs (Snap)", "Programs installed as snaps"),
    "packages-flatpak": ("Installed programs (Flatpak)", "Programs installed as Flatpaks"),
    "packagekit": ("Install and remove programs", "The system's package service"),
    "authorization": (
        "Administrator permission prompts",
        "How Linux asks before privileged changes",
    ),
    "session-manager": ("Sign-in and power", "Sessions, restart, shut down"),
    "journal": ("Event log", "System and application log entries"),
    "printing": ("Printers", "Printers and print queues"),
    "bluetooth": ("Bluetooth", "Bluetooth adapters and devices"),
    "desktop-portals": ("Desktop integration", "Screenshots, notifications, file dialogs"),
    "desktop-shell": ("Desktop shell", "The GNOME desktop, search, tray"),
    "power": ("Battery and power", "Battery state and power sources"),
    "processes": ("Task Manager data", "Running programs and their usage"),
}


def _row(title: str = "", subtitle: str = "") -> Adw.ActionRow:
    """ActionRow with markup off: titles come from data and the system, not from us."""
    row = Adw.ActionRow(title=title, subtitle=subtitle)
    row.set_use_markup(False)
    return row


class SystemInfoPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self, discover: Any) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._discover = discover
        self._page = Adw.PreferencesPage()
        self._page.update_property([Gtk.AccessibleProperty.LABEL], ["System Information"])
        self._env_group = Adw.PreferencesGroup(title="This computer")
        self._cap_group = Adw.PreferencesGroup(
            title="What Trier Bridge can see",
            description=(
                "Read-only check of the Linux services on this computer. "
                "Nothing is changed by looking."
            ),
        )
        self._status = _row(title="Checking…")
        self._env_group.add(self._status)
        self._page.add(self._env_group)
        self._page.add(self._cap_group)
        self._refresh_button = Gtk.Button(label="Check again")
        self._refresh_button.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Runs the read-only check again. Nothing is changed."],
        )
        self._refresh_button.connect("clicked", lambda *_: self.refresh())
        self._cap_group.set_header_suffix(self._refresh_button)
        scroller = Gtk.ScrolledWindow(child=self._page, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroller.set_vexpand(True)
        self.append(scroller)
        self._rows: list[Gtk.Widget] = []
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._started = True
            self.refresh()

    def refresh(self) -> None:
        self._refresh_button.set_sensitive(False)
        self._status.set_title("Checking…")
        threading.Thread(target=self._worker, name="tb-discovery", daemon=True).start()

    def _worker(self) -> None:
        try:
            env, recs = self._discover()
        except Exception as exc:  # structured failure: show, never hide (TB-INV-004)
            log.exception("discovery failed")
            GLib.idle_add(self._show_error, str(exc))
            return
        GLib.idle_add(self._show, env, recs)

    def _clear(self) -> None:
        for w in self._rows:
            parent = w.get_parent()
            if isinstance(parent, Adw.PreferencesGroup):
                parent.remove(w)
        self._rows = []

    def _show_error(self, text: str) -> bool:
        self._status.set_title("The check could not be completed")
        self._status.set_subtitle(f"Nothing was changed. Technical detail: {text}")
        self._refresh_button.set_sensitive(True)
        return False

    def _show(self, env: EnvironmentProfile, recs: list[CapabilityRecord]) -> bool:
        self._clear()
        self._env_group.remove(self._status)
        for line in env.summary_lines():
            title, _, value = line.partition(": ")
            row = _row(title=title, subtitle=value)
            row.update_property([Gtk.AccessibleProperty.LABEL], [f"{title}: {value}"])
            self._env_group.add(row)
            self._rows.append(row)
        self._status = _row(title="Sources", subtitle=", ".join(env.evidence) or "none")
        self._env_group.add(self._status)
        self._rows.append(self._status)
        for rec in recs:
            name, what = FRIENDLY.get(rec.capability.value, (rec.capability.value, ""))
            row = _row(title=name, subtitle=what)
            badge = Gtk.Label(label=rec.plain_state)
            badge.add_css_class("caption")
            badge.add_css_class(_css_for(rec.state))
            badge.set_valign(Gtk.Align.CENTER)
            row.add_suffix(badge)
            tech = rec.backend + (f" {rec.version}" if rec.version else "")
            detail = rec.detail or rec.evidence
            row.set_tooltip_text(f"{tech}\n{detail}")
            row.update_property(
                [Gtk.AccessibleProperty.LABEL, Gtk.AccessibleProperty.DESCRIPTION],
                [f"{name}: {rec.plain_state}", f"{what}. Backend {tech}. {detail}"],
            )
            self._cap_group.add(row)
            self._rows.append(row)
        self._refresh_button.set_sensitive(True)
        return False


def _css_for(state: CapabilityState) -> str:
    return {
        CapabilityState.SUPPORTED: "success",
        CapabilityState.DEGRADED: "warning",
        CapabilityState.UNSUPPORTED: "dim-label",
        CapabilityState.UNKNOWN: "dim-label",
        CapabilityState.ERROR: "error",
    }[state]
