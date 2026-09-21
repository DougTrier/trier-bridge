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
"""Capability and environment records (docs/PLATFORMS.md sections 2 and 6).

Every record says where its evidence came from and when it was observed,
so a consumer can decide whether revalidation is required (TB-INV-037).
Stale records never authorize mutation; there is no mutation here anyway.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, unique

from ..core.state import CapabilityState, PrivilegeClass

DEFAULT_TTL_SECONDS = 60.0


@unique
class Capability(Enum):
    """The subsystems Trier Bridge needs to know about on the first target."""

    SERVICE_MANAGER = "service-manager"
    NETWORK_MANAGER = "network-manager"
    STORAGE = "storage"
    PACKAGES_NATIVE = "packages-native"
    PACKAGES_SNAP = "packages-snap"
    PACKAGES_FLATPAK = "packages-flatpak"
    PACKAGEKIT = "packagekit"
    AUTHORIZATION = "authorization"
    SESSION_MANAGER = "session-manager"
    JOURNAL = "journal"
    PRINTING = "printing"
    BLUETOOTH = "bluetooth"
    POWER = "power"
    PORTALS = "desktop-portals"
    SHELL = "desktop-shell"
    PROCESSES = "processes"


@dataclass(frozen=True)
class CapabilityRecord:
    capability: Capability
    state: CapabilityState
    backend: str = ""
    version: str = ""
    evidence: str = (
        ""  # where the fact came from, e.g. "system bus org.freedesktop.systemd1 Version"
    )
    detail: str = ""  # plain-language note or the structured error text
    read_operations: tuple[str, ...] = ()
    mutation_operations: tuple[str, ...] = ()
    privilege: PrivilegeClass = PrivilegeClass.A_READ_ONLY
    limitations: tuple[str, ...] = ()
    observed_monotonic: float = field(default_factory=time.monotonic)
    observed_wall: float = field(default_factory=time.time)

    def is_fresh(
        self, now_monotonic: float | None = None, ttl: float = DEFAULT_TTL_SECONDS
    ) -> bool:
        now = time.monotonic() if now_monotonic is None else now_monotonic
        return (now - self.observed_monotonic) <= ttl

    @property
    def plain_state(self) -> str:
        """User-facing word. Never collapses Unknown into Off or Denied into Unsupported."""
        return {
            CapabilityState.SUPPORTED: "Available",
            CapabilityState.DEGRADED: "Partly available",
            CapabilityState.UNSUPPORTED: "Not available on this computer",
            CapabilityState.UNKNOWN: "Unknown",
            CapabilityState.ERROR: "Could not be checked",
        }[self.state]


@dataclass(frozen=True)
class EnvironmentProfile:
    """The facts a support claim must bind to (docs/PLATFORMS.md section 2)."""

    distro_id: str = ""  # "ubuntu"; empty means unknown
    distro_version: str = ""  # "24.04"
    distro_name: str = ""  # PRETTY_NAME
    distro_like: tuple[str, ...] = ()  # ID_LIKE, e.g. ("debian",)
    architecture: str = ""  # "x86_64"
    kernel: str = ""
    virtualization: str = ""  # "microsoft", "kvm", "none", "" unknown
    session_type: str = ""  # "wayland", "x11", "tty", "" unknown
    session_class: str = ""  # "user", "greeter", ...
    session_remote: bool | None = None
    session_active: bool | None = None
    desktop: str = ""  # XDG_CURRENT_DESKTOP, e.g. "ubuntu:GNOME"
    hostname: str = ""
    user_id: int = -1
    user_name: str = ""
    groups: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()  # one line per source read
    observed_wall: float = field(default_factory=time.time)

    @property
    def is_known_distro(self) -> bool:
        return bool(self.distro_id)

    @property
    def is_graphical_local_session(self) -> bool | None:
        """True for a local Wayland/X11 user session; None when facts are missing (TB-INV-023)."""
        if not self.session_type or self.session_remote is None:
            return None
        return self.session_type in ("wayland", "x11") and not self.session_remote

    def summary_lines(self) -> list[str]:
        """Plain facts for the System Information view; blanks are shown as Unknown."""

        def show(v: object) -> str:
            if v is None or v == "" or v == ():
                return "Unknown"
            if isinstance(v, bool):
                return "Yes" if v else "No"
            if isinstance(v, tuple):
                return ", ".join(str(x) for x in v)
            return str(v)

        return [
            f"Operating system: {show(self.distro_name or self.distro_id)}",
            f"Version: {show(self.distro_version)}",
            f"Based on: {show(self.distro_like)}",
            f"Architecture: {show(self.architecture)}",
            f"Kernel: {show(self.kernel)}",
            f"Virtual machine: {show(self.virtualization or None)}",
            f"Session: {show(self.session_type)} ({show(self.session_class)})",
            f"Remote session: {show(self.session_remote)}",
            f"Desktop: {show(self.desktop)}",
            f"Computer name: {show(self.hostname)}",
            f"User: {show(self.user_name)}",
        ]
