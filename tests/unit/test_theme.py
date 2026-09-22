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
"""Real, no-mock tests for the pure color/CSS math behind the shell theme (TB-INV-252)."""
from __future__ import annotations

from trier_bridge.ui import theme


def test_clamp_hue_keeps_in_range_values_unchanged() -> None:
    assert theme.clamp_hue(0) == 0
    assert theme.clamp_hue(213) == 213
    assert theme.clamp_hue(360) == 360


def test_clamp_hue_clamps_out_of_range_values() -> None:
    assert theme.clamp_hue(-50) == theme.MIN_HUE
    assert theme.clamp_hue(9999) == theme.MAX_HUE


def test_clamp_zoom_clamps_out_of_range_values() -> None:
    assert theme.clamp_zoom(10) == theme.MIN_ZOOM
    assert theme.clamp_zoom(1000) == theme.MAX_ZOOM
    assert theme.clamp_zoom(100) == 100


def test_sidebar_colors_are_real_hex_and_vary_with_hue() -> None:
    top_a, bottom_a = theme.sidebar_colors(0)
    top_b, bottom_b = theme.sidebar_colors(213)
    for value in (top_a, bottom_a, top_b, bottom_b):
        assert value.startswith("#")
        assert len(value) == 7
        int(value[1:], 16)  # raises ValueError if it is not real hex
    assert top_a != top_b
    assert bottom_a != bottom_b


def test_sidebar_colors_clamp_an_out_of_range_hue() -> None:
    assert theme.sidebar_colors(-40) == theme.sidebar_colors(theme.MIN_HUE)
    assert theme.sidebar_colors(720) == theme.sidebar_colors(theme.MAX_HUE)


def test_generate_css_embeds_the_real_computed_colors() -> None:
    hue = 90
    top, bottom = theme.sidebar_colors(hue)
    css = theme.generate_css(hue, 100)
    assert top in css
    assert bottom in css
    assert ".tb-sidebar" in css
    assert ".tb-content-zoom" in css


def test_generate_css_zoom_percentage_is_clamped_and_embedded() -> None:
    css_low = theme.generate_css(theme.DEFAULT_HUE, 10)
    css_high = theme.generate_css(theme.DEFAULT_HUE, 1000)
    assert f"font-size: {theme.MIN_ZOOM}%" in css_low
    assert f"font-size: {theme.MAX_ZOOM}%" in css_high
