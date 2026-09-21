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
"""links: verify markdown links and backticked file mentions resolve."""
from __future__ import annotations

import re
from urllib.parse import unquote

from .common import ROOT, Report, glob_match, iter_files, read_text, rel

LINK_RX = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
MENTION_RX = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./ -]*\.(?:md|MD|txt|json|ps1|py|cmd|bat|sh))`")
EXTERNAL = ("http://", "https://", "mailto:", "#")


def check_links(cfg: dict) -> Report:
    rep = Report("links")
    allow = cfg.get("links", {}).get("mention_allow_files", [])
    n_files = n_links = n_mentions = 0
    all_files = list(iter_files(cfg))
    basenames = {p.name.lower() for p in all_files}
    for p in all_files:
        if p.suffix.lower() != ".md":
            continue
        n_files += 1
        r = rel(p)
        for i, ln in enumerate(read_text(p).splitlines(), 1):
            for m in LINK_RX.finditer(ln):
                target = m.group(2)
                if target.startswith(EXTERNAL):
                    continue
                n_links += 1
                t = unquote(target.split("#", 1)[0])
                if not t:
                    continue
                if (p.parent / t).exists():
                    continue
                if (ROOT / t).exists():
                    rep.add("warn", "link-root-only", r, i, f"'{target}' resolves only from repo root, not from this file")
                else:
                    rep.add("error", "link-broken", r, i, f"'{target}' does not exist")
            if glob_match(r, allow):
                continue
            for m in MENTION_RX.finditer(ln):
                t = m.group(1).strip()
                if "*" in t:
                    continue
                n_mentions += 1
                cands = [p.parent / t, ROOT / t, ROOT / "docs" / t, ROOT / "tools" / t]
                if any(c.exists() for c in cands):
                    continue
                if "/" not in t and t.lower() in basenames:
                    continue  # bare filename that exists somewhere in the tree
                rep.add("info", "mention-unresolved", r, i, f"`{t}` not found (mention, not a link)")
    rep.summary = {"md_files": n_files, "links": n_links, "mentions": n_mentions}
    return rep


def cmd_links(args, cfg: dict) -> int:
    rep = check_links(cfg)
    rep.print(full=args.full, limit=cfg.get("brief_limit", 25))
    if args.json:
        print(f"  wrote {rel(rep.write_json())}")
    return rep.exit_code()
