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


def test_clamp_zoom_snaps_to_the_step() -> None:
    assert theme.clamp_zoom(103) == 105
    assert theme.clamp_zoom(97) == 95
    assert theme.clamp_zoom(102) == 100
    assert theme.clamp_zoom(100) == 100


def test_group_css_class_is_one_token_per_sidebar_group() -> None:
    assert theme.group_css_class("Everyday") == "tb-tint-everyday"
    assert theme.group_css_class("Trier Bridge") == "tb-tint-trier-bridge"
    assert " " not in theme.group_css_class("Trier Bridge")


def test_generate_css_carries_the_whole_shell_vocabulary() -> None:
    css = theme.generate_css(theme.DEFAULT_HUE, theme.DEFAULT_ZOOM)
    for selector in (
        ".tb-sidebar",
        ".tb-topbar",
        ".tb-zoombar",
        ".tb-hero",
        ".tb-hero-chip",
        ".tb-pill",
        ".tb-pill-ok",
        ".tb-pill-error",
        ".tb-card",
        ".tb-app-icon",
        ".tb-support-coffee",
    ):
        assert selector in css, selector
    for group in theme.GROUP_ACCENTS:
        assert f".{theme.group_css_class(group)}" in css
    assert ".tb-tint-trier-bridge" in css


def test_top_and_bottom_bars_use_the_sidebar_gradient_ends() -> None:
    top, bottom = theme.sidebar_colors(90)
    css = theme.generate_css(90, 100)
    assert f".tb-topbar {{\n  background-color: {top};" in css
    assert f".tb-zoombar {{\n  background-color: {bottom};" in css
