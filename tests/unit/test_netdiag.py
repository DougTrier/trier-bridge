# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T119/TB-T082: hosts are validated as data; ping and nslookup are Bridge commands."""
from pathlib import Path

import pytest

from trier_bridge.bridge.grammar import Failure, ParseFailure, parse

gi = pytest.importorskip("gi")

from trier_bridge.bridge.commands import Exit, Session, run_line  # noqa: E402
from trier_bridge.system.netdiag import valid_host  # noqa: E402


def test_host_names_and_addresses_are_validated() -> None:
    assert valid_host("ubuntu.com") == "ubuntu.com"
    assert valid_host(" 10.0.0.1 ") == "10.0.0.1"
    assert valid_host("::1") == "::1"
    assert valid_host("my-host.local.") == "my-host.local."
    for bad in ("", "a b", "host;rm", "-lead.example", "$(x)", "x" * 300):
        with pytest.raises(ValueError):
            valid_host(bad)


def test_ping_and_nslookup_parse_and_refuse_bad_input(tmp_path: Path) -> None:
    cmd = parse("ping -n 2 ubuntu.com")
    assert not isinstance(cmd, ParseFailure) and cmd.args == ("-n", "2", "ubuntu.com")
    assert isinstance(parse("ping"), ParseFailure)
    session = Session(tmp_path)
    assert run_line("ping bad host", session).exit is Exit.PARSE_ERROR
    assert run_line("ping ubuntu.com -n 0", session).exit is Exit.PARSE_ERROR
    assert run_line("nslookup not@valid", session).exit is Exit.PARSE_ERROR
    bad = parse("ping ubuntu.com; rm -rf /")
    assert isinstance(bad, ParseFailure) and bad.failure is Failure.SHELL_SYNTAX
    out = run_line("ipconfig /renew", session)
    assert out.exit is Exit.UNSUPPORTED and "netsh" in out.lines[0]


def test_cmdlet_names_map_to_the_diagnostics(tmp_path: Path) -> None:
    from trier_bridge.bridge.cmdlets import translate

    assert translate(["Test-Connection", "ubuntu.com", "-Count", "2"]).tokens == [
        "ping",
        "-n",
        "2",
        "ubuntu.com",
    ]
    assert translate(["Resolve-DnsName", "ubuntu.com"]).tokens == ["nslookup", "ubuntu.com"]
    assert translate(["Clear-DnsClientCache"]).tokens == ["ipconfig", "/flushdns"]
