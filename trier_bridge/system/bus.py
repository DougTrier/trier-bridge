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
"""Read-only D-Bus helper shared by discovery and the system adapters.

OWNERSHIP: the one place that knows how to read properties, call methods,
and list names with bounded timeouts and structured failure (TB-INV-040,
TB-INV-041). Nothing here writes; the methods it exposes are used only for
reads in Foundation 04. Mutation adapters (Foundation 06) add their own
explicitly named calls.
"""
from __future__ import annotations

from typing import Any

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

CALL_TIMEOUT_MS = 3000
PROPS = "org.freedesktop.DBus.Properties"


class Bus:
    def __init__(self, bus_type: Any) -> None:
        self.error = ""
        try:
            self.conn: Any = Gio.bus_get_sync(bus_type, None)
        except GLib.Error as exc:
            self.conn = None
            self.error = f"{exc.domain}: {exc.message}"
        self._names: set[str] | None = None
        self._activatable: set[str] | None = None

    @classmethod
    def system(cls) -> "Bus":
        return cls(Gio.BusType.SYSTEM)

    @classmethod
    def session(cls) -> "Bus":
        return cls(Gio.BusType.SESSION)

    def names(self) -> set[str]:
        if self._names is None:
            self._names = set(self._call_dbus("ListNames"))
        return self._names

    def activatable(self) -> set[str]:
        if self._activatable is None:
            self._activatable = set(self._call_dbus("ListActivatableNames"))
        return self._activatable

    def _call_dbus(self, method: str) -> list[str]:
        res, err = self.call(
            "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", method
        )
        return list(res[0]) if not err and res else []

    def call(
        self, name: str, path: str, iface: str, method: str, args: Any = None
    ) -> tuple[Any, str]:
        """Return (unpacked result tuple, error text). Never raises."""
        if self.conn is None:
            return None, self.error or "bus unavailable"
        try:
            res = self.conn.call_sync(
                name, path, iface, method, args, None, Gio.DBusCallFlags.NONE, CALL_TIMEOUT_MS, None
            )
            return res.unpack(), ""
        except GLib.Error as exc:
            return None, f"{exc.domain}: {exc.message}"

    def property(self, name: str, path: str, iface: str, prop: str) -> tuple[Any, str]:
        res, err = self.call(name, path, PROPS, "Get", GLib.Variant("(ss)", (iface, prop)))
        return (res[0] if res else None), err

    def properties(self, name: str, path: str, iface: str) -> dict[str, Any]:
        """All properties of one interface, or {} on failure (missing means Unknown)."""
        res, err = self.call(name, path, PROPS, "GetAll", GLib.Variant("(s)", (iface,)))
        if err or not res:
            return {}
        return dict(res[0])

    def managed_objects(self, name: str, root: str) -> dict[str, dict[str, dict[str, Any]]]:
        res, err = self.call(name, root, "org.freedesktop.DBus.ObjectManager", "GetManagedObjects")
        if err or not res:
            return {}
        return dict(res[0])
