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
"""The sidebar's section table and the default-app type list, as data (no widgets built).

Needs ``gi`` because ``window.py`` imports GTK at module level; runs in the VM gate.
"""
from __future__ import annotations

import pytest

gi = pytest.importorskip("gi")

from trier_bridge.apps.inventory import COMMON_TYPES  # noqa: E402
from trier_bridge.ui import theme  # noqa: E402
from trier_bridge.ui.window import SECTIONS  # noqa: E402


def test_every_section_has_a_plain_blurb_for_the_hero() -> None:
    for s in SECTIONS:
        assert s.blurb.strip(), s.key
        assert len(s.blurb) <= 120, (s.key, len(s.blurb))
        assert s.blurb[0].isupper() and s.blurb.endswith("."), s.key


def test_section_keys_are_unique_and_groups_have_a_tint() -> None:
    keys = [s.key for s in SECTIONS]
    assert len(keys) == len(set(keys))
    css = theme.generate_css(theme.DEFAULT_HUE, theme.DEFAULT_ZOOM)
    for s in SECTIONS:
        assert f".{theme.group_css_class(s.group)}" in css, s.group


def test_about_sits_directly_above_help_in_the_trier_bridge_group() -> None:
    keys = [s.key for s in SECTIONS]
    assert keys.index("about") + 1 == keys.index("help")
    about = next(s for s in SECTIONS if s.key == "about")
    help_ = next(s for s in SECTIONS if s.key == "help")
    assert about.group == help_.group == "Trier Bridge"
    assert "[" not in about.familiar and "]" not in about.familiar


def test_deb_installers_are_a_default_app_choice() -> None:
    mimes = dict(COMMON_TYPES)
    assert "application/vnd.debian.binary-package" in mimes
    assert "deb" in mimes["application/vnd.debian.binary-package"].casefold()
