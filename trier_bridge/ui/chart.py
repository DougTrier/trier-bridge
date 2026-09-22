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
"""
from __future__ import annotations

from collections import deque
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

# A calm accent color independent of the desktop theme (Cairo has no reliable
# cross-theme way to read the current accent from a plain DrawingArea).
_LINE_RGBA = (0.80, 0.22, 0.42, 0.95)
_FILL_RGBA = (0.80, 0.22, 0.42, 0.16)
_GRID_RGBA = (1.0, 1.0, 1.0, 0.08)


class Chart(Gtk.DrawingArea):  # type: ignore[misc]
    """Bounded rolling-window line chart. ``push()`` appends one new sample per tick."""

    def __init__(self, capacity: int, fill: bool = True) -> None:
        super().__init__()
        self._capacity = capacity
        self._fill = fill
        self._values: deque[float | None] = deque(maxlen=capacity)
        self._max_value: float | None = None  # None = auto-scale to the data's own peak
        self.set_draw_func(self._draw)

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

        cr.set_source_rgba(*_GRID_RGBA)
        cr.set_line_width(1)
        cr.move_to(0, height / 2)
        cr.line_to(width, height / 2)
        cr.stroke()

        points: list[tuple[float, float]] = []
        cr.set_source_rgba(*_LINE_RGBA)
        cr.set_line_width(1.6)
        drawing = False
        for i, v in enumerate(values):
            x = i * step
            if v is None:
                if drawing:
                    cr.stroke()
                    drawing = False
                continue
            y = height - (min(v, peak) / peak) * height
            points.append((x, y))
            if drawing:
                cr.line_to(x, y)
            else:
                cr.move_to(x, y)
                drawing = True
        if drawing:
            cr.stroke()

        if self._fill and points:
            cr.set_source_rgba(*_FILL_RGBA)
            cr.move_to(points[0][0], height)
            for x, y in points:
                cr.line_to(x, y)
            cr.line_to(points[-1][0], height)
            cr.close_path()
            cr.fill()
