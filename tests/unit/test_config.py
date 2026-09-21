# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T029/TB-T181/TB-T182: XDG paths and atomic writes against a real temporary filesystem."""
import json
from pathlib import Path

import pytest

from trier_bridge.config import (
    StateSchemaTooNew,
    StateWriteError,
    atomic_write_bytes,
    atomic_write_text,
    load_json,
    resolve_paths,
    save_json,
)


def test_paths_follow_xdg_overrides(tmp_path: Path) -> None:
    env = {
        "HOME": str(tmp_path / "home"),
        "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
        "XDG_STATE_HOME": "",
    }
    p = resolve_paths(env)
    assert p.config == tmp_path / "cfg" / "trier-bridge"
    assert p.state == tmp_path / "home" / ".local" / "state" / "trier-bridge"
    assert p.preferences_file.name == "preferences.json"


def test_atomic_write_replaces_and_leaves_no_temp(tmp_path: Path) -> None:
    target = tmp_path / "prefs.json"
    atomic_write_text(target, "one")
    atomic_write_text(target, "two")
    assert target.read_text(encoding="utf-8") == "two"
    assert [p.name for p in tmp_path.iterdir()] == ["prefs.json"]


def test_failed_validation_keeps_original(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    atomic_write_text(target, "good")
    with pytest.raises(StateWriteError):
        atomic_write_bytes(target, b"bad", validate=lambda raw: False)
    assert target.read_text(encoding="utf-8") == "good"
    assert [p.name for p in tmp_path.iterdir()] == ["state.json"]


def test_save_and_load_json_roundtrip(tmp_path: Path) -> None:
    f = tmp_path / "doc.json"
    save_json(f, {"mode": "familiar", "pins": ["tb.taskmanager"]})
    doc = load_json(f)
    assert doc is not None and doc["schema"] == 1 and doc["mode"] == "familiar"
    assert load_json(tmp_path / "absent.json") is None


def test_newer_schema_is_refused_not_guessed(tmp_path: Path) -> None:
    f = tmp_path / "doc.json"
    f.write_text(json.dumps({"schema": 99, "mode": "x"}), encoding="utf-8")
    with pytest.raises(StateSchemaTooNew):
        load_json(f)


def test_corrupt_file_raises_rather_than_returning_empty(tmp_path: Path) -> None:
    f = tmp_path / "doc.json"
    f.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_json(f)
