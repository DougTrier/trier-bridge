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
"""Event Viewer data: the systemd journal through the native sd-journal API.

Uses libsystemd directly (ctypes), the native API the code-quality standard
prefers over parsing CLI output (CODE-QUALITY section 12, TB-INV-045). No
dependency beyond what Ubuntu ships.

SECURITY: log text is untrusted data. Control characters are stripped before
anything reaches the UI (TB-INV-100, TB-INV-144); nothing in a message is ever
interpreted or opened (TB-INV-148). Reads are bounded by entry count and
cancellable between entries (TB-INV-146). Access restrictions are reported as
restricted, not as "no events" (TB-INV-145). Familiar views are filters; the
native fields ride along untouched (TB-INV-068, TB-INV-147).
"""
from __future__ import annotations

import ctypes
import ctypes.util
import os
import re
import threading
from dataclasses import dataclass
from enum import Enum, unique

SD_JOURNAL_LOCAL_ONLY = 1 << 0
DEFAULT_LIMIT = 500
FIELDS = (
    "MESSAGE",
    "PRIORITY",
    "_SYSTEMD_UNIT",
    "_SYSTEMD_USER_UNIT",
    "SYSLOG_IDENTIFIER",
    "_COMM",
    "_PID",
    "_UID",
    "_TRANSPORT",
    "_HOSTNAME",
    "_BOOT_ID",
)

_CONTROL_RX = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[@-Z\\-_]"
)


def sanitize(text: str) -> str:
    """Strip ANSI escapes and control characters; keep tabs and newlines as spaces."""
    text = _CONTROL_RX.sub("", text)
    return text.replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()


@unique
class Level(Enum):
    ERROR = "Error"
    WARNING = "Warning"
    INFORMATION = "Information"
    DEBUG = "Debug"
    UNKNOWN = "Unknown"


def level_for_priority(priority: str | None) -> Level:
    try:
        p = int(priority) if priority is not None else -1
    except ValueError:
        return Level.UNKNOWN
    if p < 0:
        return Level.UNKNOWN
    if p <= 3:
        return Level.ERROR
    if p == 4:
        return Level.WARNING
    if p <= 6:
        return Level.INFORMATION
    return Level.DEBUG


@unique
class View(Enum):
    """Familiar Windows Event Viewer views, as filters over the one journal."""

    ALL = "All events"
    ERRORS = "Errors and warnings"
    SYSTEM = "System"
    APPLICATION = "Application"
    SECURITY = "Security"
    BOOT = "Boot and hardware"


SECURITY_IDENTIFIERS = {
    "sudo",
    "sshd",
    "polkitd",
    "gdm",
    "gdm-password]",
    "gnome-keyring-daemon",
    "su",
    "login",
    "systemd-logind",
    "PackageKit",
    "gdm-session-worker",
}


@dataclass(frozen=True)
class Entry:
    realtime_usec: int
    level: Level
    message: str
    source: str  # unit or identifier or comm, whatever is most specific
    fields: dict[str, str]  # native fields, sanitized, provenance preserved (TB-INV-147)

    @property
    def transport(self) -> str:
        return self.fields.get("_TRANSPORT", "")

    def matches(self, view: View) -> bool:
        f = self.fields
        if view is View.ALL:
            return True
        if view is View.ERRORS:
            return self.level in (Level.ERROR, Level.WARNING)
        if view is View.BOOT:
            return self.transport in ("kernel", "audit")
        ident = f.get("SYSLOG_IDENTIFIER", "") or f.get("_COMM", "")
        if view is View.SECURITY:
            return ident in SECURITY_IDENTIFIERS or f.get("_SYSTEMD_UNIT", "") in (
                "ssh.service",
                "gdm.service",
                "polkit.service",
                "systemd-logind.service",
            )
        if view is View.SYSTEM:
            return (
                bool(f.get("_SYSTEMD_UNIT"))
                and not f.get("_SYSTEMD_USER_UNIT")
                and self.transport != "kernel"
            )
        # View.APPLICATION: user units, and anything that is neither a system unit nor kernel/audit
        return bool(f.get("_SYSTEMD_USER_UNIT")) or (
            not f.get("_SYSTEMD_UNIT") and self.transport not in ("kernel", "audit")
        )


@dataclass(frozen=True)
class JournalAccess:
    available: bool
    system_readable: bool  # False: only this user's entries (TB-INV-145)
    detail: str


def journal_access() -> JournalAccess:
    lib = ctypes.util.find_library("systemd")
    if lib is None:
        return JournalAccess(False, False, "libsystemd is not present; the journal cannot be read.")
    groups: set[str] = set()
    uid = -1
    try:
        import grp
        import pwd

        uid = os.getuid()
        user = pwd.getpwuid(uid).pw_name
        groups = {g.gr_name for g in grp.getgrall() if user in g.gr_mem}
        groups.add(grp.getgrgid(os.getgid()).gr_name)
    except (KeyError, OSError, ImportError, AttributeError):
        pass
    if uid == 0 or groups & {"adm", "systemd-journal", "wheel"}:
        return JournalAccess(
            True, True, "System and user log entries are readable for this account."
        )
    return JournalAccess(
        True,
        False,
        "The system log is restricted for this account; only this user's entries are shown.",
    )


class JournalReader:
    """Bounded, cancellable read of the newest entries through sd-journal."""

    def __init__(self) -> None:
        name = ctypes.util.find_library("systemd")
        self._lib = ctypes.CDLL(name) if name else None
        self.cancel = threading.Event()
        if self._lib is not None:
            L = self._lib
            L.sd_journal_open.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
            L.sd_journal_close.argtypes = [ctypes.c_void_p]
            L.sd_journal_seek_tail.argtypes = [ctypes.c_void_p]
            L.sd_journal_previous.argtypes = [ctypes.c_void_p]
            L.sd_journal_get_data.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
                ctypes.POINTER(ctypes.c_void_p),
                ctypes.POINTER(ctypes.c_size_t),
            ]
            L.sd_journal_get_realtime_usec.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_uint64),
            ]

    @property
    def available(self) -> bool:
        return self._lib is not None

    def _field(self, j: ctypes.c_void_p, name: str) -> str | None:
        data = ctypes.c_void_p()
        length = ctypes.c_size_t()
        if self._lib is None:
            return None
        rc = self._lib.sd_journal_get_data(
            j, name.encode(), ctypes.byref(data), ctypes.byref(length)
        )
        if rc < 0 or not data.value:
            return None
        raw = ctypes.string_at(data.value, length.value)
        key, _, value = raw.partition(b"=")
        return value.decode("utf-8", "replace")

    def newest(self, limit: int = DEFAULT_LIMIT) -> list[Entry]:
        """Newest ``limit`` entries, newest first. Empty list when the journal is unavailable."""
        if self._lib is None:
            return []
        L = self._lib
        j = ctypes.c_void_p()
        if L.sd_journal_open(ctypes.byref(j), SD_JOURNAL_LOCAL_ONLY) < 0:
            return []
        out: list[Entry] = []
        try:
            if L.sd_journal_seek_tail(j) < 0:
                return []
            while len(out) < limit and not self.cancel.is_set():
                if L.sd_journal_previous(j) <= 0:
                    break
                fields: dict[str, str] = {}
                for name in FIELDS:
                    v = self._field(j, name)
                    if v is not None:
                        fields[name] = sanitize(v)
                usec = ctypes.c_uint64()
                L.sd_journal_get_realtime_usec(j, ctypes.byref(usec))
                source = (
                    fields.get("_SYSTEMD_USER_UNIT")
                    or fields.get("_SYSTEMD_UNIT")
                    or fields.get("SYSLOG_IDENTIFIER")
                    or fields.get("_COMM")
                    or ("kernel" if fields.get("_TRANSPORT") == "kernel" else "Unknown")
                )
                out.append(
                    Entry(
                        realtime_usec=int(usec.value),
                        level=level_for_priority(fields.get("PRIORITY")),
                        message=fields.get("MESSAGE", "")[:2000],
                        source=source,
                        fields=fields,
                    )
                )
        finally:
            L.sd_journal_close(j)
        return out
