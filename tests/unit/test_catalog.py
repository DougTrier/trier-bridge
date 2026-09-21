# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T003/TB-T065/TB-T105: the concept catalog loads, validates, maps, and searches."""
import json
from pathlib import Path

import pytest

from trier_bridge.catalog.model import Catalog, CatalogError, Equivalence, RouteKind

DATA = Path(__file__).resolve().parents[2] / "data" / "catalog" / "concepts.json"


def test_shipped_catalog_loads_and_every_nonexact_has_a_note() -> None:
    cat = Catalog.load(DATA)
    assert len(cat.concepts) >= 30
    for c in cat.concepts:
        assert c.windows_terms and c.title and c.linux and c.group
        if c.equivalence is not Equivalence.EXACT:
            assert c.note, c.id
        assert "Linux" in c.mapping_note() or c.equivalence is Equivalence.EXACT


def test_windows_vocabulary_routes_correctly() -> None:
    cat = Catalog.load(DATA)
    assert cat.search("Task Manager")[0].concept.id == "tb.taskmanager"
    assert cat.search("add or remove programs")[0].concept.route.target == "apps"
    assert cat.search("ncpa.cpl")[0].concept.id == "tb.network"
    assert cat.search("regedit")[0].concept.equivalence is Equivalence.NONE
    assert cat.search("My Documents")[0].concept.route.kind is RouteKind.FOLDER


def test_search_is_case_and_accent_insensitive_and_partial() -> None:
    cat = Catalog.load(DATA)
    assert cat.search("TASK")[0].concept.id == "tb.taskmanager"
    assert any(m.concept.id == "tb.taskmanager" for m in cat.search("task man"))
    assert cat.search("printérs")[0].concept.id == "tb.printers"
    assert cat.search("") == []
    assert cat.search("zzzz-nothing") == []


def test_no_equivalent_concepts_cannot_open() -> None:
    cat = Catalog.load(DATA)
    reg = cat.get("tb.registry")
    assert reg is not None and not reg.can_open  # educational only (TB-INV-105)
    assert "No direct equivalent" in reg.mapping_note()
    shot = cat.get("tb.screenshot")
    # Print Screen became an action the window performs through the portal (IMP-03.08)
    assert shot is not None and shot.can_open and shot.route.kind is RouteKind.ACTION


def test_malformed_catalog_is_a_hard_error(tmp_path: Path) -> None:
    bad = tmp_path / "c.json"
    bad.write_text(
        json.dumps(
            {
                "schema": 1,
                "concepts": [
                    {
                        "id": "x",
                        "title": "X",
                        "windows": ["x"],
                        "route": {"kind": "section", "target": "s"},
                        "linux": "l",
                        "equivalence": "approximate",
                        "group": "g",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogError):  # non-exact without a note
        Catalog.load(bad)
    bad.write_text(json.dumps({"schema": 99, "concepts": []}), encoding="utf-8")
    with pytest.raises(CatalogError):
        Catalog.load(bad)
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(CatalogError):
        Catalog.load(bad)


def test_duplicate_ids_rejected(tmp_path: Path) -> None:
    entry = {
        "id": "dup",
        "title": "D",
        "windows": ["d"],
        "route": {"kind": "teach"},
        "linux": "l",
        "equivalence": "exact",
        "group": "g",
    }
    f = tmp_path / "c.json"
    f.write_text(json.dumps({"schema": 1, "concepts": [entry, entry]}), encoding="utf-8")
    with pytest.raises(CatalogError):
        Catalog.load(f)
