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
"""Network diagnostics a Windows user reaches for first: nslookup, ping, tracert, flushdns.

nslookup is answered in-process (the system resolver plus systemd-resolved's
own lookup and server list). ping and tracert cannot be sent from an
unprivileged process on Ubuntu (ICMP sockets are reserved: ping_group_range is
empty), so they open the system's own ping or tracepath in a terminal window
with a validated host name, exactly as the PowerShell entry does; no shell of
ours is involved (TB-SEC-003). Flushing the DNS cache is one D-Bus call to
systemd-resolved, verified by re-reading its cache statistics.

TB-INV-101: commands that may hang need documented timeout/cancellation
behavior. Every D-Bus call here goes through ``Bus``, which already bounds
its calls (``CALL_TIMEOUT_MS``); ``ping``/``tracert`` hand off to a separate
terminal window and return immediately. The one call in this module with no
native timeout is the standard-library resolver (``socket.getaddrinfo``,
``socket.getfqdn``), which can block far longer than a user will wait against
an unreachable or slow name server. ``_bounded`` wraps such a call with a
wall-clock deadline; past the deadline it returns a timeout error while the
call itself keeps running to completion on an orphaned daemon thread (Python
has no way to force a blocked libc call to return early), which is safe here
because the call only reads and writes nothing Trier Bridge owns.
"""
from __future__ import annotations

import ipaddress
import re
import shutil
import socket
import threading
from dataclasses import dataclass, field
from typing import Callable, TypeVar

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from .bus import Bus  # noqa: E402

_T = TypeVar("_T")
RESOLVE_TIMEOUT_S = 5.0


def _bounded(fn: Callable[[], _T], timeout_s: float, what: str) -> tuple[_T | None, str]:
    """Run a blocking call under a wall-clock bound. Returns ``(value, "")`` on success
    or ``(None, message)`` on an ``OSError`` from the call or on timing out."""
    result: list[_T] = []
    error: list[OSError] = []
    done = threading.Event()

    def work() -> None:
        try:
            result.append(fn())
        except OSError as exc:
            error.append(exc)
        finally:
            done.set()

    threading.Thread(target=work, name=f"tb-{what}", daemon=True).start()
    if not done.wait(timeout_s):
        return None, f"No answer from the resolver within {timeout_s:g} seconds."
    if error:
        return None, str(error[0].strerror or error[0])
    return (result[0] if result else None), ""


RESOLVED = "org.freedesktop.resolve1"
RESOLVED_PATH = "/org/freedesktop/resolve1"
RESOLVED_MANAGER = f"{RESOLVED}.Manager"
_LABEL = r"[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
_HOST = re.compile(r"^(?=.{1,253}$)" + _LABEL + r"(\." + _LABEL + r")*\.?$")


def valid_host(text: str) -> str:
    """A host name or IP address as typed, or ValueError with a plain reason (TB-INV-119)."""
    t = text.strip()
    try:
        return str(ipaddress.ip_address(t))
    except ValueError:
        pass
    if _HOST.match(t):
        return t
    raise ValueError(f"'{text}' is not a host name or IP address.")


@dataclass(frozen=True)
class Lookup:
    name: str
    addresses: tuple[str, ...]
    canonical: str = ""
    servers: tuple[str, ...] = field(default_factory=tuple)  # DNS servers in use
    error: str = ""


def dns_servers(bus: Bus | None = None) -> tuple[str, ...]:
    bus = bus or Bus.system()
    value, err = bus.property(RESOLVED, RESOLVED_PATH, RESOLVED_MANAGER, "DNS")
    if err or not value:
        return ()
    out = []
    for _ifindex, family, raw in value:
        try:
            out.append(str(ipaddress.ip_address(bytes(raw))))
        except ValueError:
            continue
    return tuple(dict.fromkeys(out))


def lookup(name: str, bus: Bus | None = None) -> Lookup:
    """Windows nslookup: what this name resolves to and which servers answer here.

    TB-INV-101: an unreachable or slow name server can make the standard-library
    resolver block far longer than a Bridge Terminal user will wait, with no
    native timeout parameter to bound it; ``_bounded`` gives both resolver calls
    a wall-clock deadline instead."""
    host = valid_host(name)
    servers = dns_servers(bus)
    infos, err = _bounded(
        lambda: socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP),
        RESOLVE_TIMEOUT_S,
        "nslookup",
    )
    if err or infos is None:
        return Lookup(host, (), "", servers, err or "The resolver returned no result.")
    addresses = tuple(dict.fromkeys(str(i[4][0]) for i in infos))
    canonical = ""
    if not _is_ip(host):
        fqdn, _ = _bounded(lambda: socket.getfqdn(host), RESOLVE_TIMEOUT_S, "nslookup-fqdn")
        canonical = fqdn or ""
    return Lookup(host, addresses, canonical if canonical != host else "", servers)


def _is_ip(text: str) -> bool:
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


def cache_size(bus: Bus | None = None) -> int | None:
    bus = bus or Bus.system()
    value, err = bus.property(RESOLVED, RESOLVED_PATH, RESOLVED_MANAGER, "CacheStatistics")
    if err or not value:
        return None
    return int(value[0])


def flush_dns(bus: Bus | None = None) -> tuple[bool, str]:
    """ipconfig /flushdns: systemd-resolved drops its cache; verified by the size afterwards."""
    bus = bus or Bus.system()
    if bus.conn is None:
        return False, f"The system bus is not reachable: {bus.error}"
    try:
        bus.conn.call_sync(
            RESOLVED,
            RESOLVED_PATH,
            RESOLVED_MANAGER,
            "FlushCaches",
            None,
            None,
            Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION,
            10000,
            None,
        )
    except GLib.Error as exc:
        low = exc.message.lower()
        if "access" in low or "authoriz" in low:
            return False, "Linux did not grant permission to flush the DNS cache."
        return False, f"The resolver did not flush its cache: {exc.message}"
    size = cache_size(bus)
    if size == 0:
        return True, "Successfully flushed the DNS Resolver Cache."
    return False, f"The flush returned but the resolver still reports {size} cached entries."


def diagnostic_tool(kind: str) -> tuple[str, list[str]]:
    """(program, base argv) for ping or tracert on this system, or ('', []) if absent."""
    if kind == "ping":
        exe = shutil.which("ping")
        return (exe, [exe, "-c", "4"]) if exe else ("", [])
    for candidate in ("tracepath", "traceroute"):
        exe = shutil.which(candidate)
        if exe:
            return exe, [exe]
    return "", []


_STAY_OPEN_TAIL = "; echo; printf '%s' 'Press Enter to close... '; read _"


def run_in_terminal(argv: list[str], title: str) -> tuple[bool, str]:
    """Open the desktop's terminal running a fixed program with validated arguments.

    The terminal's own "close when the command exits" behavior would otherwise
    close the window the instant ping/tracepath finishes (a few seconds), before
    the user can read the replies. ``_STAY_OPEN_TAIL`` is a fixed string with no
    user-controlled content, appended after the already-quoted argv so the shell
    pauses for a keypress instead (TB-SEC-003: still no shell of ours runs
    unvalidated text, only this constant plus individually quoted argv tokens).
    """
    commandline = " ".join(GLib.shell_quote(a) for a in argv) + _STAY_OPEN_TAIL
    try:
        info = Gio.AppInfo.create_from_commandline(
            commandline, title, Gio.AppInfoCreateFlags.NEEDS_TERMINAL
        )
        ok = bool(info.launch([], None))
    except GLib.Error as exc:
        return False, f"The terminal window could not be opened: {exc.message}"
    return (
        (True, f"{title} opened in a terminal window.")
        if ok
        else (False, "The terminal window could not be opened.")
    )
