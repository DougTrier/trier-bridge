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
"""Pure parsers for machine facts. No I/O: callers pass text they read.

INVARIANT: distribution identity comes from os-release, never from branding,
theme, or hostname (TB-INV-016). Ambiguity stays ambiguous.
"""
from __future__ import annotations

import re

_OS_RELEASE_LINE = re.compile(
    r'^\s*([A-Z][A-Z0-9_]*)\s*=\s*(?:"((?:[^"\\]|\\.)*)"|\'([^\']*)\'|([^\s#]*))\s*$'
)


def parse_os_release(text: str) -> dict[str, str]:
    """Parse os-release(5) text into a dict. Unknown or malformed lines are skipped."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _OS_RELEASE_LINE.match(line)
        if not m:
            continue
        key = m.group(1)
        value = next((g for g in m.groups()[1:] if g is not None), "")
        out[key] = value.replace("\\$", "$").replace('\\"', '"').replace("\\\\", "\\")
    return out


def distro_from_os_release(fields: dict[str, str]) -> tuple[str, str, str, tuple[str, ...]]:
    """Return (id, version_id, pretty_name, id_like). Empty strings mean unknown."""
    distro_id = fields.get("ID", "").strip().lower()
    version = fields.get("VERSION_ID", "").strip()
    pretty = fields.get("PRETTY_NAME", "").strip() or fields.get("NAME", "").strip()
    like = tuple(x for x in fields.get("ID_LIKE", "").lower().split() if x)
    return distro_id, version, pretty, like


def parse_proc_stat_starttime(stat_text: str) -> int | None:
    """Field 22 of /proc/PID/stat (start time in clock ticks); robust to spaces in comm."""
    try:
        after = stat_text.rsplit(")", 1)[1].split()
        return int(after[19])
    except (IndexError, ValueError):
        return None


def parse_group_file(text: str, user: str) -> tuple[str, ...]:
    """Groups that list ``user`` as a member in /etc/group text (supplementary groups only)."""
    groups: list[str] = []
    for line in text.splitlines():
        parts = line.split(":")
        if len(parts) < 4:
            continue
        members = [m for m in parts[3].strip().split(",") if m]
        if user in members:
            groups.append(parts[0])
    return tuple(groups)
