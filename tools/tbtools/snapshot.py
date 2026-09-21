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
"""snapshot / changes / status.

WHY: a reviewer (human or agent) should not reread the whole project every
session. `snapshot` records what was last reviewed; `changes` lists only what
differs since then; `status` is a one-screen digest.
"""
from __future__ import annotations

import datetime as dt
import json
import shutil

from . import ledger
from .common import (
    REPORT_DIR,
    ROOT,
    Report,
    central_now,
    fmt_bytes,
    git_info,
    iter_files,
    rel,
    sha256_file,
)

MANIFEST = REPORT_DIR / "manifest.json"
MANIFEST_PREV = REPORT_DIR / "manifest.prev.json"


def build_manifest(cfg: dict) -> dict:
    files = {}
    total = 0
    for p in iter_files(cfg):
        st = p.stat()
        files[rel(p)] = {
            "size": st.st_size,
            "sha256": sha256_file(p),
            "mtime": dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        }
        total += st.st_size
    return {"taken": central_now(), "files": len(files), "bytes": total, "entries": files}


def load_manifest() -> dict | None:
    if not MANIFEST.is_file():
        return None
    with MANIFEST.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def diff_manifest(old: dict, new: dict) -> dict:
    o, n = old.get("entries", {}), new.get("entries", {})
    added = sorted(k for k in n if k not in o)
    removed = sorted(k for k in o if k not in n)
    modified = sorted(k for k in n if k in o and n[k]["sha256"] != o[k]["sha256"])
    return {"added": added, "removed": removed, "modified": modified}


def cmd_snapshot(args, cfg: dict) -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if MANIFEST.is_file():
        shutil.copyfile(MANIFEST, MANIFEST_PREV)
    m = build_manifest(cfg)
    with MANIFEST.open("w", encoding="utf-8") as fh:
        json.dump(m, fh, indent=1)
    size = fmt_bytes(m["bytes"])
    print(f"snapshot taken {m['taken']}: {m['files']} files, {size} -> {rel(MANIFEST)}")
    return 0


def cmd_changes(args, cfg: dict) -> int:
    old = load_manifest()
    if old is None:
        print("no snapshot yet; run `tb snapshot` after reviewing the project")
        return 0
    new = build_manifest(cfg)
    d = diff_manifest(old, new)
    rep = Report("changes")
    rep.summary = {
        "since": old["taken"],
        "added": len(d["added"]),
        "removed": len(d["removed"]),
        "modified": len(d["modified"]),
    }
    for k in d["added"]:
        rep.add("warn", "added", k, None, fmt_bytes(new["entries"][k]["size"]))
    for k in d["removed"]:
        rep.add("warn", "removed", k, None, "")
    for k in d["modified"]:
        before = fmt_bytes(old["entries"][k]["size"])
        after = fmt_bytes(new["entries"][k]["size"])
        rep.add("warn", "modified", k, None, f"{before} -> {after}")
    rep.print(full=True)
    if not rep.findings:
        print("  no changes since snapshot")
    if getattr(args, "json", False):
        print(f"  wrote {rel(rep.write_json())}")
    return rep.exit_code()


def cmd_status(args, cfg: dict) -> int:
    print(f"Trier Bridge status - {central_now()}")
    print(f"root: {ROOT}")
    files = list(iter_files(cfg))
    total = sum(p.stat().st_size for p in files)
    top = sorted({rel(p).split("/")[0] for p in files if "/" in rel(p)})
    print(f"files: {len(files)} ({fmt_bytes(total)}); dirs: {', '.join(top) or '-'}")

    g = git_info()
    if g is None:
        print("git: no repository")
    elif "error" in g:
        print(f"git: {g['error']}")
    else:
        changed = f"{g['dirty']} changed ({g['untracked']} untracked)"
        print(f"git: {g['branch']}; {changed}; last: {g['last_commit']}")

    old = load_manifest()
    if old is None:
        print("snapshot: none (run `tb snapshot`)")
    else:
        d = diff_manifest(old, build_manifest(cfg))
        n = len(d["added"]) + len(d["removed"]) + len(d["modified"])
        hint = " (run `tb changes`)" if n else ""
        print(f"snapshot: {old['taken']} ({old['files']} files); unreviewed changes: {n}{hint}")

    try:
        s = ledger.summarize(cfg)
        dash = s["dashboard"]
        print(f"ledger: active={dash.get('Active task', '?')}")
        print(f"        next={dash.get('Next bounded step', '?')}")
        parts = [f"{sec['short']} {sec['done']}/{sec['total']}" for sec in s["sections"]]
        print("        " + "; ".join(parts))
    except FileNotFoundError:
        print("ledger: file not found")

    recent = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    print("recent: " + ", ".join(rel(p) for p in recent))
    return 0
