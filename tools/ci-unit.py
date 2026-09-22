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
"""CI-01: explicit non-destructive unit subset; see docs/CI.md for VM-only coverage."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Positive selection: new test modules do not silently gain cloud-runner authority.
MODULES = (
    "bridge_commands",
    "capability_model",
    "catalog",
    "cmdlets",
    "config",
    "driveletters",
    "facts",
    "filelisting",
    "grammar",
    "hold_terminal",
    "identity",
    "journal",
    "logging",
    "operations",
    "provenance",
    "resources",
    "screenshot_route",
    "state",
    "theme",
)
CASES = (
    "diskio::test_is_whole_disk_matches_the_real_device_naming_rules",
    "diskio::test_parse_diskstats_keeps_only_whole_disks",
    "diskio::test_whole_disk_name_strips_the_right_partition_suffix",
    "netio::test_parse_net_dev_excludes_loopback",
    "processes::test_stat_parses_comm_with_spaces_and_parens",
    "processes::test_status_uid_and_meminfo_and_cpu_total",
    "processes::test_classification_protects_system_processes",
    "processes::test_classification_protects_session_critical_processes",
    "processes::test_plan_terminate_refuses_session_critical_with_an_accurate_reason",
    "integrations::test_catalog_groups_and_defaults",
    "integrations::test_ledger_survives_reload_and_marks_setup",
    "help_and_printers::test_help_is_generated_from_the_build",
    "state_journal::test_records_are_written_atomically_and_reloaded",
    "state_journal::test_preferences_defaults_durability_and_unknown_keys",
    "state_journal::test_bad_operation_ids_are_rejected",
)


def main() -> int:
    targets = [f"tests/unit/test_{name}.py" for name in MODULES]
    for case in CASES:
        module, test = case.split("::")
        targets.append(f"tests/unit/test_{module}.py::{test}")
    report = ROOT / "reports" / "local" / "ci-unit.xml"
    report.parent.mkdir(parents=True, exist_ok=True)
    print("CI unit subset only; desktop, privilege, mutation and fault tests remain VM-only.")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *targets,
            "--deselect=tests/unit/test_filelisting.py::test_permission_denied_reports_plainly",
            "-ra",
            f"--junitxml={report}",
        ],
        cwd=ROOT,
    ).returncode


if __name__ == "__main__":
    sys.exit(main())
