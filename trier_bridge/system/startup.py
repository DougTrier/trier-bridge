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
"""Startup Apps data, read-only: XDG autostart entries and user systemd units.

Linux has several startup mechanisms; each entry says which one it is
(docs catalog note for tb.startup). Enabling and disabling arrive with the
mutation foundation. Pure file parsing; no GTK, no D-Bus.
"""
from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StartupEntry:
    name: str
    mechanism: str  # "Autostart (this user)", "Autostart (all users)", "User service"
    enabled: bool | None  # None = Unknown
    source_path: str
    command: str
    comment: str = ""
    overridden_by_user: bool = False  # a system entry masked/changed by a user copy


def parse_autostart(path: Path) -> StartupEntry | None:
    cp = configparser.RawConfigParser(strict=False, interpolation=None)
    try:
        cp.read(path, encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError):
        return None
    if not cp.has_section("Desktop Entry"):
        return None
    sec = cp["Desktop Entry"]
    hidden = sec.get("Hidden", "false").strip().lower() == "true"
    gnome_enabled = sec.get("X-GNOME-Autostart-enabled", "true").strip().lower() != "false"
    return StartupEntry(
        name=sec.get("Name", path.stem).strip(),
        mechanism="",
        enabled=not hidden and gnome_enabled,
        source_path=str(path),
        command=sec.get("Exec", "").strip(),
        comment=sec.get("Comment", "").strip(),
    )


def read_startup(
    home: Path, xdg_config_dirs: tuple[Path, ...] = (Path("/etc/xdg"),)
) -> list[StartupEntry]:
    entries: list[StartupEntry] = []
    user_dir = home / ".config" / "autostart"
    user_names: set[str] = set()
    if user_dir.is_dir():
        for p in sorted(user_dir.glob("*.desktop")):
            e = parse_autostart(p)
            if e is not None:
                user_names.add(p.name)
                entries.append(
                    StartupEntry(
                        e.name,
                        "Autostart (this user)",
                        e.enabled,
                        e.source_path,
                        e.command,
                        e.comment,
                    )
                )
    for cfg in xdg_config_dirs:
        sys_dir = cfg / "autostart"
        if not sys_dir.is_dir():
            continue
        for p in sorted(sys_dir.glob("*.desktop")):
            e = parse_autostart(p)
            if e is None:
                continue
            entries.append(
                StartupEntry(
                    e.name,
                    "Autostart (all users)",
                    e.enabled,
                    e.source_path,
                    e.command,
                    e.comment,
                    overridden_by_user=p.name in user_names,
                )
            )
    wants = home / ".config" / "systemd" / "user" / "default.target.wants"
    if wants.is_dir():
        for p in sorted(wants.iterdir()):
            entries.append(
                StartupEntry(
                    name=p.name,
                    mechanism="User service",
                    enabled=True,
                    source_path=str(p),
                    command="systemd user unit",
                )
            )
    return entries
