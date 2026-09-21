# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Shipped data resolution: override, source tree, packaged location."""
from pathlib import Path

from trier_bridge.resources import PACKAGED_DATA_DIR, catalog_path, data_dir


def test_override_wins(tmp_path: Path) -> None:
    assert data_dir({"TRIER_BRIDGE_DATA_DIR": str(tmp_path)}) == tmp_path
    assert (
        catalog_path({"TRIER_BRIDGE_DATA_DIR": str(tmp_path)})
        == tmp_path / "catalog" / "concepts.json"
    )


def test_source_tree_is_found_from_a_checkout() -> None:
    d = data_dir({})
    assert (d / "catalog" / "concepts.json").is_file() or d == PACKAGED_DATA_DIR
