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
"""invariants: index TB-INV / TB-SEC / TB-IA identifiers and cross-check references.

WHY: INVARIANTS.md is 57 KB. `tb inv show 050` or `tb inv find <regex>` returns
one row instead of the whole file, and `tb inv` catches references to IDs that
do not exist (a common drift once code cites invariants).
"""
from __future__ import annotations

import re

from .common import ROOT, Report, is_text, iter_files, read_text, rel

INV_ROW = re.compile(r"^\|\s*\*\*(TB-INV-\d{3})\*\*\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")
SEC_HEAD = re.compile(r"^##\s+(TB-SEC-\d{3})\s*[—-]+\s*(.*)$")
IA_ROW = re.compile(r"^\|\s*(TB-IA-\d{2})\s*\|\s*(.*?)\s*\|\s*$")
FAMILY_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*TB-INV-(\d{3})[–-]TB-INV-(\d{3})\s*\|\s*$")
TOTAL_RX = re.compile(r"Total baseline invariants:\s*(\d+)")
REF_RX = re.compile(r"\bTB-(INV|SEC|T|IA)-(\d{2,3})\b")


def load_index(cfg: dict) -> dict:
    inv, sec, ia, families = {}, {}, {}, []
    total_claim = None
    inv_path = ROOT / cfg["invariants_file"]
    for i, ln in enumerate(read_text(inv_path).splitlines(), 1):
        m = INV_ROW.match(ln)
        if m:
            inv[m.group(1)] = {"must": m.group(2), "failure": m.group(3), "line": i}
            continue
        m = FAMILY_ROW.match(ln)
        if m and m.group(1) != "Family":
            families.append((m.group(1), int(m.group(2)), int(m.group(3))))
        m = TOTAL_RX.search(ln)
        if m:
            total_claim = int(m.group(1))
    sec_path = ROOT / cfg["security_file"]
    for i, ln in enumerate(read_text(sec_path).splitlines(), 1):
        m = SEC_HEAD.match(ln)
        if m:
            sec[m.group(1)] = {"title": m.group(2).strip(), "line": i}
    ia_path = ROOT / cfg["acceptance_file"]
    if ia_path.is_file():
        for i, ln in enumerate(read_text(ia_path).splitlines(), 1):
            m = IA_ROW.match(ln)
            if m:
                ia[m.group(1)] = {"case": m.group(2), "line": i}
    return {"inv": inv, "sec": sec, "ia": ia, "families": families, "total_claim": total_claim}


def check_invariants(cfg: dict) -> Report:
    rep = Report("invariants")
    idx = load_index(cfg)
    inv, sec, ia = idx["inv"], idx["sec"], idx["ia"]
    inv_file = cfg["invariants_file"]
    sec_file = cfg["security_file"]

    nums = sorted(int(k[-3:]) for k in inv)
    max_inv = nums[-1] if nums else 0
    missing = [n for n in range(1, max_inv + 1) if n not in set(nums)]
    if missing:
        rep.add(
            "error", "inv-gap", inv_file, None, f"missing IDs in 001..{max_inv:03d}: {missing[:10]}"
        )
    if idx["total_claim"] is not None and idx["total_claim"] != len(inv):
        rep.add(
            "error",
            "inv-total",
            inv_file,
            None,
            f"file claims {idx['total_claim']} invariants but defines {len(inv)}",
        )
    covered = set()
    for name, a, b in idx["families"]:
        for n in range(a, b + 1):
            if n in covered:
                rep.add(
                    "error", "family-overlap", inv_file, None, f"{name} overlaps at TB-INV-{n:03d}"
                )
            covered.add(n)
    if idx["families"] and covered != set(nums):
        diff = sorted(set(nums) ^ covered)
        rep.add(
            "error",
            "family-coverage",
            inv_file,
            None,
            f"family index does not match defined IDs: {diff[:10]}",
        )

    refs: dict[str, set[str]] = {}
    n_refs = 0
    ref_files = set()
    for p in iter_files(cfg):
        if not is_text(p, cfg):
            continue
        r = rel(p)
        for i, ln in enumerate(read_text(p).splitlines(), 1):
            for m in REF_RX.finditer(ln):
                fam, num = m.group(1), m.group(2)
                full = f"TB-{fam}-{num}"
                n_refs += 1
                ref_files.add(r)
                if fam == "INV":
                    if r == inv_file and INV_ROW.match(ln):
                        continue
                    refs.setdefault(full, set()).add(r)
                    if full not in inv:
                        rep.add(
                            "error", "ref-undefined", r, i, f"{full} is not defined in {inv_file}"
                        )
                elif fam == "SEC":
                    if r == sec_file and SEC_HEAD.match(ln):
                        continue
                    if full not in sec:
                        rep.add(
                            "error", "ref-undefined", r, i, f"{full} is not defined in {sec_file}"
                        )
                elif fam == "T":
                    if int(num) < 1 or int(num) > max_inv:
                        rep.add(
                            "warn",
                            "ref-test-range",
                            r,
                            i,
                            f"{full} has no TB-INV-{num} counterpart",
                        )
                elif fam == "IA":
                    if r == cfg["acceptance_file"] and IA_ROW.match(ln):
                        continue
                    if ia and full not in ia:
                        rep.add(
                            "error",
                            "ref-undefined",
                            r,
                            i,
                            f"{full} is not defined in {cfg['acceptance_file']}",
                        )
    unreferenced = [k for k in inv if k not in refs]
    rep.summary = {
        "inv": len(inv),
        "sec": len(sec),
        "ia": len(ia),
        "families": len(idx["families"]),
        "refs": n_refs,
        "ref_files": len(ref_files),
        "inv_unreferenced": len(unreferenced),
    }
    return rep


def _norm(token: str, fam_default: str) -> str:
    t = token.upper()
    if t.startswith("TB-"):
        return t
    m = re.match(r"^(INV|SEC|IA|T)-?(\d+)$", t)
    if m:
        fam, num = m.group(1), m.group(2)
    else:
        fam, num = fam_default, re.sub(r"\D", "", t)
    width = 2 if fam == "IA" else 3
    return f"TB-{fam}-{int(num):0{width}d}"


def cmd_invariants(args, cfg: dict) -> int:
    sub = getattr(args, "inv_cmd", None)
    if sub == "show":
        idx = load_index(cfg)
        rc = 0
        for tok in args.ids:
            key = _norm(tok, "INV")
            if key in idx["inv"]:
                row = idx["inv"][key]
                print(f"{key}  ({cfg['invariants_file']}:{row['line']})")
                print(f"  Must remain true: {row['must']}")
                print(f"  Graceful failure: {row['failure']}")
            elif key in idx["sec"]:
                row = idx["sec"][key]
                print(f"{key}  {row['title']}  ({cfg['security_file']}:{row['line']})")
            elif key in idx["ia"]:
                row = idx["ia"][key]
                print(f"{key}  {row['case']}  ({cfg['acceptance_file']}:{row['line']})")
            else:
                print(f"{key}: not defined")
                rc = 1
        return rc
    if sub == "find":
        idx = load_index(cfg)
        rx = re.compile(args.pattern, re.I)
        hits = 0
        for key, row in idx["inv"].items():
            text = row["must"] + " || " + row["failure"]
            if rx.search(text):
                hits += 1
                print(f"{key}  {row['must'][:140]}")
        for key, row in idx["sec"].items():
            if rx.search(row["title"]):
                hits += 1
                print(f"{key}  {row['title']}")
        print(f"-- {hits} match(es)")
        return 0
    rep = check_invariants(cfg)
    rep.print(full=args.full, limit=cfg.get("brief_limit", 25))
    if args.json:
        print(f"  wrote {rel(rep.write_json())}")
    return rep.exit_code()
