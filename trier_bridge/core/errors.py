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
"""Semantically distinct errors (docs/CODE-QUALITY.md section 9, "Errors").

Each error carries a plain-language explanation and, separately, technical
detail. The plain text must be understandable without Linux knowledge and
must say whether anything changed (TB-INV-078, TB-INV-192).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .state import SystemChange


@dataclass(eq=False)
class TrierBridgeError(Exception):
    plain: str
    technical: str = ""
    changed: SystemChange = SystemChange.NO
    safest_next_step: str = ""
    details: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__init__(self.plain)

    def __str__(self) -> str:
        return self.plain


class PermissionDenied(TrierBridgeError):
    """Linux or polkit said no. Nothing changed. Never routed around (TB-SEC-007)."""


class Unsupported(TrierBridgeError):
    """No qualified adapter route exists on this machine (TB-INV-005)."""


class UnknownCapability(TrierBridgeError):
    """Discovery could not establish support; Unknown is not Unsupported (TB-INV-035)."""


class NoFaithfulEquivalent(TrierBridgeError):
    """A Windows concept with no faithful Linux counterpart; educational only (TB-INV-105)."""


class Busy(TrierBridgeError):
    """A lock or in-use condition; recoverable by waiting, never by killing (TB-INV-170)."""


class StaleTarget(TrierBridgeError):
    """The target changed between preview and execution; cancelled, not retargeted (TB-SEC-021)."""


class InvalidInput(TrierBridgeError):
    """Parse or validation failure at a trust boundary; no operation was performed."""


class PartialCompletion(TrierBridgeError):
    """Some steps succeeded and some did not; both lists are required (TB-INV-193)."""

    def __init__(
        self,
        plain: str,
        succeeded: tuple[str, ...],
        failed: tuple[str, ...],
        pending: tuple[str, ...] = (),
        technical: str = "",
        safest_next_step: str = "",
    ) -> None:
        super().__init__(
            plain=plain,
            technical=technical,
            changed=SystemChange.PARTIAL,
            safest_next_step=safest_next_step,
            details={
                "succeeded": ", ".join(succeeded),
                "failed": ", ".join(failed),
                "pending": ", ".join(pending),
            },
        )
        self.succeeded = succeeded
        self.failed = failed
        self.pending = pending


class VerificationFailed(TrierBridgeError):
    """The operation was dispatched but the expected postcondition was not observed (TB-INV-006)."""

    def __init__(self, plain: str, technical: str = "", safest_next_step: str = "") -> None:
        super().__init__(
            plain=plain,
            technical=technical,
            changed=SystemChange.UNKNOWN,
            safest_next_step=safest_next_step,
        )


class RecoveryRequired(TrierBridgeError):
    """The system is in an explicit, recoverable degraded state (TB-SEC-025)."""

    def __init__(self, plain: str, technical: str = "", safest_next_step: str = "") -> None:
        super().__init__(
            plain=plain,
            technical=technical,
            changed=SystemChange.UNKNOWN,
            safest_next_step=safest_next_step,
        )
