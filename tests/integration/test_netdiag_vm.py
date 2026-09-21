# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""nslookup answers from the live resolver; flushdns is a verified resolved call; ping opens a window."""
import os
from pathlib import Path

import pytest

gi = pytest.importorskip("gi")

from trier_bridge.bridge.commands import ActionPlan, Exit, Session, run_line  # noqa: E402
from trier_bridge.system.netdiag import cache_size, dns_servers, lookup  # noqa: E402

pytestmark = pytest.mark.integration


def test_nslookup_localhost_and_servers(tmp_path: Path) -> None:
    res = lookup("localhost")
    assert "127.0.0.1" in res.addresses and not res.error
    servers = dns_servers()
    assert servers, "systemd-resolved reported no DNS servers"
    out = run_line("nslookup localhost", Session(tmp_path))
    assert (
        out.exit is Exit.OK
        and out.lines[0].startswith("Server:  ")
        and "127.0.0.1" in " ".join(out.lines)
    )
    missing = run_line("nslookup no-such-host.invalid", Session(tmp_path))
    assert missing.exit is Exit.FAILED and "Can't find" in missing.lines[-1]


def test_flushdns_is_planned_then_verified(tmp_path: Path) -> None:
    lookup("ubuntu.com")  # put something in the cache if the network allows
    out = run_line("ipconfig /flushdns", Session(tmp_path))
    assert out.exit is Exit.NEEDS_CONFIRMATION and isinstance(out.pending_operation, ActionPlan)
    ok, plain = out.pending_operation.run()
    assert ok, plain
    assert plain == "Successfully flushed the DNS Resolver Cache."
    assert cache_size() == 0


def test_ping_opens_the_system_ping_or_says_why(tmp_path: Path) -> None:
    out = run_line("ping -n 1 127.0.0.1", Session(tmp_path))
    if os.environ.get("WAYLAND_DISPLAY"):
        assert out.exit is Exit.OK and "terminal window" in out.lines[0], out
    else:
        assert out.exit in (Exit.OK, Exit.FAILED) and out.lines, out
    assert out.linux_equivalent == "ping -c 1 127.0.0.1"
