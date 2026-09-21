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
"""Task Manager, observation only (Foundation 04, IMP-04.01).

Tabs: Apps and processes (this user's), Background (system and other users),
Performance (CPU, memory, load, uptime). Sampling runs on a worker thread every
two seconds while the page is visible and stops when it is hidden
(TB-INV-200). No End task button exists yet: termination is a mutation and
arrives in Foundation 06 with identity revalidation (TB-INV-050, TB-INV-134).
Unknown values read "Unknown", never 0 (TB-INV-131). Command lines are shown
only in the tooltip and truncated (TB-INV-133).
"""
from __future__ import annotations

import logging
import threading
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..system.processes import ProcessKind, ProcessSample  # noqa: E402
from ..system.processes import ProcessSampler, SystemTotals  # noqa: E402

log = logging.getLogger("trier_bridge.ui.taskmanager")

INTERVAL_MS = 2000
MAX_ROWS = 150

KIND_LABEL = {
    ProcessKind.APP: "App",
    ProcessKind.USER: "Yours",
    ProcessKind.OTHER_USER: "Other user",
    ProcessKind.SYSTEM: "System",
    ProcessKind.KERNEL: "Kernel",
    ProcessKind.CRITICAL: "Critical",
}


def _fmt_bytes(n: int | None) -> str:
    if n is None:
        return "Unknown"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    if n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / (1024 * 1024 * 1024):.2f} GB"


def _fmt_pct(v: float | None) -> str:
    return "Unknown" if v is None else f"{v:.1f}%"


def _fmt_uptime(s: float | None) -> str:
    if s is None:
        return "Unknown"
    d, rem = divmod(int(s), 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    return f"{d}d {h}h {m}m" if d else f"{h}h {m}m"


class _ProcessList(Gtk.Box):  # type: ignore[misc]
    """One list of processes with a search box; rows are rebuilt from each sample."""

    def __init__(self, kinds: set[ProcessKind], empty_text: str) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._kinds = kinds
        self._empty_text = empty_text
        self._entry = Gtk.SearchEntry(placeholder_text="Find a process…")
        self._entry.update_property([Gtk.AccessibleProperty.LABEL], ["Find a process"])
        self._entry.set_margin_start(12)
        self._entry.set_margin_end(12)
        self._entry.set_margin_top(6)
        self.append(self._entry)
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
        self._rows: list[Gtk.Widget] = []
        self._latest: list[ProcessSample] = []
        self._entry.connect("search-changed", lambda *_: self._render())

    def update(self, samples: list[ProcessSample]) -> None:
        self._latest = [s for s in samples if s.kind in self._kinds]
        self._render()

    def _render(self) -> None:
        for w in self._rows:
            self._list.remove(w)
        self._rows = []
        q = self._entry.get_text().strip().casefold()
        rows = [
            s
            for s in self._latest
            if not q
            or q in s.name.casefold()
            or q in s.cmdline.casefold()
            or q == str(s.identity.pid)
        ]
        rows.sort(key=lambda s: (-(s.cpu_percent or 0.0), -(s.rss_bytes or 0), s.name.casefold()))
        self._summary.set_text(
            f"{len(rows)} shown of {len(self._latest)}" if rows else self._empty_text
        )
        for s in rows[:MAX_ROWS]:
            row = Adw.ActionRow(use_markup=False)
            row.set_title(s.name)
            row.set_subtitle(
                f"CPU {_fmt_pct(s.cpu_percent)} · Memory {_fmt_bytes(s.rss_bytes)} · "
                f"PID {s.identity.pid} · {s.user} · {KIND_LABEL[s.kind]}"
            )
            tip = (
                s.cmdline[:200]
                if s.cmdline
                else (
                    "Not readable for this account"
                    if not s.readable
                    else "No command line (kernel task)"
                )
            )
            row.set_tooltip_text(tip)
            spoken = (
                f"{s.name}, CPU {_fmt_pct(s.cpu_percent)}, "
                f"memory {_fmt_bytes(s.rss_bytes)}, {KIND_LABEL[s.kind]}"
            )
            row.update_property([Gtk.AccessibleProperty.LABEL], [spoken])
            self._list.append(row)
            self._rows.append(row)
        if len(rows) > MAX_ROWS:
            more = Adw.ActionRow(use_markup=False)
            more.set_title(f"{len(rows) - MAX_ROWS} more; narrow the search to see them")
            self._list.append(more)
            self._rows.append(more)


class _PerformancePage(Gtk.Box):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        page = Adw.PreferencesPage()
        self._group = Adw.PreferencesGroup(
            title="Performance",
            description="Read from the kernel every two seconds while this page is visible.",
        )
        self._rows: dict[str, Adw.ActionRow] = {}
        for key, title in (
            ("cpu", "CPU usage"),
            ("cores", "Processors"),
            ("mem", "Memory in use"),
            ("memtotal", "Memory total"),
            ("load", "Load (1 minute)"),
            ("uptime", "Up time"),
            ("procs", "Processes"),
        ):
            row = Adw.ActionRow(use_markup=False)
            row.set_title(title)
            row.set_subtitle("Unknown")
            self._group.add(row)
            self._rows[key] = row
        page.add(self._group)
        self.append(page)
        self._prev_total: int | None = None
        self._prev_busy: int | None = None

    def update(self, totals: SystemTotals, nprocs: int, samples: list[ProcessSample]) -> None:
        cpu_text = "Unknown"
        if totals.cpu_ticks_total is not None:
            busy = sum(s.cpu_ticks for s in samples)
            if self._prev_total is not None and self._prev_busy is not None:
                dt = totals.cpu_ticks_total - self._prev_total
                if dt > 0:
                    cpu_text = f"{min(100.0, 100.0 * (busy - self._prev_busy) / dt):.1f}%"
            self._prev_total, self._prev_busy = totals.cpu_ticks_total, busy
        self._rows["cpu"].set_subtitle(cpu_text)
        self._rows["cores"].set_subtitle(str(totals.cpu_count))
        if totals.mem_total_bytes is not None and totals.mem_available_bytes is not None:
            used = totals.mem_total_bytes - totals.mem_available_bytes
            self._rows["mem"].set_subtitle(
                f"{_fmt_bytes(used)} ({100.0 * used / totals.mem_total_bytes:.0f}%)"
            )
        else:
            self._rows["mem"].set_subtitle("Unknown")
        self._rows["memtotal"].set_subtitle(_fmt_bytes(totals.mem_total_bytes))
        self._rows["load"].set_subtitle(
            "Unknown" if totals.load1 is None else f"{totals.load1:.2f}"
        )
        self._rows["uptime"].set_subtitle(_fmt_uptime(totals.uptime_seconds))
        self._rows["procs"].set_subtitle(str(nprocs))


class TaskManagerPage(Gtk.Box):  # type: ignore[misc]
    def __init__(self, sampler_factory: Callable[[], ProcessSampler] = ProcessSampler) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._sampler = sampler_factory()
        self._visible = False
        self._timer: int | None = None
        self._busy = False
        banner = Adw.Banner(
            title="Observation only in this build. Ending a task arrives in a later foundation.",
            revealed=True,
        )
        self.append(banner)
        self._stack = Adw.ViewStack()
        self._apps = _ProcessList(
            {ProcessKind.APP, ProcessKind.USER}, "No processes of yours are running"
        )
        self._background = _ProcessList(
            {ProcessKind.SYSTEM, ProcessKind.OTHER_USER, ProcessKind.KERNEL, ProcessKind.CRITICAL},
            "No background processes are visible to this account",
        )
        self._perf = _PerformancePage()
        for child, name, title, icon in (
            (self._apps, "apps", "Apps and processes", "view-list-symbolic"),
            (self._background, "background", "Background", "system-run-symbolic"),
            (self._perf, "performance", "Performance", "utilities-system-monitor-symbolic"),
        ):
            p = self._stack.add_titled(child, name, title)
            p.set_icon_name(icon)
        switcher = Adw.ViewSwitcher(stack=self._stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        switcher.set_margin_top(6)
        switcher.set_margin_bottom(6)
        self.append(switcher)
        self.append(self._stack)
        self._stack.set_vexpand(True)
        self._status = Gtk.Label(label="Not sampling", xalign=0.0, margin_start=12, margin_bottom=6)
        self._status.add_css_class("dim-label")
        self.append(self._status)

    # visibility drives sampling (TB-INV-200)
    def set_active(self, active: bool) -> None:
        if active and not self._visible:
            self._visible = True
            self._tick()
            self._timer = GLib.timeout_add(INTERVAL_MS, self._tick)
        elif not active and self._visible:
            self._visible = False
            if self._timer is not None:
                GLib.source_remove(self._timer)
                self._timer = None
            self._status.set_text("Paused (page hidden)")

    def _tick(self) -> bool:
        if not self._visible:
            return False
        if not self._busy:
            self._busy = True
            threading.Thread(target=self._worker, name="tb-procs", daemon=True).start()
        return True

    def _worker(self) -> None:
        try:
            samples, totals = self._sampler.sample()
        except Exception as exc:  # report, never hide (TB-INV-004)
            log.exception("process sampling failed")
            GLib.idle_add(self._fail, str(exc))
            return
        GLib.idle_add(self._apply, samples, totals)

    def _fail(self, text: str) -> bool:
        self._status.set_text(f"Could not read processes: {text}")
        self._busy = False
        return False

    def _apply(self, samples: list[ProcessSample], totals: SystemTotals) -> bool:
        self._apps.update(samples)
        self._background.update(samples)
        self._perf.update(totals, len(samples), samples)
        unreadable = sum(1 for s in samples if not s.readable)
        note = f"; {unreadable} not fully readable for this account" if unreadable else ""
        self._status.set_text(f"{len(samples)} processes, sampled every 2 s while visible{note}")
        self._busy = False
        return False
