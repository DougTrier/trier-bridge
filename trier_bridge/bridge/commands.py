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
"""Bridge command implementations (IMP-07.02, IMP-07.03).

Every read-only command maps to a Foundation 04 adapter; output is familiar
in shape but never fabricates fields (TB-INV-096) and stays bounded
(TB-INV-099). Mutating commands (taskkill) build the same typed operation the
GUI uses and return it for confirmation rather than executing here
(TB-INV-094, TB-INV-104). Each result carries the Linux equivalent for
teaching (TB-INV-080).
"""
from __future__ import annotations

import re
import shutil

import os
import platform
import socket
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum, unique
from pathlib import Path
from typing import Callable

from ..capability.facts import distro_from_os_release, parse_os_release
from ..core.identity import ProcessIdentity
from ..core.state import PrivilegeClass, OperationState
from ..system.driveletters import to_linux_path, to_windows_path
from .cmdlets import cmdlet_for, cmdlet_lines
from .grammar import COMMANDS, BridgeCommand, CommandSpec, ParseFailure, parse

MAX_OUTPUT_LINES = 400
MAX_FILE_BYTES = 64 * 1024


@unique
class Exit(Enum):
    OK = 0
    PARSE_ERROR = 2
    UNSUPPORTED = 3
    DENIED = 4
    FAILED = 5
    NEEDS_CONFIRMATION = 6
    TRUNCATED = 7


@dataclass(frozen=True)
class CommandOutput:
    exit: Exit
    lines: tuple[str, ...]
    linux_equivalent: str = ""
    performed: bool = False  # True only when something was read or done
    pending_operation: object | None = None  # a typed plan the UI must confirm (taskkill)
    truncated: bool = False


class Session:
    """Per-terminal state: the familiar current folder shown as a real Linux path (TB-INV-092)."""

    def __init__(self, cwd: Path | None = None) -> None:
        self.cwd = cwd or Path.home()


def _bounded(lines: list[str], equivalent: str, exit: Exit = Exit.OK) -> CommandOutput:
    if len(lines) > MAX_OUTPUT_LINES:
        cut = lines[:MAX_OUTPUT_LINES] + [
            f"... {len(lines) - MAX_OUTPUT_LINES} more lines not shown"
        ]
        return CommandOutput(Exit.TRUNCATED, tuple(cut), equivalent, True, None, True)
    return CommandOutput(exit, tuple(lines), equivalent, True)


def cmd_help(cmd: BridgeCommand, session: Session) -> CommandOutput:
    if cmd.args:
        want = cmd.args[0].lower()
        spec = next((s for s in COMMANDS if s.name == want or want in s.aliases), None)
        cmdlet = cmdlet_for(want)
        if spec is None and cmdlet is not None:
            target = " ".join(cmdlet.bridge) if cmdlet.bridge else "(explains only)"
            params = " ".join(cmdlet.params) or "(no parameters)"
            return CommandOutput(
                Exit.OK,
                (
                    f"{cmdlet.name}  becomes Bridge: {target}",
                    f"  parameters: {params}",
                    f"  also: {', '.join(cmdlet.aliases) or '-'}",
                    cmdlet.teach or "Same typed operation as the Bridge command.",
                ),
                target,
            )
        if spec is None:
            return CommandOutput(
                Exit.UNSUPPORTED, (f"'{cmd.args[0]}' is not a Bridge command.",), performed=False
            )
        sw = " ".join(f"/{s}" for s in spec.switches) or "(no switches)"
        return CommandOutput(
            Exit.OK,
            (
                f"{spec.name.upper()}  {spec.summary}",
                f"  switches: {sw}",
                f"  Linux: {spec.linux}",
                f"  class: {spec.privilege.value}",
            ),
            spec.linux,
        )
    lines = ["Bridge Mode commands (Windows words, typed Linux operations):"]
    for s in COMMANDS:
        tag = {
            "A": "",
            "B": " [asks first]",
            "C": " [admin]",
            "D": " [deferred]",
            "E": " [no equivalent]",
        }[s.privilege.value]
        lines.append(f"  {s.name:<11}{s.summary}{tag}")
    lines.append("Unknown commands, unknown switches, and shell syntax do nothing.")
    lines.extend(cmdlet_lines())
    return CommandOutput(Exit.OK, tuple(lines), "man / --help")


def _os_fields() -> tuple[str, str, str, tuple[str, ...]]:
    for cand in ("/etc/os-release", "/usr/lib/os-release"):
        p = Path(cand)
        if p.is_file():
            return distro_from_os_release(
                parse_os_release(p.read_text(encoding="utf-8", errors="replace"))
            )
    return "", "", "", ()


def cmd_ver(cmd: BridgeCommand, session: Session) -> CommandOutput:
    _, _, pretty, _ = _os_fields()
    return CommandOutput(
        Exit.OK,
        (pretty or "Unknown Linux", f"Kernel {platform.release()}"),
        "cat /etc/os-release; uname -r",
        True,
    )


def cmd_hostname(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return CommandOutput(Exit.OK, (socket.gethostname(),), "hostname", True)


def cmd_whoami(cmd: BridgeCommand, session: Session) -> CommandOutput:
    try:
        import pwd

        user = pwd.getpwuid(os.getuid()).pw_name
    except (ImportError, KeyError, AttributeError):
        user = os.environ.get("USER", "Unknown")
    return CommandOutput(Exit.OK, (f"{socket.gethostname()}\\{user}",), "id -un", True)


def cmd_echo(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return CommandOutput(Exit.OK, (expand_vars(" ".join(cmd.args)),), "echo", True)


def _text_lines(target: Path) -> list[str] | CommandOutput:
    try:
        raw = target.read_bytes()[: MAX_FILE_BYTES + 1]
    except PermissionError:
        return CommandOutput(Exit.DENIED, (f"Access is denied: {target}",), "grep", False)
    except OSError as exc:
        return CommandOutput(Exit.FAILED, (f"{target}: {exc.strerror}",), "grep", False)
    if b"\x00" in raw[:4096]:
        return []
    return raw[:MAX_FILE_BYTES].decode("utf-8", "replace").splitlines()


def _search(cmd: BridgeCommand, session: Session, files: list[str]) -> CommandOutput:
    """The shared body of findstr and find: bounded, read-only, binary files skipped."""
    pattern = cmd.args[0]
    fold = "i" in cmd.switches
    needle = pattern.casefold() if fold else pattern
    targets: list[Path] = []
    for spec_text in files:
        p = _path_arg(session, spec_text)
        if isinstance(p, CommandOutput):
            return p
        if any(ch in spec_text for ch in "*?"):
            targets.extend(sorted(x for x in p.parent.glob(p.name) if x.is_file()))
        elif p.is_file():
            targets.append(p)
        else:
            return CommandOutput(Exit.FAILED, (f"File not found - {spec_text}",), "grep", False)
    if not targets:
        return CommandOutput(Exit.FAILED, ("File not found",), "grep", False)
    lines: list[str] = []
    for t in targets:
        text = _text_lines(t)
        if isinstance(text, CommandOutput):
            return text
        hits = 0
        for no, line in enumerate(text, 1):
            hay = line.casefold() if fold else line
            matched = needle in hay
            if "v" in cmd.switches:
                matched = not matched
            if not matched:
                continue
            hits += 1
            if "c" in cmd.switches:
                continue
            prefix = f"{t.name}:" if len(targets) > 1 else ""
            number = f"{no}:" if "n" in cmd.switches else ""
            lines.append(f"{prefix}{number}{line}")
        if "c" in cmd.switches:
            lines.append(f"{t.name}: {hits}")
    if not lines:
        return CommandOutput(Exit.FAILED, (f"No lines contain '{pattern}'.",), "grep", True)
    return _bounded(
        lines, "grep" + (" -i" if fold else "") + (" -n" if "n" in cmd.switches else "")
    )


def cmd_findstr(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return _search(cmd, session, list(cmd.args[1:]))


def cmd_find(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return _search(cmd, session, [cmd.args[1]])


def cmd_where(cmd: BridgeCommand, session: Session) -> CommandOutput:
    name = cmd.args[0]
    found = shutil.which(name) or shutil.which(name.removesuffix(".exe"))
    if found:
        return CommandOutput(Exit.OK, (found,), f"which {name}", True)
    local = (
        sorted(p for p in session.cwd.glob(name) if p.exists())
        if any(c in name for c in "*?.")
        else []
    )
    if local:
        return _bounded([str(p) for p in local], "ls")
    return CommandOutput(
        Exit.FAILED,
        (f"INFO: Could not find files for the given pattern(s): {name}",),
        f"which {name}",
        True,
    )


def cmd_set(cmd: BridgeCommand, session: Session) -> CommandOutput:
    values = {name: fn() for name, fn in WINDOWS_VARS.items()}
    for key, value in os.environ.items():
        if key not in values and not is_sensitive(key):
            values[key] = value
    prefix = cmd.args[0].upper() if cmd.args else ""
    lines = [f"{k}={v}" for k, v in sorted(values.items()) if k.upper().startswith(prefix)]
    if not lines:
        return CommandOutput(
            Exit.FAILED, (f"Environment variable {cmd.args[0]} not defined",), "env", True
        )
    return _bounded(lines, "env")


def cmd_path(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return CommandOutput(Exit.OK, (f"PATH={os.environ.get('PATH', '')}",), "echo $PATH", True)


def cmd_tree(cmd: BridgeCommand, session: Session) -> CommandOutput:
    root = _path_arg(session, cmd.args[0]) if cmd.args else session.cwd
    if isinstance(root, CommandOutput):
        return root
    if not root.is_dir():
        return CommandOutput(Exit.FAILED, (f"Invalid path - {root}",), "tree", False)
    show_files = "f" in cmd.switches
    lines = [f"Folder PATH listing for {to_windows_path(root)} ({root})", f"{root.name or root}"]
    count = 0

    def walk(folder: Path, indent: str, depth: int) -> None:
        nonlocal count
        if depth > 6 or count > MAX_OUTPUT_LINES:
            return
        try:
            entries = sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold()))
        except PermissionError:
            lines.append(f"{indent}(access denied)")
            return
        for e in entries:
            if e.name.startswith(".") and "a" not in cmd.switches:
                continue
            if e.is_dir() and not e.is_symlink():
                lines.append(f"{indent}+---{e.name}")
                count += 1
                walk(e, indent + "|   ", depth + 1)
            elif show_files:
                lines.append(f"{indent}    {e.name}")
                count += 1

    walk(root, "", 0)
    return _bounded(lines, "tree" + (" -a" if "a" in cmd.switches else ""))


def cmd_exit(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return CommandOutput(
        Exit.OK,
        (
            "There is no session to close here: pick another section on the left, or close "
            "the window.",
        ),
        "-",
        True,
    )


def cmd_cls(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return CommandOutput(Exit.OK, ("\x0c",), "clear", True)


WINDOWS_VARS: dict[str, Callable[[], str]] = {
    "USERPROFILE": lambda: str(Path.home()),
    "HOMEPATH": lambda: str(Path.home()),
    "HOME": lambda: str(Path.home()),
    "USERNAME": lambda: os.environ.get("USER", "") or os.environ.get("LOGNAME", ""),
    "COMPUTERNAME": lambda: socket.gethostname(),
    "TEMP": lambda: os.environ.get("TMPDIR", "/tmp"),
    "TMP": lambda: os.environ.get("TMPDIR", "/tmp"),
    "APPDATA": lambda: os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")),
    "LOCALAPPDATA": lambda: os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")),
    "SYSTEMROOT": lambda: "/",
    "WINDIR": lambda: "/",
    "PROGRAMFILES": lambda: "/usr",
    "SYSTEMDRIVE": lambda: "C:",
    "PATH": lambda: os.environ.get("PATH", ""),
}


def expand_vars(text: str) -> str:
    """%USERPROFILE% and friends become their Linux values; unknown names stay as typed."""

    def one(m: re.Match[str]) -> str:
        name = m.group(1).upper()
        if name in WINDOWS_VARS:
            return WINDOWS_VARS[name]()
        return os.environ.get(name, os.environ.get(m.group(1), m.group(0)))

    return re.sub(r"%([A-Za-z_][A-Za-z0-9_]*)%", one, text)


def _path_arg(session: Session, text: str) -> Path | CommandOutput:
    """A typed path (Windows or Linux spelling, %VAR% expanded) as an absolute Linux path."""
    try:
        return to_linux_path(expand_vars(text), session.cwd).resolve()
    except ValueError as exc:
        return CommandOutput(Exit.FAILED, (str(exc),), "mount", False)


def cmd_cd(cmd: BridgeCommand, session: Session) -> CommandOutput:
    if not cmd.args:
        return CommandOutput(
            Exit.OK, (f"{session.cwd}  ({to_windows_path(session.cwd)})",), "pwd", True
        )
    target = _path_arg(session, cmd.args[0])
    if isinstance(target, CommandOutput):
        return target
    if not target.is_dir():
        return CommandOutput(
            Exit.FAILED, (f"The system cannot find the path specified: {cmd.args[0]}",), "cd", False
        )
    session.cwd = target
    return CommandOutput(Exit.OK, (f"{target}  ({to_windows_path(target)})",), "cd", True)


def cmd_dir(cmd: BridgeCommand, session: Session) -> CommandOutput:
    target = session.cwd if not cmd.args else _path_arg(session, cmd.args[0])
    if isinstance(target, CommandOutput):
        return target
    if not target.is_dir():
        return CommandOutput(
            Exit.FAILED, (f"File Not Found: {cmd.args[0] if cmd.args else target}",), "ls -l", False
        )
    lines = [f" Directory of {target}  ({to_windows_path(target)})", ""]
    try:
        entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold()))
    except PermissionError:
        return CommandOutput(Exit.DENIED, (f"Access is denied: {target}",), "ls -l", False)
    files = dirs = 0
    for p in entries:
        if p.name.startswith(".") and "a" not in cmd.switches:
            continue
        try:
            st = p.lstat()
            when = datetime.fromtimestamp(st.st_mtime).strftime("%m/%d/%Y  %I:%M %p")
            if p.is_dir():
                dirs += 1
                lines.append(f"{when}    <DIR>          {p.name}")
            else:
                files += 1
                lines.append(f"{when} {st.st_size:>14,} {p.name}")
        except OSError:
            lines.append(f"{'?':>20} {'?':>14} {p.name}")
    lines.append(f"{files:>16} File(s)")
    lines.append(f"{dirs:>16} Dir(s)")
    return _bounded(lines, "ls -l" + (" -a" if "a" in cmd.switches else ""))


def cmd_type(cmd: BridgeCommand, session: Session) -> CommandOutput:
    target = _path_arg(session, cmd.args[0])
    if isinstance(target, CommandOutput):
        return target
    if not target.is_file():
        return CommandOutput(
            Exit.FAILED,
            (f"The system cannot find the file specified: {cmd.args[0]}",),
            "cat",
            False,
        )
    try:
        raw = target.read_bytes()[: MAX_FILE_BYTES + 1]
    except PermissionError:
        return CommandOutput(Exit.DENIED, (f"Access is denied: {target}",), "cat", False)
    if b"\x00" in raw[:4096]:
        return CommandOutput(
            Exit.UNSUPPORTED, ("This is not a text file; it is not shown.",), "file", False
        )
    text = raw[:MAX_FILE_BYTES].decode("utf-8", "replace")
    lines = [ln.replace("\x1b", "?") for ln in text.splitlines()]
    out = _bounded(lines, "cat")
    if len(raw) > MAX_FILE_BYTES:
        return CommandOutput(
            Exit.TRUNCATED,
            out.lines + (f"... only the first {MAX_FILE_BYTES // 1024} KB are shown",),
            "cat",
            True,
            None,
            True,
        )
    return out


def cmd_systeminfo(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..capability.discovery import Discovery
    from ..system.processes import ProcessSampler

    env = Discovery().environment()
    totals = ProcessSampler().totals()
    mem = (
        "Unknown"
        if totals.mem_total_bytes is None
        else f"{totals.mem_total_bytes // (1024 * 1024):,} MB"
    )
    avail = (
        "Unknown"
        if totals.mem_available_bytes is None
        else f"{totals.mem_available_bytes // (1024 * 1024):,} MB"
    )
    up = (
        "Unknown"
        if totals.uptime_seconds is None
        else f"{int(totals.uptime_seconds // 3600)} h {int(totals.uptime_seconds % 3600 // 60)} min"
    )
    lines = [
        f"Host Name:                 {env.hostname or 'Unknown'}",
        f"OS Name:                   {env.distro_name or 'Unknown'}",
        f"OS Version:                {env.distro_version or 'Unknown'} "
        f"(kernel {env.kernel or 'Unknown'})",
        f"System Type:               {env.architecture or 'Unknown'}",
        f"Virtual Machine:           {env.virtualization or 'Unknown'}",
        f"Session:                   {env.session_type or 'Unknown'}",
        f"Total Physical Memory:     {mem}",
        f"Available Physical Memory: {avail}",
        f"System Up Time:            {up}",
        f"Processors:                {totals.cpu_count}",
        f"Signed-in User:            {env.user_name or 'Unknown'}",
    ]
    return CommandOutput(Exit.OK, tuple(lines), "hostnamectl; uname -a; free -m; uptime", True)


def cmd_ipconfig(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..system.network import read_network

    if "flushdns" in cmd.switches:
        return _flushdns_plan()
    if "renew" in cmd.switches or "release" in cmd.switches:
        return CommandOutput(
            Exit.UNSUPPORTED,
            (
                "Linux renews addresses by reconnecting the adapter: use netsh interface set "
                "interface <name> disable, then enable, or the Network page.",
            ),
            "nmcli device reapply",
            False,
        )
    nw = read_network()
    if not nw.available:
        return CommandOutput(Exit.UNSUPPORTED, (nw.detail,), "nmcli device show", False)
    lines = ["Linux IP Configuration", ""]
    for d in nw.devices:
        if d.is_loopback:
            continue
        lines.append(f"{d.kind} adapter {d.interface}:")
        lines.append("")
        lines.append(f"   Link State . . . . . . . . . . . : {d.link_state}")
        if "all" in cmd.switches:
            lines.append(f"   Connection Profile . . . . . . . : {d.connection_name or 'None'}")
            lines.append(f"   Driver . . . . . . . . . . . . . : {d.driver or 'Unknown'}")
            lines.append(f"   Physical Address . . . . . . . . : {d.mac or 'Unknown'}")
        for a in d.ipv4:
            lines.append(f"   IPv4 Address . . . . . . . . . . : {a}")
        for a in d.ipv6:
            lines.append(f"   IPv6 Address . . . . . . . . . . : {a}")
        lines.append(f"   Default Gateway . . . . . . . . . : {d.gateway4 or 'None'}")
        if "all" in cmd.switches:
            lines.append(f"   DNS Servers . . . . . . . . . . . : {', '.join(d.dns) or 'None'}")
        lines.append("")
    lines.append(f"Connectivity check: {nw.connectivity}")
    return _bounded(lines, "nmcli device show; ip addr")


@dataclass(frozen=True)
class ActionPlan:
    """A small confirmed action with no target identity (flush a cache): the UI asks,
    then calls ``run`` off the main loop and shows its plain result."""

    heading: str
    preview: str
    run: Callable[[], tuple[bool, str]]
    linux: str = ""


def _flushdns_plan() -> CommandOutput:
    from ..system.netdiag import flush_dns

    plan = ActionPlan(
        "Flush the DNS cache",
        "Clear the names this computer has already looked up (systemd-resolved cache)? "
        "Nothing else changes; new lookups fill it again.",
        flush_dns,
        "resolvectl flush-caches",
    )
    return CommandOutput(
        Exit.NEEDS_CONFIRMATION,
        (plan.preview, "Confirm in the dialog to continue; nothing has happened yet."),
        plan.linux,
        False,
        plan,
    )


def cmd_ping(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..system.netdiag import diagnostic_tool, run_in_terminal, valid_host

    args = list(cmd.args)
    count = "4"
    if "-n" in args:
        i = args.index("-n")
        if i + 1 >= len(args) or not args[i + 1].isdigit() or not 1 <= int(args[i + 1]) <= 100:
            return CommandOutput(
                Exit.PARSE_ERROR, ("ping -n needs a count from 1 to 100.",), "ping", False
            )
        count = args[i + 1]
        del args[i : i + 2]
    if len(args) != 1:
        return CommandOutput(Exit.PARSE_ERROR, ("ping <host> [-n count]",), "ping", False)
    try:
        host = valid_host(args[0])
    except ValueError as exc:
        return CommandOutput(Exit.PARSE_ERROR, (str(exc),), "ping", False)
    exe, argv = diagnostic_tool("ping")
    if not exe:
        return CommandOutput(Exit.UNSUPPORTED, ("ping is not installed here.",), "ping", False)
    ok, plain = run_in_terminal([exe, "-c", count, host], f"ping {host}")
    return CommandOutput(
        Exit.OK if ok else Exit.FAILED,
        (
            plain,
            "Ubuntu reserves raw network sockets, so the system ping runs in its own "
            "window; the replies you know appear there.",
        ),
        f"ping -c {count} {host}",
        ok,
    )


def cmd_tracert(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..system.netdiag import diagnostic_tool, run_in_terminal, valid_host

    try:
        host = valid_host(cmd.args[0])
    except ValueError as exc:
        return CommandOutput(Exit.PARSE_ERROR, (str(exc),), "tracepath", False)
    exe, argv = diagnostic_tool("tracert")
    if not exe:
        return CommandOutput(
            Exit.UNSUPPORTED,
            ("Neither tracepath nor traceroute is installed here.",),
            "tracepath",
            False,
        )
    ok, plain = run_in_terminal(argv + [host], f"tracert {host}")
    return CommandOutput(Exit.OK if ok else Exit.FAILED, (plain,), f"{exe} {host}", ok)


def cmd_nslookup(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..system.netdiag import lookup

    try:
        res = lookup(cmd.args[0])
    except ValueError as exc:
        return CommandOutput(Exit.PARSE_ERROR, (str(exc),), "getent hosts", False)
    lines = [f"Server:  {res.servers[0] if res.servers else 'Unknown'}"]
    if len(res.servers) > 1:
        lines.append(f"Also:    {', '.join(res.servers[1:])}")
    lines.append("")
    if res.error:
        lines.append(f"*** Can't find {res.name}: {res.error}")
        return CommandOutput(Exit.FAILED, tuple(lines), "getent hosts", True)
    lines.append(f"Name:    {res.canonical or res.name}")
    if res.canonical:
        lines.append(f"Alias:   {res.name}")
    for a in res.addresses:
        lines.append(f"Address: {a}")
    return CommandOutput(Exit.OK, tuple(lines), "getent hosts / resolvectl query", True)


def cmd_getmac(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..system.network import read_network

    nw = read_network()
    if not nw.available:
        return CommandOutput(Exit.UNSUPPORTED, (nw.detail,), "ip link", False)
    lines = [
        f"{'Physical Address':<20} {'Adapter':<12} {'Link'}",
        f"{'=' * 20} {'=' * 12} {'=' * 12}",
    ]
    for d in nw.devices:
        if not d.is_loopback:
            lines.append(f"{d.mac or 'Unknown':<20} {d.interface:<12} {d.link_state}")
    return _bounded(lines, "ip link")


def cmd_tasklist(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..system.processes import ProcessSampler

    rows, _ = ProcessSampler().sample()
    verbose = "v" in cmd.switches
    head = f"{'Image Name':<28} {'PID':>8} {'Mem Usage':>12}" + (
        f" {'User':<12} {'Kind':<10}" if verbose else ""
    )
    lines = [head, "=" * len(head)]
    for r in sorted(rows, key=lambda r: r.identity.pid):
        mem = "Unknown" if r.rss_bytes is None else f"{r.rss_bytes // 1024:,} K"
        line = f"{r.name[:28]:<28} {r.identity.pid:>8} {mem:>12}"
        if verbose:
            line += f" {r.user[:12]:<12} {r.kind.value:<10}"
        lines.append(line)
    return _bounded(lines, "ps -eo comm,pid,rss,user")


def cmd_sc(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..system.services import Scope, list_services, read_unit

    verb = cmd.args[0].lower()
    if verb in ("start", "stop", "restart", "enable", "disable"):
        return _sc_mutation(verb, cmd)
    if verb != "query":
        return CommandOutput(
            Exit.UNSUPPORTED,
            (f"sc {verb} is not available in this build; use the Services page.",),
            "systemctl",
            False,
        )
    if len(cmd.args) == 2:
        name = cmd.args[1] if cmd.args[1].endswith(".service") else cmd.args[1] + ".service"
        info, err = read_unit(Scope.SYSTEM, name)
        if info is None:
            return CommandOutput(
                Exit.FAILED,
                (f"The specified service does not exist as an installed service: {name}",),
                f"systemctl status {name}",
                False,
            )
        lines = [
            f"SERVICE_NAME: {info.identity.name}",
            f"        STATE              : {info.plain_running} "
            f"({info.active_state}/{info.sub_state})",
            f"        START_TYPE         : {info.plain_startup} "
            f"({info.unit_file_state or 'unknown'})",
            f"        DESCRIPTION        : {info.description}",
            f"        UNIT_FILE          : {info.identity.fragment_path or 'Unknown'}",
        ]
        return CommandOutput(Exit.OK, tuple(lines), f"systemctl status {name}", True)
    services, err = list_services(Scope.SYSTEM)
    if err:
        return CommandOutput(Exit.UNSUPPORTED, (err,), "systemctl list-units", False)
    lines = []
    for s in services:
        lines.append(f"SERVICE_NAME: {s.identity.name}")
        lines.append(f"        STATE: {s.plain_running:<10} START: {s.plain_startup}")
    return _bounded(lines, "systemctl list-units --type=service")


def _sc_mutation(verb: str, cmd: BridgeCommand) -> CommandOutput:
    """sc stop <name> and friends: the same typed ServicePlan as the Services page,
    confirmed in the UI; system scope asks Linux (polkit) for this one action only."""
    from ..operations.service import ServicePlan, plan_service
    from ..system.services import Scope, read_unit

    if len(cmd.args) < 2:
        return CommandOutput(
            Exit.PARSE_ERROR, (f"sc {verb} needs a service name.",), "systemctl", False
        )
    name = cmd.args[1] if cmd.args[1].endswith(".service") else cmd.args[1] + ".service"
    info, err = read_unit(Scope.SYSTEM, name)
    if info is None:
        return CommandOutput(
            Exit.FAILED,
            (f"The specified service does not exist as an installed service: {name}",),
            f"systemctl {verb} {name}",
            False,
        )
    plan = plan_service(info, verb)
    if not isinstance(plan, ServicePlan):
        return CommandOutput(Exit.UNSUPPORTED, (plan.plain,), f"systemctl {verb}", False)
    asks = (
        " Linux will ask for administrator permission for this one action."
        if plan.needs_admin
        else ""
    )
    return CommandOutput(
        Exit.NEEDS_CONFIRMATION,
        (plan.preview + asks, "Confirm in the dialog to continue; nothing has happened yet."),
        f"systemctl {verb} {name}",
        False,
        plan,
    )


def cmd_netstat(cmd: BridgeCommand, session: Session) -> CommandOutput:
    lines = ["Proto  Local Address          State"]
    for proto, path in (
        ("TCP", "/proc/net/tcp"),
        ("TCP6", "/proc/net/tcp6"),
        ("UDP", "/proc/net/udp"),
    ):
        try:
            rows = Path(path).read_text(encoding="utf-8").splitlines()[1:]
        except OSError:
            continue
        for row in rows:
            f = row.split()
            if len(f) < 4:
                continue
            state = f[3]
            if proto.startswith("TCP") and state != "0A" and "a" not in cmd.switches:
                continue  # only LISTEN by default, like netstat without -a
            addr, port = f[1].rsplit(":", 1)
            if len(addr) == 8:
                ip = ".".join(str(int(addr[i : i + 2], 16)) for i in (6, 4, 2, 0))
            else:
                ip = "[ipv6]"
            lines.append(
                f"{proto:<6} {ip}:{int(port, 16):<15} {'LISTEN' if state == '0A' else state}"
            )
    return _bounded(lines, "ss -tulpn")


FAMILIAR_PROGRAMS = {
    "notepad": "org.gnome.TextEditor.desktop",
    "calc": "org.gnome.Calculator.desktop",
    "explorer": "org.gnome.Nautilus.desktop",
    "control": "org.gnome.Settings.desktop",
    "mspaint": "",
    "cmd": "",
}


def cmd_explorer(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..desktop.launch import Launcher

    target = _path_arg(session, cmd.args[0]) if cmd.args else session.cwd
    if isinstance(target, CommandOutput):
        return target
    if not target.is_dir():
        return CommandOutput(
            Exit.FAILED,
            (f"The system cannot find the path specified: {target}",),
            "nautilus",
            False,
        )
    res = Launcher().show_folder(f"file://{target}")
    return CommandOutput(
        Exit.OK if res.ok else Exit.FAILED,
        (f"{res.plain} ({target}, {to_windows_path(target)})" if res.ok else res.plain,),
        f"nautilus {target}",
        res.ok,
    )


def cmd_start(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..desktop.launch import Launcher

    what = cmd.args[0]
    low = what.lower().removesuffix(".exe")
    launcher = Launcher()
    if low in FAMILIAR_PROGRAMS:
        desktop_id = FAMILIAR_PROGRAMS[low]
        if low == "cmd":
            return CommandOutput(
                Exit.OK, ("You are in it: this is the Command Prompt (Bridge Mode).",), "-", True
            )
        if not desktop_id:
            return CommandOutput(
                Exit.UNSUPPORTED,
                (f"{what} has no direct equivalent here; look under Apps for an image editor.",),
                "-",
                False,
            )
        res = launcher.launch_app(desktop_id)
        return CommandOutput(
            Exit.OK if res.ok else Exit.FAILED, (res.plain,), f"gtk-launch {desktop_id}", res.ok
        )
    if "://" in what or low.startswith("www."):
        uri = what if "://" in what else f"https://{what}"
        res = launcher.open_uri(uri)
        return CommandOutput(
            Exit.OK if res.ok else Exit.FAILED, (res.plain,), f"gio open {uri}", res.ok
        )
    target = _path_arg(session, what)
    if isinstance(target, CommandOutput):
        return target
    if not target.exists():
        return CommandOutput(
            Exit.FAILED,
            (
                f"Windows cannot find '{what}'. Programs here are started from Apps; files and "
                "folders by their path.",
            ),
            "gio open",
            False,
        )
    if target.is_dir():
        res = launcher.show_folder(f"file://{target}")
    else:
        res = launcher.open_uri(f"file://{target}")
    return CommandOutput(
        Exit.OK if res.ok else Exit.FAILED, (res.plain,), f"gio open {target}", res.ok
    )


def cmd_net(cmd: BridgeCommand, session: Session) -> CommandOutput:
    verb = cmd.args[0].lower()
    if verb in ("start", "stop"):
        if len(cmd.args) < 2:
            return CommandOutput(
                Exit.PARSE_ERROR, (f"net {verb} needs a service name.",), "systemctl", False
            )
        fake = BridgeCommand(cmd.spec, cmd.switches, (verb, cmd.args[1]), cmd.raw, cmd.note)
        return _sc_mutation(verb, fake)
    teach = {
        "user": "Accounts are managed in Settings, Users (or the Apps page). There is no "
        "NetBIOS domain here.",
        "use": "Network shares are opened in Files (Other Locations, smb://server/share); "
        "nothing maps a drive letter.",
        "share": "Sharing a folder is done in Files (folder Properties, Local Network Share).",
        "view": "Network computers are listed in Files under Other Locations.",
    }
    if verb in teach:
        return CommandOutput(Exit.UNSUPPORTED, (teach[verb],), "Files / Settings", False)
    return CommandOutput(
        Exit.UNSUPPORTED, ("net here accepts start, stop, user, use, share, view.",), "-", False
    )


def cmd_date(cmd: BridgeCommand, session: Session) -> CommandOutput:
    import datetime

    now = datetime.datetime.now().astimezone()
    label = "date" if cmd.spec.name == "date" else "time"
    shown = now.strftime("%a %m/%d/%Y") if label == "date" else now.strftime("%H:%M:%S")
    return CommandOutput(
        Exit.OK,
        (
            f"The current {label} is: {shown} ({now.tzname()})",
            "Change it in Settings, Date and Time.",
        ),
        "date; timedatectl",
        True,
    )


def cmd_taskkill(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..operations.process import TerminatePlan, plan_terminate
    from ..system.processes import ProcessSampler

    if "im" in cmd.switches and cmd.args:
        rows, _ = ProcessSampler().sample()
        wanted = cmd.args[0].lower().removesuffix(".exe")
        mine = [r for r in rows if r.kind.actionable_by_user and r.name.lower() == wanted]
        if not mine:
            return CommandOutput(
                Exit.FAILED, (f'The process "{cmd.args[0]}" not found.',), "pkill", False
            )
        if len(mine) > 1:
            pids = ", ".join(str(r.identity.pid) for r in mine)
            return CommandOutput(
                Exit.UNSUPPORTED,
                (
                    f"{len(mine)} processes are named {cmd.args[0]} (PIDs {pids}); use "
                    "taskkill /PID <number> to pick one.",
                ),
                "pkill",
                False,
            )
        plan = plan_terminate(mine[0].identity, mine[0].kind, force="f" in cmd.switches)
        if not isinstance(plan, TerminatePlan):
            return CommandOutput(Exit.UNSUPPORTED, (plan.plain,), "kill", False)
        return CommandOutput(
            Exit.NEEDS_CONFIRMATION,
            (plan.preview, "Confirm in the dialog to continue; nothing has happened yet."),
            "kill -TERM" if not plan.force else "kill -KILL",
            False,
            plan,
        )
    if "pid" not in cmd.switches:
        return CommandOutput(
            Exit.UNSUPPORTED,
            (
                "taskkill here accepts /PID <number> [/F] or /IM <name> [/F] when exactly one "
                "of your programs has that name.",
            ),
            "kill",
            False,
        )
    try:
        pid = int(cmd.args[0])
    except ValueError:
        return CommandOutput(
            Exit.PARSE_ERROR, (f"'{cmd.args[0]}' is not a process number.",), "kill", False
        )
    rows, _ = ProcessSampler().sample()
    row = next((r for r in rows if r.identity.pid == pid), None)
    if row is None:
        return CommandOutput(Exit.FAILED, (f'The process "{pid}" not found.',), "kill", False)
    plan = plan_terminate(row.identity, row.kind, force="f" in cmd.switches)
    if not isinstance(plan, TerminatePlan):
        return CommandOutput(Exit.UNSUPPORTED, (plan.plain,), "kill", False)
    return CommandOutput(
        Exit.NEEDS_CONFIRMATION,
        (plan.preview, "Confirm in the dialog to continue; nothing has happened yet."),
        "kill -TERM" if not plan.force else "kill -KILL",
        False,
        plan,
    )


def _file_command(verb: str, cmd: BridgeCommand, session: Session) -> CommandOutput:
    """Plan a file operation; the UI confirms before anything happens (class B)."""
    from ..operations.files import FilePlan, VERBS, plan_file

    dest = cmd.args[1] if len(cmd.args) > 1 else None
    plan = plan_file(verb, cmd.args[0], dest, session.cwd)
    linux = VERBS[verb][2]
    if not isinstance(plan, FilePlan):
        exit = Exit.UNSUPPORTED if plan.state is OperationState.UNSUPPORTED else Exit.FAILED
        lines = (plan.plain,) + ((plan.safest_next_step,) if plan.safest_next_step else ())
        return CommandOutput(exit, lines, linux, False)
    return CommandOutput(
        Exit.NEEDS_CONFIRMATION,
        (plan.preview, "Confirm in the dialog to continue; nothing has happened yet."),
        linux,
        False,
        plan,
    )


def cmd_copy(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return _file_command("copy", cmd, session)


def cmd_move(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return _file_command("move", cmd, session)


def cmd_ren(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return _file_command("rename", cmd, session)


def cmd_del(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return _file_command("trash", cmd, session)


def cmd_md(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return _file_command("mkdir", cmd, session)


def cmd_rd(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return _file_command("rmdir", cmd, session)


def cmd_assoc(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..apps.inventory import default_apps

    lines = [f"{d.label:<18} {d.app_name or '(nothing is set)'}" for d in default_apps()]
    lines.append("Change these under Apps, Default apps, in Trier Bridge or in Settings.")
    return CommandOutput(Exit.OK, tuple(lines), "xdg-mime query default", True)


NETSH_HELP = (
    "netsh here accepts: interface set interface <name> enable|disable; "
    "interface ip set address <name> static <ip> <mask> [gateway] | dhcp; "
    "interface ip set dns <name> static <ip> | dhcp."
)


def _netsh_interface(a: list[str]) -> tuple[str, str, dict[str, str]] | str:
    """netsh interface set interface <name> enable|disable"""
    name = a[3].split("=", 1)[-1]
    state = a[4].lower()
    if state in ("enable", "enabled"):
        return name, "connect", {}
    if state in ("disable", "disabled"):
        return name, "disconnect", {}
    return f"netsh: '{a[4]}' is not enable or disable."


def _netsh_ip_address(name: str, rest: list[str]) -> tuple[str, str, dict[str, str]] | str:
    """netsh interface ip set address <name> static <ip> <mask> [gateway] | dhcp"""
    if rest and rest[0].lower() == "dhcp":
        return name, "auto", {}
    if len(rest) >= 3 and rest[0].lower() == "static":
        gateway = rest[3] if len(rest) > 3 else ""
        return name, "static", {"address": rest[1], "mask": rest[2], "gateway": gateway}
    return "netsh: use 'static <ip> <mask> [gateway]' or 'dhcp' after the interface name."


def _netsh_ip_dns(name: str, rest: list[str]) -> tuple[str, str, dict[str, str]] | str:
    """netsh interface ip set dns <name> static <ip> [ip...] | dhcp"""
    if rest and rest[0].lower() == "dhcp":
        return name, "dns-auto", {}
    if len(rest) >= 2 and rest[0].lower() == "static":
        return name, "dns", {"dns": ",".join(rest[1:])}
    return "netsh: use 'static <ip> [ip...]' or 'dhcp' after the interface name."


def netsh_request(args: tuple[str, ...]) -> tuple[str, str, dict[str, str]] | str:
    """Parse the netsh forms this build accepts into (interface, verb, fields), or a plain
    reason. name="x" is accepted where Windows accepts it."""
    a = [x for x in args]
    low = [x.lower() for x in a[:3]]
    if len(a) >= 5 and low == ["interface", "set", "interface"]:
        return _netsh_interface(a)
    if len(a) >= 5 and low == ["interface", "ip", "set"]:
        what = a[3].lower()
        name = a[4].split("=", 1)[-1]
        if what in ("address", "addr"):
            return _netsh_ip_address(name, a[5:])
        if what in ("dns", "dnsservers"):
            return _netsh_ip_dns(name, a[5:])
        return f"netsh: 'ip set {a[3]}' is not available here (address or dns)."
    return NETSH_HELP


def cmd_netsh(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..operations.network import NetworkPlan, ipv4_settings, plan_connect, plan_network
    from ..system.network import read_network

    req = netsh_request(cmd.args)
    if isinstance(req, str):
        return CommandOutput(Exit.PARSE_ERROR, (req,), "nmcli", False)
    name, verb, fields = req
    nw = read_network()
    device = next((d for d in nw.devices if d.interface.lower() == name.lower()), None)
    if device is None and verb == "connect":
        plan = plan_connect(name)
        if not isinstance(plan, NetworkPlan):
            return CommandOutput(Exit.FAILED, (plan.plain,), "nmcli", False)
        return CommandOutput(
            Exit.NEEDS_CONFIRMATION,
            (plan.preview, "Confirm in the dialog to continue; nothing has happened yet."),
            f"nmcli connection up {name}",
            False,
            plan,
        )
    if device is None:
        known = ", ".join(d.interface for d in nw.devices if not d.is_loopback) or "none"
        return CommandOutput(
            Exit.FAILED, (f"No adapter named '{name}'. Adapters here: {known}.",), "nmcli", False
        )
    try:
        settings = (
            ipv4_settings(fields["address"], fields["mask"], fields.get("gateway", ""))
            if verb == "static"
            else None
        )
        dns = tuple(ipv4_settings("0.0.0.0", "0", "", fields["dns"]).dns) if verb == "dns" else ()
    except ValueError as exc:
        return CommandOutput(Exit.PARSE_ERROR, (str(exc),), "nmcli", False)
    plan = plan_network(device, verb, settings, dns)
    if not isinstance(plan, NetworkPlan):
        return CommandOutput(Exit.UNSUPPORTED, (plan.plain,), "nmcli", False)
    return CommandOutput(
        Exit.NEEDS_CONFIRMATION,
        (plan.preview, "Confirm in the dialog to continue; nothing has happened yet."),
        f"nmcli device/connection modify {device.interface}",
        False,
        plan,
    )


def pwsh_path() -> str:
    """An installed PowerShell 7, never a bundled one (DEC-008)."""
    found = shutil.which("pwsh")
    if found:
        return found
    snap = Path("/snap/bin/pwsh")
    return str(snap) if snap.exists() else ""


def cmd_powershell(cmd: BridgeCommand, session: Session) -> CommandOutput:
    exe = pwsh_path()
    if not exe:
        return CommandOutput(
            Exit.UNSUPPORTED,
            (
                "PowerShell is not installed on this computer. On Ubuntu it is the "
                "'powershell' snap (App Center: PowerShell); Trier Bridge never bundles it.",
                "Bridge Mode already understands Get-Process, Get-Service, and other "
                "cmdlet names: type help.",
            ),
            "pwsh",
            False,
        )
    from gi.repository import Gio

    # The desktop opens its own terminal with a fixed program path; no shell of ours.
    info = Gio.AppInfo.create_from_commandline(
        exe, "PowerShell", Gio.AppInfoCreateFlags.NEEDS_TERMINAL
    )
    launched = bool(info.launch([], None))
    if not launched:
        return CommandOutput(
            Exit.FAILED, ("The terminal window could not be opened.",), "pwsh", False
        )
    return CommandOutput(
        Exit.OK,
        (
            f"PowerShell 7 opened in a terminal window ({exe}).",
            "On Linux the execution policy is Unrestricted and nothing enforces one; "
            "scripts run with your own permissions, exactly like any program you start.",
        ),
        "pwsh",
        True,
    )


def power_ability(action: str) -> str:
    """What logind says about this user doing the action: yes, challenge, no, or na."""
    from ..system.bus import Bus

    bus = Bus.system()
    res, err = bus.call(
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager",
        "CanPowerOff" if action == "poweroff" else "CanReboot",
    )
    return str(res[0]) if res and not err else "unknown"


def power_action(action: str) -> tuple[bool, str]:
    """Ask logind to power off or reboot; polkit decides. Runs only after the dialog."""
    from gi.repository import Gio, GLib

    from ..system.bus import Bus

    bus = Bus.system()
    if bus.conn is None:
        return False, f"The system bus is not reachable: {bus.error}"
    try:
        bus.conn.call_sync(
            "org.freedesktop.login1",
            "/org/freedesktop/login1",
            "org.freedesktop.login1.Manager",
            "PowerOff" if action == "poweroff" else "Reboot",
            GLib.Variant("(b)", (True,)),
            None,
            Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION,
            30000,
            None,
        )
    except GLib.Error as exc:
        low = exc.message.lower()
        if "access" in low or "authoriz" in low:
            return False, "Linux did not grant permission to power off or restart."
        return False, f"The system did not accept the request: {exc.message}"
    return True, (
        "The computer is shutting down." if action == "poweroff" else "The computer is restarting."
    )


def cmd_shutdown(cmd: BridgeCommand, session: Session) -> CommandOutput:
    if "a" in cmd.switches:
        return CommandOutput(
            Exit.UNSUPPORTED,
            ("Nothing here schedules a shutdown, so there is nothing to abort.",),
            "shutdown -c",
            False,
        )
    if "s" in cmd.switches and "r" in cmd.switches:
        return CommandOutput(
            Exit.PARSE_ERROR, ("Choose /s (shut down) or /r (restart).",), "-", False
        )
    if "s" not in cmd.switches and "r" not in cmd.switches:
        return CommandOutput(
            Exit.PARSE_ERROR,
            ("shutdown /s shuts down, shutdown /r restarts; /t <seconds> delays.",),
            "-",
            False,
        )
    action = "poweroff" if "s" in cmd.switches else "reboot"
    delay = 0
    if "t" in cmd.switches:
        if not cmd.args or not cmd.args[0].isdigit() or int(cmd.args[0]) > 3600:
            return CommandOutput(
                Exit.PARSE_ERROR, ("/t needs a number of seconds (0-3600).",), "-", False
            )
        delay = int(cmd.args[0])
    ability = power_ability(action)
    verb_text = "shut down" if action == "poweroff" else "restart"
    if ability == "no":
        return CommandOutput(
            Exit.DENIED,
            (f"Linux does not allow this account to {verb_text} the computer.",),
            "loginctl",
            False,
        )
    what = "Shut down" if action == "poweroff" else "Restart"
    asks = " Linux will ask for permission." if ability == "challenge" else ""
    when = f" after {delay} seconds" if delay else " now"
    plan = ActionPlan(
        f"{what} the computer",
        f"{what} this computer{when}? Unsaved work in other programs may be lost; other users "
        f"signed in here are affected too.{asks}",
        lambda: _delayed_power(action, delay),
        "systemctl poweroff" if action == "poweroff" else "systemctl reboot",
    )
    return CommandOutput(
        Exit.NEEDS_CONFIRMATION,
        (plan.preview, "Confirm in the dialog to continue; nothing has happened yet."),
        plan.linux,
        False,
        plan,
    )


def _delayed_power(action: str, delay: int) -> tuple[bool, str]:
    import time

    if delay:
        time.sleep(delay)
    return power_action(action)


HANDLERS: dict[str, Callable[[BridgeCommand, Session], CommandOutput]] = {
    "help": cmd_help,
    "ver": cmd_ver,
    "hostname": cmd_hostname,
    "whoami": cmd_whoami,
    "systeminfo": cmd_systeminfo,
    "ipconfig": cmd_ipconfig,
    "tasklist": cmd_tasklist,
    "sc": cmd_sc,
    "dir": cmd_dir,
    "cd": cmd_cd,
    "cls": cmd_cls,
    "echo": cmd_echo,
    "type": cmd_type,
    "getmac": cmd_getmac,
    "netstat": cmd_netstat,
    "taskkill": cmd_taskkill,
    "shutdown": cmd_shutdown,
    "powershell": cmd_powershell,
    "assoc": cmd_assoc,
    "netsh": cmd_netsh,
    "ping": cmd_ping,
    "tracert": cmd_tracert,
    "nslookup": cmd_nslookup,
    "findstr": cmd_findstr,
    "find": cmd_find,
    "where": cmd_where,
    "set": cmd_set,
    "path": cmd_path,
    "tree": cmd_tree,
    "exit": cmd_exit,
    "explorer": cmd_explorer,
    "start": cmd_start,
    "net": cmd_net,
    "date": cmd_date,
    "time": cmd_date,
    "copy": cmd_copy,
    "move": cmd_move,
    "ren": cmd_ren,
    "del": cmd_del,
    "md": cmd_md,
    "rd": cmd_rd,
}


def run_line(line: str, session: Session) -> CommandOutput:
    """Parse and run one Bridge Mode line. A parse failure performs nothing (TB-INV-083)."""
    parsed = parse(line)
    if isinstance(parsed, ParseFailure):
        return CommandOutput(
            Exit.PARSE_ERROR, (parsed.plain,) if parsed.plain else (), performed=False
        )
    handler = HANDLERS.get(parsed.spec.name)
    if handler is None:
        return CommandOutput(
            Exit.UNSUPPORTED,
            (f"{parsed.spec.name} is recognized but not available in this build.",),
            parsed.spec.linux,
            False,
        )
    try:
        out = handler(parsed, session)
        if parsed.note:
            out = replace(out, lines=(f"PowerShell {parsed.note}",) + out.lines)
        return out
    except Exception as exc:  # structured, never a traceback into the terminal
        return CommandOutput(
            Exit.FAILED,
            (f"{parsed.spec.name} could not complete: {exc}",),
            parsed.spec.linux,
            False,
        )


def is_sensitive(line: str) -> bool:
    """History excludes lines that look like they carry secrets (TB-INV-098)."""
    low = line.lower()
    return any(w in low for w in ("password", "passwd", "token", "secret", "apikey", "api_key"))


def teach_line(spec: CommandSpec) -> str:
    return f"Linux: {spec.linux}"


def privilege_note(spec: CommandSpec) -> str:
    return {
        PrivilegeClass.A_READ_ONLY: "read-only",
        PrivilegeClass.B_USER_MUTATION: "changes something of yours; asks first",
        PrivilegeClass.C_ADMIN_MUTATION: "needs administrator permission",
        PrivilegeClass.D_HIGH_RISK: "deferred",
        PrivilegeClass.E_NO_EQUIVALENT: "no equivalent",
    }[spec.privilege]


__all__ = [
    "CommandOutput",
    "Exit",
    "Session",
    "run_line",
    "is_sensitive",
    "ProcessIdentity",
    "field",
]
