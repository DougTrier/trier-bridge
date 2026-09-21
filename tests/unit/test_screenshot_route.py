# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T119: the screenshot concept is an action the window performs through the portal."""
from trier_bridge.catalog.model import Catalog, Equivalence, RouteKind
from trier_bridge.resources import catalog_path


def test_screenshot_is_an_action_with_a_target() -> None:
    c = Catalog.load(catalog_path()).get("tb.screenshot")
    assert c is not None
    assert c.route.kind is RouteKind.ACTION and c.route.target == "screenshot"
    assert c.equivalence is Equivalence.EXACT and c.can_open
    assert "Print Screen" in c.windows_terms
    assert Catalog.load(catalog_path()).search("snipping tool")[0].concept.id == "tb.screenshot"
