# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T004/TB-T035/TB-T057/TB-T183/TB-T193/TB-T194: state vocabulary and transitions."""
import pytest

from trier_bridge.core.state import (
    AuthorizationState,
    CapabilityState,
    InvalidTransition,
    OperationState,
    PrivilegeClass,
    SystemChange,
    transition,
)


def test_states_are_distinct_and_named() -> None:
    values = {s.value for s in OperationState}
    assert len(values) == len(OperationState) == 14
    assert {"unsupported", "denied", "cancelled", "failed", "partial", "outcome_unknown"} <= values


def test_only_verified_is_success() -> None:
    assert OperationState.VERIFIED.is_success
    assert not OperationState.COMMITTED.is_success  # dispatched is not done (TB-INV-006)
    assert not OperationState.PARTIAL.is_success


def test_partial_is_not_success_and_reports_partial_change() -> None:
    assert OperationState.PARTIAL.system_change is SystemChange.PARTIAL
    assert OperationState.OUTCOME_UNKNOWN.system_change is SystemChange.UNKNOWN
    assert OperationState.DENIED.system_change is SystemChange.NO


def test_happy_path_transitions() -> None:
    s = OperationState.DRAFT
    for nxt in (
        OperationState.PREVIEWED,
        OperationState.AUTHORIZED,
        OperationState.EXECUTING,
        OperationState.COMMITTED,
        OperationState.VERIFYING,
        OperationState.VERIFIED,
    ):
        s = transition(s, nxt)
    assert s is OperationState.VERIFIED and s.is_terminal


def test_cancel_after_execution_started_is_forbidden() -> None:
    # Cancellation has a boundary: once executing, the outcome is FAILED/PARTIAL/UNKNOWN (TB-INV-057)
    with pytest.raises(InvalidTransition):
        transition(OperationState.EXECUTING, OperationState.CANCELLED)


def test_terminal_states_cannot_move() -> None:
    with pytest.raises(InvalidTransition):
        transition(OperationState.VERIFIED, OperationState.DRAFT)
    with pytest.raises(InvalidTransition):
        transition(OperationState.DENIED, OperationState.AUTHORIZED)


def test_committed_cannot_skip_verification_to_verified() -> None:
    with pytest.raises(InvalidTransition):
        transition(OperationState.COMMITTED, OperationState.VERIFIED)


def test_capability_only_supported_allows_mutation() -> None:
    assert CapabilityState.SUPPORTED.allows_mutation
    for s in (
        CapabilityState.UNKNOWN,
        CapabilityState.DEGRADED,
        CapabilityState.ERROR,
        CapabilityState.UNSUPPORTED,
    ):
        assert not s.allows_mutation


def test_authorization_permits_execution() -> None:
    assert AuthorizationState.GRANTED.permits_execution
    assert AuthorizationState.NOT_REQUIRED.permits_execution
    for s in (
        AuthorizationState.DENIED,
        AuthorizationState.CANCELLED,
        AuthorizationState.EXPIRED,
        AuthorizationState.REQUESTED,
    ):
        assert not s.permits_execution


def test_privilege_classes() -> None:
    assert not PrivilegeClass.A_READ_ONLY.requires_authorization
    assert PrivilegeClass.C_ADMIN_MUTATION.requires_authorization
    assert not PrivilegeClass.E_NO_EQUIVALENT.may_execute  # educational only (TB-INV-105)
    assert not PrivilegeClass.D_HIGH_RISK.may_execute  # deferred in the first release
