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
"""Print Screen: the desktop's own screenshot tool through the portal (IMP-03.08).

Trier Bridge never captures pixels itself. It asks xdg-desktop-portal for an
interactive screenshot, which brings up GNOME's screenshot UI exactly as the
Print Screen key does; the user picks the area and confirms or cancels there.
The answer is a file URI or a cancellation, reported in plain words. Nothing
is captured or saved without the user acting in that UI (TB-INV-119).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Callable

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from .launch import LaunchResult  # noqa: E402

log = logging.getLogger("trier_bridge.desktop.screenshot")

PORTAL = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
SCREENSHOT_IFACE = "org.freedesktop.portal.Screenshot"
REQUEST_IFACE = "org.freedesktop.portal.Request"
NO_ANSWER_SECONDS = 60  # the tool either appeared or it did not; do not wait forever

_counter = 0


class ScreenshotRequest:
    """One interactive screenshot through the portal; the result arrives on the main loop."""

    def __init__(self, on_done: Callable[[LaunchResult], None]) -> None:
        self._on_done = on_done
        self._conn: Any = None
        self._sub = 0
        self.request_path = ""
        self._watchdog = 0
        self._done = False

    def start(self) -> LaunchResult:
        global _counter
        try:
            self._conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error as exc:
            return LaunchResult(False, "The session bus is not reachable.", exc.message)
        _counter += 1
        token = f"trierbridge{os.getpid()}_{_counter}"
        sender = (self._conn.get_unique_name() or "").lstrip(":").replace(".", "_")
        self.request_path = f"/org/freedesktop/portal/desktop/request/{sender}/{token}"
        # Subscribe before calling so a fast Response cannot be missed (portal contract).
        self._sub = self._conn.signal_subscribe(
            PORTAL,
            REQUEST_IFACE,
            "Response",
            self.request_path,
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_response,
        )
        options = {
            "handle_token": GLib.Variant("s", token),
            "interactive": GLib.Variant("b", True),
            "modal": GLib.Variant("b", False),
        }
        self._conn.call(
            PORTAL,
            PORTAL_PATH,
            SCREENSHOT_IFACE,
            "Screenshot",
            GLib.Variant("(sa{sv})", ("", options)),
            None,
            Gio.DBusCallFlags.NONE,
            10000,
            None,
            self._on_called,
        )
        log.info("screenshot request %s sent to the portal", self.request_path)
        self._watchdog = GLib.timeout_add_seconds(NO_ANSWER_SECONDS, self._no_answer)
        return LaunchResult(
            True,
            "Asked the desktop for a screenshot; its screenshot tool should appear now. "
            "If it does not, press Print Screen.",
        )

    def _no_answer(self) -> bool:
        """Neither a picture nor a cancellation arrived: say so, and stop waiting."""
        self._watchdog = 0
        if not self._done:
            self.cancel()
            self._finish(
                LaunchResult(
                    False,
                    f"The desktop screenshot tool gave no answer within {NO_ANSWER_SECONDS} "
                    "seconds. Press Print Screen to use it directly.",
                    "portal request without Response; closed",
                )
            )
        return False

    def _on_called(self, conn: Any, res: Any) -> None:
        try:
            conn.call_finish(res)
        except GLib.Error as exc:
            self._finish(
                LaunchResult(
                    False, "The screenshot tool could not be opened on this desktop.", exc.message
                )
            )

    def _on_response(self, _c: Any, _s: Any, _p: Any, _i: Any, _sig: Any, params: Any) -> None:
        code, results = params.unpack()
        if code == 0:
            uri = str(results.get("uri", ""))
            path = GLib.filename_from_uri(uri)[0] if uri.startswith("file://") else uri
            self._finish(LaunchResult(True, f"Screenshot saved: {path}", uri))
        elif code == 1:
            self._finish(LaunchResult(False, "Screenshot cancelled.", "portal response 1"))
        else:
            self._finish(LaunchResult(False, "The screenshot did not happen.", f"portal {code}"))

    def cancel(self) -> None:
        if self._conn is not None and self.request_path:
            try:
                self._conn.call_sync(
                    PORTAL,
                    self.request_path,
                    REQUEST_IFACE,
                    "Close",
                    None,
                    None,
                    Gio.DBusCallFlags.NONE,
                    3000,
                    None,
                )
            except GLib.Error as exc:
                log.info("screenshot request close: %s", exc.message)

    def _finish(self, result: LaunchResult) -> None:
        if self._done:
            return
        self._done = True
        if self._watchdog:
            GLib.source_remove(self._watchdog)
            self._watchdog = 0
        log.info(
            "screenshot request %s: %s (%s)", self.request_path, result.plain, result.technical
        )
        if self._conn is not None and self._sub:
            self._conn.signal_unsubscribe(self._sub)
            self._sub = 0
        self._on_done(result)
