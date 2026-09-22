# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T136: plan_service refuses session-critical user units before any D-Bus call is made."""
import pytest

from trier_bridge.core.identity import UnitIdentity
from trier_bridge.core.operations import OperationResult

gi = pytest.importorskip("gi")

from trier_bridge.operations.service import (  # noqa: E402
    ServicePlan,
    is_session_critical_user_unit,
    plan_service,
)
from trier_bridge.system.services import Scope, ServiceInfo  # noqa: E402


def _service(name: str, scope: Scope) -> ServiceInfo:
    return ServiceInfo(
        identity=UnitIdentity(name=name, object_path=f"/org/freedesktop/systemd1/unit/{name}"),
        scope=scope,
        description="test unit",
        active_state="active",
        sub_state="running",
        unit_file_state="enabled",
        can_start=True,
        can_stop=True,
        can_reload=True,
    )


def test_session_critical_user_units_are_named_correctly() -> None:
    assert is_session_critical_user_unit("dbus.service")
    assert is_session_critical_user_unit("gnome-session-monitor.service")
    assert is_session_critical_user_unit("gnome-session-manager@ubuntu.service")
    assert not is_session_critical_user_unit("gnome-keyring-daemon.service")
    assert not is_session_critical_user_unit("gvfs-daemon.service")


@pytest.mark.parametrize("name", ["dbus.service", "gnome-session-manager@ubuntu.service"])
@pytest.mark.parametrize("verb", ["stop", "restart", "disable"])
def test_plan_service_refuses_session_critical_user_units(name: str, verb: str) -> None:
    res = plan_service(_service(name, Scope.USER), verb)
    assert isinstance(res, OperationResult)
    assert "sign you out" in res.plain
    assert "Nothing was changed" in res.plain


def test_plan_service_still_allows_start_and_ordinary_user_units() -> None:
    # starting a session-critical unit back up isn't refused, only stop/restart/disable
    plan = plan_service(_service("dbus.service", Scope.USER), "start")
    assert isinstance(plan, ServicePlan)
    ordinary = plan_service(_service("gvfs-daemon.service", Scope.USER), "restart")
    assert isinstance(ordinary, ServicePlan)


def test_plan_service_does_not_refuse_the_same_names_at_system_scope() -> None:
    # the protection is specific to the no-polkit-prompt user scope; system-scope dbus.service
    # (a different unit entirely) already goes through polkit and isn't this code's concern
    plan = plan_service(_service("dbus.service", Scope.SYSTEM), "restart")
    assert isinstance(plan, ServicePlan) and plan.needs_admin
