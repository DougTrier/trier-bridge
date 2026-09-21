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
"""outline / section: navigate large markdown files by heading.

WHY: SECURITY.md and INVARIANTS.md are ~50 KB each. `tb outline SECURITY.md`
gives heading + line number + size; `tb section SECURITY.md "6.3"` prints just
that section. A reviewer reads the piece that matters instead of the file.
"""
from __future__ import annotations

import re

from .common import read_text, rel, resolve_project_file

HEAD_RX = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def headings(lines: list[str]) -> list[dict]:
    out = []
    fence = False
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = HEAD_RX.match(ln)
        if m:
            out.append({"level": len(m.group(1)), "title": m.group(2), "line": i})
    for k, h in enumerate(out):
        end = len(lines) + 1
        for nxt in out[k + 1 :]:
            if nxt["level"] <= h["level"]:
                end = nxt["line"]
                break
        h["end"] = end
        h["lines"] = end - h["line"]
    return out


def cmd_outline(args, cfg: dict) -> int:
    p = resolve_project_file(args.file, cfg)
    if p is None:
        print(f"file not found: {args.file}")
        return 2
    lines = read_text(p).splitlines()
    hs = headings(lines)
    depth = getattr(args, "depth", 0) or 99
    print(f"== outline: {rel(p)} ({len(lines)} lines, {len(hs)} headings)")
    for h in hs:
        if h["level"] > depth:
            continue
        print(f"  L{h['line']:>5} {'  ' * (h['level'] - 1)}{h['title']}  [{h['lines']} lines]")
    return 0


def cmd_section(args, cfg: dict) -> int:
    p = resolve_project_file(args.file, cfg)
    if p is None:
        print(f"file not found: {args.file}")
        return 2
    lines = read_text(p).splitlines()
    hs = headings(lines)
    rx = re.compile(args.pattern, re.I)
    hits = [h for h in hs if rx.search(h["title"])]
    if not hits:
        print(f"no heading in {rel(p)} matches /{args.pattern}/")
        return 1
    if len(hits) > 1 and not getattr(args, "all", False):
        print(f"{len(hits)} headings match; showing the first (use --all for every match):")
        for h in hits:
            print(f"  L{h['line']:>5} {h['title']}")
        hits = hits[:1]
    for h in hits:
        print(f"== {rel(p)} L{h['line']}-{h['end'] - 1}: {h['title']}")
        for i in range(h["line"], h["end"]):
            if getattr(args, "numbers", False):
                print(f"{i:>5}  {lines[i - 1]}")
            else:
                print(lines[i - 1])
    return 0
