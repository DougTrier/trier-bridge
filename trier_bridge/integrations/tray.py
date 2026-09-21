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
"""The tray icon "T" (DEC-019): a StatusNotifierItem with a small menu.

Runs as its own small process, started at login by a per-user autostart entry
the user chose at setup. It speaks the StatusNotifierItem and dbusmenu
protocols directly over the session bus, so it needs nothing beyond GLib and
shows up wherever a StatusNotifier host exists (Ubuntu's AppIndicator
extension). No host: it waits briefly, then exits. Everything it can do is
open the Bridge window, open the Integrations page, or turn itself off.
"""
from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from .. import APP_ID, __version__  # noqa: E402
from ..config import resolve_paths  # noqa: E402
from ..logging_setup import configure  # noqa: E402

log = logging.getLogger("trier_bridge.tray")

TRAY_NAME = "org.triertech.TrierBridge.Tray"
TRAY_PATH = "/org/triertech/TrierBridge/Tray"
WATCHER = "org.kde.StatusNotifierWatcher"
WATCHER_PATH = "/StatusNotifierWatcher"
ITEM_PATH = "/StatusNotifierItem"
MENU_PATH = "/org/triertech/TrierBridge/Tray/Menu"
ICON_NAME = f"{APP_ID}-symbolic"
NO_HOST_SECONDS = 120

TRAY_XML = f"""
<node>
  <interface name="{TRAY_NAME}">
    <method name="Quit"/>
    <method name="Ping"><arg type="s" direction="out"/></method>
  </interface>
</node>
"""

ITEM_XML = """
<node>
  <interface name="org.kde.StatusNotifierItem">
    <property name="Category" type="s" access="read"/>
    <property name="Id" type="s" access="read"/>
    <property name="Title" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="IconName" type="s" access="read"/>
    <property name="IconThemePath" type="s" access="read"/>
    <property name="Menu" type="o" access="read"/>
    <property name="ItemIsMenu" type="b" access="read"/>
    <property name="ToolTip" type="(sa(iiay)ss)" access="read"/>
    <method name="Activate">
      <arg type="i" direction="in"/><arg type="i" direction="in"/>
    </method>
    <method name="SecondaryActivate">
      <arg type="i" direction="in"/><arg type="i" direction="in"/>
    </method>
    <method name="ContextMenu">
      <arg type="i" direction="in"/><arg type="i" direction="in"/>
    </method>
    <method name="Scroll">
      <arg type="i" direction="in"/><arg type="s" direction="in"/>
    </method>
    <signal name="NewIcon"/>
    <signal name="NewTitle"/>
    <signal name="NewStatus"><arg type="s"/></signal>
  </interface>
</node>
"""

MENU_XML = """
<node>
  <interface name="com.canonical.dbusmenu">
    <property name="Version" type="u" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="TextDirection" type="s" access="read"/>
    <property name="IconThemePath" type="as" access="read"/>
    <method name="GetLayout">
      <arg type="i" direction="in"/><arg type="i" direction="in"/><arg type="as" direction="in"/>
      <arg type="u" direction="out"/><arg type="(ia{sv}av)" direction="out"/>
    </method>
    <method name="GetGroupProperties">
      <arg type="ai" direction="in"/><arg type="as" direction="in"/>
      <arg type="a(ia{sv})" direction="out"/>
    </method>
    <method name="GetProperty">
      <arg type="i" direction="in"/><arg type="s" direction="in"/><arg type="v" direction="out"/>
    </method>
    <method name="Event">
      <arg type="i" direction="in"/><arg type="s" direction="in"/>
      <arg type="v" direction="in"/><arg type="u" direction="in"/>
    </method>
    <method name="EventGroup">
      <arg type="a(isvu)" direction="in"/><arg type="ai" direction="out"/>
    </method>
    <method name="AboutToShow">
      <arg type="i" direction="in"/><arg type="b" direction="out"/>
    </method>
    <method name="AboutToShowGroup">
      <arg type="ai" direction="in"/><arg type="ai" direction="out"/>
      <arg type="ai" direction="out"/>
    </method>
    <signal name="ItemsPropertiesUpdated"><arg type="a(ia{sv})"/><arg type="a(ias)"/></signal>
    <signal name="LayoutUpdated"><arg type="u"/><arg type="i"/></signal>
    <signal name="ItemActivationRequested"><arg type="i"/><arg type="u"/></signal>
  </interface>
</node>
"""

# id, label ("" = separator), argv to launch ("off" turns the tray integration off)
MENU_ITEMS: tuple[tuple[int, str, str], ...] = (
    (1, "Open Trier Bridge", "open"),
    (2, "Task Manager", "taskmanager"),
    (3, "Command Prompt", "terminal"),
    (4, "", ""),
    (5, "Change integrations", "integrations"),
    (6, "", ""),
    (7, "Turn off the tray icon", "off"),
)


def app_argv() -> list[str]:
    """How to start the Bridge window: the installed command, else this checkout."""
    exe = shutil.which("trier-bridge")
    return [exe] if exe else [sys.executable, "-m", "trier_bridge"]


def tray_argv() -> list[str]:
    exe = shutil.which("trier-bridge-tray")
    return [exe] if exe else [sys.executable, "-m", "trier_bridge.integrations.tray"]


def icon_dir() -> str:
    """Directory holding the tray icon file (checkout first, then the packaged theme)."""
    source = Path(__file__).resolve().parents[2] / "data/icons/hicolor/symbolic/apps"
    if (source / f"{ICON_NAME}.svg").is_file():
        return str(source)
    return "/usr/share/icons/hicolor/symbolic/apps"


def spawn(argv: list[str]) -> None:
    # Fixed argument list through GLib; no shell anywhere (TB-SEC-003).
    GLib.spawn_async(argv, flags=GLib.SpawnFlags.SEARCH_PATH | GLib.SpawnFlags.DO_NOT_REAP_CHILD)


def _s(value: str) -> GLib.Variant:
    return GLib.Variant("s", value)


class Tray:
    def __init__(self) -> None:
        self.loop = GLib.MainLoop()
        self.conn: Any = None
        self.item_name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
        self.revision = 1
        self.registered = False
        self._no_host_source = 0

    # ---- StatusNotifierItem ---------------------------------------------------------
    def item_property(self, _c: Any, _sender: Any, _p: Any, _i: Any, name: str) -> GLib.Variant:
        values: dict[str, GLib.Variant] = {
            "Category": _s("ApplicationStatus"),
            "Id": _s("trier-bridge"),
            "Title": _s("Trier Bridge"),
            "Status": _s("Active"),
            "IconName": _s(ICON_NAME),
            "IconThemePath": _s(icon_dir()),
            "Menu": GLib.Variant("o", MENU_PATH),
            "ItemIsMenu": GLib.Variant("b", False),
            "ToolTip": GLib.Variant(
                "(sa(iiay)ss)", ("", [], "Trier Bridge", "Everything you know. Linux underneath.")
            ),
        }
        return values[name]

    def item_call(  # type: ignore[no-untyped-def]
        self, _c, _sender, _p, _i, method, _params, invocation
    ) -> None:
        if method in ("Activate", "SecondaryActivate"):
            self.act("open")
        invocation.return_value(None)

    # ---- dbusmenu ---------------------------------------------------------------------
    def menu_property(self, _c: Any, _sender: Any, _p: Any, _i: Any, name: str) -> GLib.Variant:
        values: dict[str, GLib.Variant] = {
            "Version": GLib.Variant("u", 3),
            "Status": _s("normal"),
            "TextDirection": _s("ltr"),
            "IconThemePath": GLib.Variant("as", []),
        }
        return values[name]

    @staticmethod
    def _props(item_id: int) -> dict[str, GLib.Variant]:
        for iid, label, _ in MENU_ITEMS:
            if iid == item_id:
                if not label:
                    return {"type": _s("separator")}
                return {"label": _s(label), "enabled": GLib.Variant("b", True)}
        if item_id == 0:
            return {"children-display": _s("submenu")}
        return {}

    def _layout(self) -> GLib.Variant:
        children = [
            GLib.Variant("(ia{sv}av)", (iid, self._props(iid), [])) for iid, _, _ in MENU_ITEMS
        ]
        return GLib.Variant("(u(ia{sv}av))", (self.revision, (0, self._props(0), children)))

    def menu_call(  # type: ignore[no-untyped-def]
        self, _c, _sender, _p, _i, method, params, invocation
    ) -> None:
        if method == "GetLayout":
            invocation.return_value(self._layout())
        elif method == "GetGroupProperties":
            ids = params.unpack()[0] or [0] + [iid for iid, _, _ in MENU_ITEMS]
            invocation.return_value(
                GLib.Variant("(a(ia{sv}))", ([(i, self._props(i)) for i in ids],))
            )
        elif method == "GetProperty":
            iid, name = params.unpack()
            value = self._props(iid).get(name, _s(""))
            invocation.return_value(GLib.Variant("(v)", (value,)))
        elif method == "Event":
            iid, event, _data, _ts = params.unpack()
            if event == "clicked":
                self.click(iid)
            invocation.return_value(None)
        elif method == "EventGroup":
            for iid, event, _data, _ts in params.unpack()[0]:
                if event == "clicked":
                    self.click(iid)
            invocation.return_value(GLib.Variant("(ai)", ([],)))
        elif method == "AboutToShow":
            invocation.return_value(GLib.Variant("(b)", (False,)))
        elif method == "AboutToShowGroup":
            invocation.return_value(GLib.Variant("(aiai)", ([], [])))
        else:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", method)

    def click(self, item_id: int) -> None:
        for iid, _, action in MENU_ITEMS:
            if iid == item_id and action:
                self.act(action)

    def act(self, action: str) -> None:
        if action == "open":
            spawn(app_argv())
        elif action in ("integrations", "taskmanager", "terminal"):
            spawn(app_argv() + ["--section", action])
        elif action == "off":
            self.turn_off()

    def turn_off(self) -> None:
        """Turn the tray integration off exactly as the Integrations page would, then exit."""
        from .catalog import remove
        from .ledger import IntegrationLedger

        ledger = IntegrationLedger(resolve_paths().integration_ledger_file, __version__)
        result = remove("tray-icon", ledger)
        log.info("tray turned off from its menu: %s", result.plain)
        self.loop.quit()

    # ---- own control interface --------------------------------------------------------
    def tray_call(  # type: ignore[no-untyped-def]
        self, _c, _sender, _p, _i, method, _params, invocation
    ) -> None:
        if method == "Quit":
            invocation.return_value(None)
            self.loop.quit()
        elif method == "Ping":
            invocation.return_value(GLib.Variant("(s)", (__version__,)))
        else:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", method)

    # ---- registration -----------------------------------------------------------------
    def register(self) -> None:
        try:
            self.conn.call_sync(
                WATCHER,
                WATCHER_PATH,
                WATCHER,
                "RegisterStatusNotifierItem",
                GLib.Variant("(s)", (self.item_name,)),
                None,
                Gio.DBusCallFlags.NONE,
                5000,
                None,
            )
            self.registered = True
            if self._no_host_source:
                GLib.source_remove(self._no_host_source)
                self._no_host_source = 0
            log.info("tray icon registered with %s", WATCHER)
        except GLib.Error as exc:
            log.warning("tray icon could not register: %s", exc.message)

    def _no_host(self) -> bool:
        if not self.registered:
            log.info("no StatusNotifier host after %ds; tray exits", NO_HOST_SECONDS)
            self.loop.quit()
        self._no_host_source = 0
        return False

    def run(self) -> int:
        item_node = Gio.DBusNodeInfo.new_for_xml(ITEM_XML)
        menu_node = Gio.DBusNodeInfo.new_for_xml(MENU_XML)
        tray_node = Gio.DBusNodeInfo.new_for_xml(TRAY_XML)

        def on_control_bus(conn: Any, _name: str) -> None:
            self.conn = conn
            conn.register_object(TRAY_PATH, tray_node.interfaces[0], self.tray_call, None, None)
            conn.register_object(
                ITEM_PATH, item_node.interfaces[0], self.item_call, self.item_property, None
            )
            conn.register_object(
                MENU_PATH, menu_node.interfaces[0], self.menu_call, self.menu_property, None
            )
            Gio.bus_own_name_on_connection(
                conn, self.item_name, Gio.BusNameOwnerFlags.NONE, None, None
            )
            Gio.bus_watch_name_on_connection(
                conn,
                WATCHER,
                Gio.BusNameWatcherFlags.NONE,
                lambda *_: self.register(),
                lambda *_: setattr(self, "registered", False),
            )
            self._no_host_source = GLib.timeout_add_seconds(NO_HOST_SECONDS, self._no_host)

        def on_lost(_conn: Any, _name: str) -> None:
            # Another tray is already running for this user; one is enough.
            log.info("tray already running; exiting")
            self.loop.quit()

        Gio.bus_own_name(
            Gio.BusType.SESSION,
            TRAY_NAME,
            Gio.BusNameOwnerFlags.DO_NOT_QUEUE,
            on_control_bus,
            None,
            on_lost,
        )
        self.loop.run()
        return 0


# ---- used by the Integrations page ---------------------------------------------------


def is_running() -> bool:
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        res = bus.call_sync(
            TRAY_NAME, TRAY_PATH, TRAY_NAME, "Ping", None, None, Gio.DBusCallFlags.NONE, 2000, None
        )
        return bool(res)
    except GLib.Error:
        return False


def start() -> tuple[bool, str]:
    if is_running():
        return True, "The tray icon is already showing."
    try:
        spawn(tray_argv())
    except GLib.Error as exc:
        return False, f"The tray icon could not be started now ({exc.message}); it starts at login."
    return True, "The tray icon is starting."


def stop() -> tuple[bool, str]:
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        bus.call_sync(
            TRAY_NAME, TRAY_PATH, TRAY_NAME, "Quit", None, None, Gio.DBusCallFlags.NONE, 2000, None
        )
        return True, "The tray icon was closed."
    except GLib.Error:
        return True, "The tray icon was not running."


def main() -> int:
    paths = resolve_paths()
    configure(paths.log_dir, also_stderr="--verbose" in sys.argv)
    return Tray().run()


if __name__ == "__main__":
    sys.exit(main())
