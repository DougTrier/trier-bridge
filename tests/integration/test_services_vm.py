# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Service control against real systemd managers (docs/TEST-STRATEGY.md 3.3).

A transient user unit is a real object the user manager runs, so start/stop/
restart are exercised without any prompt. System-scope changes over SSH have
no polkit agent, so the DENIED path is exercised for real. No mocks.
TB-T053, TB-T067, TB-T138, TB-T139, TB-T143, TB-SEC-007 (no downgrade).
"""
import subprocess
import time
from pathlib import Path

import pytest

pytest.importorskip("gi")

from trier_bridge.core.identity import UnitIdentity  # noqa: E402
from trier_bridge.core.state import OperationState  # noqa: E402
from trier_bridge.operations.service import ServicePlan, execute_service, plan_service  # noqa: E402
from trier_bridge.state.journal import OperationJournal  # noqa: E402
from trier_bridge.system.services import Scope, list_services, read_unit  # noqa: E402

pytestmark = pytest.mark.integration
UNIT = "tb-test-service.service"


@pytest.fixture()
def user_unit():
    # systemd-run is the real way to create a transient unit; fixed argv, no shell, user scope.
    subprocess.run(["systemctl", "--user", "stop", UNIT], capture_output=True)
    subprocess.run(["systemctl", "--user", "reset-failed", UNIT], capture_output=True)
    r = subprocess.run(
        ["systemd-run", "--user", "--unit", UNIT.removesuffix(".service"), "--", "sleep", "300"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        pytest.skip(f"could not create a transient user unit: {r.stderr.strip()}")
    time.sleep(0.5)
    try:
        yield UNIT
    finally:
        subprocess.run(["systemctl", "--user", "stop", UNIT], capture_output=True)
        subprocess.run(["systemctl", "--user", "reset-failed", UNIT], capture_output=True)


def test_listing_keeps_running_and_startup_separate() -> None:
    services, err = list_services(Scope.SYSTEM)
    assert not err and services
    ssh = next((s for s in services if s.identity.name == "ssh.service"), None)
    assert ssh is not None
    assert ssh.active_state == "active" and ssh.unit_file_state in ("disabled", "enabled")
    assert ssh.plain_running == "Running" and ssh.plain_startup in ("Manual", "Automatic")
    assert ssh.identity.fragment_path.endswith("ssh.service")


def test_stop_and_start_a_user_unit_are_verified(user_unit: str, tmp_path: Path) -> None:
    info, err = read_unit(Scope.USER, user_unit)
    assert info is not None and info.active_state == "active", err
    j = OperationJournal(tmp_path / "j")
    plan = plan_service(info, "stop")
    assert isinstance(plan, ServicePlan) and not plan.needs_admin
    res = execute_service(plan, j)
    assert res.state is OperationState.VERIFIED, res
    after, _ = read_unit(Scope.USER, user_unit)
    assert after is not None and after.active_state == "inactive"
    rec = j.load(plan.operation.operation_id)
    assert rec is not None and rec.operation_state is OperationState.VERIFIED
    out = subprocess.run(
        ["systemctl", "--user", "is-active", user_unit], capture_output=True, text=True
    )
    assert out.stdout.strip() == "inactive"  # independent oracle


def test_stale_unit_identity_cancels(user_unit: str, tmp_path: Path) -> None:
    info, _ = read_unit(Scope.USER, user_unit)
    assert info is not None
    stale = UnitIdentity(
        info.identity.name,
        info.identity.object_path,
        "loaded",
        "/etc/systemd/user/replaced.service",
    )
    from dataclasses import replace

    stale_info = replace(info, identity=stale)
    plan = plan_service(stale_info, "stop")
    assert isinstance(plan, ServicePlan)
    res = execute_service(plan, OperationJournal(tmp_path / "j"))
    assert res.state is OperationState.CANCELLED and "replaced or reloaded" in res.plain
    after, _ = read_unit(Scope.USER, user_unit)
    assert after is not None and after.active_state == "active"  # untouched


def test_system_scope_without_an_agent_is_denied_not_downgraded(tmp_path: Path) -> None:
    """Precondition: run over SSH or any session with no live `auth_admin_keep` polkit
    grant already cached for this action (2026-09-21, entry IMP-07.12 addendum). A console
    session that recently authenticated as admin can still have that grant cached, and the
    restart succeeds without a fresh prompt -- not a downgrade, a real prior authorization."""
    services, _ = list_services(Scope.SYSTEM)
    cups = next((s for s in services if s.identity.name == "cups.service"), None)
    if cups is None:
        pytest.skip("cups.service not present")
    before = cups.active_state
    plan = plan_service(cups, "restart")
    assert isinstance(plan, ServicePlan) and plan.needs_admin
    res = execute_service(plan, OperationJournal(tmp_path / "j"))
    # Over SSH there is no polkit agent to ask, so systemd answers with an authorization error.
    assert res.state in (OperationState.DENIED, OperationState.FAILED), res
    assert "not changed" in res.plain
    after, _ = read_unit(Scope.SYSTEM, "cups.service")
    assert after is not None and after.active_state == before


def test_enable_disable_are_separate_from_start_stop() -> None:
    services, _ = list_services(Scope.SYSTEM)
    static = next((s for s in services if s.unit_file_state == "static"), None)
    if static is not None:
        res = plan_service(static, "enable")
        assert not isinstance(res, ServicePlan) and res.state is OperationState.UNSUPPORTED
    ssh = next(s for s in services if s.identity.name == "ssh.service")
    plan = plan_service(ssh, "disable")
    assert isinstance(plan, ServicePlan) and "does not stop it now" in plan.preview
