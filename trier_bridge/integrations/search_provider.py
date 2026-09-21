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
"""GNOME Shell search provider: Windows words in Activities search (RESEARCH F16).

Started by D-Bus activation only when the user has enabled the integration;
exits after a minute of inactivity so nothing lingers (DEC-018 c). Answers
come from the concept catalog; activating a result launches the Bridge window
at that section through the desktop, never a shell.
"""
from __future__ import annotations

import sys
import time

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from ..catalog.model import Catalog, RouteKind  # noqa: E402
from ..resources import catalog_path  # noqa: E402

BUS_NAME = "org.triertech.TrierBridge.SearchProvider"
OBJ_PATH = "/org/triertech/TrierBridge/SearchProvider"
IDLE_SECONDS = 60

XML = """
<node>
  <interface name="org.gnome.Shell.SearchProvider2">
    <method name="GetInitialResultSet">
      <arg type="as" direction="in"/><arg type="as" direction="out"/>
    </method>
    <method name="GetSubsearchResultSet">
      <arg type="as" direction="in"/><arg type="as" direction="in"/>
      <arg type="as" direction="out"/>
    </method>
    <method name="GetResultMetas">
      <arg type="as" direction="in"/><arg type="aa{sv}" direction="out"/>
    </method>
    <method name="ActivateResult">
      <arg type="s" direction="in"/><arg type="as" direction="in"/><arg type="u" direction="in"/>
    </method>
    <method name="LaunchSearch">
      <arg type="as" direction="in"/><arg type="u" direction="in"/>
    </method>
  </interface>
</node>
"""


class Provider:
    def __init__(self) -> None:
        self.catalog = Catalog.load(catalog_path())
        self.last = time.monotonic()
        self.loop = GLib.MainLoop()

    def search(self, terms: list[str]) -> list[str]:
        query = " ".join(terms).strip()
        if len(query) < 2:
            return []
        return [m.concept.id for m in self.catalog.search(query, limit=6)]

    def handle(  # type: ignore[no-untyped-def]
        self, conn, sender, path, iface, method, params, invocation
    ) -> None:
        self.last = time.monotonic()
        if method == "GetInitialResultSet":
            invocation.return_value(GLib.Variant("(as)", (self.search(params.unpack()[0]),)))
        elif method == "GetSubsearchResultSet":
            invocation.return_value(GLib.Variant("(as)", (self.search(params.unpack()[1]),)))
        elif method == "GetResultMetas":
            metas: list[dict[str, GLib.Variant]] = []
            for cid in params.unpack()[0]:
                c = self.catalog.get(cid)
                if c is None:
                    continue
                metas.append(
                    {
                        "id": GLib.Variant("s", cid),
                        "name": GLib.Variant("s", c.title),
                        "description": GLib.Variant("s", f"{c.linux} · {c.mapping_note()}"[:120]),
                        "gicon": GLib.Variant("s", "org.triertech.TrierBridge"),
                    }
                )
            invocation.return_value(GLib.Variant("(aa{sv})", (metas,)))
        elif method == "ActivateResult":
            cid = params.unpack()[0]
            self.activate(cid)
            invocation.return_value(None)
        elif method == "LaunchSearch":
            self.launch(["trier-bridge"])
            invocation.return_value(None)
        else:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", method)

    def activate(self, cid: str) -> None:
        c = self.catalog.get(cid)
        argv = ["trier-bridge"]
        if c is not None and c.route.kind is RouteKind.SECTION:
            argv += ["--section", c.route.target]
        elif c is not None and c.can_open:
            argv += ["--open", cid]
        self.launch(argv)

    @staticmethod
    def launch(argv: list[str]) -> None:
        # Fixed argv through GLib, no shell (TB-SEC-003).
        GLib.spawn_async(
            argv, flags=GLib.SpawnFlags.SEARCH_PATH | GLib.SpawnFlags.DO_NOT_REAP_CHILD
        )

    def idle(self) -> bool:
        if time.monotonic() - self.last > IDLE_SECONDS:
            self.loop.quit()
        return True

    def run(self) -> int:
        node = Gio.DBusNodeInfo.new_for_xml(XML)

        def on_bus(conn, name):  # type: ignore[no-untyped-def]
            conn.register_object(OBJ_PATH, node.interfaces[0], self.handle, None, None)

        Gio.bus_own_name(
            Gio.BusType.SESSION,
            BUS_NAME,
            Gio.BusNameOwnerFlags.NONE,
            on_bus,
            None,
            lambda c, n: self.loop.quit(),
        )
        GLib.timeout_add_seconds(10, self.idle)
        self.loop.run()
        return 0


def main() -> int:
    return Provider().run()


if __name__ == "__main__":
    sys.exit(main())
