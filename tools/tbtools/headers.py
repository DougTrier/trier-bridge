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
"""headers: source-header compliance per LICENSING.md sections 5-7.

Read-only: reports missing headers, never inserts them (LICENSING.md section 7
requires classification before any rewrite).
"""
from __future__ import annotations

import re

from .common import Report, glob_match, iter_files, read_text, rel

COPYRIGHT_RX = re.compile(r"Copyright \d{4} Doug Trier")
LICENSE_RX = re.compile(
    r"Licensed under the Apache License, Version 2\.0|SPDX-License-Identifier:\s*Apache-2\.0"
)


def check_headers(cfg: dict) -> Report:
    rep = Report("headers")
    hcfg = cfg.get("headers", {})
    exts = set(hcfg.get("extensions", []))
    excl = hcfg.get("exclude_globs", [])
    max_lines = int(hcfg.get("max_lines", 20))
    checked = ok = 0
    for p in iter_files(cfg):
        if p.suffix not in exts:
            continue
        r = rel(p)
        if glob_match(r, excl):
            continue
        checked += 1
        head = "\n".join(read_text(p).splitlines()[:max_lines])
        has_c, has_l = bool(COPYRIGHT_RX.search(head)), bool(LICENSE_RX.search(head))
        if has_c and has_l:
            ok += 1
        elif not has_c and not has_l:
            rep.add("warn", "header-missing", r, 1, "no copyright/license header in first lines")
        else:
            rep.add(
                "warn",
                "header-partial",
                r,
                1,
                (
                    "copyright present, license missing"
                    if has_c
                    else "license present, copyright missing"
                ),
            )
    rep.summary = {"checked": checked, "compliant": ok}
    if checked == 0:
        rep.summary["note"] = "no source files yet"
    return rep


def cmd_headers(args, cfg: dict) -> int:
    rep = check_headers(cfg)
    rep.print(full=args.full, limit=cfg.get("brief_limit", 25))
    if args.json:
        print(f"  wrote {rel(rep.write_json())}")
    return rep.exit_code()
