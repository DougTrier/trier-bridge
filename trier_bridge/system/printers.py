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
"""Printers and print queues, read from CUPS (Printers & scanners on Windows).

Read-only. Uses ``python3-cups`` (pycups), which Ubuntu Desktop installs with
its printer tools; it is an optional dependency here (Recommends), and when it
is absent only this page says so (TB-INV-033). Changing printers, defaults,
and queues stays with GNOME Settings and the CUPS tools, which the page opens.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PRINTER_STATES = {3: "Ready", 4: "Printing", 5: "Stopped"}
JOB_STATES = {
    3: "Waiting",
    4: "Held",
    5: "Printing",
    6: "Stopped",
    7: "Cancelled",
    8: "Aborted",
    9: "Completed",
}


@dataclass(frozen=True)
class PrintJob:
    job_id: int
    title: str
    user: str
    state: str
    printer: str


@dataclass(frozen=True)
class Printer:
    name: str
    description: str
    location: str
    make_model: str
    state: str
    reason: str  # e.g. "media-empty", "" when none
    is_default: bool
    accepting: bool
    shared: bool
    uri: str
    jobs: tuple[PrintJob, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PrinterOverview:
    available: bool
    detail: str
    printers: tuple[Printer, ...] = field(default_factory=tuple)
    default_name: str = ""


def _str(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value if str(v) != "none")
    return "" if value is None else str(value)


def read_printers() -> PrinterOverview:
    try:
        import cups
    except ImportError:
        return PrinterOverview(
            False,
            "The printer library (python3-cups) is not installed; printers are managed in "
            "Settings.",
        )
    try:
        conn = cups.Connection()
        raw = conn.getPrinters()
        default = conn.getDefault() or ""
        jobs_raw = conn.getJobs(which_jobs="not-completed")
    except (cups.IPPError, RuntimeError, OSError) as exc:
        return PrinterOverview(False, f"The print service (CUPS) did not answer: {exc}")
    jobs_by_printer: dict[str, list[PrintJob]] = {}
    for job_id, attrs in sorted(jobs_raw.items()):
        try:
            job_attrs = conn.getJobAttributes(job_id)
        except (cups.IPPError, RuntimeError):
            job_attrs = attrs
        uri = _str(job_attrs.get("job-printer-uri", attrs.get("job-printer-uri", "")))
        printer = uri.rsplit("/", 1)[-1]
        jobs_by_printer.setdefault(printer, []).append(
            PrintJob(
                int(job_id),
                _str(job_attrs.get("job-name", "")) or f"Job {job_id}",
                _str(job_attrs.get("job-originating-user-name", "")),
                JOB_STATES.get(int(job_attrs.get("job-state", 0) or 0), "Unknown"),
                printer,
            )
        )
    printers = []
    for name, p in sorted(raw.items()):
        reasons = _str(p.get("printer-state-reasons", ""))
        printers.append(
            Printer(
                name=name,
                description=_str(p.get("printer-info", "")),
                location=_str(p.get("printer-location", "")),
                make_model=_str(p.get("printer-make-and-model", "")),
                state=PRINTER_STATES.get(int(p.get("printer-state", 0) or 0), "Unknown"),
                reason="" if reasons in ("", "none") else reasons,
                is_default=(name == default),
                accepting=bool(p.get("printer-is-accepting-jobs", False)),
                shared=bool(p.get("printer-is-shared", False)),
                uri=_str(p.get("device-uri", "")),
                jobs=tuple(jobs_by_printer.get(name, [])),
            )
        )
    return PrinterOverview(True, "Read from CUPS.", tuple(printers), default)
