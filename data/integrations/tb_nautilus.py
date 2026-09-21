# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Trier Bridge Files integration (Nautilus python extension).

Copied into ~/.local/share/nautilus-python/extensions by the user's own choice
at setup, and deleted when the integration is turned off. Adds one context-menu
item to folders; it opens Trier Bridge with a fixed argument list. No shell.
"""
import urllib.parse

import gi

gi.require_version("Nautilus", "4.0")
from gi.repository import GLib, Nautilus, GObject  # noqa: E402


def _path(item):
    uri = item.get_uri()
    if not uri.startswith("file://"):
        return None
    return urllib.parse.unquote(uri[len("file://") :])


def _launch(argv):
    GLib.spawn_async(argv, flags=GLib.SpawnFlags.SEARCH_PATH | GLib.SpawnFlags.DO_NOT_REAP_CHILD)


class TrierBridgeMenu(GObject.GObject, Nautilus.MenuProvider):
    def _items(self, folder):
        path = _path(folder)
        if path is None:
            return []
        prompt = Nautilus.MenuItem(
            name="TrierBridge::prompt",
            label="Open Command Prompt here (Trier Bridge)",
            tip="Bridge Terminal, starting in this folder",
        )
        prompt.connect(
            "activate", lambda *_: _launch(["trier-bridge", "--section", "terminal", "--cwd", path])
        )
        return [prompt]

    def get_background_items(self, folder):
        return self._items(folder)

    def get_file_items(self, files):
        if len(files) == 1 and files[0].is_directory():
            return self._items(files[0])
        return []
