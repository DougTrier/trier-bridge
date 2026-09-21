# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T055/TB-T059/TB-T060/TB-T183/TB-T194/TB-T196/TB-T179/TB-T180: journal and preferences on real files."""
import json
import os
import time
from pathlib import Path

import pytest

from trier_bridge.core.state import OperationState, RecoveryState
from trier_bridge.state.journal import JournalCorrupt, JournalRecord, OperationJournal
from trier_bridge.state.preferences import DEFAULTS, Preferences


def _open(j: OperationJournal, oid: str = "op1") -> JournalRecord:
    return j.open(
        oid, "service.restart", "service", "cups.service", {"name": "cups.service"}, "Restart CUPS"
    )


def test_records_are_written_atomically_and_reloaded(tmp_path: Path) -> None:
    j = OperationJournal(tmp_path / "journal", app_version="0.1")
    rec = _open(j)
    assert (tmp_path / "journal" / "op1.json").is_file()
    assert [p.name for p in (tmp_path / "journal").iterdir()] == ["op1.json"]  # no temp left
    j.advance(rec, OperationState.PREVIEWED)
    j.advance(rec, OperationState.AUTHORIZED)
    j.advance(rec, OperationState.EXECUTING)
    again = j.load("op1")
    assert again is not None and again.operation_state is OperationState.EXECUTING
    assert [h["state"] for h in again.history] == ["draft", "previewed", "authorized", "executing"]
    assert again.app_version == "0.1" and again.target_identity == {"name": "cups.service"}


def test_restart_reconciliation_never_turns_pending_into_success(tmp_path: Path) -> None:
    j = OperationJournal(tmp_path / "j")
    executing = _open(j, "a")
    j.advance(executing, OperationState.PREVIEWED)
    j.advance(executing, OperationState.AUTHORIZED)
    j.advance(executing, OperationState.EXECUTING)
    done = _open(j, "b")
    j.advance(done, OperationState.PREVIEWED)
    j.advance(done, OperationState.DENIED, plain_result="Not permitted.")
    # "crash": a new journal instance on the same directory
    j2 = OperationJournal(tmp_path / "j")
    flagged = j2.reconcile_on_start()
    assert [r.operation_id for r in flagged] == ["a"]
    a = j2.load("a")
    assert a is not None
    assert a.operation_state is OperationState.OUTCOME_UNKNOWN
    assert a.recovery == RecoveryState.NEEDS_REVIEW.value and not a.resolved
    assert "not certain" in a.plain_result
    b = j2.load("b")
    assert b is not None and b.operation_state is OperationState.DENIED and b.resolved
    assert [r.operation_id for r in j2.unresolved()] == ["a"]
    # review resolves it; a second restart flags nothing
    j2.resolve(a, "checked Services: the service is running")
    assert j2.unresolved() == []
    assert OperationJournal(tmp_path / "j").reconcile_on_start() == []


def test_corrupt_record_is_quarantined_not_deleted_or_guessed(tmp_path: Path) -> None:
    j = OperationJournal(tmp_path / "j")
    _open(j, "good")
    (tmp_path / "j" / "bad.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(JournalCorrupt):
        j.load("bad")
    ids = [r.operation_id for r in j.all()]
    assert ids == ["good"]
    assert (tmp_path / "j" / "corrupt" / "bad.json").is_file()


def test_newer_schema_record_is_left_alone(tmp_path: Path) -> None:
    j = OperationJournal(tmp_path / "j")
    (tmp_path / "j" / "future.json").write_text(
        json.dumps({"schema": 99, "operation_id": "future"}), encoding="utf-8"
    )
    assert j.all() == []
    assert (tmp_path / "j" / "future.json").is_file()  # untouched, not quarantined


def test_prune_keeps_unresolved_and_recent(tmp_path: Path) -> None:
    j = OperationJournal(tmp_path / "j")
    for i in range(5):
        r = _open(j, f"done{i}")
        j.advance(r, OperationState.PREVIEWED)
        j.advance(r, OperationState.CANCELLED)
    pending = _open(j, "pending")
    j.advance(pending, OperationState.PREVIEWED)
    j.advance(pending, OperationState.EXECUTING)
    old = _open(j, "old")
    j.advance(old, OperationState.PREVIEWED)
    j.advance(old, OperationState.CANCELLED)
    old.updated_wall = time.time() - 400 * 86400
    j._write(old)
    removed = j.prune(retain=3, max_age_days=90)
    remaining = {r.operation_id for r in j.all()}
    assert "pending" in remaining  # unresolved is protected (TB-INV-196)
    assert "old" not in remaining
    assert removed >= 3 and len([r for r in j.all() if r.resolved]) <= 3


def test_bad_operation_ids_are_rejected(tmp_path: Path) -> None:
    j = OperationJournal(tmp_path / "j")
    for bad in ("", "../x", "a/b", ".hidden"):
        with pytest.raises(ValueError):
            j.open(bad, "k", "t", "l", {})


def test_preferences_defaults_durability_and_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "prefs.json"
    p = Preferences(path)
    assert p.get("mode") == "familiar" and p.as_dict() == DEFAULTS
    res = p.set("mode", "bridge")
    assert res.durable and json.loads(path.read_text())["mode"] == "bridge"
    # a newer build's key survives a round trip
    doc = json.loads(path.read_text())
    doc["future_key"] = {"x": 1}
    path.write_text(json.dumps(doc), encoding="utf-8")
    p2 = Preferences(path)
    p2.set("last_section", "apps")
    assert json.loads(path.read_text())["future_key"] == {"x": 1}
    with pytest.raises(KeyError):
        p2.get("nope")


def test_preferences_failed_write_is_reported_and_value_reverted(tmp_path: Path) -> None:
    path = tmp_path / "prefs.json"
    p = Preferences(path)
    p.set("mode", "bridge")
    # make the directory unwritable so the temp file cannot be created (skip on Windows)
    if os.name == "nt":
        pytest.skip("permission bits are not enforced the same way on Windows")
    os.chmod(tmp_path, 0o500)
    try:
        res = p.set("mode", "native")
    finally:
        os.chmod(tmp_path, 0o700)
    assert not res.durable and "not changed" in res.plain
    assert p.get("mode") == "bridge"
    assert json.loads(path.read_text())["mode"] == "bridge"


def test_preferences_newer_schema_is_read_only(tmp_path: Path) -> None:
    path = tmp_path / "prefs.json"
    path.write_text(json.dumps({"schema": 99, "mode": "native"}), encoding="utf-8")
    p = Preferences(path)
    assert p.read_only
    assert not p.set("mode", "bridge").durable
