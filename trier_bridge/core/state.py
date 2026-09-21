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
"""State vocabularies (docs/STATE-AND-PERSISTENCE.md sections 2 to 7).

INVARIANT: these enums are the canonical distinct states. Nothing collapses
Unknown into Off, Denied into Unsupported, Partial into Success, Committed
into Verified, or missing permission into Empty (TB-INV-004, TB-INV-035,
TB-INV-183, TB-INV-193, TB-INV-194).
"""
from __future__ import annotations

from enum import Enum, unique


@unique
class CapabilityState(Enum):
    """What an adapter can truthfully claim about one operation on this machine."""

    UNKNOWN = "unknown"
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    DEGRADED = "degraded"
    ERROR = "error"

    @property
    def allows_mutation(self) -> bool:
        """Only SUPPORTED may mutate; DEGRADED may read; UNKNOWN never defaults to SUPPORTED."""
        return self is CapabilityState.SUPPORTED


@unique
class AuthorizationState(Enum):
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    REQUESTED = "requested"
    GRANTED = "granted"
    DENIED = "denied"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    UNAVAILABLE = "unavailable"

    @property
    def permits_execution(self) -> bool:
        return self in (AuthorizationState.NOT_REQUIRED, AuthorizationState.GRANTED)


@unique
class SystemChange(Enum):
    """Answer to the first question every result must answer: did anything change?"""

    NO = "no"
    YES = "yes"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@unique
class OperationState(Enum):
    DRAFT = "draft"
    PREVIEWED = "previewed"
    AUTHORIZED = "authorized"
    EXECUTING = "executing"
    COMMITTED = "committed"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    # alternate terminal states
    UNSUPPORTED = "unsupported"
    DENIED = "denied"
    CANCELLED = "cancelled"
    FAILED = "failed"
    PARTIAL = "partial"
    OUTCOME_UNKNOWN = "outcome_unknown"
    RECOVERY_REQUIRED = "recovery_required"

    @property
    def is_terminal(self) -> bool:
        return self in _TERMINAL

    @property
    def is_success(self) -> bool:
        """Only VERIFIED is success. COMMITTED is not (TB-INV-006)."""
        return self is OperationState.VERIFIED

    @property
    def system_change(self) -> SystemChange:
        return _CHANGE[self]


_TERMINAL = frozenset(
    {
        OperationState.VERIFIED,
        OperationState.UNSUPPORTED,
        OperationState.DENIED,
        OperationState.CANCELLED,
        OperationState.FAILED,
        OperationState.PARTIAL,
        OperationState.OUTCOME_UNKNOWN,
        OperationState.RECOVERY_REQUIRED,
    }
)

_CHANGE: dict[OperationState, SystemChange] = {
    OperationState.DRAFT: SystemChange.NO,
    OperationState.PREVIEWED: SystemChange.NO,
    OperationState.AUTHORIZED: SystemChange.NO,
    OperationState.EXECUTING: SystemChange.UNKNOWN,
    OperationState.COMMITTED: SystemChange.YES,
    OperationState.VERIFYING: SystemChange.YES,
    OperationState.VERIFIED: SystemChange.YES,
    OperationState.UNSUPPORTED: SystemChange.NO,
    OperationState.DENIED: SystemChange.NO,
    OperationState.CANCELLED: SystemChange.NO,
    OperationState.FAILED: SystemChange.UNKNOWN,
    OperationState.PARTIAL: SystemChange.PARTIAL,
    OperationState.OUTCOME_UNKNOWN: SystemChange.UNKNOWN,
    OperationState.RECOVERY_REQUIRED: SystemChange.UNKNOWN,
}

# Allowed transitions (docs/STATE-AND-PERSISTENCE.md section 4). Cancellation
# has a defined boundary: before commit it yields CANCELLED; once EXECUTING has
# started, cancel resolves to FAILED, PARTIAL, or OUTCOME_UNKNOWN, never a
# false CANCELLED (TB-INV-057, TB-INV-195).
_TRANSITIONS: dict[OperationState, frozenset[OperationState]] = {
    OperationState.DRAFT: frozenset(
        {OperationState.PREVIEWED, OperationState.UNSUPPORTED, OperationState.CANCELLED}
    ),
    OperationState.PREVIEWED: frozenset(
        {
            OperationState.AUTHORIZED,
            OperationState.DENIED,
            OperationState.CANCELLED,
            OperationState.UNSUPPORTED,
            OperationState.FAILED,
        }
    ),
    OperationState.AUTHORIZED: frozenset(
        {OperationState.EXECUTING, OperationState.CANCELLED, OperationState.FAILED}
    ),
    OperationState.EXECUTING: frozenset(
        {
            OperationState.COMMITTED,
            OperationState.FAILED,
            OperationState.PARTIAL,
            OperationState.OUTCOME_UNKNOWN,
        }
    ),
    OperationState.COMMITTED: frozenset(
        {OperationState.VERIFYING, OperationState.OUTCOME_UNKNOWN, OperationState.RECOVERY_REQUIRED}
    ),
    OperationState.VERIFYING: frozenset(
        {
            OperationState.VERIFIED,
            OperationState.PARTIAL,
            OperationState.OUTCOME_UNKNOWN,
            OperationState.RECOVERY_REQUIRED,
        }
    ),
}


class InvalidTransition(ValueError):
    """Raised when an operation would move between states the model forbids."""


def transition(current: OperationState, new: OperationState) -> OperationState:
    """Return ``new`` if the move is allowed, else raise InvalidTransition."""
    if current.is_terminal:
        raise InvalidTransition(f"{current.value} is terminal; cannot move to {new.value}")
    if new not in _TRANSITIONS[current]:
        raise InvalidTransition(f"{current.value} -> {new.value} is not allowed")
    return new


@unique
class RecoveryState(Enum):
    NO_RECOVERY_NEEDED = "no_recovery_needed"
    RECOVERY_AVAILABLE = "recovery_available"
    RECOVERY_IN_PROGRESS = "recovery_in_progress"
    RECOVERY_FAILED = "recovery_failed"
    NEEDS_REVIEW = "needs_review"


@unique
class SettingState(Enum):
    """Desired versus actual for settings Trier Bridge owns (section 6)."""

    DESIRED = "desired"
    PENDING = "pending"
    DURABLE = "durable"
    EFFECTIVE = "effective"
    FAILED = "failed"


@unique
class PrivilegeClass(Enum):
    """Windows-command / operation security classes (docs/SECURITY.md section 10)."""

    A_READ_ONLY = "A"
    B_USER_MUTATION = "B"
    C_ADMIN_MUTATION = "C"
    D_HIGH_RISK = "D"
    E_NO_EQUIVALENT = "E"

    @property
    def requires_authorization(self) -> bool:
        return self in (PrivilegeClass.C_ADMIN_MUTATION, PrivilegeClass.D_HIGH_RISK)

    @property
    def may_execute(self) -> bool:
        """Class E is educational only (TB-INV-105); class D is deferred in the first release."""
        return self in (
            PrivilegeClass.A_READ_ONLY,
            PrivilegeClass.B_USER_MUTATION,
            PrivilegeClass.C_ADMIN_MUTATION,
        )
