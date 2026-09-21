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
"""Bridge Mode grammar (docs/SECURITY.md section 9.2, SCOPE-08).

A command line is tokenized with CMD-style quoting, then matched against a
finite command table. Each command declares its class (A read-only, B user
mutation, C admin, E no equivalent), its allowed switches, and its positional
arity. The result is a typed BridgeCommand or a ParseFailure; nothing here
executes anything.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum, unique

from ..core.state import PrivilegeClass

MAX_LINE = 4096
SHELL_META = set(";&|<>`$()^\n\r")


@unique
class Failure(Enum):
    EMPTY = "empty"
    TOO_LONG = "too long"
    SHELL_SYNTAX = "shell syntax"
    BAD_QUOTING = "bad quoting"
    BAD_ENCODING = "bad encoding"
    UNKNOWN_COMMAND = "unknown command"
    UNKNOWN_SWITCH = "unknown switch"
    TOO_MANY_ARGS = "too many arguments"
    MISSING_ARG = "missing argument"
    NO_EQUIVALENT = "no equivalent"


@dataclass(frozen=True)
class ParseFailure:
    failure: Failure
    plain: str
    token: str = ""

    @property
    def performed(self) -> bool:
        return False  # a parse failure never performs anything (TB-INV-083)


@dataclass(frozen=True)
class CommandSpec:
    name: str
    aliases: tuple[str, ...]
    privilege: PrivilegeClass
    switches: tuple[str, ...]  # lowercase, without the leading slash
    max_args: int
    min_args: int = 0
    linux: str = ""  # what answers this on Linux, for teaching (TB-INV-080)
    summary: str = ""


@dataclass(frozen=True)
class BridgeCommand:
    spec: CommandSpec
    switches: tuple[str, ...]  # normalized lowercase without slash, in order
    args: tuple[str, ...]
    raw: str
    note: str = ""  # "Get-Process → tasklist" when a PowerShell name was accepted


FILE_COMMANDS: tuple[str, ...] = (
    "copy",
    "move",
    "ren",
    "del",
    "md",
    "rd",
    "explorer",
    "start",
    "where",
    "tree",
    "findstr",
    "find",
)

COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec(
        "help",
        ("?",),
        PrivilegeClass.A_READ_ONLY,
        (),
        1,
        linux="Trier Bridge command table",
        summary="List Bridge commands or describe one.",
    ),
    CommandSpec(
        "ver",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        linux="/etc/os-release, uname",
        summary="Show the Linux version.",
    ),
    CommandSpec(
        "hostname",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        linux="hostname / hostnamectl",
        summary="Show the computer name.",
    ),
    CommandSpec(
        "whoami",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        linux="id, whoami",
        summary="Show the signed-in user.",
    ),
    CommandSpec(
        "systeminfo",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        linux="os-release, uname, /proc/meminfo, systemd",
        summary="Show system facts.",
    ),
    CommandSpec(
        "ipconfig",
        (),
        PrivilegeClass.A_READ_ONLY,
        ("all", "flushdns", "renew", "release"),
        0,
        linux="NetworkManager (nmcli, ip addr); systemd-resolved",
        summary="Show adapters and addresses; /flushdns clears the DNS cache (asks).",
    ),
    CommandSpec(
        "tasklist",
        (),
        PrivilegeClass.A_READ_ONLY,
        ("v",),
        0,
        linux="procfs (ps, top)",
        summary="List running processes.",
    ),
    CommandSpec(
        "sc",
        (),
        PrivilegeClass.C_ADMIN_MUTATION,
        (),
        2,
        min_args=1,
        linux="systemctl",
        summary="sc query [name] shows services; sc start|stop|restart|enable|disable <name> asks.",
    ),
    CommandSpec(
        "dir",
        (),
        PrivilegeClass.A_READ_ONLY,
        ("a", "b", "s", "w"),
        1,
        linux="ls -l",
        summary="List a folder.",
    ),
    CommandSpec(
        "cd",
        ("chdir",),
        PrivilegeClass.A_READ_ONLY,
        (),
        1,
        linux="cd, pwd",
        summary="Show or change the current folder for this terminal.",
    ),
    CommandSpec(
        "cls",
        ("clear",),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        linux="clear",
        summary="Clear the screen.",
    ),
    CommandSpec(
        "echo", (), PrivilegeClass.A_READ_ONLY, (), 64, linux="echo", summary="Print text."
    ),
    CommandSpec(
        "type",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        1,
        min_args=1,
        linux="cat",
        summary="Show a text file (bounded).",
    ),
    CommandSpec(
        "getmac",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        linux="ip link",
        summary="Show physical addresses.",
    ),
    CommandSpec(
        "netstat",
        (),
        PrivilegeClass.A_READ_ONLY,
        ("a", "n"),
        0,
        linux="ss -tulpn",
        summary="Show listening sockets (bounded).",
    ),
    CommandSpec(
        "taskkill",
        (),
        PrivilegeClass.B_USER_MUTATION,
        ("pid", "im", "f"),
        1,
        min_args=1,
        linux="kill (SIGTERM / SIGKILL)",
        summary="End one of your own programs by PID, after confirmation.",
    ),
    CommandSpec(
        "shutdown",
        (),
        PrivilegeClass.C_ADMIN_MUTATION,
        ("s", "r", "t", "a", "f"),
        1,
        linux="systemctl poweroff / reboot (logind)",
        summary="shutdown /s (power off) or /r (restart) [/t seconds]; asks first.",
    ),
    CommandSpec(
        "regedit",
        (),
        PrivilegeClass.E_NO_EQUIVALENT,
        (),
        0,
        linux="no registry; dconf/gsettings and files",
        summary="No equivalent on Linux.",
    ),
    CommandSpec(
        "copy",
        (),
        PrivilegeClass.B_USER_MUTATION,
        (),
        2,
        min_args=2,
        linux="cp (GIO)",
        summary="Copy a file; asks first; never overwrites.",
    ),
    CommandSpec(
        "move",
        (),
        PrivilegeClass.B_USER_MUTATION,
        (),
        2,
        min_args=2,
        linux="mv (GIO)",
        summary="Move a file or folder; asks first; never overwrites.",
    ),
    CommandSpec(
        "ren",
        ("rename",),
        PrivilegeClass.B_USER_MUTATION,
        (),
        2,
        min_args=2,
        linux="mv (GIO)",
        summary="Rename a file or folder; asks first.",
    ),
    CommandSpec(
        "del",
        ("erase",),
        PrivilegeClass.B_USER_MUTATION,
        (),
        1,
        min_args=1,
        linux="gio trash",
        summary="Move a file or folder to the Trash (restorable); asks first.",
    ),
    CommandSpec(
        "md",
        ("mkdir",),
        PrivilegeClass.B_USER_MUTATION,
        (),
        1,
        min_args=1,
        linux="mkdir (GIO)",
        summary="Create a folder; asks first.",
    ),
    CommandSpec(
        "rd",
        ("rmdir",),
        PrivilegeClass.B_USER_MUTATION,
        (),
        1,
        min_args=1,
        linux="rmdir (GIO)",
        summary="Remove an empty folder; asks first.",
    ),
    CommandSpec(
        "assoc",
        ("ftype",),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        linux="mimeapps.list via GIO (xdg-mime)",
        summary="Show which program opens each common kind of file.",
    ),
    CommandSpec(
        "netsh",
        (),
        PrivilegeClass.C_ADMIN_MUTATION,
        (),
        9,
        min_args=3,
        linux="NetworkManager (nmcli)",
        summary="interface set interface <name> enable|disable; interface ip set "
        "address|dns <name> static ...|dhcp; asks first.",
    ),
    CommandSpec(
        "ping",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        3,
        min_args=1,
        linux="ping (in a terminal window)",
        summary="Ping a host: opens the system ping for 4 echoes in a terminal window.",
    ),
    CommandSpec(
        "tracert",
        ("traceroute",),
        PrivilegeClass.A_READ_ONLY,
        (),
        1,
        min_args=1,
        linux="tracepath (in a terminal window)",
        summary="Trace the route to a host in a terminal window.",
    ),
    CommandSpec(
        "nslookup",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        1,
        min_args=1,
        linux="getaddrinfo, systemd-resolved",
        summary="Look up a name: addresses and the DNS servers in use.",
    ),
    CommandSpec(
        "taskmgr",
        (
            "devmgmt.msc",
            "diskmgmt.msc",
            "eventvwr",
            "eventvwr.msc",
            "services.msc",
            "msconfig",
            "ncpa.cpl",
            "appwiz.cpl",
            "msinfo32",
            "compmgmt.msc",
        ),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        linux="Trier Bridge pages",
        summary="taskmgr, devmgmt.msc, services.msc, eventvwr, ...: open that page here.",
    ),
    CommandSpec(
        "explorer",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        1,
        min_args=0,
        linux="Files (FileManager1 ShowFolders)",
        summary="Open a folder in Files (this folder if none is given).",
    ),
    CommandSpec(
        "start",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        1,
        min_args=1,
        linux="gio open / desktop entries",
        summary="Open a web address, a file, or a program (notepad, calc, explorer).",
    ),
    CommandSpec(
        "net",
        (),
        PrivilegeClass.C_ADMIN_MUTATION,
        (),
        3,
        min_args=1,
        linux="systemctl (services); no NetBIOS",
        summary="net start|stop <service> (asks); net user, net use, net share explain.",
    ),
    CommandSpec(
        "date",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        min_args=0,
        linux="date; timedatectl",
        summary="Show the date; changing it is in Settings, Date and Time.",
    ),
    CommandSpec(
        "time",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        min_args=0,
        linux="date; timedatectl",
        summary="Show the time; changing it is in Settings, Date and Time.",
    ),
    CommandSpec(
        "sfc",
        (),
        PrivilegeClass.E_NO_EQUIVALENT,
        (),
        2,
        min_args=0,
        linux="debsums / apt reinstall; no System File Checker",
        summary="No equivalent on Linux.",
    ),
    CommandSpec(
        "chkdsk",
        (),
        PrivilegeClass.E_NO_EQUIVALENT,
        (),
        3,
        min_args=0,
        linux="fsck at boot; GNOME Disks checks a volume",
        summary="No equivalent from here.",
    ),
    CommandSpec(
        "xcopy",
        ("robocopy",),
        PrivilegeClass.E_NO_EQUIVALENT,
        (),
        9,
        min_args=0,
        linux="Files copies folders; rsync",
        summary="Folders are copied in Files.",
    ),
    CommandSpec(
        "gpedit",
        (),
        PrivilegeClass.E_NO_EQUIVALENT,
        (),
        0,
        min_args=0,
        linux="no Group Policy; dconf profiles",
        summary="No equivalent on Linux.",
    ),
    CommandSpec(
        "findstr",
        (),
        PrivilegeClass.A_READ_ONLY,
        ("i", "n", "c", "v", "r", "l"),
        4,
        min_args=2,
        linux="grep",
        summary="findstr [/I] [/N] [/R] text file [file...]: lines containing text (/R: pattern).",
    ),
    CommandSpec(
        "find",
        (),
        PrivilegeClass.A_READ_ONLY,
        (
            "i",
            "n",
            "c",
            "v",
        ),
        2,
        min_args=2,
        linux="grep",
        summary="find [/I] [/N] text file: lines containing text (Windows find).",
    ),
    CommandSpec(
        "where",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        1,
        min_args=1,
        linux="which",
        summary="Show where a program lives on this computer.",
    ),
    CommandSpec(
        "set",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        1,
        min_args=0,
        linux="env",
        summary="Show environment variables (familiar Windows names included).",
    ),
    CommandSpec(
        "path",
        (),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        min_args=0,
        linux="echo $PATH",
        summary="Show the program search path.",
    ),
    CommandSpec(
        "tree",
        (),
        PrivilegeClass.A_READ_ONLY,
        (
            "f",
            "a",
        ),
        1,
        min_args=0,
        linux="tree",
        summary="Show folders (and files with /F) below a folder, bounded.",
    ),
    CommandSpec(
        "attrib",
        (),
        PrivilegeClass.E_NO_EQUIVALENT,
        (),
        9,
        min_args=0,
        linux="chmod, chattr; Files Properties, Permissions",
        summary="No equivalent here.",
    ),
    CommandSpec(
        "icacls",
        (
            "cacls",
            "takeown",
        ),
        PrivilegeClass.E_NO_EQUIVALENT,
        (),
        9,
        min_args=0,
        linux="chmod, chown, setfacl; Files Properties, Permissions",
        summary="No equivalent here.",
    ),
    CommandSpec(
        "exit",
        ("logoff",),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        min_args=0,
        linux="-",
        summary="Nothing to close: pick another section or close the window.",
    ),
    CommandSpec(
        "powershell",
        ("pwsh",),
        PrivilegeClass.A_READ_ONLY,
        (),
        0,
        linux="pwsh (PowerShell 7, the powershell snap)",
        summary="Open real PowerShell in your terminal, if it is installed.",
    ),
    CommandSpec(
        "format",
        (),
        PrivilegeClass.E_NO_EQUIVALENT,
        (),
        8,
        linux="GNOME Disks / mkfs (never from here)",
        summary="Deliberately unsupported.",
    ),
)

_BY_NAME: dict[str, CommandSpec] = {}
for _spec in COMMANDS:
    _BY_NAME[_spec.name] = _spec
    for _alias in _spec.aliases:
        _BY_NAME[_alias] = _spec


def tokenize(line: str) -> list[str] | ParseFailure:
    """CMD-style tokens: whitespace separated, double quotes group, "" inside quotes is a quote."""
    if len(line) > MAX_LINE:
        return ParseFailure(
            Failure.TOO_LONG, f"The command is longer than {MAX_LINE} characters. Nothing was run."
        )
    if any(unicodedata.category(c) == "Cc" and c not in "\t" for c in line):
        return ParseFailure(
            Failure.BAD_ENCODING, "The command contains control characters. Nothing was run."
        )
    bad = next((c for c in line if c in SHELL_META), None)
    if bad is not None:
        return ParseFailure(
            Failure.SHELL_SYNTAX,
            f"Bridge Mode does not chain or redirect commands ('{bad}'). Nothing was run.",
            bad,
        )
    tokens: list[str] = []
    cur: list[str] = []
    in_q = False
    had_token = False
    i = 0
    while i < len(line):
        c = line[i]
        if in_q:
            if c == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    cur.append('"')
                    i += 1
                else:
                    in_q = False
            else:
                cur.append(c)
        elif c == '"':
            in_q = True
            had_token = True
        elif c in " \t":
            if cur or had_token:
                tokens.append("".join(cur))
                cur = []
                had_token = False
        else:
            cur.append(c)
            had_token = True
        i += 1
    if in_q:
        return ParseFailure(
            Failure.BAD_QUOTING, "A quotation mark was not closed. Nothing was run."
        )
    if cur or had_token:
        tokens.append("".join(cur))
    return tokens


def parse(line: str) -> BridgeCommand | ParseFailure:
    toks = tokenize(line.strip())
    if isinstance(toks, ParseFailure):
        return toks
    if not toks:
        return ParseFailure(Failure.EMPTY, "")
    from .cmdlets import translate  # PowerShell names become Bridge tokens first

    tr = translate(toks)
    if tr.failure:
        return ParseFailure(Failure[tr.failure_kind], tr.failure, tr.token)
    toks = tr.tokens
    name = toks[0].lower()
    if name.endswith(".exe"):
        name = name[:-4]
    spec = _BY_NAME.get(name)
    if spec is None:
        return ParseFailure(
            Failure.UNKNOWN_COMMAND,
            f"'{toks[0]}' is not a Bridge command. Nothing was run. Type help for the list.",
            toks[0],
        )
    if spec.privilege is PrivilegeClass.E_NO_EQUIVALENT:
        return ParseFailure(
            Failure.NO_EQUIVALENT,
            f"'{spec.name}' has no faithful Linux equivalent ({spec.linux}). Nothing was run.",
            spec.name,
        )
    switches: list[str] = []
    args: list[str] = []
    for tok in toks[1:]:
        if (
            tok.startswith("/")
            and len(tok) > 1
            and (
                spec.name not in ("echo", "type", "dir", "cd") + FILE_COMMANDS
                or tok[1:].lower() in spec.switches  # a known switch wins over a path
            )
        ):
            sw = tok[1:].lower()
            if sw not in spec.switches:
                return ParseFailure(
                    Failure.UNKNOWN_SWITCH,
                    f"'{tok}' is not a switch that {spec.name} understands here. Nothing was run.",
                    tok,
                )
            switches.append(sw)
        elif tok.startswith("/") and len(tok) > 1 and spec.name == "dir":
            sw = tok[1:].lower()
            if sw not in spec.switches:
                return ParseFailure(
                    Failure.UNKNOWN_SWITCH,
                    f"'{tok}' is not a switch that dir understands here. Nothing was run.",
                    tok,
                )
            switches.append(sw)
        else:
            args.append(tok)
    if len(args) > spec.max_args:
        return ParseFailure(
            Failure.TOO_MANY_ARGS,
            f"{spec.name} was given more than it accepts. Nothing was run.",
            args[spec.max_args],
        )
    if len(args) < spec.min_args:
        return ParseFailure(Failure.MISSING_ARG, f"{spec.name} needs an argument. Nothing was run.")
    return BridgeCommand(spec, tuple(switches), tuple(args), line, tr.note)


def specs() -> tuple[CommandSpec, ...]:
    return COMMANDS
