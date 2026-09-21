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
"""dev - Trier Bridge development checks (IMP-01.04 entry points).

Usage: python tools/dev.py <command>

  format      black --check (add --fix to rewrite)
  lint        flake8
  typecheck   mypy --strict (configured in pyproject.toml)
  test        pytest tests/unit (add --integration for tests/integration; VM only)
  headers     source-header compliance (tb headers)
  inventory   dependency inventory (debian/control, docs/TOOLCHAIN.md pins, runtime imports)
  size        size of the source tree and, if present, the built package
  all         format, lint, typecheck, test, headers

Runs tools with a fixed argv (no shell). May write tool caches; never writes
product state. Uses the interpreter it is run with: the host virtualenv
(.venv) or the VM's system python3 with the archive-pinned tools.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
CODE_DIRS = ["trier_bridge", "tests", "tools"]


def run(argv: list[str], label: str) -> int:
    print(f"== {label}: {' '.join(argv[1:]) if argv[0] == PY else ' '.join(argv)}")
    sys.stdout.flush()
    proc = subprocess.run(argv, cwd=ROOT)
    print(f"-- {label}: {'ok' if proc.returncode == 0 else f'exit {proc.returncode}'}")
    return proc.returncode


def cmd_format(args: argparse.Namespace) -> int:
    argv = [PY, "-m", "black"] + ([] if args.fix else ["--check", "--diff"]) + CODE_DIRS
    return run(argv, "black")


def cmd_lint(args: argparse.Namespace) -> int:
    return run([PY, "-m", "flake8"] + CODE_DIRS, "flake8")


def cmd_typecheck(args: argparse.Namespace) -> int:
    return run([PY, "-m", "mypy"], "mypy")


def cmd_test(args: argparse.Namespace) -> int:
    target = "tests/integration" if args.integration else "tests/unit"
    if args.integration and not (ROOT / "tests" / "integration").is_dir():
        print("no tests/integration yet")
        return 0
    return run(
        [PY, "-m", "pytest", target] + (["-m", "integration"] if args.integration else []), "pytest"
    )


def cmd_headers(args: argparse.Namespace) -> int:
    return run([PY, str(ROOT / "tools" / "tb.py"), "headers"], "headers")


def cmd_inventory(args: argparse.Namespace) -> int:
    print("== dependency inventory")
    control = ROOT / "debian" / "control"
    if control.is_file():
        text = control.read_text(encoding="utf-8")
        for field in ("Build-Depends", "Depends", "Recommends", "Suggests"):
            m = re.search(rf"^{field}:\s*(.+?)(?=^\S|\Z)", text, re.M | re.S)
            if m:
                items = [i.strip() for i in re.sub(r"\s+", " ", m.group(1)).split(",") if i.strip()]
                print(f"  {field} ({len(items)}):")
                for i in items:
                    print(f"    {i}")
    else:
        print("  debian/control: not present yet (ARC-11)")
    pins = ROOT / "docs" / "TOOLCHAIN.md"
    if pins.is_file():
        rows = [
            ln
            for ln in pins.read_text(encoding="utf-8").splitlines()
            if ln.startswith("| ") and "`" in ln and not ln.startswith("| Component")
        ]
        print(f"  docs/TOOLCHAIN.md pins: {len(rows)} rows")
    py_files = list((ROOT / "trier_bridge").rglob("*.py"))
    imports: set[str] = set()
    for p in py_files:
        for m in re.finditer(
            r"^(?:from|import)\s+([A-Za-z_][\w]*)", p.read_text(encoding="utf-8"), re.M
        ):
            imports.add(m.group(1))
    std = set(sys.stdlib_module_names)
    third = sorted(i for i in imports if i not in std and i != "trier_bridge")
    print(f"  runtime imports outside the standard library: {third or 'none'}")
    return 0


def cmd_size(args: argparse.Namespace) -> int:
    total = 0
    files = 0
    for p in (ROOT / "trier_bridge").rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            total += p.stat().st_size
            files += 1
    print(f"== size: trier_bridge/ {files} files, {total / 1024:.1f} KB")
    for deb in sorted(ROOT.parent.glob("trier-bridge_*.deb")) + sorted(ROOT.glob("dist/*.deb")):
        print(f"   package {deb.name}: {deb.stat().st_size / 1024:.1f} KB")
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    rc = 0
    for fn in (cmd_format, cmd_lint, cmd_typecheck, cmd_test, cmd_headers):
        rc = max(rc, fn(args))
    print(f"== all: {'clean' if rc == 0 else 'findings'}")
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="dev", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("format")
    p.add_argument("--fix", action="store_true")
    p.set_defaults(fn=cmd_format)
    sub.add_parser("lint").set_defaults(fn=cmd_lint)
    sub.add_parser("typecheck").set_defaults(fn=cmd_typecheck)
    p = sub.add_parser("test")
    p.add_argument("--integration", action="store_true")
    p.set_defaults(fn=cmd_test)
    sub.add_parser("headers").set_defaults(fn=cmd_headers)
    sub.add_parser("inventory").set_defaults(fn=cmd_inventory)
    sub.add_parser("size").set_defaults(fn=cmd_size)
    p = sub.add_parser("all")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--integration", action="store_true")
    p.set_defaults(fn=cmd_all)
    args = ap.parse_args(argv)
    os.chdir(ROOT)
    return int(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
