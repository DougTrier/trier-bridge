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
"""ledger: parse the Engine Spec Tasklist without reading it in full.

The ledger format is: a '## Resume dashboard' table, then H1 sections each
containing '- [ ] **ID** text' tasks with optional indented note lines.
"""
from __future__ import annotations

import re

from .common import ROOT, read_text

TASK_RX = re.compile(r"^- \[( |x|X)\] \*\*([A-Z]+-[0-9][0-9.]*)\*\*\s*(.*)$")
DASH_RX = re.compile(r"^\|\s*\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*$")
H1_RX = re.compile(r"^# (.+)$")


def parse(cfg: dict) -> dict:
    path = ROOT / cfg["ledger_file"]
    lines = read_text(path).splitlines()
    dashboard: dict[str, str] = {}
    sections: list[dict] = []
    tasks: list[dict] = []
    in_dash = False
    cur = None
    last_task = None
    for i, ln in enumerate(lines, 1):
        if ln.startswith("## Resume dashboard"):
            in_dash = True
            continue
        if in_dash:
            if ln.startswith("---"):
                in_dash = False
            else:
                m = DASH_RX.match(ln)
                if m and m.group(1) != "Field":
                    dashboard[m.group(1)] = m.group(2)
            continue
        m = H1_RX.match(ln)
        if m and not ln.startswith("# Engine Spec"):
            cur = {"name": m.group(1).strip(), "line": i, "tasks": []}
            sections.append(cur)
            last_task = None
            continue
        m = TASK_RX.match(ln)
        if m and cur is not None:
            t = {"id": m.group(2), "done": m.group(1).lower() == "x", "text": m.group(3).strip(),
                 "line": i, "section": cur["name"], "notes": []}
            cur["tasks"].append(t)
            tasks.append(t)
            last_task = t
            continue
        if last_task is not None and ln.startswith("  ") and ln.strip():
            last_task["notes"].append(ln.strip())
        elif ln.strip() == "":
            continue
        else:
            last_task = None
    return {"file": cfg["ledger_file"], "dashboard": dashboard, "sections": sections, "tasks": tasks}


def summarize(cfg: dict) -> dict:
    p = parse(cfg)
    out = []
    for s in p["sections"]:
        if not s["tasks"]:
            continue
        done = sum(1 for t in s["tasks"] if t["done"])
        nxt = next((t for t in s["tasks"] if not t["done"]), None)
        short = s["name"].split(" — ")[0].split(" / ")[0]
        short = re.sub(r"^(Foundation \d+).*$", r"\1", short)
        out.append({"name": s["name"], "short": short[:24], "done": done, "total": len(s["tasks"]),
                    "next": f"{nxt['id']} {nxt['text']}" if nxt else "-"})
    return {"dashboard": p["dashboard"], "sections": out, "tasks": p["tasks"]}


def cmd_ledger(args, cfg: dict) -> int:
    p = parse(cfg)
    want = getattr(args, "task", None)
    if want:
        want = want.upper()
        hits = [t for t in p["tasks"] if t["id"].upper() == want or t["id"].upper().startswith(want)]
        if not hits:
            print(f"no task matching {want}")
            return 1
        for t in hits:
            mark = "x" if t["done"] else " "
            print(f"[{mark}] {t['id']}  {t['text']}   ({p['file']}:{t['line']}, {t['section']})")
            for n in t["notes"]:
                print(f"      {n}")
        return 0

    s = summarize(cfg)
    print(f"== ledger: {p['file']}")
    for k, v in s["dashboard"].items():
        print(f"  {k}: {v}")
    print("  --")
    for sec in s["sections"]:
        print(f"  {sec['done']:>2}/{sec['total']:<2} {sec['name'][:48]:<48} next: {sec['next'][:60]}")
    if getattr(args, "full", False):
        print("  --")
        for t in p["tasks"]:
            mark = "x" if t["done"] else " "
            print(f"  [{mark}] {t['id']:<10} {t['text']}")
            for n in t["notes"]:
                print(f"        {n}")
    return 0
