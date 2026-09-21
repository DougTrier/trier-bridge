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
  TRIER_BRIDGE_DEV_SECTION=<key>       open that sidebar section at start
  TRIER_BRIDGE_DEV_CANCEL_SCREENSHOT_AFTER=<seconds>  close an open portal screenshot request
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .. import APP_ID, APP_NAME, __version__  # noqa: E402
from ..config import Paths  # noqa: E402
from ..integrations.ledger import IntegrationLedger  # noqa: E402
from ..state.journal import OperationJournal  # noqa: E402
from ..state.preferences import Preferences  # noqa: E402
from .window import MainWindow  # noqa: E402

log = logging.getLogger("trier_bridge.ui")


class TrierBridgeApplication(Adw.Application):  # type: ignore[misc]
    def __init__(
        self, paths: Paths, journal: OperationJournal, options: dict[str, str] | None = None
    ) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.paths = paths
        self.journal = journal
        self.options = options or {}
        self.preferences = Preferences(paths.preferences_file)
        self.ledger = IntegrationLedger(paths.integration_ledger_file, __version__)
        GLib.set_application_name(APP_NAME)
        GLib.set_prgname("trier-bridge")  # AT-SPI application name (RESEARCH F17)
        self._window: MainWindow | None = None
        self._add_action("about", self._on_about)
        self._add_action("quit", lambda *_: self.quit())
        self._add_param_action("open-section", self._on_open_section)
        self._add_param_action("open-concept", self._on_open_concept)
        self._add_param_action("open-terminal-at", self._on_open_terminal_at)
        self.set_accels_for_action("app.quit", ["<Control>q"])

    def _add_action(self, name: str, callback: Any) -> None:
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)

    def _add_param_action(self, name: str, callback: Any) -> None:
        action = Gio.SimpleAction.new(name, GLib.VariantType.new("s"))
        action.connect("activate", callback)
        self.add_action(action)

    def _on_open_section(self, _action: Any, param: Any) -> None:
        self.do_activate()
        if self._window is not None:
            self._window.select_section(str(param.get_string()))

    def _on_open_concept(self, _action: Any, param: Any) -> None:
        self.do_activate()
        if self._window is not None:
            self._window.open_concept(str(param.get_string()))

    def _on_open_terminal_at(self, _action: Any, param: Any) -> None:
        self.do_activate()
        if self._window is not None:
            self._window.open_terminal_at(str(param.get_string()))

    def do_activate(self) -> None:
        if self._window is None:
            self._window = MainWindow(application=self)
            self._window.show_unresolved(self.journal.unresolved())
            self._install_dev_aids(self._window)
        section = self.options.get("section", "")
        if section:
            self._window.select_section(section)
        concept = self.options.get("open", "")
        if concept:
            self._window.open_concept(concept)
        self.options = {}
        if not self.ledger.setup_completed and not self.ledger.read_only:
            GLib.idle_add(self._window.show_setup)
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
        section = os.environ.get("TRIER_BRIDGE_DEV_SECTION", "")
        if section:
            window.select_section(section)
        if snapshot:
            self._snapshot_tries = 0
            GLib.timeout_add(1500, self._dev_snapshot, window, snapshot)
        cancel_shot = os.environ.get("TRIER_BRIDGE_DEV_CANCEL_SCREENSHOT_AFTER", "")
        if cancel_shot:
            GLib.timeout_add(int(float(cancel_shot) * 1000), self._dev_cancel_screenshot, window)
        if quit_after:
            try:
                seconds = float(quit_after)
            except ValueError:
                seconds = 5.0
            GLib.timeout_add(int(seconds * 1000), self._dev_quit)

    def _dev_snapshot(self, window: MainWindow, path: str) -> bool:
        try:
            # Render the window's current widget tree to a texture through its own renderer.
            paintable = Gtk.WidgetPaintable.new(window)
            width = paintable.get_intrinsic_width() or window.get_width()
            height = paintable.get_intrinsic_height() or window.get_height()
            snapshot = Gtk.Snapshot()
            paintable.snapshot(snapshot, width, height)
            node = snapshot.to_node()
            renderer = window.get_native().get_renderer()
            if node is None or renderer is None:
                self._snapshot_tries += 1
                if self._snapshot_tries < 10:
                    return True  # not laid out yet; try again on the next tick
                log.warning("dev snapshot: nothing to render after %d tries", self._snapshot_tries)
                return False
            texture = renderer.render_texture(node, None)
            if isinstance(texture, Gdk.Texture):
                texture.save_to_png(path)
                log.info("dev snapshot saved to %s (%dx%d)", path, width, height)
            else:
                log.warning("dev snapshot: renderer returned no texture")
        except Exception as exc:  # development aid only; never affects the product path
            log.warning("dev snapshot failed: %s", exc)
        return False

    def _dev_cancel_screenshot(self, window: MainWindow) -> bool:
        window.cancel_screenshot()
        return False

    def _dev_quit(self) -> bool:
        self.quit()
        return False


def run(
    argv: list[str], paths: Paths, journal: OperationJournal, options: dict[str, str] | None = None
) -> int:
    opts = options or {}
    if not Gtk.init_check():  # no display: say so plainly instead of a traceback in a callback
        log.error("no display could be opened")
        print(
            "Trier Bridge needs a desktop session to show its window (no display could be "
            "opened). Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    app = TrierBridgeApplication(paths, journal, opts)
    app.register(None)
    if app.get_is_remote():
        # Already running: hand the request to that window and leave (single instance).
        if opts.get("cwd") and opts.get("section") == "terminal":
            app.activate_action("open-terminal-at", GLib.Variant("s", opts["cwd"]))
        elif opts.get("section"):
            app.activate_action("open-section", GLib.Variant("s", opts["section"]))
        elif opts.get("open"):
            app.activate_action("open-concept", GLib.Variant("s", opts["open"]))
        else:
            app.activate()
        return 0
    return int(app.run(argv))
