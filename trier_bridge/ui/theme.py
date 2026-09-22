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
"""Shell theming: sidebar accent color, zoom, and the content-area style vocabulary.

No ``gi`` import here on purpose (TB-INV-252): the color math and CSS
generation are pure functions, so they get real host-side unit tests without
needing PyGObject. ``window.py`` is the only place that actually loads the
generated text into a ``Gtk.CssProvider``.

Personalization only (TB-INV-253/254): every value here is clamped to a safe
range before use, and nothing generated here changes what any row does or
what any page shows -- only how it is painted.

The content area uses libadwaita's named colors (``@card_bg_color``,
``@headerbar_bg_color``, ...) rather than fixed hex values wherever the
surface is the desktop's own, so the app still follows a dark desktop
theme; only the sidebar, which is always the chosen accent, is fixed.
"""
from __future__ import annotations

import colorsys

MIN_HUE = 0
MAX_HUE = 360
DEFAULT_HUE = 213  # the branded navy the owner picked from the mockups

MIN_ZOOM = 80
MAX_ZOOM = 150
ZOOM_STEP = 5
DEFAULT_ZOOM = 100

# One accent per sidebar group, matching the launcher icon suite; the
# "Trier Bridge" group follows the chosen sidebar hue instead.
GROUP_ACCENTS: dict[str, str] = {
    "Everyday": "#1f6f65",
    "Troubleshooting": "#a2681f",
    "Advanced": "#5138a8",
}


def clamp_hue(value: int) -> int:
    return max(MIN_HUE, min(MAX_HUE, int(value)))


def clamp_zoom(value: int) -> int:
    snapped = round(int(value) / ZOOM_STEP) * ZOOM_STEP
    return max(MIN_ZOOM, min(MAX_ZOOM, snapped))


def group_css_class(group: str) -> str:
    """The tint class for a sidebar group's hero chip and pills."""
    return f"tb-tint-{group.casefold().replace(' ', '-')}"


def _hex(hue: int, saturation: float, lightness: float) -> str:
    r, g, b = colorsys.hls_to_rgb((hue % 360) / 360.0, lightness, saturation)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def sidebar_colors(hue: int) -> tuple[str, str]:
    """(top, bottom) hex colors for the sidebar's gradient, at a given hue."""
    hue = clamp_hue(hue)
    return _hex(hue, 0.46, 0.30), _hex(hue, 0.55, 0.14)


def accent_color(hue: int) -> str:
    """A mid-tone of the chosen hue for chips and pills on light surfaces."""
    return _hex(clamp_hue(hue), 0.50, 0.34)


def generate_css(hue: int, zoom_percent: int) -> str:
    """The window's whole custom stylesheet for the given hue and zoom level."""
    top, bottom = sidebar_colors(hue)
    accent = accent_color(hue)
    zoom = clamp_zoom(zoom_percent)
    tints = "\n".join(
        f".{group_css_class(g)} {{ background-color: alpha({c}, 0.14); color: {c}; }}"
        for g, c in GROUP_ACCENTS.items()
    )
    return f"""
/* ---- sidebar: always the chosen accent ---- */
.tb-sidebar {{
  background-image: linear-gradient(180deg, {top} 0%, {bottom} 100%);
}}
.tb-sidebar .navigation-sidebar,
.tb-sidebar .navigation-sidebar row {{
  background: transparent;
  color: #cfdbea;
}}
.tb-sidebar .navigation-sidebar row:selected {{
  background: rgba(255, 255, 255, 0.14);
  color: #ffffff;
  font-weight: 600;
}}
.tb-sidebar .navigation-sidebar row:hover {{
  background: rgba(255, 255, 255, 0.07);
}}
.tb-group-label,
.tb-wordmark-sub,
.tb-hue-label {{
  color: #7fa0c4;
}}
.tb-wordmark-pill {{
  background: #f4f7fb;
  color: {bottom};
  border-radius: 9px;
  padding: 6px 12px;
  font-weight: 700;
}}

/* ---- window chrome: the same accent frames the content on three sides ---- */
.tb-topbar {{
  background-color: {top};
  color: #ffffff;
  box-shadow: none;
}}
.tb-topbar windowtitle .subtitle,
.tb-topbar .subtitle {{
  color: #cfdbea;
}}
.tb-zoombar {{
  background-color: {bottom};
  color: #cfdbea;
  border-top: none;
  padding: 6px 16px;
}}
.tb-shell revealer.bottom-bar {{
  background-color: {bottom};
}}
.tb-zoombar button {{
  color: #ffffff;
}}
.tb-zoombar scale trough,
.tb-sidebar scale trough {{
  background-color: alpha(#ffffff, 0.18);
}}
.tb-zoombar scale highlight,
.tb-sidebar scale highlight {{
  background-color: alpha(#ffffff, 0.85);
}}
.tb-zoombar scale slider,
.tb-sidebar scale slider {{
  background-color: #ffffff;
  border-color: alpha(#000000, 0.25);
}}
.tb-content-zoom {{
  font-size: {zoom}%;
}}

/* ---- content hero: one per page, shared by the window ---- */
.tb-hero {{
  padding: 18px 28px 10px 28px;
}}
.tb-hero-chip {{
  border-radius: 12px;
  padding: 10px;
  min-width: 26px;
  min-height: 26px;
}}
.tb-hero-title {{
  font-weight: 700;
}}
.tb-hero-blurb {{
  color: alpha(@window_fg_color, 0.65);
}}
{tints}
.tb-tint-trier-bridge {{
  background-color: alpha({accent}, 0.14);
  color: {accent};
}}

/* ---- pills: small status/context labels ---- */
.tb-pill {{
  font-size: 0.8em;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 999px;
  min-height: 0;
}}
.tb-pill-neutral {{
  background-color: alpha(@window_fg_color, 0.09);
  color: alpha(@window_fg_color, 0.75);
}}
.tb-pill-windows {{
  background-color: alpha({accent}, 0.12);
  color: {accent};
}}
.tb-pill-ok {{
  background-color: alpha(#2f8552, 0.16);
  color: #237243;
}}
.tb-pill-warn {{
  background-color: alpha(#a2681f, 0.16);
  color: #8a5716;
}}
.tb-pill-error {{
  background-color: alpha(#c0392b, 0.14);
  color: #b0281a;
}}
.tb-pill-off {{
  background-color: alpha(@window_fg_color, 0.07);
  color: alpha(@window_fg_color, 0.6);
}}

/* ---- cards: Home's quick-access grid ---- */
.tb-card {{
  background-color: @card_bg_color;
  color: @card_fg_color;
  border: 1px solid alpha(@window_fg_color, 0.10);
  border-radius: 14px;
  padding: 16px;
  min-height: 0;
}}
.tb-card:hover {{
  border-color: alpha({accent}, 0.45);
  background-color: alpha({accent}, 0.04);
}}
.tb-card-icon {{
  border-radius: 10px;
  padding: 8px;
  min-width: 20px;
  min-height: 20px;
}}
.tb-card-title {{
  font-weight: 700;
}}
.tb-card-text {{
  color: alpha(@card_fg_color, 0.65);
  font-size: 0.92em;
}}

/* ---- Task Manager Performance: one color per resource, stat cards ---- */
.tb-perf-dot {{
  border-radius: 6px;
  min-width: 10px;
  min-height: 10px;
}}
.tb-perf-dot.tb-perf-cpu {{ background-color: #1f6f65; }}
.tb-perf-dot.tb-perf-mem {{ background-color: #5138a8; }}
.tb-perf-dot.tb-perf-disk {{ background-color: #a2681f; }}
.tb-perf-dot.tb-perf-net {{ background-color: #1f4f85; }}
.tb-perf-value {{
  font-weight: 700;
  font-size: 1.6em;
}}
.tb-perf-value.tb-perf-cpu {{ color: #1f6f65; }}
.tb-perf-value.tb-perf-mem {{ color: #5138a8; }}
.tb-perf-value.tb-perf-disk {{ color: #a2681f; }}
.tb-perf-value.tb-perf-net {{ color: #1f4f85; }}
.tb-stat {{
  background-color: @card_bg_color;
  color: @card_fg_color;
  border: 1px solid alpha(@window_fg_color, 0.10);
  border-radius: 12px;
  padding: 12px 14px;
}}
.tb-stat-label {{
  font-size: 0.85em;
  color: alpha(@card_fg_color, 0.6);
}}
.tb-stat-value {{
  font-weight: 700;
  font-size: 1.15em;
}}

/* ---- rows: real application icons and support links ---- */
.tb-app-icon {{
  border-radius: 8px;
}}
.tb-support-icon {{
  border-radius: 10px;
  padding: 6px;
  min-width: 24px;
  min-height: 24px;
}}
.tb-support-sponsors {{
  background-color: alpha(#e8a317, 0.16);
  color: #b7790f;
}}
.tb-support-coffee {{
  background-color: alpha(#a2681f, 0.14);
  color: #a2681f;
}}
"""
