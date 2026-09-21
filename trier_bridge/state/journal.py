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
"""Operation journal (IMP-05.02, IMP-05.03, IMP-05.05).

Every consequential operation gets one record file, written atomically at
each state change (TB-INV-055, TB-INV-183). On startup, reconciliation turns
any record left in a non-terminal state into OUTCOME_UNKNOWN with
RecoveryState.NEEDS_REVIEW: a crash never converts Pending into Success
(TB-INV-059) and nothing is replayed automatically (TB-INV-060, TB-INV-189).
Retention is bounded but never expires a record that is still unresolved
(TB-INV-196).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..config import StateSchemaTooNew, atomic_write_bytes, ensure_dir
from ..core.state import OperationState, RecoveryState

JOURNAL_SCHEMA = 1
DEFAULT_RETAIN = 200
DEFAULT_MAX_AGE_DAYS = 90


@dataclass
class JournalRecord:
    operation_id: str
    kind: str
    target_kind: str
    target_label: str
    target_identity: dict[str, str]
    state: str  # OperationState value
    recovery: str = RecoveryState.NO_RECOVERY_NEEDED.value
    preview: str = ""
    plain_result: str = ""
    technical: str = ""
    created_wall: float = field(default_factory=time.time)
    updated_wall: float = field(default_factory=time.time)
    app_version: str = ""
    history: list[dict[str, str | float]] = field(default_factory=list)

    @property
    def operation_state(self) -> OperationState:
        return OperationState(self.state)

    @property
    def resolved(self) -> bool:
        """Terminal, and not awaiting human review."""
        return (
            self.operation_state.is_terminal and self.recovery != RecoveryState.NEEDS_REVIEW.value
        )

    def to_json(self) -> bytes:
        return json.dumps(
            {"schema": JOURNAL_SCHEMA, **asdict(self)}, indent=2, sort_keys=True
        ).encode("utf-8")

    @classmethod
    def from_json(cls, raw: bytes) -> "JournalRecord":
        doc = json.loads(raw.decode("utf-8"))
        if not isinstance(doc, dict):
            raise ValueError("journal record is not an object")
        schema = int(doc.pop("schema", 0))
        if schema > JOURNAL_SCHEMA:
            raise StateSchemaTooNew(f"journal schema {schema} is newer than {JOURNAL_SCHEMA}")
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in doc.items() if k in known})


class JournalCorrupt(ValueError):
    """A record could not be parsed. It is kept aside, never deleted or guessed (TB-INV-194)."""


def _valid_json(raw: bytes) -> bool:
    try:
        json.loads(raw.decode("utf-8"))
        return True
    except (ValueError, UnicodeDecodeError):
        return False


class OperationJournal:
    def __init__(self, directory: Path, app_version: str = "") -> None:
        self.dir = ensure_dir(directory)
        self.quarantine = self.dir / "corrupt"
        self.app_version = app_version

    def _path(self, operation_id: str) -> Path:
        if (
            not operation_id
            or "/" in operation_id
            or "\\" in operation_id
            or operation_id.startswith(".")
        ):
            raise ValueError("bad operation id")
        return self.dir / f"{operation_id}.json"

    # ---- writes (each one atomic) -------------------------------------------
    def open(
        self,
        operation_id: str,
        kind: str,
        target_kind: str,
        target_label: str,
        target_identity: dict[str, str],
        preview: str = "",
    ) -> JournalRecord:
        rec = JournalRecord(
            operation_id=operation_id,
            kind=kind,
            target_kind=target_kind,
            target_label=target_label,
            target_identity=dict(target_identity),
            state=OperationState.DRAFT.value,
            preview=preview,
            app_version=self.app_version,
        )
        rec.history.append({"state": rec.state, "at": rec.created_wall})
        self._write(rec)
        return rec

    def advance(
        self,
        rec: JournalRecord,
        state: OperationState,
        plain_result: str = "",
        technical: str = "",
        recovery: RecoveryState | None = None,
    ) -> JournalRecord:
        rec.state = state.value
        rec.updated_wall = time.time()
        if plain_result:
            rec.plain_result = plain_result
        if technical:
            rec.technical = technical
        if recovery is not None:
            rec.recovery = recovery.value
        rec.history.append({"state": rec.state, "at": rec.updated_wall})
        self._write(rec)
        return rec

    def _write(self, rec: JournalRecord) -> None:
        atomic_write_bytes(self._path(rec.operation_id), rec.to_json(), validate=_valid_json)

    # ---- reads -----------------------------------------------------------------
    def load(self, operation_id: str) -> JournalRecord | None:
        p = self._path(operation_id)
        if not p.is_file():
            return None
        try:
            return JournalRecord.from_json(p.read_bytes())
        except (ValueError, KeyError, TypeError) as exc:
            raise JournalCorrupt(f"{p.name}: {exc}") from exc

    def all(self) -> list[JournalRecord]:
        out: list[JournalRecord] = []
        for p in sorted(self.dir.glob("*.json")):
            try:
                out.append(JournalRecord.from_json(p.read_bytes()))
            except StateSchemaTooNew:
                continue  # newer build wrote it; leave it alone (TB-INV-029)
            except (ValueError, KeyError, TypeError):
                self._quarantine(p)
        out.sort(key=lambda r: r.created_wall, reverse=True)
        return out

    def unresolved(self) -> list[JournalRecord]:
        return [r for r in self.all() if not r.resolved]

    def _quarantine(self, p: Path) -> None:
        ensure_dir(self.quarantine)
        try:
            os.replace(p, self.quarantine / p.name)
        except OSError:
            pass

    # ---- reconciliation (IMP-05.03) ---------------------------------------------
    def reconcile_on_start(self) -> list[JournalRecord]:
        """Mark every non-terminal record OUTCOME_UNKNOWN + NEEDS_REVIEW. Returns them.

        The operation may or may not have taken effect; only a fresh look at the
        real system can say, so the record asks for review instead of guessing.
        """
        flagged: list[JournalRecord] = []
        for rec in self.all():
            if rec.operation_state.is_terminal:
                continue
            rec.state = OperationState.OUTCOME_UNKNOWN.value
            rec.recovery = RecoveryState.NEEDS_REVIEW.value
            rec.updated_wall = time.time()
            rec.plain_result = (
                "Trier Bridge was interrupted while this was in progress. "
                "It is not certain whether the change was made; check the current state before "
                "trying again."
            )
            rec.history.append({"state": rec.state, "at": rec.updated_wall, "reason": "restart"})
            self._write(rec)
            flagged.append(rec)
        return flagged

    def resolve(self, rec: JournalRecord, note: str = "") -> JournalRecord:
        """A human (or a verified re-observation) reviewed an unknown outcome."""
        rec.recovery = RecoveryState.NO_RECOVERY_NEEDED.value
        rec.updated_wall = time.time()
        if note:
            rec.technical = (rec.technical + "\n" if rec.technical else "") + note
        rec.history.append({"state": rec.state, "at": rec.updated_wall, "reason": "reviewed"})
        self._write(rec)
        return rec

    # ---- retention (IMP-05.05) ---------------------------------------------------
    def prune(self, retain: int = DEFAULT_RETAIN, max_age_days: int = DEFAULT_MAX_AGE_DAYS) -> int:
        """Delete old resolved records beyond ``retain``; unresolved records are never pruned."""
        cutoff = time.time() - max_age_days * 86400
        records = self.all()
        resolved = [r for r in records if r.resolved]
        removed = 0
        for index, rec in enumerate(resolved):
            if index >= retain or rec.updated_wall < cutoff:
                try:
                    self._path(rec.operation_id).unlink()
                    removed += 1
                except OSError:
                    pass
        return removed
