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
"""The Adw.Application: single instance per session, theme follows the desktop.

Development aids (never active unless the environment variable is set):
  TRIER_BRIDGE_DEV_SNAPSHOT=<file.png>  save an image of the main window after it is shown
  TRIER_BRIDGE_DEV_QUIT_AFTER=<seconds> quit automatically (automated runs)
"""
from __future__ import annotations

import logging
import os
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .. import APP_ID, APP_NAME, __version__  # noqa: E402
from .window import MainWindow  # noqa: E402

log = logging.getLogger("trier_bridge.ui")


class TrierBridgeApplication(Adw.Application):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        GLib.set_application_name(APP_NAME)
        GLib.set_prgname("trier-bridge")  # AT-SPI application name (RESEARCH F17)
        self._window: MainWindow | None = None
        self._add_action("about", self._on_about)
        self._add_action("quit", lambda *_: self.quit())
        self.set_accels_for_action("app.quit", ["<Control>q"])

    def _add_action(self, name: str, callback: Any) -> None:
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)

    def do_activate(self) -> None:
        if self._window is None:
            self._window = MainWindow(application=self)
            self._install_dev_aids(self._window)
        self._window.present()

    def _on_about(self, *_: Any) -> None:
        about = Adw.AboutDialog(
            application_name=APP_NAME,
            application_icon=APP_ID,
            developer_name="Doug Trier",
            version=__version__,
            license_type=Gtk.License.APACHE_2_0,
            comments="Everything you know. Linux underneath.",
            copyright="Copyright 2026 Doug Trier",
        )
        about.present(self._window)

    # ---- development aids -------------------------------------------------
    def _install_dev_aids(self, window: MainWindow) -> None:
        snapshot = os.environ.get("TRIER_BRIDGE_DEV_SNAPSHOT", "")
        quit_after = os.environ.get("TRIER_BRIDGE_DEV_QUIT_AFTER", "")
        if snapshot:
            GLib.timeout_add(1500, self._dev_snapshot, window, snapshot)
        if quit_after:
            try:
                seconds = float(quit_after)
            except ValueError:
                seconds = 5.0
            GLib.timeout_add(int(seconds * 1000), self._dev_quit)

    def _dev_snapshot(self, window: MainWindow, path: str) -> bool:
        try:
            paintable = Gtk.WidgetPaintable.new(window)
            image = paintable.get_current_image()
            if isinstance(image, Gdk.Texture):
                image.save_to_png(path)
                log.info("dev snapshot saved to %s", path)
            else:
                log.warning("dev snapshot: no texture available")
        except Exception as exc:  # development aid only; never affects the product path
            log.warning("dev snapshot failed: %s", exc)
        return False

    def _dev_quit(self) -> bool:
        self.quit()
        return False


def run(argv: list[str]) -> int:
    app = TrierBridgeApplication()
    return int(app.run(argv))
