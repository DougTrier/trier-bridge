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
"""Per-user preferences with truthful durability (IMP-05.01).

A change is acknowledged to the user only after it is durable on disk
(TB-INV-180); a failed write is reported, never swallowed. Every key has a
declared default and the file is versioned (TB-INV-179). Unknown keys from a
newer build are preserved, not dropped.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, unique
from pathlib import Path
from typing import Any

from ..config import StateSchemaTooNew, StateWriteError, load_json, save_json

log = logging.getLogger("trier_bridge.state.preferences")


@unique
class Mode(Enum):
    FAMILIAR = "familiar"
    BRIDGE = "bridge"
    NATIVE = "native"


DEFAULTS: dict[str, Any] = {
    "mode": Mode.FAMILIAR.value,  # terminology depth only; never authorization (TB-INV-064)
    "pinned": [],  # concept ids pinned on Home
    "last_section": "home",
    "task_manager_interval_ms": 2000,
    "show_command_lines": False,  # TB-INV-133: off by default
    "sidebar_hue": 213,  # cosmetic only (TB-INV-253); clamped on read, see ui/theme.py
    "ui_zoom_percent": 100,  # cosmetic only (TB-INV-253/254); clamped on read
}


@dataclass(frozen=True)
class SetResult:
    key: str
    durable: bool
    plain: str


class Preferences:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._values: dict[str, Any] = dict(DEFAULTS)
        self._unknown: dict[str, Any] = {}
        self.read_only = False
        self.load_error = ""
        self._load()

    def _load(self) -> None:
        try:
            doc = load_json(self.path)
        except StateSchemaTooNew as exc:
            self.read_only = True
            self.load_error = str(exc)
            log.warning("preferences opened read-only: %s", exc)
            return
        except (ValueError, OSError) as exc:
            self.load_error = f"preferences file unreadable, defaults in use: {exc}"
            log.warning(self.load_error)
            return
        if not doc:
            return
        for k, v in doc.items():
            if k == "schema":
                continue
            if k in DEFAULTS:
                self._values[k] = v
            else:
                self._unknown[k] = v  # preserved for a newer build (TB-INV-179)

    def get(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"unknown preference {key}")
        return self._values[key]

    def set(self, key: str, value: Any) -> SetResult:
        """Desired -> Pending -> Durable. Returns durable=False with a plain reason on failure."""
        if key not in DEFAULTS:
            raise KeyError(f"unknown preference {key}")
        if self.read_only:
            return SetResult(key, False, "Settings are read-only: a newer Trier Bridge wrote them.")
        previous = self._values[key]
        self._values[key] = value
        try:
            save_json(self.path, {**self._unknown, **self._values})
        except StateWriteError as exc:
            self._values[key] = previous  # Desired is not Durable; do not pretend (TB-INV-180)
            return SetResult(
                key, False, f"The setting could not be saved and was not changed. {exc}"
            )
        return SetResult(key, True, "Saved.")

    def as_dict(self) -> dict[str, Any]:
        return dict(self._values)
