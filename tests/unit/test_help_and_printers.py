# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T004: Help describes only what the build contains; printers are read from CUPS or say why not."""
from pathlib import Path

import pytest

from trier_bridge.catalog.model import Catalog
from trier_bridge.config import resolve_paths
from trier_bridge.help import sections
from trier_bridge.resources import catalog_path


def test_help_is_generated_from_the_build(tmp_path: Path) -> None:
    paths = resolve_paths({"HOME": str(tmp_path)})
    secs = sections(Catalog.load(catalog_path()), paths)
    titles = [s.title for s in secs]
    assert titles[0] == "How Trier Bridge works"
    assert "Command Prompt (Bridge Mode)" in titles and "Integrations" in titles
    commands = next(s for s in secs if s.title == "Command Prompt (Bridge Mode)")
    names = [r[0].split(" ")[0] for r in commands.rows]
    assert "tasklist" in names and "del" in names and "powershell" in names
    assert all(r[1] for r in commands.rows)  # every command explains its class and Linux side
    words = [s for s in secs if s.title.startswith("Windows words: ")]
    assert words and any("Task Manager" in r[0] for s in words for r in s.rows)
    files = next(s for s in secs if s.title.startswith("Where Trier Bridge keeps"))
    assert all(r[0].startswith(str(tmp_path)) for r in files.rows)


def test_printers_read_from_cups_or_explain() -> None:
    from trier_bridge.system.printers import read_printers

    o = read_printers()
    try:
        import cups  # noqa: F401
    except ImportError:
        assert not o.available and "python3-cups" in o.detail
        pytest.skip("python3-cups not installed here")
    assert o.available, o.detail
    for p in o.printers:
        assert p.state in ("Ready", "Printing", "Stopped", "Unknown")
        for j in p.jobs:
            assert j.printer == p.name
