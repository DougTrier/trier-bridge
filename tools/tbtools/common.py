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
"""Shared helpers: repo layout, config, file walking, hashing, reports, time.

OWNERSHIP: every tool goes through these helpers so the read-only contract
(writes only under reports/local/) lives in one place.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Iterator

TOOLS_DIR = Path(__file__).resolve().parent.parent
ROOT = TOOLS_DIR.parent
CONFIG_PATH = TOOLS_DIR / "tb-config.json"
REPORT_DIR = ROOT / "reports" / "local"

SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}


# --------------------------------------------------------------------------- config


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- time


def _us_central_fallback(now_utc: dt.datetime) -> tuple[dt.datetime, str]:
    """Compute America/Chicago without tzdata (Windows lacks the IANA db).

    US DST: starts second Sunday of March 02:00 CST (08:00 UTC),
    ends first Sunday of November 02:00 CDT (07:00 UTC).
    """
    y = now_utc.year

    def nth_sunday(month: int, n: int) -> dt.date:
        d = dt.date(y, month, 1)
        offset = (6 - d.weekday()) % 7  # Monday=0 ... Sunday=6
        return d + dt.timedelta(days=offset + 7 * (n - 1))

    start = dt.datetime.combine(nth_sunday(3, 2), dt.time(8, 0), tzinfo=dt.timezone.utc)
    end = dt.datetime.combine(nth_sunday(11, 1), dt.time(7, 0), tzinfo=dt.timezone.utc)
    if start <= now_utc < end:
        return now_utc.astimezone(dt.timezone(dt.timedelta(hours=-5))), "CDT"
    return now_utc.astimezone(dt.timezone(dt.timedelta(hours=-6))), "CST"


def central_now() -> str:
    """Project timestamp per AGENTS.md section 3, e.g. '2026-09-20 09:36 PM CDT'."""
    now_utc = dt.datetime.now(dt.timezone.utc)
    try:
        from zoneinfo import ZoneInfo  # type: ignore

        local = now_utc.astimezone(ZoneInfo("America/Chicago"))
        tz = local.strftime("%Z") or "CT"
    except Exception:  # zoneinfo db unavailable on this host
        local, tz = _us_central_fallback(now_utc)
    hour = local.hour % 12 or 12
    return f"{local:%Y-%m-%d} {hour:02d}:{local:%M} {local:%p} {tz}"


# --------------------------------------------------------------------------- files


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def glob_to_regex(glob: str) -> re.Pattern:
    """Translate a path glob to a regex. '**/' matches any depth including none;
    '*' does not cross '/'. Matching is against the repo-relative posix path."""
    out = ""
    i = 0
    while i < len(glob):
        c = glob[i]
        if glob.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
            continue
        if glob.startswith("**", i):
            out += ".*"
            i += 2
            continue
        if c == "*":
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        else:
            out += re.escape(c)
        i += 1
    return re.compile("^" + out + "$")


_GLOB_CACHE: dict[str, re.Pattern] = {}


def glob_match(relpath: str, globs: Iterable[str]) -> bool:
    for g in globs:
        rx = _GLOB_CACHE.get(g)
        if rx is None:
            rx = _GLOB_CACHE[g] = glob_to_regex(g)
        if rx.match(relpath):
            return True
    return False


def iter_files(cfg: dict) -> Iterator[Path]:
    """Yield every project file, skipping ignored directories and globs."""
    ignore_dirs = set(cfg.get("ignore_dirs", []))
    ignore_globs = cfg.get("ignore_globs", [])
    stack = [ROOT]
    while stack:
        d = stack.pop()
        try:
            entries = sorted(d.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            continue
        for p in entries:
            if p.is_dir():
                if p.name in ignore_dirs:
                    continue
                stack.append(p)
            elif p.is_file():
                r = rel(p)
                if glob_match(r, ignore_globs) or glob_match(p.name, ignore_globs):
                    continue
                yield p


def is_text(path: Path, cfg: dict) -> bool:
    if path.name in cfg.get("text_names", []):
        return True
    return path.suffix in cfg.get("text_extensions", [])


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def resolve_project_file(name: str, cfg: dict) -> Path | None:
    """Accept a path as given, relative to root, or a bare filename found in
    the root, docs/, or tools/."""
    cands = [Path(name), ROOT / name, ROOT / "docs" / name, ROOT / "tools" / name]
    for c in cands:
        if c.is_file():
            return c
    base = Path(name).name.lower()
    for p in iter_files(cfg):
        if p.name.lower() == base:
            return p
    return None


# --------------------------------------------------------------------------- git


def git_info() -> dict | None:
    """Read-only git facts, or None when there is no repository/git binary."""
    if not (ROOT / ".git").exists():
        return None
    try:
        st = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain", "--branch"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        lg = subprocess.run(
            ["git", "-C", str(ROOT), "log", "-1", "--format=%h %cs %s"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"error": "git unavailable"}
    lines = st.stdout.splitlines()
    branch = lines[0][3:] if lines and lines[0].startswith("## ") else "?"
    dirty = [ln for ln in lines[1:] if ln.strip()]
    return {
        "branch": branch,
        "dirty": len(dirty),
        "untracked": sum(1 for ln in dirty if ln.startswith("??")),
        "last_commit": lg.stdout.strip() or "(no commits)",
    }


# --------------------------------------------------------------------------- reports


@dataclass
class Finding:
    severity: str
    rule: str
    file: str
    line: int | None
    message: str

    def sort_key(self):
        return (SEVERITY_ORDER.get(self.severity, 9), self.file, self.line or 0)


class Report:
    """Findings plus a summary. Exit code: 0 clean, 1 warn/error findings."""

    def __init__(self, tool: str):
        self.tool = tool
        self.taken = central_now()
        self.findings: list[Finding] = []
        self.summary: dict = {}

    def add(self, severity: str, rule: str, file: str, line: int | None, message: str) -> None:
        self.findings.append(Finding(severity, rule, file, line, message))

    def counts(self) -> dict[str, int]:
        c = {"error": 0, "warn": 0, "info": 0}
        for f in self.findings:
            c[f.severity] = c.get(f.severity, 0) + 1
        return c

    def exit_code(self) -> int:
        c = self.counts()
        return 1 if (c["error"] or c["warn"]) else 0

    def header(self) -> str:
        c = self.counts()
        summ = "  ".join(f"{k}={v}" for k, v in self.summary.items())
        counts = f"{c['error']} error, {c['warn']} warn, {c['info']} info"
        return f"== {self.tool}: {counts}   {summ}".rstrip()

    def print(self, full: bool = False, limit: int = 25) -> None:
        print(self.header())
        items = sorted(self.findings, key=Finding.sort_key)
        if not full:
            shown = [f for f in items if f.severity != "info"]
            hidden_info = len(items) - len(shown)
        else:
            shown, hidden_info = items, 0
        for f in shown[: None if full else limit]:
            loc = f"{f.file}:{f.line}" if f.line else f.file
            print(f"  [{f.severity}] {f.rule} {loc}  {f.message}")
        if not full and len(shown) > limit:
            print(f"  ... {len(shown) - limit} more (use --full)")
        if hidden_info:
            print(f"  ({hidden_info} info hidden; use --full)")

    def to_dict(self) -> dict:
        return {
            "tool": self.tool,
            "taken": self.taken,
            "summary": self.summary,
            "counts": self.counts(),
            "findings": [asdict(f) for f in sorted(self.findings, key=Finding.sort_key)],
        }

    def write_json(self, name: str | None = None) -> Path:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORT_DIR / f"{name or self.tool}.json"
        with out.open("w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        return out
