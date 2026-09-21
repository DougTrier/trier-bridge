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
"""terms: policy-phrase and code-smell scan driven by tools/tb-config.json.

Rules are data, not code, so adding a project rule never requires editing
this module. Each rule: id, pattern, severity, message, optional flags,
include/exclude globs, and code_only (restrict to code globs).
"""
from __future__ import annotations

import re

from .common import Report, glob_match, is_text, iter_files, read_text, rel


def _compile_rules(cfg: dict) -> list[dict]:
    out = []
    for r in cfg.get("terms", {}).get("rules", []):
        flags = re.I if "i" in r.get("flags", "") else 0
        out.append({**r, "rx": re.compile(r["pattern"], flags)})
    return out


def check_terms(cfg: dict) -> Report:
    rep = Report("terms")
    tcfg = cfg.get("terms", {})
    code_globs = tcfg.get("code_globs", [])
    global_exclude = tcfg.get("exclude_globs", [])
    rules = _compile_rules(cfg)
    n_files = n_lines = 0
    for p in iter_files(cfg):
        if not is_text(p, cfg):
            continue
        r = rel(p)
        if glob_match(r, global_exclude):
            continue
        is_code = glob_match(r, code_globs)
        active = []
        for rule in rules:
            if rule.get("code_only") and not is_code:
                continue
            inc = rule.get("include")
            if inc and not glob_match(r, inc):
                continue
            if glob_match(r, rule.get("exclude", [])):
                continue
            active.append(rule)
        if not active:
            continue
        n_files += 1
        for i, ln in enumerate(read_text(p).splitlines(), 1):
            n_lines += 1
            for rule in active:
                m = rule["rx"].search(ln)
                if m:
                    snippet = ln.strip()
                    if len(snippet) > 90:
                        s = max(0, m.start() - 30)
                        snippet = "..." + ln[s : s + 90].strip() + "..."
                    rep.add(rule["severity"], rule["id"], r, i, f"{rule['message']}  | {snippet}")
    rep.summary = {"rules": len(rules), "files": n_files, "lines": n_lines}
    return rep


def cmd_terms(args, cfg: dict) -> int:
    rep = check_terms(cfg)
    rep.print(full=args.full, limit=cfg.get("brief_limit", 25))
    if args.json:
        print(f"  wrote {rel(rep.write_json())}")
    return rep.exit_code()
