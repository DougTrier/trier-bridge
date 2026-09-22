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
(TB-INV-200). End task is a class B mutation: it asks first and revalidates the
process identity right before acting (TB-INV-050, TB-INV-134).
Unknown values read "Unknown", never 0 (TB-INV-131). Command lines are shown
only in the tooltip and truncated (TB-INV-133).
"""
from __future__ import annotations

import logging
import threading
from collections import deque
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..operations.process import (  # noqa: E402
    WHY_NOT_ACTIONABLE,
    TerminatePlan,
    execute_terminate,
    plan_terminate,
)
from ..state.journal import OperationJournal  # noqa: E402
from ..system.diskio import DiskIoSampler, DiskRate, disk_drive_letters  # noqa: E402
from ..system.netio import NetIoSampler, NetRate  # noqa: E402
from ..system.processes import ProcessKind, ProcessSample  # noqa: E402
from ..system.processes import ProcessSampler, SystemTotals  # noqa: E402
from .chart import Chart  # noqa: E402

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
    ProcessKind.SESSION_CRITICAL: "Critical (session)",
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

    def __init__(
        self,
        kinds: set[ProcessKind],
        empty_text: str,
        on_end: Callable[[ProcessSample, bool], None] | None = None,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._kinds = kinds
        self._empty_text = empty_text
        self._on_end = on_end
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
        self._by_pid: dict[int, Adw.ActionRow] = {}
        self._rank: dict[int, int] = {}
        self._latest: list[ProcessSample] = []
        self._more = Adw.ActionRow(use_markup=False)
        self._more.set_visible(False)
        self._list.append(self._more)
        self._list.set_sort_func(self._sort)
        self._entry.connect("search-changed", lambda *_: self._render())

    def update(self, samples: list[ProcessSample]) -> None:
        self._latest = [s for s in samples if s.kind in self._kinds]
        self._render()

    def _matches(self, s: ProcessSample, q: str) -> bool:
        return (
            not q or q in s.name.casefold() or q in s.cmdline.casefold() or q == str(s.identity.pid)
        )

    def _render(self) -> None:
        """Reuse one row per process: rebuilding widgets every tick cost a whole CPU core
        under software rendering (IMP-08.08). Rows are updated in place, sorted by rank,
        and hidden rather than destroyed when they fall outside the search or the cap."""
        q = self._entry.get_text().strip().casefold()
        shown = [s for s in self._latest if self._matches(s, q)]
        shown.sort(key=lambda s: (-(s.cpu_percent or 0.0), -(s.rss_bytes or 0), s.name.casefold()))
        self._summary.set_text(
            f"{len(shown)} shown of {len(self._latest)}" if shown else self._empty_text
        )
        self._rank = {s.identity.pid: i for i, s in enumerate(shown)}
        live = {s.identity.pid: s for s in self._latest}
        for pid, row in list(self._by_pid.items()):
            if pid not in live:
                self._list.remove(row)
                del self._by_pid[pid]
        for s in self._latest:
            row = self._by_pid.get(s.identity.pid)
            if row is None:
                row = self._make_row(s)
                self._by_pid[s.identity.pid] = row
                self._list.append(row)
            self._fill_row(row, s)
            rank = self._rank.get(s.identity.pid)
            row.set_visible(rank is not None and rank < MAX_ROWS)
        self._more.set_title(f"{len(shown) - MAX_ROWS} more; narrow the search to see them")
        self._more.set_visible(len(shown) > MAX_ROWS)
        self._list.invalidate_sort()

    def _sort(self, a: Gtk.ListBoxRow, b: Gtk.ListBoxRow) -> int:
        ra = self._rank.get(getattr(a, "tb_pid", -1), 1 << 30)
        rb = self._rank.get(getattr(b, "tb_pid", -1), 1 << 30)
        if a is self._more:
            ra = 1 << 31
        if b is self._more:
            rb = 1 << 31
        return (ra > rb) - (ra < rb)

    def _make_row(self, s: ProcessSample) -> Adw.ActionRow:
        row = Adw.ActionRow(use_markup=False)
        row.tb_pid = s.identity.pid
        if self._on_end is not None and s.kind.actionable_by_user:
            end = Gtk.Button(label="End task")
            end.set_valign(Gtk.Align.CENTER)
            end.update_property(
                [Gtk.AccessibleProperty.DESCRIPTION],
                [
                    f"Ask {s.name} to close. Unsaved work may be lost. "
                    "You will be asked to confirm."
                ],
            )
            end.connect("clicked", lambda *_, pid=s.identity.pid: self._end_by_pid(pid))
            row.add_suffix(end)
        return row

    def _end_by_pid(self, pid: int) -> None:
        # the latest sample for this pid, never a stale one captured at row creation
        sample = next((s for s in self._latest if s.identity.pid == pid), None)
        if sample is not None and self._on_end is not None:
            self._on_end(sample, False)

    def _fill_row(self, row: Adw.ActionRow, s: ProcessSample) -> None:
        subtitle = (
            f"CPU {_fmt_pct(s.cpu_percent)} · Memory {_fmt_bytes(s.rss_bytes)} · "
            f"PID {s.identity.pid} · {s.user} · {KIND_LABEL[s.kind]}"
        )
        if row.get_title() != s.name:
            row.set_title(s.name)
        if row.get_subtitle() != subtitle:
            row.set_subtitle(subtitle)
            row.update_property(
                [Gtk.AccessibleProperty.LABEL],
                [
                    f"{s.name}, CPU {_fmt_pct(s.cpu_percent)}, "
                    f"memory {_fmt_bytes(s.rss_bytes)}, {KIND_LABEL[s.kind]}"
                ],
            )
        why = WHY_NOT_ACTIONABLE.get(s.kind)
        tip = (
            f"Cannot be ended: {why}"
            if why is not None
            else (
                s.cmdline[:200]
                if s.cmdline
                else (
                    "Not readable for this account"
                    if not s.readable
                    else "No command line (kernel task)"
                )
            )
        )
        if row.get_tooltip_text() != tip:
            row.set_tooltip_text(tip)


CHART_CAPACITY = 30  # 30 samples * 2 s tick = 60 seconds, matching Windows' own "60 seconds" span


def _fmt_bps(n: float | None) -> str:
    """Bytes/sec, not bits -- consistent with _fmt_bytes elsewhere, unlike real Windows'
    network-in-bits convention, which would be its own small honesty problem to replicate."""
    if n is None:
        return "Unknown"
    if n < 1024:
        return f"{n:.0f} B/s"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB/s"
    return f"{n / (1024 * 1024):.1f} MB/s"


def _caption_label(halign: Gtk.Align, valign: Gtk.Align) -> Gtk.Label:
    label = Gtk.Label(margin_top=4, margin_bottom=4, margin_start=4, margin_end=4)
    label.add_css_class("caption")
    label.set_halign(halign)
    label.set_valign(valign)
    return label


class _Tile:
    """One graphed resource: a sidebar row with a mini chart, and enough state to rebuild
    the big detail chart when this tile is selected (TB-INV-248: both share one bounded
    rolling window, neither grows without limit)."""

    def __init__(self, key: str, kind: str, device: str, title: str) -> None:
        self.key = key
        self.kind = kind  # "cpu", "mem", "disk", "net"
        self.device = device  # real name behind the label: "", "sda", "eth0", ... (TB-INV-249)
        self.title = title
        self.history: deque[float | None] = deque(maxlen=CHART_CAPACITY)
        self.facts: dict[str, str] = {}
        self.subtitle = "Unknown"
        self.row = Adw.ActionRow(use_markup=False, title=title, subtitle="Unknown")
        self.row.tb_key = key
        self.mini = Chart(CHART_CAPACITY, fill=False)
        self.mini.set_size_request(56, 28)
        self.mini.set_valign(Gtk.Align.CENTER)
        if kind in ("cpu", "mem"):
            self.mini.set_max_value(100.0)
        self.row.add_suffix(self.mini)

    def push(self, value: float | None, subtitle: str, facts: dict[str, str]) -> None:
        self.history.append(value)
        self.subtitle = subtitle
        self.facts = facts
        self.mini.push(value)
        self.row.set_subtitle(subtitle)


class _PerformancePage(Gtk.Box):  # type: ignore[misc]
    """Windows-style Performance tab (DEC-026): a sidebar of live resource tiles, a big
    chart for whichever one is selected. GPU is deliberately not included -- there is no
    portable, generic way to read GPU utilization on Linux without vendor-specific tooling
    (nvidia-smi, vendor sysfs counters), the same "needs real hardware" boundary IMP-03.08
    and CQ-09 already carry."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self._prev_total: int | None = None
        self._prev_busy: int | None = None
        self._tiles: dict[str, _Tile] = {}
        self._selected: str | None = None

        self._sidebar = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self._sidebar.add_css_class("navigation-sidebar")
        self._sidebar.connect("row-selected", self._on_row_selected)
        sidebar_scroll = Gtk.ScrolledWindow(
            child=self._sidebar, hscrollbar_policy=Gtk.PolicyType.NEVER
        )
        sidebar_scroll.set_size_request(280, -1)
        sidebar_scroll.set_vexpand(True)
        self.append(sidebar_scroll)

        detail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        detail.set_margin_top(12)
        detail.set_margin_start(12)
        detail.set_margin_end(12)
        detail.set_margin_bottom(12)
        detail.set_hexpand(True)
        self._detail_title = Gtk.Label(xalign=0.0)
        self._detail_title.add_css_class("title-2")
        detail.append(self._detail_title)
        self._detail_subtitle = Gtk.Label(xalign=0.0)
        self._detail_subtitle.add_css_class("dim-label")
        detail.append(self._detail_subtitle)

        overlay = Gtk.Overlay()
        self._detail_chart = Chart(CHART_CAPACITY, fill=True)
        self._detail_chart.set_size_request(-1, 240)
        self._detail_chart.set_vexpand(True)
        overlay.set_child(self._detail_chart)
        self._peak_label = _caption_label(Gtk.Align.END, Gtk.Align.START)
        overlay.add_overlay(self._peak_label)
        self._floor_label = _caption_label(Gtk.Align.END, Gtk.Align.END)
        self._floor_label.set_text("0")
        overlay.add_overlay(self._floor_label)
        self._span_label = _caption_label(Gtk.Align.START, Gtk.Align.END)
        self._span_label.set_text("60 seconds")
        overlay.add_overlay(self._span_label)
        detail.append(overlay)

        self._facts_group = Adw.PreferencesGroup()
        self._fact_rows: dict[str, Adw.ActionRow] = {}
        detail.append(self._facts_group)
        self.append(detail)

        self._add_tile("cpu", "cpu", "", "CPU")
        self._add_tile("mem", "mem", "", "Memory")
        self._select_key("cpu")

    # ---- tiles -----------------------------------------------------------
    def _add_tile(self, key: str, kind: str, device: str, title: str) -> _Tile:
        tile = _Tile(key, kind, device, title)
        self._tiles[key] = tile
        self._sidebar.append(tile.row)
        return tile

    def _on_row_selected(self, _box: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        key = getattr(row, "tb_key", None) if row is not None else None
        if key is not None:
            self._select_key(key)

    def _select_key(self, key: str) -> None:
        tile = self._tiles.get(key)
        if tile is None:
            return
        self._selected = key
        self._detail_title.set_text(tile.title)
        self._detail_subtitle.set_text(tile.device or tile.subtitle)
        self._detail_chart.set_max_value(100.0 if tile.kind in ("cpu", "mem") else None)
        self._detail_chart.set_values(list(tile.history))
        self._update_facts(tile)
        self._peak_label.set_text(
            "100%" if tile.kind in ("cpu", "mem") else _fmt_bps(self._detail_chart.peak())
        )

    def _update_facts(self, tile: _Tile) -> None:
        for w in list(self._fact_rows.values()):
            self._facts_group.remove(w)
        self._fact_rows = {}
        for label, value in tile.facts.items():
            row = Adw.ActionRow(use_markup=False, title=label, subtitle=value)
            self._facts_group.add(row)
            self._fact_rows[label] = row

    # ---- sampling (values already collected off the main thread; TB-INV-246) ---------
    def update(
        self,
        totals: SystemTotals,
        nprocs: int,
        samples: list[ProcessSample],
        disk_rates: list[DiskRate],
        net_rates: list[NetRate],
        disk_letters: dict[str, list[str]],
    ) -> None:
        self._update_cpu(totals, nprocs, samples)
        self._update_mem(totals)
        self._update_disks(disk_rates, disk_letters)
        self._update_nets(net_rates)
        if self._selected is not None and self._selected in self._tiles:
            self._refresh_selected()

    def _update_cpu(self, totals: SystemTotals, nprocs: int, samples: list[ProcessSample]) -> None:
        cpu_pct: float | None = None
        if totals.cpu_ticks_total is not None:
            busy = sum(s.cpu_ticks for s in samples)
            if self._prev_total is not None and self._prev_busy is not None:
                dt = totals.cpu_ticks_total - self._prev_total
                if dt > 0:
                    cpu_pct = min(100.0, 100.0 * (busy - self._prev_busy) / dt)
            self._prev_total, self._prev_busy = totals.cpu_ticks_total, busy
        facts = {
            "Processors": str(totals.cpu_count),
            "Processes": str(nprocs),
            "Load (1 minute)": "Unknown" if totals.load1 is None else f"{totals.load1:.2f}",
            "Up time": _fmt_uptime(totals.uptime_seconds),
        }
        self._tiles["cpu"].push(cpu_pct, _fmt_pct(cpu_pct), facts)

    def _update_mem(self, totals: SystemTotals) -> None:
        mem_pct: float | None = None
        subtitle = "Unknown"
        facts = {"Memory total": _fmt_bytes(totals.mem_total_bytes)}
        if totals.mem_total_bytes is not None and totals.mem_available_bytes is not None:
            used = totals.mem_total_bytes - totals.mem_available_bytes
            mem_pct = 100.0 * used / totals.mem_total_bytes
            subtitle = f"{_fmt_pct(mem_pct)} ({_fmt_bytes(used)} used)"
            facts["Memory in use"] = _fmt_bytes(used)
        self._tiles["mem"].push(mem_pct, subtitle, facts)

    def _update_disks(self, rates: list[DiskRate], letters: dict[str, list[str]]) -> None:
        seen = set()
        for r in rates:
            seen.add(r.name)
            key = f"disk:{r.name}"
            if key not in self._tiles:
                letter_bits = letters.get(r.name)
                title = f"{r.name} ({', '.join(letter_bits)})" if letter_bits else r.name
                self._add_tile(key, "disk", r.name, title)
            combined = None
            if r.read_bytes_per_sec is not None and r.write_bytes_per_sec is not None:
                combined = r.read_bytes_per_sec + r.write_bytes_per_sec
            facts = {
                "Read speed": _fmt_bps(r.read_bytes_per_sec),
                "Write speed": _fmt_bps(r.write_bytes_per_sec),
            }
            self._tiles[key].push(combined, _fmt_bps(combined), facts)
        # a disk that vanished between ticks (unplugged) keeps its tile and goes Unknown,
        # rather than being removed mid-session and losing the owner's place if selected
        for key, tile in self._tiles.items():
            if tile.kind == "disk" and tile.device not in seen:
                tile.push(None, "Unknown", tile.facts)

    def _update_nets(self, rates: list[NetRate]) -> None:
        seen = set()
        for r in rates:
            seen.add(r.name)
            key = f"net:{r.name}"
            if key not in self._tiles:
                self._add_tile(key, "net", r.name, r.name.capitalize())
            combined = None
            if r.rx_bytes_per_sec is not None and r.tx_bytes_per_sec is not None:
                combined = r.rx_bytes_per_sec + r.tx_bytes_per_sec
            facts = {"Send": _fmt_bps(r.tx_bytes_per_sec), "Receive": _fmt_bps(r.rx_bytes_per_sec)}
            self._tiles[key].push(combined, _fmt_bps(combined), facts)
        for key, tile in self._tiles.items():
            if tile.kind == "net" and tile.device not in seen:
                tile.push(None, "Unknown", tile.facts)

    def _refresh_selected(self) -> None:
        if self._selected is None:
            return
        tile = self._tiles[self._selected]
        self._detail_chart.push(tile.history[-1] if tile.history else None)
        self._detail_subtitle.set_text(tile.device or tile.subtitle)
        self._update_facts(tile)
        self._peak_label.set_text(
            "100%" if tile.kind in ("cpu", "mem") else _fmt_bps(self._detail_chart.peak())
        )


class TaskManagerPage(Gtk.Box):  # type: ignore[misc]
    def __init__(
        self,
        journal: OperationJournal | None = None,
        notify: Callable[[str], None] | None = None,
        sampler_factory: Callable[[], ProcessSampler] = ProcessSampler,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._journal = journal
        self._notify = notify or (lambda text: None)
        self._sampler = sampler_factory()
        self._disk_sampler = DiskIoSampler()
        self._net_sampler = NetIoSampler()
        self._disk_letters: dict[str, list[str]] = {}
        self._disk_letters_loaded = False
        self._visible = False
        self._timer: int | None = None
        self._busy = False
        banner = Adw.Banner(
            title=(
                "End task closes one of your own programs after you confirm. "
                "System and kernel processes cannot be ended here."
            ),
            revealed=True,
        )
        self.append(banner)
        self._stack = Adw.ViewStack()
        self._apps = _ProcessList(
            {ProcessKind.APP, ProcessKind.USER}, "No processes of yours are running", self._ask_end
        )
        self._background = _ProcessList(
            {
                ProcessKind.SYSTEM,
                ProcessKind.OTHER_USER,
                ProcessKind.KERNEL,
                ProcessKind.CRITICAL,
                ProcessKind.SESSION_CRITICAL,
            },
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
            disk_rates = self._disk_sampler.sample()
            net_rates = self._net_sampler.sample()
            if not self._disk_letters_loaded:
                # a D-Bus inventory call (disks.py's own pattern): once here, off the main
                # thread, not on every 2-second tick (TB-INV-246) -- drive letters rarely change
                self._disk_letters = disk_drive_letters()
                self._disk_letters_loaded = True
        except Exception as exc:  # report, never hide (TB-INV-004)
            log.exception("process sampling failed")
            GLib.idle_add(self._fail, str(exc))
            return
        GLib.idle_add(self._apply, samples, totals, disk_rates, net_rates)

    def _fail(self, text: str) -> bool:
        self._status.set_text(f"Could not read processes: {text}")
        self._busy = False
        return False

    # ---- End task (IMP-06.04): preview, confirm, execute off the main loop, report plainly
    def _ask_end(self, sample: ProcessSample, force: bool) -> None:
        plan = plan_terminate(sample.identity, sample.kind, force)
        if not isinstance(plan, TerminatePlan):
            self._notify(plan.plain)
            return
        dialog = Adw.AlertDialog(
            heading="Force end task?" if force else "End task?", body=plan.preview
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("end", "Force end" if force else "End task")
        dialog.set_response_appearance("end", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_confirm, plan)
        dialog.present(self.get_root())

    def _on_confirm(self, _dialog: Adw.AlertDialog, response: str, plan: TerminatePlan) -> None:
        if response != "end":
            self._notify(f"Cancelled. {plan.label} was left running.")
            return
        threading.Thread(target=self._run_end, args=(plan,), name="tb-endtask", daemon=True).start()

    def _run_end(self, plan: TerminatePlan) -> None:
        try:
            result = execute_terminate(plan, self._journal)
        except Exception as exc:  # report, never hide
            log.exception("end task failed")
            GLib.idle_add(self._notify, f"Ending {plan.label} failed unexpectedly: {exc}")
            return
        answers = result.three_answers()
        text = f"{result.plain} {answers['Did anything change?']}"
        if result.safest_next_step and not result.state.is_success:
            text += f" Next: {result.safest_next_step}"
        GLib.idle_add(self._notify, text)
        GLib.idle_add(self._tick)

    def _apply(
        self,
        samples: list[ProcessSample],
        totals: SystemTotals,
        disk_rates: list[DiskRate],
        net_rates: list[NetRate],
    ) -> bool:
        self._apps.update(samples)
        self._background.update(samples)
        self._perf.update(totals, len(samples), samples, disk_rates, net_rates, self._disk_letters)
        unreadable = sum(1 for s in samples if not s.readable)
        note = f"; {unreadable} not fully readable for this account" if unreadable else ""
        self._status.set_text(f"{len(samples)} processes, sampled every 2 s while visible{note}")
        self._busy = False
        return False
