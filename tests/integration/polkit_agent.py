# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""A real polkit authentication agent for tests (DEC-021: real objects, no mocks).

polkit calls this agent exactly as it calls the desktop's own agent. In
``cancel`` mode it dismisses every prompt; in ``grant`` mode it runs the
system's setuid ``polkit-agent-helper-1`` with the test account's password
(from ``TRIER_BRIDGE_TEST_PASSWORD``, never stored in the repository), which
is how every graphical agent authenticates. It lives on its own thread with a
private system-bus connection so the product's blocking call can be answered.
"""
from __future__ import annotations

import os
import pwd
import subprocess
import threading
from typing import Any

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

AUTHORITY = "org.freedesktop.PolicyKit1"
AUTHORITY_PATH = "/org/freedesktop/PolicyKit1/Authority"
AUTHORITY_IFACE = "org.freedesktop.PolicyKit1.Authority"
AGENT_PATH = "/org/triertech/TrierBridge/PolkitTestAgent"
HELPER = "/usr/lib/polkit-1/polkit-agent-helper-1"

AGENT_XML = """
<node>
  <interface name="org.freedesktop.PolicyKit1.AuthenticationAgent">
    <method name="BeginAuthentication">
      <arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="s" direction="in"/>
      <arg type="a{ss}" direction="in"/><arg type="s" direction="in"/>
      <arg type="a(sa{sv})" direction="in"/>
    </method>
    <method name="CancelAuthentication"><arg type="s" direction="in"/></method>
  </interface>
</node>
"""


def _subject() -> tuple[str, dict[str, GLib.Variant]]:
    """polkit subject as a plain tuple, nested by the callers into their signatures."""
    session = os.environ.get("XDG_SESSION_ID", "").strip()
    if session:
        return ("unix-session", {"session-id": GLib.Variant("s", session)})
    with open("/proc/self/stat", encoding="utf-8") as fh:
        start_ticks = int(fh.read().rsplit(")", 1)[1].split()[19])
    return (
        "unix-process",
        {
            "pid": GLib.Variant("u", os.getpid()),
            "start-time": GLib.Variant("t", start_ticks),
            "uid": GLib.Variant("i", os.getuid()),
        },
    )


class PolkitTestAgent:
    def __init__(self, mode: str, password: str | None = None) -> None:
        assert mode in ("cancel", "grant")
        self.mode = mode
        self.password = password
        self.prompts: list[str] = []  # action ids polkit asked about
        self.helper_results: list[str] = []
        self._ready = threading.Event()
        self._error = ""
        self._loop: Any = None
        self._conn: Any = None
        self._thread = threading.Thread(target=self._run, name="polkit-test-agent", daemon=True)

    # ---- lifecycle ----------------------------------------------------------------
    def __enter__(self) -> "PolkitTestAgent":
        self._thread.start()
        self._ready.wait(10)
        if self._error:
            raise RuntimeError(self._error)
        return self

    def __exit__(self, *_: Any) -> None:
        if self._conn is not None:
            try:
                self._conn.call_sync(
                    AUTHORITY,
                    AUTHORITY_PATH,
                    AUTHORITY_IFACE,
                    "UnregisterAuthenticationAgent",
                    GLib.Variant("((sa{sv})s)", (_subject(), AGENT_PATH)),
                    None,
                    Gio.DBusCallFlags.NONE,
                    5000,
                    None,
                )
            except GLib.Error:
                pass
        if self._loop is not None:
            self._loop.quit()
        self._thread.join(5)

    def _run(self) -> None:
        ctx = GLib.MainContext()
        ctx.push_thread_default()
        try:
            addr = Gio.dbus_address_get_for_bus_sync(Gio.BusType.SYSTEM, None)
            self._conn = Gio.DBusConnection.new_for_address_sync(
                addr,
                Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT
                | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,
                None,
                None,
            )
            node = Gio.DBusNodeInfo.new_for_xml(AGENT_XML)
            self._conn.register_object(AGENT_PATH, node.interfaces[0], self._call, None, None)
            self._conn.call_sync(
                AUTHORITY,
                AUTHORITY_PATH,
                AUTHORITY_IFACE,
                "RegisterAuthenticationAgent",
                GLib.Variant("((sa{sv})ss)", (_subject(), "C.UTF-8", AGENT_PATH)),
                None,
                Gio.DBusCallFlags.NONE,
                5000,
                None,
            )
        except GLib.Error as exc:
            self._error = f"agent registration failed: {exc.message}"
            self._ready.set()
            return
        self._loop = GLib.MainLoop(ctx)
        self._ready.set()
        self._loop.run()
        ctx.pop_thread_default()

    # ---- the agent interface ------------------------------------------------------
    def _call(  # type: ignore[no-untyped-def]
        self, _conn, _sender, _path, _iface, method, params, invocation
    ) -> None:
        if method == "CancelAuthentication":
            invocation.return_value(None)
            return
        action_id, _message, _icon, _details, cookie, identities = params.unpack()
        self.prompts.append(action_id)
        if self.mode == "cancel":
            invocation.return_dbus_error(
                "org.freedesktop.PolicyKit1.Error.Cancelled", "dismissed by the test agent"
            )
            return
        user = self._pick_user(identities)
        if self._authenticate(user, cookie):
            invocation.return_value(None)
        else:
            invocation.return_dbus_error(
                "org.freedesktop.PolicyKit1.Error.Failed", "authentication failed"
            )

    @staticmethod
    def _pick_user(identities: list[tuple[str, dict[str, Any]]]) -> str:
        uids = [int(d["uid"]) for kind, d in identities if kind == "unix-user" and "uid" in d]
        uid = os.getuid() if os.getuid() in uids else (uids[0] if uids else os.getuid())
        return pwd.getpwuid(uid).pw_name

    def _authenticate(self, user: str, cookie: str) -> bool:
        """Drive the system's own setuid helper; it reports the result to polkit itself."""
        helper = subprocess.Popen(
            [HELPER, user],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert helper.stdin is not None and helper.stdout is not None
        ok = False
        try:
            helper.stdin.write(cookie + "\n")
            helper.stdin.flush()
            for line in helper.stdout:
                line = line.rstrip("\n")
                if line.startswith("PAM_PROMPT_ECHO"):
                    helper.stdin.write((self.password or "") + "\n")
                    helper.stdin.flush()
                elif line.startswith("SUCCESS"):
                    ok = True
                elif line.startswith("FAILURE"):
                    ok = False
                self.helper_results.append(line if "Password" not in line else "PAM_PROMPT")
        finally:
            try:
                helper.stdin.close()
            except OSError:
                pass
            helper.wait(15)
        return ok
