# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""IMP-06.06: network changes on a real NetworkManager dummy interface, never the VM's uplink.

The dummy connection is created with nmcli (sudo) as a real test object; every
change goes through Trier Bridge's typed operations with polkit answered by the
real test agent (grant needs TRIER_BRIDGE_TEST_PASSWORD).
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

gi = pytest.importorskip("gi")

from trier_bridge.bridge.commands import Exit, Session, run_line  # noqa: E402
from trier_bridge.core.state import OperationState  # noqa: E402
from trier_bridge.operations.network import (  # noqa: E402
    NetworkPlan,
    execute_network,
    ipv4_settings,
    plan_connect,
    plan_network,
)
from trier_bridge.state.journal import OperationJournal  # noqa: E402
from trier_bridge.system.network import NetworkDevice, read_network  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from polkit_agent import PolkitTestAgent  # noqa: E402

pytestmark = pytest.mark.integration
IFACE = "tbdummy0"
CONN = "tb-dummy"


def _sudo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["sudo", "-n", *args], capture_output=True, text=True)


@pytest.fixture()
def dummy():
    _sudo("nmcli", "con", "delete", CONN)
    r = _sudo(
        "nmcli",
        "con",
        "add",
        "type",
        "dummy",
        "ifname",
        IFACE,
        "con-name",
        CONN,
        "ipv4.method",
        "manual",
        "ipv4.addresses",
        "192.0.2.10/24",
        "ipv6.method",
        "disabled",
    )
    if r.returncode != 0:
        pytest.skip(f"could not create a dummy connection: {r.stderr.strip()}")
    time.sleep(2)
    try:
        yield IFACE
    finally:
        _sudo("nmcli", "con", "delete", CONN)


def _device(name: str) -> NetworkDevice:
    nw = read_network()
    dev = next((d for d in nw.devices if d.interface == name), None)
    assert dev is not None, [d.interface for d in nw.devices]
    return dev


def _password() -> str:
    pw = os.environ.get("TRIER_BRIDGE_TEST_PASSWORD", "")
    if not pw:
        pytest.skip("TRIER_BRIDGE_TEST_PASSWORD not set; polkit grants need the account password")
    return pw


def test_disconnect_and_connect_are_verified_on_the_dummy(dummy: str, tmp_path: Path) -> None:
    pw = _password()
    dev = _device(dummy)
    assert dev.connection_uuid and dev.link_state == "Connected", dev
    journal = OperationJournal(tmp_path / "j")
    plan = plan_network(dev, "disconnect")
    assert isinstance(plan, NetworkPlan) and "administrator" in plan.preview
    with PolkitTestAgent("grant", pw) as agent:
        res = execute_network(plan, journal)
    assert res.state is OperationState.VERIFIED, res
    assert all(d.interface != dummy for d in read_network().devices)  # removed while off
    assert "org.freedesktop.NetworkManager.network-control" in agent.prompts or agent.prompts == []
    # the uplink is untouched
    up = [d for d in read_network().devices if not d.is_loopback and d.interface != dummy]
    assert any(d.link_state == "Connected" for d in up)
    # a disconnected virtual adapter is removed by NetworkManager; connect from the profile
    plan = plan_connect(dummy)
    assert isinstance(plan, NetworkPlan) and "tb-dummy" in plan.preview
    with PolkitTestAgent("grant", pw):
        res = execute_network(plan, journal)
    assert res.state is OperationState.VERIFIED, res
    after = _device(dummy)
    assert after.connection_uuid and "192.0.2.10/24" in after.ipv4
    assert journal.unresolved() == []


def test_fixed_address_and_dns_are_saved_and_applied(dummy: str, tmp_path: Path) -> None:
    pw = _password()
    dev = _device(dummy)
    settings = ipv4_settings("192.0.2.11", "255.255.255.0", "", "192.0.2.53")
    plan = plan_network(dev, "static", settings)
    assert isinstance(plan, NetworkPlan) and "192.0.2.11/24" in plan.preview
    with PolkitTestAgent("grant", pw):
        res = execute_network(plan, OperationJournal(tmp_path / "j"))
    assert res.state is OperationState.VERIFIED, res
    after = _device(dummy)
    assert "192.0.2.11/24" in after.ipv4 and "192.0.2.53" in after.dns, after
    plan = plan_network(after, "dns-auto")
    assert isinstance(plan, NetworkPlan)
    with PolkitTestAgent("grant", pw):
        res = execute_network(plan)
    assert res.state is OperationState.VERIFIED, res


def test_stale_connection_cancels_and_loopback_is_refused(dummy: str, tmp_path: Path) -> None:
    pw = _password()
    dev = _device(dummy)
    plan = plan_network(dev, "disconnect")
    assert isinstance(plan, NetworkPlan)
    # the connection changes underneath (nmcli, as another tool would): the plan must cancel
    r = _sudo("nmcli", "dev", "disconnect", dummy)
    assert r.returncode == 0, r.stderr
    time.sleep(1)
    with PolkitTestAgent("grant", pw):
        res = execute_network(plan, OperationJournal(tmp_path / "j"))
    assert res.state is OperationState.CANCELLED and (
        "changed its connection" in res.plain or "no longer present" in res.plain
    )
    lo = next(d for d in read_network().devices if d.is_loopback)
    refused = plan_network(lo, "disconnect")
    assert not isinstance(refused, NetworkPlan) and refused.state is OperationState.UNSUPPORTED


def test_netsh_plans_but_does_not_act(dummy: str, tmp_path: Path) -> None:
    out = run_line(
        f"netsh interface ip set address {dummy} static 192.0.2.12 255.255.255.0", Session(tmp_path)
    )
    assert out.exit is Exit.NEEDS_CONFIRMATION and isinstance(out.pending_operation, NetworkPlan)
    assert "192.0.2.10/24" in _device(dummy).ipv4  # unchanged: nothing runs without the dialog
    out = run_line("netsh interface set interface nosuch0 disable", Session(tmp_path))
    assert out.exit is Exit.FAILED and "No adapter named" in out.lines[0]
    out = run_line("netsh interface set interface nosuch0 enable", Session(tmp_path))
    assert out.exit is Exit.FAILED and "no saved connection profile" in out.lines[0]
    out = run_line("netsh wlan show profiles", Session(tmp_path))
    assert out.exit is Exit.PARSE_ERROR
