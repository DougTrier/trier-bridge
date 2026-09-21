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
"""Read-only discovery of the environment and available backends.

SECURITY: only D-Bus reads (properties, GetManagedObjects, ListNames,
GetSessionByPID) and file reads. No method here can change anything
(TB-INV-036, TB-INV-046). Every D-Bus call has a bounded timeout
(TB-INV-041). Errors become structured records, never exceptions to the
caller (TB-INV-040). No shell, no subprocess.

COMPATIBILITY: written against the Ubuntu 24.04 profile (RESEARCH F6-F10,
F15). On other systems a missing bus name is UNSUPPORTED, a bus that cannot be
reached is ERROR, and anything not probed is UNKNOWN.
"""
from __future__ import annotations

import grp
import os
import platform
import pwd
import socket
from pathlib import Path
from typing import Any

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from ..core.state import CapabilityState, PrivilegeClass  # noqa: E402
from . import facts  # noqa: E402
from .model import Capability, CapabilityRecord, EnvironmentProfile  # noqa: E402

CALL_TIMEOUT_MS = 3000


class _Bus:
    """Thin read-only D-Bus helper with bounded timeouts and structured failure."""

    def __init__(self, bus_type: Any) -> None:
        self.error = ""
        try:
            self.conn = Gio.bus_get_sync(bus_type, None)
        except GLib.Error as exc:
            self.conn = None
            self.error = f"{exc.domain}: {exc.message}"
        self._names: set[str] | None = None
        self._activatable: set[str] | None = None

    def names(self) -> set[str]:
        if self._names is None:
            self._names = set(self._call_dbus("ListNames"))
        return self._names

    def activatable(self) -> set[str]:
        if self._activatable is None:
            self._activatable = set(self._call_dbus("ListActivatableNames"))
        return self._activatable

    def _call_dbus(self, method: str) -> list[str]:
        if self.conn is None:
            return []
        try:
            res = self.conn.call_sync(
                "org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus",
                method,
                None,
                GLib.VariantType("(as)"),
                Gio.DBusCallFlags.NONE,
                CALL_TIMEOUT_MS,
                None,
            )
            return list(res.unpack()[0])
        except GLib.Error:
            return []

    def property(self, name: str, path: str, iface: str, prop: str) -> tuple[Any, str]:
        """Return (value, error). Reading a property never activates a mutation."""
        if self.conn is None:
            return None, self.error or "bus unavailable"
        try:
            res = self.conn.call_sync(
                name,
                path,
                "org.freedesktop.DBus.Properties",
                "Get",
                GLib.Variant("(ss)", (iface, prop)),
                GLib.VariantType("(v)"),
                Gio.DBusCallFlags.NONE,
                CALL_TIMEOUT_MS,
                None,
            )
            return res.unpack()[0], ""
        except GLib.Error as exc:
            return None, f"{exc.domain}: {exc.message}"

    def call(
        self, name: str, path: str, iface: str, method: str, args: Any = None
    ) -> tuple[Any, str]:
        if self.conn is None:
            return None, self.error or "bus unavailable"
        try:
            res = self.conn.call_sync(
                name, path, iface, method, args, None, Gio.DBusCallFlags.NONE, CALL_TIMEOUT_MS, None
            )
            return res.unpack(), ""
        except GLib.Error as exc:
            return None, f"{exc.domain}: {exc.message}"


class Discovery:
    """One discovery pass. Construct, call ``environment()`` and ``capabilities()``."""

    def __init__(self, root: Path = Path("/")) -> None:
        self.root = root
        self.system = _Bus(Gio.BusType.SYSTEM)
        self.session = _Bus(Gio.BusType.SESSION)

    # ---- environment ---------------------------------------------------------
    def environment(self) -> EnvironmentProfile:
        evidence: list[str] = []
        distro_id = version = pretty = ""
        like: tuple[str, ...] = ()
        for candidate in ("etc/os-release", "usr/lib/os-release"):
            p = self.root / candidate
            if p.is_file():
                distro_id, version, pretty, like = facts.distro_from_os_release(
                    facts.parse_os_release(p.read_text(encoding="utf-8", errors="replace"))
                )
                evidence.append(f"/{candidate}")
                break
        kernel = ""
        krel = self.root / "proc/sys/kernel/osrelease"
        if krel.is_file():
            kernel = krel.read_text(encoding="utf-8", errors="replace").strip()
            evidence.append("/proc/sys/kernel/osrelease")
        arch = platform.machine()
        evidence.append("platform.machine()")

        virt = ""
        value, err = self.system.property(
            "org.freedesktop.systemd1",
            "/org/freedesktop/systemd1",
            "org.freedesktop.systemd1.Manager",
            "Virtualization",
        )
        if not err and isinstance(value, str):
            virt = value or "none"
            evidence.append("systemd1 Manager.Virtualization")

        session_type = session_class = ""
        remote: bool | None = None
        active: bool | None = None
        res, err = self.system.call(
            "org.freedesktop.login1",
            "/org/freedesktop/login1",
            "org.freedesktop.login1.Manager",
            "GetSessionByPID",
            GLib.Variant("(u)", (os.getpid(),)),
        )
        if not err and res:
            spath = res[0]
            for prop in ("Type", "Class", "Remote", "Active"):
                val, perr = self.system.property(
                    "org.freedesktop.login1", spath, "org.freedesktop.login1.Session", prop
                )
                if perr:
                    continue
                if prop == "Type":
                    session_type = str(val)
                elif prop == "Class":
                    session_class = str(val)
                elif prop == "Remote":
                    remote = bool(val)
                elif prop == "Active":
                    active = bool(val)
            evidence.append("login1 Session properties for this PID")

        uid = os.getuid()
        try:
            user = pwd.getpwuid(uid).pw_name
        except KeyError:
            user = ""
        groups: tuple[str, ...] = ()
        try:
            groups = tuple(sorted(g.gr_name for g in grp.getgrall() if user in g.gr_mem))
            primary = grp.getgrgid(os.getgid()).gr_name
            if primary not in groups:
                groups = (primary,) + groups
        except (KeyError, OSError):
            pass

        return EnvironmentProfile(
            distro_id=distro_id,
            distro_version=version,
            distro_name=pretty,
            distro_like=like,
            architecture=arch,
            kernel=kernel,
            virtualization=virt,
            session_type=session_type,
            session_class=session_class,
            session_remote=remote,
            session_active=active,
            desktop=os.environ.get("XDG_CURRENT_DESKTOP", ""),
            hostname=socket.gethostname(),
            user_id=uid,
            user_name=user,
            groups=groups,
            evidence=tuple(evidence),
        )

    # ---- capabilities ---------------------------------------------------------
    def capabilities(self) -> list[CapabilityRecord]:
        recs = [
            self._systemd(),
            self._network_manager(),
            self._udisks(),
            self._polkit(),
            self._login1(),
            self._packagekit(),
            self._apt(),
            self._snap(),
            self._flatpak(),
            self._journal(),
            self._cups(),
            self._bus_service(
                Capability.BLUETOOTH, "org.bluez", "BlueZ", read_ops=("list adapters/devices",)
            ),
            self._bus_service(
                Capability.POWER,
                "org.freedesktop.UPower",
                "UPower",
                read_ops=("battery, power state",),
            ),
            self._session_service(
                Capability.PORTALS, "org.freedesktop.portal.Desktop", "xdg-desktop-portal"
            ),
            self._session_service(Capability.SHELL, "org.gnome.Shell", "GNOME Shell"),
            self._processes(),
        ]
        return recs

    # -- helpers
    def _bus_service(
        self,
        cap: Capability,
        name: str,
        backend: str,
        read_ops: tuple[str, ...] = (),
        mutation_ops: tuple[str, ...] = (),
        privilege: PrivilegeClass = PrivilegeClass.A_READ_ONLY,
        version_prop: tuple[str, str, str] | None = None,
    ) -> CapabilityRecord:
        bus = self.system
        if bus.conn is None:
            return CapabilityRecord(cap, CapabilityState.ERROR, backend, detail=bus.error)
        active = name in bus.names()
        activatable = name in bus.activatable()
        if not active and not activatable:
            return CapabilityRecord(
                cap,
                CapabilityState.UNSUPPORTED,
                backend,
                evidence=f"system bus: {name} neither active nor activatable",
                detail=f"{backend} is not present on this computer.",
            )
        version = ""
        evidence = f"system bus: {name} {'active' if active else 'activatable'}"
        if version_prop is not None:
            val, err = bus.property(name, *version_prop)
            if not err and val is not None:
                version = str(val)
                evidence += f"; {version_prop[2]}={version}"
        return CapabilityRecord(
            cap,
            CapabilityState.SUPPORTED,
            backend,
            version,
            evidence,
            read_operations=read_ops,
            mutation_operations=mutation_ops,
            privilege=privilege,
        )

    def _session_service(self, cap: Capability, name: str, backend: str) -> CapabilityRecord:
        bus = self.session
        if bus.conn is None:
            return CapabilityRecord(
                cap,
                CapabilityState.UNKNOWN,
                backend,
                evidence="no session bus",
                detail="No desktop session bus is reachable; this is not a desktop session.",
            )
        present = name in bus.names() or name in bus.activatable()
        return CapabilityRecord(
            cap,
            CapabilityState.SUPPORTED if present else CapabilityState.UNSUPPORTED,
            backend,
            evidence=f"session bus: {name} {'present' if present else 'absent'}",
        )

    def _systemd(self) -> CapabilityRecord:
        rec = self._bus_service(
            Capability.SERVICE_MANAGER,
            "org.freedesktop.systemd1",
            "systemd",
            read_ops=("list units", "unit state"),
            mutation_ops=("start", "stop", "restart", "enable", "disable"),
            privilege=PrivilegeClass.C_ADMIN_MUTATION,
            version_prop=(
                "/org/freedesktop/systemd1",
                "org.freedesktop.systemd1.Manager",
                "Version",
            ),
        )
        return rec

    def _network_manager(self) -> CapabilityRecord:
        return self._bus_service(
            Capability.NETWORK_MANAGER,
            "org.freedesktop.NetworkManager",
            "NetworkManager",
            read_ops=("devices", "connections", "IP configuration", "connectivity"),
            mutation_ops=("activate/deactivate connection", "edit profile (checkpointed)"),
            privilege=PrivilegeClass.C_ADMIN_MUTATION,
            version_prop=(
                "/org/freedesktop/NetworkManager",
                "org.freedesktop.NetworkManager",
                "Version",
            ),
        )

    def _udisks(self) -> CapabilityRecord:
        rec = self._bus_service(
            Capability.STORAGE,
            "org.freedesktop.UDisks2",
            "udisks2",
            read_ops=("drives", "block devices", "filesystems", "mounts"),
            mutation_ops=("mount", "unmount"),
            privilege=PrivilegeClass.C_ADMIN_MUTATION,
        )
        if rec.state is CapabilityState.SUPPORTED:
            res, err = self.system.call(
                "org.freedesktop.UDisks2",
                "/org/freedesktop/UDisks2/Manager",
                "org.freedesktop.DBus.Properties",
                "Get",
                GLib.Variant("(ss)", ("org.freedesktop.UDisks2.Manager", "Version")),
            )
            if not err and res:
                rec = CapabilityRecord(
                    rec.capability,
                    rec.state,
                    rec.backend,
                    str(res[0]),
                    rec.evidence + f"; Manager.Version={res[0]}",
                    read_operations=rec.read_operations,
                    mutation_operations=rec.mutation_operations,
                    privilege=rec.privilege,
                )
        return rec

    def _polkit(self) -> CapabilityRecord:
        return self._bus_service(
            Capability.AUTHORIZATION,
            "org.freedesktop.PolicyKit1",
            "polkit",
            read_ops=("check authorization without prompting",),
            version_prop=(
                "/org/freedesktop/PolicyKit1/Authority",
                "org.freedesktop.PolicyKit1.Authority",
                "BackendVersion",
            ),
        )

    def _login1(self) -> CapabilityRecord:
        return self._bus_service(
            Capability.SESSION_MANAGER,
            "org.freedesktop.login1",
            "systemd-logind",
            read_ops=("sessions", "seats", "power capabilities"),
            mutation_ops=("reboot", "power off", "lock"),
            privilege=PrivilegeClass.C_ADMIN_MUTATION,
        )

    def _packagekit(self) -> CapabilityRecord:
        return self._bus_service(
            Capability.PACKAGEKIT,
            "org.freedesktop.PackageKit",
            "PackageKit",
            read_ops=("resolve", "installed packages", "updates"),
            mutation_ops=("install", "remove", "update"),
            privilege=PrivilegeClass.C_ADMIN_MUTATION,
            version_prop=(
                "/org/freedesktop/PackageKit",
                "org.freedesktop.PackageKit",
                "BackendName",
            ),
        )

    def _apt(self) -> CapabilityRecord:
        status = self.root / "var/lib/dpkg/status"
        aptbin = self.root / "usr/bin/apt-get"
        if status.is_file() and aptbin.exists():
            return CapabilityRecord(
                Capability.PACKAGES_NATIVE,
                CapabilityState.SUPPORTED,
                "apt/dpkg",
                evidence="/var/lib/dpkg/status and /usr/bin/apt-get present",
                read_operations=("installed packages (dpkg status)",),
                mutation_operations=("through PackageKit only",),
            )
        return CapabilityRecord(
            Capability.PACKAGES_NATIVE,
            CapabilityState.UNSUPPORTED,
            "apt/dpkg",
            evidence="dpkg status or apt-get absent",
            detail="This computer does not use apt/dpkg packages.",
        )

    def _snap(self) -> CapabilityRecord:
        sock = self.root / "run/snapd.socket"
        binary = self.root / "usr/bin/snap"
        if sock.exists() and binary.exists():
            return CapabilityRecord(
                Capability.PACKAGES_SNAP,
                CapabilityState.SUPPORTED,
                "snapd",
                evidence="/run/snapd.socket and /usr/bin/snap present",
                read_operations=("installed snaps",),
                limitations=("snap operations are not exposed through PackageKit",),
            )
        if binary.exists():
            return CapabilityRecord(
                Capability.PACKAGES_SNAP,
                CapabilityState.DEGRADED,
                "snapd",
                evidence="/usr/bin/snap present, /run/snapd.socket absent",
                detail="snap is installed but snapd is not running.",
            )
        return CapabilityRecord(
            Capability.PACKAGES_SNAP,
            CapabilityState.UNSUPPORTED,
            "snapd",
            evidence="/usr/bin/snap absent",
        )

    def _flatpak(self) -> CapabilityRecord:
        binary = self.root / "usr/bin/flatpak"
        if binary.exists():
            return CapabilityRecord(
                Capability.PACKAGES_FLATPAK,
                CapabilityState.SUPPORTED,
                "flatpak",
                evidence="/usr/bin/flatpak present",
                read_operations=("installed flatpaks",),
            )
        return CapabilityRecord(
            Capability.PACKAGES_FLATPAK,
            CapabilityState.UNSUPPORTED,
            "flatpak",
            evidence="/usr/bin/flatpak absent",
            detail="Flatpak is not installed on this computer.",
        )

    def _journal(self) -> CapabilityRecord:
        jdir = self.root / "var/log/journal"
        rdir = self.root / "run/log/journal"
        present = jdir.is_dir() or rdir.is_dir()
        if not present:
            return CapabilityRecord(
                Capability.JOURNAL,
                CapabilityState.UNSUPPORTED,
                "systemd-journald",
                evidence="no journal directory under /var/log or /run/log",
            )
        readable = os.access(jdir if jdir.is_dir() else rdir, os.R_OK | os.X_OK)
        if readable:
            return CapabilityRecord(
                Capability.JOURNAL,
                CapabilityState.SUPPORTED,
                "systemd-journald",
                evidence="journal directory readable by this user",
                read_operations=("system and user log entries",),
            )
        return CapabilityRecord(
            Capability.JOURNAL,
            CapabilityState.DEGRADED,
            "systemd-journald",
            evidence="journal directory not readable by this user",
            detail=(
                "System log is restricted for this account; "
                "only this user's entries are visible."
            ),
            limitations=("system journal restricted (TB-INV-145)",),
        )

    def _cups(self) -> CapabilityRecord:
        sock = self.root / "run/cups/cups.sock"
        if sock.exists():
            return CapabilityRecord(
                Capability.PRINTING,
                CapabilityState.SUPPORTED,
                "CUPS",
                evidence="/run/cups/cups.sock present",
                read_operations=("printers", "queues"),
                mutation_operations=("cancel own jobs", "add printer (native dialog)"),
                privilege=PrivilegeClass.B_USER_MUTATION,
            )
        return CapabilityRecord(
            Capability.PRINTING,
            CapabilityState.UNSUPPORTED,
            "CUPS",
            evidence="/run/cups/cups.sock absent",
            detail="The print service is not running on this computer.",
        )

    def _processes(self) -> CapabilityRecord:
        proc = self.root / "proc"
        if not (proc / "self" / "stat").is_file():
            return CapabilityRecord(
                Capability.PROCESSES, CapabilityState.UNSUPPORTED, "procfs", evidence="/proc absent"
            )
        others_visible = os.access(proc / "1" / "stat", os.R_OK)
        state = CapabilityState.SUPPORTED if others_visible else CapabilityState.DEGRADED
        return CapabilityRecord(
            Capability.PROCESSES,
            state,
            "procfs",
            evidence="/proc/1/stat " + ("readable" if others_visible else "not readable (hidepid)"),
            read_operations=("process list", "per-process usage"),
            mutation_operations=("terminate own process",),
            privilege=PrivilegeClass.B_USER_MUTATION,
            limitations=() if others_visible else ("only this user's processes are visible",),
        )
