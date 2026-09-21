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
  results     run pytest and normalize the outcome to reports/local/test-results-<suite>.json
              (add --integration; pytest arguments after --)
  evidence    collect the quality evidence (complexity, security, suppressions, size, latest
              normalized test results) to reports/local/quality-evidence.json
  map         regenerate docs/FEATURE-INVARIANT-MAP.md from docs/VALIDATION.md (ARC-13)
  limitations regenerate docs/KNOWN-LIMITATIONS.md from docs/VALIDATION.md (IMP-08.09)
  all         format, lint, typecheck, security, complexity, test, headers

Runs tools with a fixed argv (no shell). May write tool caches; never writes
product state. Uses the interpreter it is run with: the host virtualenv
(.venv) or the VM's system python3 with the archive-pinned tools.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
CODE_DIRS = ["trier_bridge", "tests", "tools"]
REPORTS = ROOT / "reports" / "local"
VALIDATION = ROOT / "docs" / "VALIDATION.md"
ENTRY_HEADING = re.compile(r"^### (?P<id>[A-Z0-9]+-[\w./-]+) \u2014 (?P<title>.+?)\s*$")
FIELD_LINE = re.compile(r"^- \*\*(?P<field>[^*]+):\*\* (?P<value>.*)$")
RULE_TOKEN = re.compile(r"TB-(?:INV|SEC|IA|A11Y)-\d{2,3}(?:/\d{2,3})*")


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


def _module_present(name: str) -> bool:
    probe = subprocess.run([PY, "-c", f"import {name}"], cwd=ROOT, capture_output=True)
    return probe.returncode == 0


def _complexity_lines() -> list[str] | None:
    """Outlier lines from flake8, or None when the analyzer is not installed."""
    if not _module_present("cognitive_complexity"):
        return None
    argv = [
        PY,
        "-m",
        "flake8",
        "--isolated",  # the lint config ignores CCR001; this step is the one that reports it
        "--select=C901,CCR001",
        "--max-complexity=10",
        "--max-cognitive-complexity=15",
        "trier_bridge",
    ]
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def _complexity_counts(lines: list[str]) -> tuple[int, int]:
    cyclo = sum(1 for ln in lines if " C901 " in ln)
    cog = sum(1 for ln in lines if " CCR001 " in ln)
    return cyclo, cog


def cmd_complexity(args: argparse.Namespace) -> int:
    """Cyclomatic (mccabe) and cognitive (flake8-cognitive-complexity) outliers, reported.
    Reporting only: every outlier is dispositioned in CODE-QUALITY-REPORT.md."""
    lines = _complexity_lines()
    if lines is None:
        print("== complexity: flake8-cognitive-complexity not installed (docs/TOOLCHAIN.md)")
        return 1
    print("== complexity: flake8 --select=C901,CCR001 trier_bridge")
    cyclo, cog = _complexity_counts(lines)
    print(f"-- complexity: {cyclo} above cyclomatic 10, {cog} above cognitive 15 (reported)")
    return 0


def cmd_security(args: argparse.Namespace) -> int:
    """bandit over the product; any finding fails (dispositions live in the report)."""
    if not _module_present("bandit"):
        print("== security: bandit not installed (docs/TOOLCHAIN.md)")
        return 1
    return run([PY, "-m", "bandit", "-q", "-r", "trier_bridge"], "bandit")


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


def _revision() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def _stamp() -> str:
    return dt.datetime.now().astimezone().strftime("%Y-%m-%d %I:%M %p %Z")


def _case_outcome(case: ET.Element) -> tuple[str, str]:
    for tag in ("failure", "error", "skipped"):
        node = case.find(tag)
        if node is not None:
            return tag, (node.get("message") or "").strip()[:200]
    return "passed", ""


def _normalize_junit(xml_path: Path, suite: str, rc: int) -> dict[str, object]:
    """One shape for every environment: counts plus the names that did not pass."""
    root = ET.parse(xml_path).getroot()
    outcomes = [(c, *_case_outcome(c)) for c in root.iter("testcase")]
    kinds = ("passed", "failure", "error", "skipped")
    counts = {k: sum(1 for _c, o, _m in outcomes if o == k) for k in kinds}
    return {
        "suite": suite,
        "candidate": _revision(),
        "timestamp": _stamp(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "exit": rc,
        "total": len(outcomes),
        "passed": counts["passed"],
        "failed": counts["failure"],
        "errors": counts["error"],
        "skipped": counts["skipped"],
        "duration_s": round(sum(float(c.get("time") or 0) for c, _o, _m in outcomes), 2),
        "not_passed": [
            {"test": f"{c.get('classname')}::{c.get('name')}", "outcome": o, "message": m}
            for c, o, m in outcomes
            if o != "passed"
        ],
    }


def cmd_results(args: argparse.Namespace) -> int:
    suite = "integration" if args.integration else "unit"
    REPORTS.mkdir(parents=True, exist_ok=True)
    xml_path = REPORTS / f"test-results-{suite}.xml"
    argv = [PY, "-m", "pytest", f"tests/{suite}", "--junitxml", str(xml_path)]
    argv += ["-m", "integration"] if args.integration else []
    argv += list(args.pytest_args)
    print(f"== results: {' '.join(argv[1:])}")
    sys.stdout.flush()
    proc = subprocess.run(argv, cwd=ROOT)
    if not xml_path.is_file():
        print("-- results: pytest wrote no report")
        return 1
    summary = _normalize_junit(xml_path, suite, proc.returncode)
    out = REPORTS / f"test-results-{suite}.json"
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        f"-- results: {summary['passed']} passed, {summary['failed']} failed, "
        f"{summary['errors']} errors, {summary['skipped']} skipped -> {out.relative_to(ROOT)}"
    )
    return 0 if summary["failed"] == 0 and summary["errors"] == 0 else 1


def _suppressions() -> dict[str, int]:
    markers = {"noqa": "# noqa", "type-ignore": "type: ignore", "nosec": "# nosec"}
    counts = dict.fromkeys(markers, 0)
    for path in (ROOT / "trier_bridge").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for key, marker in markers.items():
            counts[key] += text.count(marker)
    return counts


def _bandit_findings() -> int | None:
    if not _module_present("bandit"):
        return None
    proc = subprocess.run(
        [PY, "-m", "bandit", "-q", "-r", "trier_bridge", "-f", "json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    try:
        return len(json.loads(proc.stdout)["results"])
    except (ValueError, KeyError):
        return None


def _source_size() -> dict[str, int]:
    files = [p for p in (ROOT / "trier_bridge").rglob("*.py") if "__pycache__" not in p.parts]
    lines = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in files)
    return {"files": len(files), "lines": lines}


def cmd_evidence(args: argparse.Namespace) -> int:
    """The measured inputs of CODE-QUALITY-REPORT.md, in one file, from real tool runs."""
    outliers = _complexity_lines()
    cyclo, cog = _complexity_counts(outliers or [])
    tests = {}
    for suite in ("unit", "integration"):
        path = REPORTS / f"test-results-{suite}.json"
        if path.is_file():
            tests[suite] = json.loads(path.read_text(encoding="utf-8"))
    evidence: dict[str, object] = {
        "candidate": _revision(),
        "timestamp": _stamp(),
        "platform": platform.platform(),
        "complexity": {
            "analyzer_present": outliers is not None,
            "cyclomatic_over_10": cyclo,
            "cognitive_over_15": cog,
            "outliers": outliers or [],
        },
        "bandit_findings": _bandit_findings(),
        "suppressions": _suppressions(),
        "source": _source_size(),
        "tests": tests,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "quality-evidence.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(
        f"== evidence: {cyclo} cyclomatic / {cog} cognitive outliers, bandit "
        f"{evidence['bandit_findings']}, suppressions {evidence['suppressions']}, "
        f"tests {sorted(tests)} -> {out.relative_to(ROOT)}"
    )
    return 0


def _validation_entries() -> list[dict[str, str]]:
    """Every evidence entry of docs/VALIDATION.md as {id, title, <field>: value}."""
    entries: list[dict[str, str]] = []
    in_entries = False
    for line in VALIDATION.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Entries"):
            in_entries = True
            continue
        if not in_entries:
            continue
        heading = ENTRY_HEADING.match(line)
        if heading:
            entries.append({"id": heading["id"], "title": heading["title"]})
            continue
        field = FIELD_LINE.match(line)
        if field and entries:
            entries[-1][field["field"]] = field["value"]
    return entries


def _rules_cited(text: str) -> list[str]:
    cited: set[str] = set()
    for token in RULE_TOKEN.findall(text):
        head, *rest = token.split("/")
        prefix = head.rsplit("-", 1)[0]
        cited.add(head)
        cited.update(f"{prefix}-{n}" for n in rest)
    return sorted(cited)


def _write_generated(path: Path, text: str, label: str) -> int:
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"== {label}: {path.relative_to(ROOT)} written")
    return 0


def cmd_map(args: argparse.Namespace) -> int:
    rows = []
    distinct: set[str] = set()
    for e in _validation_entries():
        cited = _rules_cited(e.get("Invariant impact", ""))
        distinct.update(cited)
        rows.append(f"| {e['id']} | {e['title']} | {', '.join(cited) or 'none cited'} |")
    text = (
        "# Feature to Invariant Map\n\n"
        '**Generated from `VALIDATION.md` (the "Invariant impact" line of every evidence '
        f"entry) by `tools/dev.py map`, {_stamp()}.** Regenerate whenever an entry is added; "
        "this file is derived, not edited by hand (ARC-13).\n\n"
        "| Evidence entry | Feature | Invariants and security rules cited |\n|---|---|---|\n"
        + "\n".join(rows)
        + f"\n\n{len(distinct)} distinct invariant and security IDs are cited by "
        f"{len(rows)} entries.\n"
    )
    return _write_generated(ROOT / "docs" / "FEATURE-INVARIANT-MAP.md", text, "map")


def cmd_limitations(args: argparse.Namespace) -> int:
    rows = [
        f"| {e['id']} | {e['title']} | {e.get('Evidence state', '')} | "
        f"{e.get('Failures/limitations', '')} |"
        for e in _validation_entries()
    ]
    text = (
        "# Known Limitations\n\n"
        '**Generated from `VALIDATION.md` (the "Failures/limitations" and "Evidence state" '
        f"lines of every evidence entry) by `tools/dev.py limitations`, {_stamp()}.** This is "
        "the known-limitations report of IMP-08.09; the release CQS is in "
        "`CODE-QUALITY-REPORT.md`. Test gaps beyond these lines are listed in "
        "`TEST-STRATEGY.md` section 7 and the open accessibility criteria in "
        "`ACCESSIBILITY.md`. Derived, not edited by hand.\n\n"
        "| Evidence entry | Feature | Evidence state | Failures and limitations |\n"
        "|---|---|---|---|\n" + "\n".join(rows) + "\n"
    )
    return _write_generated(ROOT / "docs" / "KNOWN-LIMITATIONS.md", text, "limitations")


def cmd_all(args: argparse.Namespace) -> int:
    rc = 0
    for fn in (
        cmd_format,
        cmd_lint,
        cmd_typecheck,
        cmd_security,
        cmd_complexity,
        cmd_test,
        cmd_headers,
    ):
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
    sub.add_parser("security").set_defaults(fn=cmd_security)
    sub.add_parser("complexity").set_defaults(fn=cmd_complexity)
    sub.add_parser("headers").set_defaults(fn=cmd_headers)
    sub.add_parser("inventory").set_defaults(fn=cmd_inventory)
    sub.add_parser("size").set_defaults(fn=cmd_size)
    p = sub.add_parser("results")
    p.add_argument("--integration", action="store_true")
    p.add_argument("pytest_args", nargs="*")
    p.set_defaults(fn=cmd_results)
    sub.add_parser("evidence").set_defaults(fn=cmd_evidence)
    sub.add_parser("map").set_defaults(fn=cmd_map)
    sub.add_parser("limitations").set_defaults(fn=cmd_limitations)
    p = sub.add_parser("all")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--integration", action="store_true")
    p.set_defaults(fn=cmd_all)
    args = ap.parse_args(argv)
    os.chdir(ROOT)
    return int(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
