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
"""Disk Management data from udisks2 over D-Bus, read-only.

INVARIANT: physical drive, partition, filesystem, encrypted container, loop
device, and mount are reported as distinct things, never flattened into drive
letters (TB-INV-070, TB-INV-157). Identity is the udisks object plus drive
id/serial/size and filesystem UUID, never /dev/sdX alone (TB-INV-158). Free
space comes from statvfs on the real mount point. Nothing here mounts,
unmounts, or changes anything.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from ..core.identity import BlockDeviceIdentity
from .bus import Bus

UD = "org.freedesktop.UDisks2"
UD_ROOT = "/org/freedesktop/UDisks2"


def _bytes_path(v: Any) -> str:
    """udisks encodes paths as NUL-terminated byte arrays."""
    if isinstance(v, (bytes, bytearray)):
        return bytes(v).rstrip(b"\x00").decode("utf-8", "replace")
    if isinstance(v, (list, tuple)):
        return bytes(int(b) for b in v).rstrip(b"\x00").decode("utf-8", "replace")
    return str(v or "")


@dataclass(frozen=True)
class Volume:
    identity: BlockDeviceIdentity
    device_node: str
    kind: str  # "Partition", "Filesystem", "Encrypted", "Loop", "Whole disk"
    fs_type: str
    label: str
    size_bytes: int | None
    mount_points: tuple[str, ...]
    free_bytes: int | None  # statvfs of the first mount point; None when not mounted or unknown
    partition_number: int | None
    hint_system: bool
    hint_ignore: bool

    @property
    def is_mounted(self) -> bool:
        return bool(self.mount_points)


@dataclass(frozen=True)
class Drive:
    object_path: str
    vendor: str
    model: str
    serial: str
    size_bytes: int | None
    removable: bool
    ejectable: bool
    connection_bus: str
    media_removable: bool
    volumes: tuple[Volume, ...] = field(default_factory=tuple)

    @property
    def display_name(self) -> str:
        return " ".join(x for x in (self.vendor, self.model) if x) or "Drive"


@dataclass(frozen=True)
class StorageOverview:
    available: bool
    detail: str
    drives: tuple[Drive, ...] = field(default_factory=tuple)
    loose_volumes: tuple[Volume, ...] = field(default_factory=tuple)  # loop devices, RAM disks
    hidden_count: int = 0  # HintIgnore volumes (snap loops etc.) not shown by default


def _free_space(mount: str) -> int | None:
    try:
        st = os.statvfs(mount)
        return int(st.f_bavail * st.f_frsize)
    except (OSError, AttributeError):
        return None


def read_storage(bus: Bus | None = None) -> StorageOverview:
    bus = bus or Bus.system()
    if bus.conn is None:
        return StorageOverview(False, f"The system bus is not reachable: {bus.error}")
    if UD not in bus.names() and UD not in bus.activatable():
        return StorageOverview(False, "udisks2 is not present on this computer.")
    objs = bus.managed_objects(UD, UD_ROOT)
    if not objs:
        return StorageOverview(False, "udisks2 did not answer.")
    drives: dict[str, Drive] = {}
    for path, ifaces in objs.items():
        d = ifaces.get(f"{UD}.Drive")
        if d is None:
            continue
        drives[path] = Drive(
            object_path=path,
            vendor=str(d.get("Vendor", "")).strip(),
            model=str(d.get("Model", "")).strip(),
            serial=str(d.get("Serial", "")).strip(),
            size_bytes=int(d["Size"]) if d.get("Size") else None,
            removable=bool(d.get("Removable", False)),
            ejectable=bool(d.get("Ejectable", False)),
            connection_bus=str(d.get("ConnectionBus", "")),
            media_removable=bool(d.get("MediaRemovable", False)),
        )
    by_drive: dict[str, list[Volume]] = {p: [] for p in drives}
    loose: list[Volume] = []
    hidden = 0
    for path, ifaces in objs.items():
        b = ifaces.get(f"{UD}.Block")
        if b is None:
            continue
        hint_ignore = bool(b.get("HintIgnore", False))
        fs = ifaces.get(f"{UD}.Filesystem")
        part = ifaces.get(f"{UD}.Partition")
        mounts = tuple(_bytes_path(m) for m in (fs or {}).get("MountPoints", []))
        if f"{UD}.Encrypted" in ifaces:
            kind = "Encrypted"
        elif f"{UD}.Loop" in ifaces:
            kind = "Loop"
        elif part is not None:
            kind = "Partition"
        elif fs is not None:
            kind = "Filesystem"
        else:
            kind = "Whole disk"
        drive_path = str(b.get("Drive", "/"))
        drv = drives.get(drive_path)
        vol = Volume(
            identity=BlockDeviceIdentity(
                object_path=path,
                drive_id=str(drv.model + ":" + drv.serial) if drv else "",
                serial=drv.serial if drv else "",
                size=int(b.get("Size", 0) or 0),
                fs_uuid=str(b.get("IdUUID", "") or ""),
                device_node=_bytes_path(b.get("Device")),
            ),
            device_node=_bytes_path(b.get("Device")),
            kind=kind,
            fs_type=str(b.get("IdType", "") or ""),
            label=str(b.get("IdLabel", "") or ""),
            size_bytes=int(b["Size"]) if b.get("Size") else None,
            mount_points=mounts,
            free_bytes=_free_space(mounts[0]) if mounts else None,
            partition_number=int(part["Number"]) if part and "Number" in part else None,
            hint_system=bool(b.get("HintSystem", False)),
            hint_ignore=hint_ignore,
        )
        if hint_ignore:
            hidden += 1
            continue
        if drive_path in by_drive:
            by_drive[drive_path].append(vol)
        else:
            loose.append(vol)
    out = []
    for p, drv in drives.items():
        vols = sorted(by_drive[p], key=lambda v: (v.partition_number or 0, v.device_node))
        out.append(
            Drive(
                drv.object_path,
                drv.vendor,
                drv.model,
                drv.serial,
                drv.size_bytes,
                drv.removable,
                drv.ejectable,
                drv.connection_bus,
                drv.media_removable,
                tuple(vols),
            )
        )
    out.sort(key=lambda d: (d.removable, d.display_name))
    return StorageOverview(True, "Read from udisks2.", tuple(out), tuple(loose), hidden)
