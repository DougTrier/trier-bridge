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
"""Which package system owns a desktop entry, decided from its real path. Pure."""
from __future__ import annotations

from enum import Enum, unique
from pathlib import PurePosixPath


@unique
class Provenance(Enum):
    SYSTEM = "system"  # distribution package (apt/dpkg on the first target)
    SNAP = "snap"
    FLATPAK = "flatpak"
    USER = "user"  # per-user entry under ~/.local/share/applications
    OTHER = "other"

    @property
    def label(self) -> str:
        return {
            Provenance.SYSTEM: "System package",
            Provenance.SNAP: "Snap",
            Provenance.FLATPAK: "Flatpak",
            Provenance.USER: "Installed for this user",
            Provenance.OTHER: "Other",
        }[self]


def provenance_for(path: PurePosixPath | str, home: str) -> Provenance:
    p = PurePosixPath(str(path))
    parts = p.parts
    s = str(p)
    if "/snapd/desktop/applications" in s or s.startswith("/snap/"):
        return Provenance.SNAP
    if "/flatpak/exports/" in s:
        return Provenance.FLATPAK
    if home and s.startswith(home.rstrip("/") + "/"):
        return Provenance.USER
    if len(parts) > 2 and parts[1] == "usr" and "applications" in parts:
        return Provenance.SYSTEM
    return Provenance.OTHER
