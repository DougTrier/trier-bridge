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
"""Stable target identities (docs/PRIVILEGE-MODEL.md section 4).

INVARIANT: presentation values alone (PID, /dev/sdX, list position, display
name) are never sufficient identity (TB-INV-049). Every identity here carries
the extra facts needed to detect that the target was replaced, and
``same_target`` is the one place that comparison is decided.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class StableIdentity(Protocol):
    """Anything that can be revalidated immediately before mutation (TB-INV-121)."""

    @property
    def kind(self) -> str: ...

    def same_target(self, other: object) -> bool: ...

    def label(self) -> str: ...


@dataclass(frozen=True)
class ProcessIdentity:
    """PID plus start time: a reused PID has a different start time (TB-INV-050)."""

    pid: int
    start_ticks: int
    uid: int
    exe: str = ""
    comm: str = ""

    @property
    def kind(self) -> str:
        return "process"

    def same_target(self, other: object) -> bool:
        return (
            isinstance(other, ProcessIdentity)
            and other.pid == self.pid
            and other.start_ticks == self.start_ticks
            and other.uid == self.uid
        )

    def label(self) -> str:
        return f"{self.comm or self.exe or 'process'} (PID {self.pid})"


@dataclass(frozen=True)
class UnitIdentity:
    """systemd unit name plus object path plus the load/unit-file generation seen at preview."""

    name: str
    object_path: str
    load_state: str = ""
    fragment_path: str = ""

    @property
    def kind(self) -> str:
        return "service"

    def same_target(self, other: object) -> bool:
        return (
            isinstance(other, UnitIdentity)
            and other.name == self.name
            and other.object_path == self.object_path
            and other.fragment_path == self.fragment_path
        )

    def label(self) -> str:
        return self.name


@dataclass(frozen=True)
class ConnectionIdentity:
    """NetworkManager connection UUID plus the settings Version (TB-INV-052)."""

    uuid: str
    interface: str = ""
    version: int = 0

    @property
    def kind(self) -> str:
        return "network-connection"

    def same_target(self, other: object) -> bool:
        return (
            isinstance(other, ConnectionIdentity)
            and other.uuid == self.uuid
            and other.version == self.version
        )

    def label(self) -> str:
        return f"{self.interface or 'connection'} ({self.uuid[:8]})"


@dataclass(frozen=True)
class BlockDeviceIdentity:
    """udisks2 object plus drive serial/size plus filesystem UUID, never /dev/sdX alone.

    TB-INV-158.
    """

    object_path: str
    drive_id: str = ""
    serial: str = ""
    size: int = 0
    fs_uuid: str = ""
    device_node: str = ""

    @property
    def kind(self) -> str:
        return "block-device"

    def same_target(self, other: object) -> bool:
        if not isinstance(other, BlockDeviceIdentity):
            return False
        strong = (self.drive_id or self.serial or self.fs_uuid) != ""
        if not strong:
            # Without a strong identifier we refuse to call two observations the same target.
            return False
        return (
            other.object_path == self.object_path
            and other.drive_id == self.drive_id
            and other.serial == self.serial
            and other.size == self.size
            and other.fs_uuid == self.fs_uuid
        )

    def label(self) -> str:
        return self.device_node or self.object_path.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class PackageIdentity:
    """Packaging system plus source plus name/version/arch (TB-INV-165)."""

    system: str  # "apt", "snap", "flatpak", ...
    name: str
    version: str = ""
    arch: str = ""
    source: str = ""

    @property
    def kind(self) -> str:
        return "package"

    def same_target(self, other: object) -> bool:
        return (
            isinstance(other, PackageIdentity)
            and other.system == self.system
            and other.name == self.name
            and other.version == self.version
            and other.arch == self.arch
            and other.source == self.source
        )

    def label(self) -> str:
        return f"{self.name} ({self.system})"
