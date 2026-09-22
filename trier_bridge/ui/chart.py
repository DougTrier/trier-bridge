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
"""A small, reusable line chart for live resource graphs (Task Manager Performance tab,
DEC-026). Drawn directly with Cairo via ``Gtk.DrawingArea`` — the first chart/graph widget
in this codebase; no existing precedent to follow.

Bounded to a fixed-size rolling window (``capacity``): the oldest sample drops
as the newest arrives, so a chart left open indefinitely never grows memory
(TB-INV-248). A missing sample (``None``) breaks the line rather than being
interpolated or held at the last value (TB-INV-251) — a real read failure
must look visibly different from a quiet drop to zero.

Each chart carries its own accent (``set_color``) so every resource on the
Performance tab has a recognizable color; the fill is a vertical gradient of
that accent and the newest sample gets a marker, which is presentation only
(TB-INV-253) — the values drawn are exactly the samples pushed.
"""
from __future__ import annotations

from collections import deque
from typing import Any

import cairo
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

_DEFAULT_RGB = (0.12, 0.31, 0.52)  # the brand navy; each resource overrides it
_GRID_RGBA = (0.0, 0.0, 0.0, 0.07)


class Chart(Gtk.DrawingArea):  # type: ignore[misc]
    """Bounded rolling-window line chart. ``push()`` appends one new sample per tick."""

    def __init__(self, capacity: int, fill: bool = True) -> None:
        super().__init__()
        self._capacity = capacity
        self._fill = fill
        self._rgb = _DEFAULT_RGB
        self._values: deque[float | None] = deque(maxlen=capacity)
        self._max_value: float | None = None  # None = auto-scale to the data's own peak
        self.set_draw_func(self._draw)

    def set_color(self, red: float, green: float, blue: float) -> None:
        """The accent this chart draws in (0-1 components); presentation only."""
        self._rgb = (red, green, blue)
        self.queue_draw()

    def set_max_value(self, value: float | None) -> None:
        """Fix the vertical scale (for example to 100 for a percentage chart); None auto-scales."""
        self._max_value = value

    def peak(self) -> float:
        """The value the chart is currently scaled to — what a "500 Kbps" label should show."""
        if self._max_value is not None:
            return self._max_value
        real = [v for v in self._values if v is not None]
        return max(real) if real else 1.0

    def values(self) -> list[float | None]:
        return list(self._values)

    def set_values(self, values: list[float | None]) -> None:
        """Bulk-replace the whole window at once (for example when the selected resource
        changes and the detail chart needs to catch up to a tile's already-collected history)."""
        self._values = deque(values[-self._capacity :], maxlen=self._capacity)
        self.queue_draw()

    def push(self, value: float | None) -> None:
        self._values.append(value)
        self.queue_draw()

    def clear(self) -> None:
        self._values.clear()
        self.queue_draw()

    def _draw(self, _area: Gtk.DrawingArea, cr: Any, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            return
        n = self._capacity
        values: list[float | None] = list(self._values)
        padding: list[float | None] = [None] * (n - len(values))
        values = padding + values  # left-pad: always fills the full width
        peak = max(self.peak(), 1e-9)
        step = width / max(n - 1, 1)
        r, g, b = self._rgb

        if self._fill:
            cr.set_source_rgba(*_GRID_RGBA)
            cr.set_line_width(1)
            for fraction in (0.25, 0.5, 0.75):
                y = height * fraction
                cr.move_to(0, y)
                cr.line_to(width, y)
            cr.stroke()

        points: list[tuple[float, float]] = []
        segments: list[list[tuple[float, float]]] = []
        current: list[tuple[float, float]] = []
        for i, v in enumerate(values):
            if v is None:
                if current:
                    segments.append(current)
                    current = []
                continue
            x = i * step
            y = height - (min(v, peak) / peak) * (height - 2) - 1
            current.append((x, y))
            points.append((x, y))
        if current:
            segments.append(current)

        if self._fill and points:
            gradient = cairo.LinearGradient(0, 0, 0, height)
            gradient.add_color_stop_rgba(0, r, g, b, 0.30)
            gradient.add_color_stop_rgba(1, r, g, b, 0.02)
            for segment in segments:
                cr.move_to(segment[0][0], height)
                for x, y in segment:
                    cr.line_to(x, y)
                cr.line_to(segment[-1][0], height)
                cr.close_path()
            cr.set_source(gradient)
            cr.fill()

        cr.set_source_rgba(r, g, b, 0.95)
        cr.set_line_width(2 if self._fill else 1.5)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        for segment in segments:
            cr.move_to(*segment[0])
            for x, y in segment[1:]:
                cr.line_to(x, y)
            if len(segment) == 1:
                cr.line_to(segment[0][0] + 0.1, segment[0][1])
            cr.stroke()

        if self._fill and points and values[-1] is not None:
            x, y = points[-1]
            cr.arc(x, y, 3.5, 0, 6.2832)
            cr.set_source_rgba(1, 1, 1, 1)
            cr.fill_preserve()
            cr.set_source_rgba(r, g, b, 1)
            cr.set_line_width(2)
            cr.stroke()
