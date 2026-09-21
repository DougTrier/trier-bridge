# Copyright 2026 Doug Trier
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Typed operations and results (docs/SECURITY.md section 4.4, SCOPE-06 seed).

An Operation is the authority for what will happen. Windows syntax, a menu
click, or a PowerShell cmdlet are only ways to request one. Operations are
data: no method here touches the system. Execution lives in adapters that
accept an Operation and return an OperationResult.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Mapping

from .identity import StableIdentity
from .state import (
    AuthorizationState,
    OperationState,
    PrivilegeClass,
    SystemChange,
    transition,
)


@dataclass(frozen=True)
class Operation:
    """One intended system action with a stable target and an explicit class."""

    kind: str  # dotted vocabulary, e.g. "process.terminate", "service.restart"
    target: StableIdentity | None
    privilege: PrivilegeClass
    parameters: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    operation_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_monotonic: float = field(default_factory=time.monotonic)
    created_wall: float = field(default_factory=time.time)
    state: OperationState = OperationState.DRAFT
    authorization: AuthorizationState = AuthorizationState.REQUIRED
    preview: str = ""

    def __post_init__(self) -> None:
        if not self.kind or " " in self.kind or self.kind != self.kind.lower():
            raise ValueError(f"operation kind must be lowercase dotted vocabulary: {self.kind!r}")
        if not isinstance(self.parameters, MappingProxyType):
            object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
        if not self.privilege.requires_authorization and self.authorization is (
            AuthorizationState.REQUIRED
        ):
            object.__setattr__(self, "authorization", AuthorizationState.NOT_REQUIRED)

    def with_state(self, new: OperationState) -> "Operation":
        """Return a copy in ``new`` state; the state machine decides legality."""
        return replace(self, state=transition(self.state, new))

    def with_preview(self, text: str) -> "Operation":
        return replace(self, preview=text, state=transition(self.state, OperationState.PREVIEWED))

    def with_authorization(self, auth: AuthorizationState) -> "Operation":
        op = replace(self, authorization=auth)
        if auth is AuthorizationState.GRANTED or auth is AuthorizationState.NOT_REQUIRED:
            return op.with_state(OperationState.AUTHORIZED)
        if auth is AuthorizationState.DENIED:
            return op.with_state(OperationState.DENIED)
        if auth in (AuthorizationState.CANCELLED, AuthorizationState.EXPIRED):
            return op.with_state(OperationState.CANCELLED)
        if auth is AuthorizationState.UNAVAILABLE:
            return op.with_state(OperationState.UNSUPPORTED)
        return op

    @property
    def may_execute(self) -> bool:
        return (
            self.privilege.may_execute
            and self.state is OperationState.AUTHORIZED
            and self.authorization.permits_execution
        )


@dataclass(frozen=True)
class OperationResult:
    """Structured outcome. ``plain`` must be readable without Linux knowledge (TB-INV-078)."""

    operation_id: str
    state: OperationState
    plain: str
    technical: str = ""
    safest_next_step: str = ""
    succeeded: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    pending: tuple[str, ...] = ()
    verification_note: str = ""

    def __post_init__(self) -> None:
        if not self.state.is_terminal:
            raise ValueError(f"a result must be terminal, got {self.state.value}")
        if self.state is OperationState.PARTIAL and not (self.succeeded or self.failed):
            raise ValueError("PARTIAL results must enumerate succeeded and failed steps")

    @property
    def changed(self) -> SystemChange:
        return self.state.system_change

    def three_answers(self) -> dict[str, str]:
        """The three questions every failed action must answer (docs/EXPERIENCE.md section 5)."""
        what_changed = {
            SystemChange.NO: "Nothing was changed.",
            SystemChange.YES: "The change was made.",
            SystemChange.PARTIAL: "Some of the change was made.",
            SystemChange.UNKNOWN: "It is not certain whether anything changed.",
        }[self.changed]
        if self.state is OperationState.VERIFIED:
            what_changed = "The change was made and verified."
        return {
            "Did anything change?": what_changed,
            "What stopped it?": self.plain if not self.state.is_success else "Nothing.",
            "What is the safest next step?": self.safest_next_step or "No action is needed.",
        }
