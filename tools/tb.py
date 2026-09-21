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
"""tb - Trier Bridge read-only engineering tools (dispatcher).

Usage: tb <command> [options]   (see tools/README.md)

Exit codes: 0 clean, 1 findings or changes present, 2 tool error/misuse.
Writes only under reports/local/. Never executes a shell. Never touches the network.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tbtools import headers, invariants, ledger, links, outline, snapshot, terms  # noqa: E402
from tbtools.common import REPORT_DIR, Report, central_now, load_config, rel  # noqa: E402


def cmd_all(args, cfg: dict) -> int:
    reps: list[Report] = [
        links.check_links(cfg),
        invariants.check_invariants(cfg),
        terms.check_terms(cfg),
        headers.check_headers(cfg),
    ]
    rc = 0
    for r in reps:
        r.print(full=args.full, limit=cfg.get("brief_limit", 25))
        rc = max(rc, r.exit_code())
    if args.json:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        for r in reps:
            r.write_json()
        print(f"  wrote reports to {rel(REPORT_DIR)}/")
    print(f"-- all checks done {central_now()}; exit {rc}")
    return rc


def cmd_context(args, cfg: dict) -> int:
    snapshot.cmd_status(args, cfg)
    print()
    rc = snapshot.cmd_changes(args, cfg)
    print()
    ledger.cmd_ledger(argparse.Namespace(task=None, full=False), cfg)
    return rc


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--full", action="store_true", help="show every finding, including info")
    common.add_argument("--json", action="store_true", help="also write reports/local/<tool>.json")

    ap = argparse.ArgumentParser(prog="tb", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("context", parents=[common], help="session start: status + changes + ledger").set_defaults(fn=cmd_context)
    sub.add_parser("status", parents=[common], help="one-screen project digest").set_defaults(fn=snapshot.cmd_status)
    sub.add_parser("snapshot", parents=[common], help="record the reviewed state (hash manifest)").set_defaults(fn=snapshot.cmd_snapshot)
    sub.add_parser("changes", parents=[common], help="files added/removed/modified since snapshot").set_defaults(fn=snapshot.cmd_changes)

    lp = sub.add_parser("ledger", parents=[common], help="task ledger summary, or one task with notes")
    lp.add_argument("task", nargs="?", help="task ID or prefix, e.g. ALN-13 or IMP-02")
    lp.set_defaults(fn=ledger.cmd_ledger)

    sub.add_parser("links", parents=[common], help="markdown link and path-mention check").set_defaults(fn=links.cmd_links)

    ip = sub.add_parser("inv", parents=[common], help="invariant index checks; `inv show`, `inv find`")
    isub = ip.add_subparsers(dest="inv_cmd")
    ish = isub.add_parser("show", help="print invariant rows by ID (050, INV-050, SEC-003, IA-12)")
    ish.add_argument("ids", nargs="+")
    ifd = isub.add_parser("find", help="regex search over must/failure text")
    ifd.add_argument("pattern")
    ip.set_defaults(fn=invariants.cmd_invariants)

    sub.add_parser("terms", parents=[common], help="policy-phrase and code-smell scan").set_defaults(fn=terms.cmd_terms)
    sub.add_parser("headers", parents=[common], help="source-header compliance").set_defaults(fn=headers.cmd_headers)

    op = sub.add_parser("outline", parents=[common], help="heading outline with line numbers")
    op.add_argument("file")
    op.add_argument("--depth", type=int, default=0)
    op.set_defaults(fn=outline.cmd_outline)

    sp = sub.add_parser("section", parents=[common], help="print one section of a markdown file")
    sp.add_argument("file")
    sp.add_argument("pattern", help="regex matched against heading titles")
    sp.add_argument("-n", "--numbers", action="store_true", help="prefix line numbers")
    sp.add_argument("--all", action="store_true", help="print every matching section")
    sp.set_defaults(fn=outline.cmd_section)

    sub.add_parser("all", parents=[common], help="run links, inv, terms, headers").set_defaults(fn=cmd_all)
    return ap


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config()
        return int(args.fn(args, cfg))
    except FileNotFoundError as e:
        print(f"tb: missing file: {e}")
        return 2
    except KeyboardInterrupt:
        print("tb: interrupted")
        return 2


if __name__ == "__main__":
    sys.exit(main())
