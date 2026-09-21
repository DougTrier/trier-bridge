# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""IMP-03.09: office-user journeys driven through the accessibility interface (console session).

The product is started as a real process in the desktop session; every step is
what a screen-reader or switch user could do: set text in the search field,
activate the button, read what the window says. Skipped without a console session.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

gi = pytest.importorskip("gi")
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi, GLib  # noqa: E402

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.environ.get("WAYLAND_DISPLAY"), reason="needs the console session"),
]
ROOT = Path(__file__).resolve().parents[2]
APP = "trier-bridge"


def _app():
    desktop = Atspi.get_desktop(0)
    for i in range(desktop.get_child_count()):
        a = desktop.get_child_at_index(i)
        if a is not None and (a.get_name() or "") == APP:
            return a
    return None


def _find(node, role: str, name: str, depth: int = 0):
    if node is None or depth > 40:
        return None
    try:
        if node.get_role_name() == role and (node.get_name() or "") == name:
            return node
        for i in range(node.get_child_count()):
            hit = _find(node.get_child_at_index(i), role, name, depth + 1)
            if hit is not None:
                return hit
    except Exception:
        return None
    return None


def _texts(node, depth: int = 0, out: list[str] | None = None) -> list[str]:
    out = [] if out is None else out
    if node is None or depth > 40:
        return out
    try:
        name = node.get_name() or ""
        if name:
            out.append(name)
        for i in range(node.get_child_count()):
            _texts(node.get_child_at_index(i), depth + 1, out)
    except Exception:
        pass
    return out


def _wait(predicate, seconds: float):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        # libatspi caches children and updates them from events; a test process has no
        # main loop of its own, so pump the default context and drop the app's cache
        ctx = GLib.MainContext.default()
        for _ in range(20):
            if not ctx.iteration(False):
                break
        app = _app()
        if app is not None:
            app.clear_cache()
        value = predicate()
        if value:
            return value
        time.sleep(0.3)
    return None


@pytest.fixture()
def running_app():
    env = dict(os.environ, GTK_A11Y="atspi", TRIER_BRIDGE_DEV_QUIT_AFTER="90")
    proc = subprocess.Popen(
        [sys.executable, "-m", "trier_bridge", "--section", "home"],  # not the remembered page
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        app = _wait(
            lambda: _find(_app(), "entry", "Search for anything you know from Windows") and _app(),
            20,
        )
        assert app is not None, "the window did not appear in the accessibility tree"
        yield app
    finally:
        proc.terminate()
        proc.wait(10)


def _set_text(node, text: str) -> None:
    et = node.get_editable_text_iface()
    assert et is not None and et.set_text_contents(text)


def _click(node) -> None:
    act = node.get_action_iface()
    assert act is not None and act.do_action(0)


def test_journey_add_or_remove_programs_leads_to_installed_apps(running_app) -> None:
    """A Windows word typed on Home, one button, and the Installed Apps page is showing."""
    entry = _find(_app(), "entry", "Search for anything you know from Windows")
    assert entry is not None
    _set_text(entry, "Add or Remove Programs")
    show = _wait(lambda: _find(_app(), "push button", "Show"), 5)
    assert show is not None, _texts(_app())[:40]
    _click(show)
    heading = _wait(lambda: _find(_app(), "label", "Installed Apps"), 5)
    assert heading is not None
    # the list fills from the real desktop entries; at least the search field of the page exists
    assert _wait(lambda: _find(_app(), "entry", "Find an installed program"), 5) is not None


def test_journey_no_equivalent_is_said_not_pretended(running_app) -> None:
    """Registry Editor: the answer is the truth, with no Open button (TB-INV-105)."""
    entry = _find(_app(), "entry", "Search for anything you know from Windows")
    assert entry is not None
    _set_text(entry, "regedit")
    label = _wait(lambda: _find(_app(), "label", "No equivalent"), 5)
    assert label is not None
    assert _find(_app(), "push button", "Open") is None


def test_journey_terminal_answers_a_windows_command(running_app) -> None:
    """Command Prompt: ipconfig typed as on Windows answers with this computer's facts."""
    row = _wait(lambda: _find(_app(), "list item", "Command Prompt"), 5)
    assert row is not None
    # sidebar rows carry no action; the app forwards --section to the running instance
    subprocess.run(
        [sys.executable, "-m", "trier_bridge", "--section", "terminal"], cwd=ROOT, check=True
    )
    entry = _wait(lambda: _find(_app(), "text", "Bridge command"), 5)
    assert entry is not None
    _set_text(entry, "hostname")
    _click(_find(_app(), "push button", "Run"))
    output = _wait(lambda: _find(_app(), "text", "Bridge Terminal output"), 5)
    assert output is not None
    ti = output.get_text_iface()

    def whole() -> str:
        return str(Atspi.Text.get_text(ti, 0, Atspi.Text.get_character_count(ti)))

    text = _wait(lambda: whole() if "[Linux:" in whole() else None, 8)
    assert text is not None and os.uname().nodename in text
