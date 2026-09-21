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
"""Services data from systemd over D-Bus, read-only.

Two managers exist: the system manager (system bus, polkit-mediated
changes) and this user's manager (session bus, no elevation). Both are
listed with their scope so nothing is conflated. Running (ActiveState) and
enabled-at-boot (UnitFileState) are separate facts (TB-INV-138). Identity
for mutation is the unit name plus object path plus fragment path
(TB-INV-053, TB-INV-142).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from typing import Any

from ..core.identity import UnitIdentity
from .bus import Bus

SD = "org.freedesktop.systemd1"
SD_PATH = "/org/freedesktop/systemd1"
MANAGER = f"{SD}.Manager"
UNIT = f"{SD}.Unit"


@unique
class Scope(Enum):
    SYSTEM = "system"  # needs administrator permission to change (polkit)
    USER = "user"  # this user's own services; no prompt


@dataclass(frozen=True)
class ServiceInfo:
    identity: UnitIdentity
    scope: Scope
    description: str
    active_state: str  # active, inactive, failed, activating, deactivating
    sub_state: str  # running, exited, dead, ...
    unit_file_state: str  # enabled, disabled, static, masked, ... or "" unknown
    can_start: bool
    can_stop: bool
    can_reload: bool

    @property
    def plain_running(self) -> str:
        return {
            "active": "Running" if self.sub_state == "running" else "Active",
            "inactive": "Stopped",
            "failed": "Failed",
            "activating": "Starting",
            "deactivating": "Stopping",
        }.get(self.active_state, "Unknown")

    @property
    def plain_startup(self) -> str:
        return {
            "enabled": "Automatic",
            "enabled-runtime": "Automatic (this boot)",
            "disabled": "Manual",
            "static": "As needed (static)",
            "masked": "Blocked (masked)",
            "indirect": "Indirect",
            "generated": "Generated",
            "transient": "Transient",
            "alias": "Alias",
        }.get(self.unit_file_state, "Unknown")


def bus_for(scope: Scope) -> Bus:
    return Bus.system() if scope is Scope.SYSTEM else Bus.session()


def list_services(scope: Scope, bus: Bus | None = None) -> tuple[list[ServiceInfo], str]:
    """All .service units the manager knows, plus a plain error when unavailable."""
    bus = bus or bus_for(scope)
    if bus.conn is None:
        return [], f"The {scope.value} service manager is not reachable: {bus.error}"
    res, err = bus.call(SD, SD_PATH, MANAGER, "ListUnits")
    if err:
        return [], f"systemd ({scope.value}) did not answer: {err}"
    out: list[ServiceInfo] = []
    for row in res[0]:
        name, desc, load, active, sub, _followed, path = row[:7]
        if not str(name).endswith(".service") or str(load) == "not-found":
            continue
        props = bus.properties(SD, str(path), UNIT)
        out.append(
            ServiceInfo(
                identity=UnitIdentity(
                    name=str(name),
                    object_path=str(path),
                    load_state=str(load),
                    fragment_path=str(props.get("FragmentPath", "")),
                ),
                scope=scope,
                description=str(desc),
                active_state=str(active),
                sub_state=str(sub),
                unit_file_state=str(props.get("UnitFileState", "") or ""),
                can_start=bool(props.get("CanStart", False)),
                can_stop=bool(props.get("CanStop", False)),
                can_reload=bool(props.get("CanReload", False)),
            )
        )
    out.sort(key=lambda s: (s.active_state != "active", s.identity.name))
    return out, ""


def read_unit(scope: Scope, name: str, bus: Bus | None = None) -> tuple[ServiceInfo | None, str]:
    """Fresh facts for one unit by name (used for revalidation and verification)."""
    bus = bus or bus_for(scope)
    if bus.conn is None:
        return None, bus.error
    res, err = bus.call(SD, SD_PATH, MANAGER, "LoadUnit", _variant_s(name))
    if err or not res:
        return None, err or "no such unit"
    path = str(res[0])
    props = bus.properties(SD, path, UNIT)
    if not props:
        return None, "unit properties unavailable"
    return (
        ServiceInfo(
            identity=UnitIdentity(
                name=name,
                object_path=path,
                load_state=str(props.get("LoadState", "")),
                fragment_path=str(props.get("FragmentPath", "")),
            ),
            scope=scope,
            description=str(props.get("Description", "")),
            active_state=str(props.get("ActiveState", "")),
            sub_state=str(props.get("SubState", "")),
            unit_file_state=str(props.get("UnitFileState", "") or ""),
            can_start=bool(props.get("CanStart", False)),
            can_stop=bool(props.get("CanStop", False)),
            can_reload=bool(props.get("CanReload", False)),
        ),
        "",
    )


def _variant_s(value: str) -> Any:
    from gi.repository import GLib

    return GLib.Variant("(s)", (value,))
