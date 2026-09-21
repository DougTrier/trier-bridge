# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T071/TB-T149/TB-T157: pure helpers keep network layers and storage kinds distinct."""
import pytest

pytest.importorskip("gi")

from trier_bridge.system.network import CONNECTIVITY, DEVICE_STATES  # noqa: E402
from trier_bridge.system.network import _addr_list, _ns_list  # noqa: E402
from trier_bridge.system.storage import _bytes_path  # noqa: E402


def test_connectivity_and_link_state_are_separate_vocabularies() -> None:
    assert CONNECTIVITY[4] == "Full Internet access" and CONNECTIVITY[0] == "Unknown"
    assert DEVICE_STATES[100] == "Connected" and DEVICE_STATES[0] == "Unknown"
    assert set(CONNECTIVITY.values()).isdisjoint(set(DEVICE_STATES.values()) - {"Unknown"})


def test_address_and_nameserver_lists_tolerate_odd_data() -> None:
    assert _addr_list([{"address": "10.0.0.5", "prefix": 24}]) == ("10.0.0.5/24",)
    assert _addr_list([{"address": "10.0.0.5"}, "junk", None]) == ("10.0.0.5",)
    assert _addr_list(None) == ()
    assert _ns_list([{"address": "1.1.1.1"}, {"address": ""}, 5]) == ("1.1.1.1",)


def test_udisks_byte_paths_decode() -> None:
    assert _bytes_path(b"/dev/sda1\x00") == "/dev/sda1"
    assert _bytes_path([47, 109, 110, 116, 0]) == "/mnt"
    assert _bytes_path(None) == ""
