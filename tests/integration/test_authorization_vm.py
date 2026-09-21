# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""IMP-06.07: grant, cancel, and backend-restart paths for polkit-mediated service control.

Runs in the VM. The polkit prompts are answered by a real agent registered
for this session (tests/integration/polkit_agent.py); the grant path needs the
test account's password in TRIER_BRIDGE_TEST_PASSWORD and is skipped otherwise.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

gi = pytest.importorskip("gi")

from trier_bridge.core.state import OperationState  # noqa: E402
from trier_bridge.operations.service import ServicePlan, execute_service, plan_service  # noqa: E402
from trier_bridge.state.journal import OperationJournal  # noqa: E402
from trier_bridge.system.services import Scope, list_services, read_unit  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from polkit_agent import PolkitTestAgent  # noqa: E402

pytestmark = pytest.mark.integration
SYSTEM_UNIT = "tb-test-system.service"
USER_UNIT = "tb-test-service.service"


def _sudo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["sudo", "-n", *args], capture_output=True, text=True)


@pytest.fixture()
def system_unit():
    """A transient system unit, the harmless target for a privileged stop."""
    _sudo("systemctl", "stop", SYSTEM_UNIT)
    _sudo("systemctl", "reset-failed", SYSTEM_UNIT)
    r = _sudo("systemd-run", "--unit", SYSTEM_UNIT.removesuffix(".service"), "--", "sleep", "300")
    if r.returncode != 0:
        pytest.skip(f"could not create a transient system unit: {r.stderr.strip()}")
    time.sleep(0.5)
    try:
        yield SYSTEM_UNIT
    finally:
        _sudo("systemctl", "stop", SYSTEM_UNIT)
        _sudo("systemctl", "reset-failed", SYSTEM_UNIT)


@pytest.fixture()
def user_unit():
    subprocess.run(["systemctl", "--user", "stop", USER_UNIT], capture_output=True)
    subprocess.run(["systemctl", "--user", "reset-failed", USER_UNIT], capture_output=True)
    r = subprocess.run(
        [
            "systemd-run",
            "--user",
            "--unit",
            USER_UNIT.removesuffix(".service"),
            "--",
            "sleep",
            "300",
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        pytest.skip(f"could not create a transient user unit: {r.stderr.strip()}")
    time.sleep(0.5)
    try:
        yield USER_UNIT
    finally:
        subprocess.run(["systemctl", "--user", "stop", USER_UNIT], capture_output=True)
        subprocess.run(["systemctl", "--user", "reset-failed", USER_UNIT], capture_output=True)


def test_dismissed_prompt_changes_nothing(tmp_path: Path) -> None:
    """TB-T126/TB-INV-127: a dismissed prompt is reported and the unit is untouched."""
    services, _ = list_services(Scope.SYSTEM)
    cups = next((s for s in services if s.identity.name == "cups.service"), None)
    if cups is None:
        pytest.skip("cups.service not present")
    before = cups.active_state
    plan = plan_service(cups, "restart")
    assert isinstance(plan, ServicePlan) and plan.needs_admin
    with PolkitTestAgent("cancel") as agent:
        res = execute_service(plan, OperationJournal(tmp_path / "j"))
    assert agent.prompts == ["org.freedesktop.systemd1.manage-units"], agent.prompts
    # systemd reports a dismissed polkit prompt as an authorization error; either way the
    # product says so in plain words and does nothing else.
    assert res.state in (OperationState.CANCELLED, OperationState.DENIED), res
    assert "not changed" in res.plain
    after, _ = read_unit(Scope.SYSTEM, "cups.service")
    assert after is not None and after.active_state == before


def test_granted_prompt_stops_a_system_unit_and_verifies(system_unit: str, tmp_path: Path) -> None:
    """TB-T109/TB-T110: authorization granted through polkit for this one action; verified."""
    password = os.environ.get("TRIER_BRIDGE_TEST_PASSWORD", "")
    if not password:
        pytest.skip("TRIER_BRIDGE_TEST_PASSWORD not set; the grant path needs the account password")
    info, err = read_unit(Scope.SYSTEM, system_unit)
    assert info is not None, err
    assert info.active_state == "active"
    plan = plan_service(info, "stop")
    assert isinstance(plan, ServicePlan) and plan.needs_admin
    journal = OperationJournal(tmp_path / "j")
    with PolkitTestAgent("grant", password) as agent:
        res = execute_service(plan, journal)
    assert agent.prompts == ["org.freedesktop.systemd1.manage-units"], agent.prompts
    assert any(line.startswith("SUCCESS") for line in agent.helper_results), agent.helper_results
    assert res.state is OperationState.VERIFIED, res
    after, _ = read_unit(Scope.SYSTEM, system_unit)
    assert after is not None and after.active_state in ("inactive", "deactivating"), after
    # the product itself never became root: it asked, Linux decided, systemd acted
    assert os.geteuid() != 0
    assert journal.unresolved() == []


def test_user_manager_reexec_between_read_and_execute(user_unit: str, tmp_path: Path) -> None:
    """TB-T053: the backend restarting under us is survived; identity is revalidated live."""
    info, err = read_unit(Scope.USER, user_unit)
    assert info is not None, err
    r = subprocess.run(["systemctl", "--user", "daemon-reexec"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    time.sleep(1.0)
    plan = plan_service(info, "stop")
    assert isinstance(plan, ServicePlan)
    res = execute_service(plan, OperationJournal(tmp_path / "j"))
    assert res.state is OperationState.VERIFIED, res
    after, _ = read_unit(Scope.USER, user_unit)
    assert after is not None and after.active_state in ("inactive", "deactivating")
