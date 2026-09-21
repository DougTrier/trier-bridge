# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T052/TB-T109: netsh forms and IPv4 settings are validated before anything is planned."""
import pytest

from trier_bridge.bridge.commands import netsh_request
from trier_bridge.bridge.grammar import ParseFailure, parse

gi = pytest.importorskip("gi")

from trier_bridge.operations.network import ipv4_settings, mask_to_prefix, parse_ipv4  # noqa: E402


def test_masks_and_addresses_are_validated() -> None:
    assert mask_to_prefix("255.255.255.0") == 24 and mask_to_prefix("16") == 16
    assert mask_to_prefix("255.255.0.0") == 16
    for bad in ("255.0.255.0", "300", "abc"):
        with pytest.raises(ValueError):
            mask_to_prefix(bad)
    assert parse_ipv4(" 10.0.0.5 ") == "10.0.0.5"
    with pytest.raises(ValueError):
        parse_ipv4("10.0.0.999")
    s = ipv4_settings("192.168.1.10", "255.255.255.0", "192.168.1.1", "1.1.1.1, 8.8.8.8")
    assert (s.address, s.prefix, s.gateway, s.dns) == (
        "192.168.1.10",
        24,
        "192.168.1.1",
        ("1.1.1.1", "8.8.8.8"),
    )
    s = ipv4_settings("10.0.0.5/8", "", "", "")
    assert (s.address, s.prefix, s.gateway, s.dns) == ("10.0.0.5", 8, "", ())


def test_netsh_forms_parse_into_requests() -> None:
    assert netsh_request(("interface", "set", "interface", "eth0", "disable")) == (
        "eth0",
        "disconnect",
        {},
    )
    assert netsh_request(("interface", "set", "interface", "name=eth0", "enable")) == (
        "eth0",
        "connect",
        {},
    )
    assert netsh_request(("interface", "ip", "set", "address", "eth0", "dhcp")) == (
        "eth0",
        "auto",
        {},
    )
    assert netsh_request(
        ("interface", "ip", "set", "address", "eth0", "static", "10.0.0.5", "255.0.0.0", "10.0.0.1")
    ) == (
        "eth0",
        "static",
        {"address": "10.0.0.5", "mask": "255.0.0.0", "gateway": "10.0.0.1"},
    )
    assert netsh_request(("interface", "ip", "set", "dns", "eth0", "static", "1.1.1.1")) == (
        "eth0",
        "dns",
        {"dns": "1.1.1.1"},
    )
    assert netsh_request(("interface", "ip", "set", "dns", "eth0", "dhcp")) == (
        "eth0",
        "dns-auto",
        {},
    )
    assert isinstance(netsh_request(("wlan", "show", "profiles")), str)
    assert isinstance(netsh_request(("interface", "ip", "set", "address", "eth0", "static")), str)


def test_netsh_is_a_class_c_bridge_command() -> None:
    cmd = parse('netsh interface ip set address "Wired connection 1" static 10.0.0.5 255.0.0.0')
    assert not isinstance(cmd, ParseFailure) and cmd.spec.name == "netsh"
    assert cmd.args[4] == "Wired connection 1"
    assert isinstance(parse("netsh interface"), ParseFailure)  # needs three arguments
