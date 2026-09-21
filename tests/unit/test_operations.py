# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T006/TB-T055/TB-T078/TB-T192/TB-T193: operations are typed data with truthful results."""
import pytest

from trier_bridge.core.identity import ProcessIdentity
from trier_bridge.core.operations import Operation, OperationResult
from trier_bridge.core.state import AuthorizationState, OperationState, PrivilegeClass, SystemChange


def _terminate() -> Operation:
    return Operation(
        kind="process.terminate",
        target=ProcessIdentity(pid=4271, start_ticks=1, uid=1000, comm="app"),
        privilege=PrivilegeClass.B_USER_MUTATION,
        parameters={"signal": "TERM"},
    )


def test_operation_is_immutable_typed_data() -> None:
    op = _terminate()
    assert op.state is OperationState.DRAFT
    assert op.authorization is AuthorizationState.NOT_REQUIRED  # class B needs no admin auth
    with pytest.raises(TypeError):
        op.parameters["signal"] = "KILL"  # type: ignore[index]
    assert len(op.operation_id) == 32


def test_kind_vocabulary_is_validated() -> None:
    with pytest.raises(ValueError):
        Operation(kind="Terminate Process", target=None, privilege=PrivilegeClass.A_READ_ONLY)


def test_lifecycle_through_state_machine() -> None:
    op = _terminate().with_preview("End app (PID 4271)?")
    assert op.state is OperationState.PREVIEWED
    op = op.with_authorization(AuthorizationState.NOT_REQUIRED)
    assert op.state is OperationState.AUTHORIZED and op.may_execute


def test_denied_authorization_terminates_without_execution() -> None:
    op = Operation(kind="service.restart", target=None, privilege=PrivilegeClass.C_ADMIN_MUTATION)
    op = op.with_preview("Restart a service").with_authorization(AuthorizationState.DENIED)
    assert op.state is OperationState.DENIED and not op.may_execute
    assert op.state.system_change is SystemChange.NO


def test_class_e_can_never_execute() -> None:
    op = Operation(kind="registry.edit", target=None, privilege=PrivilegeClass.E_NO_EQUIVALENT)
    op = op.with_preview("No faithful equivalent").with_authorization(
        AuthorizationState.NOT_REQUIRED
    )
    assert not op.may_execute


def test_result_must_be_terminal() -> None:
    with pytest.raises(ValueError):
        OperationResult(operation_id="x", state=OperationState.EXECUTING, plain="still running")


def test_partial_result_must_enumerate() -> None:
    with pytest.raises(ValueError):
        OperationResult(operation_id="x", state=OperationState.PARTIAL, plain="half done")
    r = OperationResult(
        operation_id="x",
        state=OperationState.PARTIAL,
        plain="The service stopped but did not start again.",
        succeeded=("stop",),
        failed=("start",),
        safest_next_step="Start the service again from Services.",
    )
    answers = r.three_answers()
    assert answers["Did anything change?"] == "Some of the change was made."
    assert "stopped" in answers["What stopped it?"]
    assert answers["What is the safest next step?"].startswith("Start")


def test_verified_result_answers_plainly() -> None:
    r = OperationResult(operation_id="x", state=OperationState.VERIFIED, plain="Restarted.")
    a = r.three_answers()
    assert a["Did anything change?"] == "The change was made and verified."
    assert a["What stopped it?"] == "Nothing."


def test_unknown_outcome_is_first_class() -> None:
    r = OperationResult(
        operation_id="x",
        state=OperationState.OUTCOME_UNKNOWN,
        plain="Lost contact with the service manager.",
        safest_next_step="Check Services after a moment.",
    )
    assert r.changed is SystemChange.UNKNOWN
    assert "not certain" in r.three_answers()["Did anything change?"]
