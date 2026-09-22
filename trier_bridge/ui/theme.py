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
"""Shell theming: sidebar accent color and zoom, as plain data and CSS text.

No ``gi`` import here on purpose (TB-INV-252): the color math and CSS
generation are pure functions, so they get real host-side unit tests without
needing PyGObject. ``window.py`` is the only place that actually loads the
generated text into a ``Gtk.CssProvider``.

Personalization only (TB-INV-253/254): every value here is clamped to a safe
range before use, and nothing generated here changes what any row does or
what any page shows -- only how it is painted.
"""
from __future__ import annotations

import colorsys

MIN_HUE = 0
MAX_HUE = 360
DEFAULT_HUE = 213  # the branded navy the owner picked from the mockups

MIN_ZOOM = 80
MAX_ZOOM = 150
DEFAULT_ZOOM = 100


def clamp_hue(value: int) -> int:
    return max(MIN_HUE, min(MAX_HUE, int(value)))


def clamp_zoom(value: int) -> int:
    return max(MIN_ZOOM, min(MAX_ZOOM, int(value)))


def _hex(hue: int, saturation: float, lightness: float) -> str:
    r, g, b = colorsys.hls_to_rgb((hue % 360) / 360.0, lightness, saturation)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def sidebar_colors(hue: int) -> tuple[str, str]:
    """(top, bottom) hex colors for the sidebar's gradient, at a given hue."""
    hue = clamp_hue(hue)
    return _hex(hue, 0.46, 0.30), _hex(hue, 0.55, 0.14)


def generate_css(hue: int, zoom_percent: int) -> str:
    """The window's whole custom stylesheet for the given hue and zoom level."""
    top, bottom = sidebar_colors(hue)
    zoom = clamp_zoom(zoom_percent)
    return f"""
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
.tb-group-label {{
  color: #7fa0c4;
}}
.tb-wordmark-pill {{
  background: #f4f7fb;
  color: {bottom};
  border-radius: 9px;
  padding: 6px 12px;
  font-weight: 700;
}}
.tb-wordmark-sub {{
  color: #7fa0c4;
}}
.tb-hue-label {{
  color: #7fa0c4;
}}
.tb-zoombar {{
  background: #eef0f4;
  border-top: 1px solid #dcdfe4;
}}
.tb-content-zoom {{
  font-size: {zoom}%;
}}
"""
