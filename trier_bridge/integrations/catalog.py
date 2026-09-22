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
"""The integration catalog (docs/DELIVERY-MODEL.md section 3).

Each integration knows the standard desktop extension point it uses, the exact
files it writes under the user's home, and how to undo itself. Groups let the
user pick a whole set at setup; shortcut items are never in a default group
(DEC-019). Applying and removing are per-user and need no privilege.
"""
from __future__ import annotations

import logging
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..config import StateWriteError, atomic_write_text
from ..resources import data_dir
from .ledger import AppliedIntegration, IntegrationLedger

log = logging.getLogger("trier_bridge.integrations")

APP_ID = "org.triertech.TrierBridge"
BUS_NAME = "org.triertech.TrierBridge.SearchProvider"
OBJ_PATH = "/org/triertech/TrierBridge/SearchProvider"


@dataclass(frozen=True)
class UserDirs:
    """The user's own XDG directories that integrations write under (not config.Paths)."""

    home: Path
    data: Path  # ~/.local/share
    config: Path  # ~/.config

    @classmethod
    def default(cls) -> "UserDirs":
        home = Path.home()
        return cls(
            home,
            Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share"),
            Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config"),
        )


@dataclass(frozen=True)
class Integration:
    id: str
    group: str
    title: str
    changes: str  # one line: what it changes
    reversal: str  # one line: how it is undone
    extension_point: str
    recommended: bool  # preselected in the recommended group
    individual_only: bool = False  # never part of a group selection (shortcuts)


@dataclass(frozen=True)
class ApplyResult:
    ok: bool
    plain: str
    files: tuple[str, ...] = field(default_factory=tuple)


def _desktop_entry(
    name: str, comment: str, exec_line: str, keywords: str, icon: str = APP_ID
) -> str:
    return (
        "[Desktop Entry]\nType=Application\n"
        f"Name={name}\nComment={comment}\nExec={exec_line}\nIcon={icon}\n"
        f"Terminal=false\nCategories=System;\nKeywords={keywords}\nStartupNotify=true\n"
    )


FAMILIAR_LAUNCHERS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "taskmanager",
        "Task Manager",
        "See running programs and end one of yours",
        "Task Manager;taskmgr;processes;",
        "utilities-system-monitor",
    ),
    (
        "events",
        "Event Viewer",
        "System and application log",
        "Event Viewer;eventvwr;logs;",
        "document-properties",
    ),
    (
        "devices",
        "Device Manager",
        "What hardware is present and which driver runs it",
        "Device Manager;devmgmt;hardware;",
        "computer",
    ),
    (
        "disks",
        "Disk Management",
        "Disks, partitions and where they are mounted",
        "Disk Management;diskmgmt;partitions;",
        "drive-harddisk",
    ),
    (
        "services",
        "Services",
        "Start, stop and inspect background services",
        "Services;services.msc;",
        "preferences-system",
    ),
    (
        "network",
        "Network Connections",
        "Adapters, IP addresses and DNS",
        "Network Connections;ncpa.cpl;ipconfig;",
        "preferences-system-network",
    ),
    (
        "apps",
        "Installed Apps",
        "What programs are installed and where they came from",
        "Add or Remove Programs;appwiz.cpl;Installed Apps;",
        "system-software-install",
    ),
    (
        "terminal",
        "Command Prompt",
        "Windows commands as typed Linux operations",
        "Command Prompt;cmd;",
        "utilities-terminal",
    ),
)


CATALOG: tuple[Integration, ...] = (
    Integration(
        "tray-icon",
        "Essentials",
        "Tray icon T at login",
        "Shows a small T in the top bar with a menu to open Trier Bridge or change "
        "integrations; it starts at login.",
        "Closes the icon and deletes its autostart entry from your home folder.",
        "StatusNotifier icon through the AppIndicator extension; per-user XDG autostart entry",
        True,
    ),
    Integration(
        "search-provider",
        "Essentials",
        "Windows words in the desktop search",
        "Adds a Trier Bridge search provider so Activities search understands Task Manager, "
        "Add or Remove Programs, and other familiar words.",
        "Removes two small files under your home folder; the desktop search returns to normal.",
        "GNOME Shell SearchProvider2 (per-user .ini and D-Bus service file)",
        True,
    ),
    Integration(
        "familiar-launchers",
        "Essentials",
        "Familiar tool names in the app grid",
        "Adds launchers named Task Manager, Event Viewer, Device Manager, Disk Management, "
        "Services, Network Connections, Installed Apps, Command Prompt.",
        "Deletes those launcher files from your home folder.",
        "Per-user .desktop entries in ~/.local/share/applications",
        True,
    ),
    Integration(
        "files-menu",
        "Files",
        "Trier Bridge actions in the Files right-click menu",
        "Adds 'Open Command Prompt here (Trier Bridge)' to the right-click menu "
        "of folders in Files.",
        "Deletes that extension file and the compiled copy Files made of it; Files "
        "returns to normal after it restarts.",
        "Nautilus extension in ~/.local/share/nautilus-python/extensions (needs python3-nautilus)",
        False,
    ),
    Integration(
        "shortcut-task-manager",
        "Shortcuts",
        "Ctrl+Shift+Esc opens Task Manager",
        "Adds one custom keyboard shortcut in GNOME Settings.",
        "Removes that shortcut and restores the previous list.",
        "GNOME custom keybinding (gsettings, per user)",
        False,
        individual_only=True,
    ),
)

GROUPS: tuple[str, ...] = ("Essentials", "Files", "Shortcuts")


def by_id(integration_id: str) -> Integration | None:
    return next((i for i in CATALOG if i.id == integration_id), None)


# ---- applying ---------------------------------------------------------------------


def _write(path: Path, text: str, written: list[str]) -> None:
    atomic_write_text(path, text)
    written.append(str(path))


def _apply_search_provider(paths: UserDirs, written: list[str]) -> None:
    exe = shutil.which("trier-bridge-search-provider") or "/usr/bin/trier-bridge-search-provider"
    _write(
        paths.data / "dbus-1/services" / f"{BUS_NAME}.service",
        f"[D-BUS Service]\nName={BUS_NAME}\nExec={exe}\n",
        written,
    )
    _write(
        paths.data / "gnome-shell/search-providers" / f"{APP_ID}.search-provider.ini",
        "[Shell Search Provider]\n"
        f"DesktopId={APP_ID}.desktop\nBusName={BUS_NAME}\n"
        f"ObjectPath={OBJ_PATH}\nVersion=2\n",
        written,
    )


def _apply_tray_icon(paths: UserDirs, written: list[str]) -> None:
    exe = shutil.which("trier-bridge-tray") or "/usr/bin/trier-bridge-tray"
    _write(
        paths.config / "autostart" / f"{APP_ID}.Tray.desktop",
        _desktop_entry("Trier Bridge tray icon", "The T in the top bar", exe, "")
        .replace("Terminal=false", "Terminal=false\nNoDisplay=true")
        .replace("StartupNotify=true", "X-GNOME-Autostart-enabled=true"),
        written,
    )


def _apply_familiar_launchers(paths: UserDirs, written: list[str]) -> None:
    for key, name, comment, keywords, icon in FAMILIAR_LAUNCHERS:
        _write(
            paths.data / "applications" / f"{APP_ID}.{key}.desktop",
            _desktop_entry(name, comment, f"trier-bridge --section {key}", keywords, icon),
            written,
        )


def _apply_files_menu(paths: UserDirs, written: list[str]) -> None:
    src = data_dir() / "integrations" / "tb_nautilus.py"
    if not src.is_file():
        raise FileNotFoundError("the Files extension is not installed with this build")
    dest = paths.data / "nautilus-python/extensions" / "tb_nautilus.py"
    _write(dest, src.read_text(encoding="utf-8"), written)


KEYBINDING_BASE = (
    "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/trier-bridge-taskmanager/"
)


def _apply_shortcut(rec: AppliedIntegration) -> None:
    from gi.repository import Gio, GLib

    media = Gio.Settings.new("org.gnome.settings-daemon.plugins.media-keys")
    current = list(media.get_strv("custom-keybindings"))
    rec.settings_written.append(
        {"key": "custom-keybindings", "previous": GLib.Variant("as", current).print_(False)}
    )
    if KEYBINDING_BASE not in current:
        media.set_strv("custom-keybindings", current + [KEYBINDING_BASE])
    binding = Gio.Settings.new_with_path(
        "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding", KEYBINDING_BASE
    )
    binding.set_string("name", "Trier Bridge Task Manager")
    binding.set_string("command", "trier-bridge --section taskmanager")
    binding.set_string("binding", "<Control><Shift>Escape")
    Gio.Settings.sync()


def _remove_shortcut(rec: AppliedIntegration) -> None:
    from gi.repository import Gio

    media = Gio.Settings.new("org.gnome.settings-daemon.plugins.media-keys")
    current = [k for k in media.get_strv("custom-keybindings") if k != KEYBINDING_BASE]
    media.set_strv("custom-keybindings", current)
    binding = Gio.Settings.new_with_path(
        "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding", KEYBINDING_BASE
    )
    for key in ("name", "command", "binding"):
        binding.reset(key)
    Gio.Settings.sync()


def apply(
    integration_id: str, ledger: IntegrationLedger, paths: UserDirs | None = None
) -> ApplyResult:
    paths = paths or UserDirs.default()
    item = by_id(integration_id)
    if item is None:
        return ApplyResult(False, "Unknown integration. Nothing was changed.")
    if ledger.read_only:
        return ApplyResult(
            False,
            "Integration settings are read-only (written by a newer build). "
            "Nothing was changed.",
        )
    rec = AppliedIntegration(integration_id, time.time())
    written: list[str] = []
    try:
        if integration_id == "tray-icon":
            _apply_tray_icon(paths, written)
        elif integration_id == "search-provider":
            _apply_search_provider(paths, written)
        elif integration_id == "familiar-launchers":
            _apply_familiar_launchers(paths, written)
        elif integration_id == "files-menu":
            _apply_files_menu(paths, written)
        elif integration_id == "shortcut-task-manager":
            _apply_shortcut(rec)
    except Exception as exc:  # roll back partial file writes so nothing half-applied remains
        for f in written:
            Path(f).unlink(missing_ok=True)
        log.exception("apply %s failed", integration_id)
        return ApplyResult(False, f"{item.title} could not be set up and was left off. {exc}")
    rec.files_written = written
    try:
        ledger.record(rec)
    except StateWriteError as exc:  # unrecorded means unremovable: undo now
        for f in written:
            Path(f).unlink(missing_ok=True)
        return ApplyResult(False, f"{item.title} was not recorded and was left off. {exc}")
    return ApplyResult(True, f"{item.title}: on.", tuple(written))


def _remove_compiled_copies(source: Path) -> None:
    """Files (Nautilus) compiles our extension into __pycache__; that copy goes too."""
    cache = source.parent / "__pycache__"
    if source.suffix != ".py" or not cache.is_dir():
        return
    for compiled in cache.glob(f"{source.stem}.*.pyc"):
        compiled.unlink(missing_ok=True)
    try:
        cache.rmdir()  # only if nothing else is in it
    except OSError:
        pass


def remove(integration_id: str, ledger: IntegrationLedger) -> ApplyResult:
    item = by_id(integration_id)
    rec = ledger.get(integration_id)
    if item is None or rec is None:
        return ApplyResult(True, "Already off.")
    failures: list[str] = []
    for f in rec.files_written:
        p = Path(f)
        try:
            if p.is_file():
                p.unlink()
            _remove_compiled_copies(p)
        except OSError as exc:
            failures.append(f"{p.name}: {exc}")
    if integration_id == "shortcut-task-manager":
        try:
            _remove_shortcut(rec)
        except Exception as exc:
            failures.append(f"shortcut: {exc}")
    if failures:
        return ApplyResult(
            False, f"{item.title}: some parts could not be removed: {'; '.join(failures)}"
        )
    ledger.forget(integration_id)
    return ApplyResult(True, f"{item.title}: off, everything it added was removed.")


def status(ledger: IntegrationLedger) -> dict[str, bool]:
    return {i.id: ledger.is_applied(i.id) for i in CATALOG}
