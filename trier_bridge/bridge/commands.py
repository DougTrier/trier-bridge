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
    return CommandOutput(Exit.OK, (" ".join(cmd.args),), "echo", True)


def cmd_cls(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return CommandOutput(Exit.OK, ("\x0c",), "clear", True)


def cmd_cd(cmd: BridgeCommand, session: Session) -> CommandOutput:
    if not cmd.args:
        return CommandOutput(Exit.OK, (str(session.cwd),), "pwd", True)
    target = (session.cwd / cmd.args[0].replace("\\", "/")).resolve()
    if not target.is_dir():
        return CommandOutput(
            Exit.FAILED, (f"The system cannot find the path specified: {cmd.args[0]}",), "cd", False
        )
    session.cwd = target
    return CommandOutput(Exit.OK, (str(target),), "cd", True)


def cmd_dir(cmd: BridgeCommand, session: Session) -> CommandOutput:
    target = (
        session.cwd if not cmd.args else (session.cwd / cmd.args[0].replace("\\", "/")).resolve()
    )
    if not target.is_dir():
        return CommandOutput(
            Exit.FAILED, (f"File Not Found: {cmd.args[0] if cmd.args else target}",), "ls -l", False
        )
    lines = [f" Directory of {target}", ""]
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
    target = (session.cwd / cmd.args[0].replace("\\", "/")).resolve()
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


def cmd_taskkill(cmd: BridgeCommand, session: Session) -> CommandOutput:
    from ..operations.process import TerminatePlan, plan_terminate
    from ..system.processes import ProcessSampler

    if "pid" not in cmd.switches:
        return CommandOutput(
            Exit.UNSUPPORTED,
            (
                "taskkill here accepts /PID <number> [/F]; names are not matched "
                "to avoid ending the wrong program.",
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


def cmd_shutdown(cmd: BridgeCommand, session: Session) -> CommandOutput:
    return CommandOutput(
        Exit.UNSUPPORTED,
        ("Shutdown and restart are not available in this build. Use the system menu.",),
        "systemctl poweroff",
        False,
    )


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
