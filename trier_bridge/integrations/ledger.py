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
"""Integration ledger: the exact record that makes every integration reversible.

The file is shared between the Bridge window and the tray process (its menu can
turn the tray integration off), so the ledger re-reads the file before every
query and every change instead of trusting an in-memory copy.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..config import StateSchemaTooNew, load_json, save_json


@dataclass
class AppliedIntegration:
    integration_id: str
    applied_wall: float
    files_written: list[str] = field(default_factory=list)  # absolute paths, all under $HOME
    settings_written: list[dict[str, str]] = field(
        default_factory=list
    )  # gsettings keys + previous
    app_version: str = ""


class IntegrationLedger:
    def __init__(self, path: Path, app_version: str = "") -> None:
        self.path = path
        self.app_version = app_version
        self.read_only = False
        self.setup_completed = False
        self._applied: dict[str, AppliedIntegration] = {}
        self._load()

    def reload(self) -> None:
        """Re-read the file; the tray process may have changed it."""
        self._applied = {}
        self.setup_completed = False
        self.read_only = False
        self._load()

    def _load(self) -> None:
        try:
            doc = load_json(self.path)
        except StateSchemaTooNew:
            self.read_only = True
            return
        except (ValueError, OSError):
            return
        if not doc:
            return
        self.setup_completed = bool(doc.get("setup_completed", False))
        for raw in doc.get("applied", []):
            try:
                rec = AppliedIntegration(
                    **{k: v for k, v in raw.items() if k in AppliedIntegration.__dataclass_fields__}
                )
            except TypeError:
                continue
            self._applied[rec.integration_id] = rec

    @property
    def exists(self) -> bool:
        return self.path.is_file()

    def is_applied(self, integration_id: str) -> bool:
        self.reload()
        return integration_id in self._applied

    def get(self, integration_id: str) -> AppliedIntegration | None:
        self.reload()
        return self._applied.get(integration_id)

    def applied_ids(self) -> list[str]:
        self.reload()
        return sorted(self._applied)

    def record(self, rec: AppliedIntegration) -> None:
        self.reload()
        rec.app_version = rec.app_version or self.app_version
        self._applied[rec.integration_id] = rec
        self._save()

    def forget(self, integration_id: str) -> None:
        self.reload()
        self._applied.pop(integration_id, None)
        self._save()

    def mark_setup_completed(self) -> None:
        self.reload()
        self.setup_completed = True
        self._save()

    def _save(self) -> None:
        payload: dict[str, Any] = {
            "setup_completed": self.setup_completed,
            "updated_wall": time.time(),
            "applied": [asdict(r) for r in self._applied.values()],
        }
        save_json(self.path, payload)
