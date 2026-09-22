# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T248/TB-T251: the rolling-window chart never grows past capacity and keeps real gaps."""
import pytest

gi = pytest.importorskip("gi")

from trier_bridge.ui.chart import Chart  # noqa: E402


def test_chart_window_is_bounded_and_drops_the_oldest_sample() -> None:
    chart = Chart(capacity=5)
    for i in range(12):
        chart.push(float(i))
    assert chart.values() == [7.0, 8.0, 9.0, 10.0, 11.0]  # never grows past capacity (TB-INV-248)


def test_chart_keeps_a_missing_sample_as_a_real_gap_not_interpolated() -> None:
    chart = Chart(capacity=4)
    chart.push(10.0)
    chart.push(None)  # a real read failure, not a quiet zero (TB-INV-251)
    chart.push(20.0)
    assert chart.values() == [10.0, None, 20.0]


def test_chart_peak_auto_scales_or_uses_a_fixed_max() -> None:
    chart = Chart(capacity=4)
    chart.push(5.0)
    chart.push(15.0)
    assert chart.peak() == 15.0
    chart.set_max_value(100.0)
    assert chart.peak() == 100.0


def test_chart_set_values_bulk_replaces_and_truncates_to_capacity() -> None:
    chart = Chart(capacity=3)
    chart.set_values([1.0, 2.0, 3.0, 4.0, 5.0])
    assert chart.values() == [3.0, 4.0, 5.0]
