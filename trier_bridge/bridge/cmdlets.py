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
"""PowerShell cmdlet names accepted in Bridge Mode (IMP-07.07).

A cmdlet line is rewritten into the equivalent Bridge command before parsing,
so it runs through the same typed operation with the same limits and the same
confirmation. Only the listed cmdlets and parameters are accepted; anything
else does nothing (TB-INV-085, TB-INV-086). Cmdlets with no faithful
counterpart teach instead of pretending (TB-INV-103, TB-INV-104). Nothing
here reimplements PowerShell: real PowerShell is the ``powershell`` command,
which opens an installed ``pwsh``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# A parameter maps to (bridge switch or "", takes a value).
Params = dict[str, tuple[str, bool]]


@dataclass(frozen=True)
class Cmdlet:
    name: str  # canonical cmdlet name, e.g. Get-Process
    aliases: tuple[str, ...]
    bridge: tuple[str, ...]  # Bridge tokens it becomes, e.g. ("sc", "query")
    params: Params = field(default_factory=dict)
    positional: int = 1  # how many plain arguments pass through; -1 = all
    teach: str = ""  # when set: no translation, explanation only


CMDLETS: tuple[Cmdlet, ...] = (
    Cmdlet("Get-Process", ("gps", "ps"), ("tasklist",), positional=0),
    Cmdlet(
        "Stop-Process",
        ("spps", "kill"),
        ("taskkill",),
        {"-id": ("/pid", True), "-force": ("/f", False)},
        positional=1,
    ),
    Cmdlet("Get-Service", ("gsv",), ("sc", "query"), {"-name": ("", True)}),
    Cmdlet("Get-NetIPConfiguration", ("gip",), ("ipconfig", "/all"), positional=0),
    Cmdlet("Get-NetIPAddress", (), ("ipconfig",), positional=0),
    Cmdlet("Get-NetTCPConnection", (), ("netstat",), positional=0),
    Cmdlet("Get-ComputerInfo", (), ("systeminfo",), positional=0),
    Cmdlet(
        "Get-ChildItem",
        ("gci", "ls"),
        ("dir",),
        {"-path": ("", True), "-literalpath": ("", True)},
    ),
    Cmdlet("Set-Location", ("sl",), ("cd",), {"-path": ("", True)}),
    Cmdlet("Get-Location", ("gl", "pwd"), ("cd",), positional=0),
    Cmdlet(
        "Get-Content",
        ("gc", "cat"),
        ("type",),
        {"-path": ("", True), "-literalpath": ("", True)},
    ),
    Cmdlet("Clear-Host", ("clear",), ("cls",), positional=0),
    Cmdlet("Write-Output", ("write", "write-host"), ("echo",), positional=-1),
    Cmdlet("Get-Help", ("man",), ("help",), {"-name": ("", True)}),
    Cmdlet(
        "Get-EventLog",
        ("get-winevent",),
        (),
        teach="Event logs live in the system journal here. Open Event Viewer in Trier Bridge "
        "(journalctl underneath).",
    ),
    Cmdlet(
        "Get-WmiObject",
        ("gwmi", "get-ciminstance"),
        (),
        teach="There is no WMI on Linux. systeminfo, Device Manager, and Disk Management read "
        "the same facts from /proc, /sys, and udisks2.",
    ),
)

_BY_NAME: dict[str, Cmdlet] = {}
for _c in CMDLETS:
    _BY_NAME[_c.name.lower()] = _c
    for _a in _c.aliases:
        _BY_NAME[_a.lower()] = _c


def cmdlet_for(name: str) -> Cmdlet | None:
    return _BY_NAME.get(name.lower())


@dataclass(frozen=True)
class Translation:
    tokens: list[str]
    note: str = ""  # "Get-Process → tasklist" when a cmdlet was rewritten
    failure: str = ""  # plain reason when the line is refused; tokens are then empty
    failure_kind: str = ""  # a grammar Failure value name
    token: str = ""


def translate(tokens: list[str]) -> Translation:
    """Rewrite a cmdlet line into Bridge tokens, or refuse it with a plain reason."""
    if not tokens:
        return Translation(tokens)
    c = _BY_NAME.get(tokens[0].lower())
    if c is None:
        return Translation(tokens)
    if c.teach:
        return Translation(
            [],
            failure=f"{c.name}: {c.teach} Nothing was run.",
            failure_kind="NO_EQUIVALENT",
            token=c.name,
        )
    out = list(c.bridge)
    plain: list[str] = []
    i = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok.startswith("-") and len(tok) > 1 and not tok[1:].isdigit():
            key = tok.lower()
            if key not in c.params:
                return Translation(
                    [],
                    failure=f"'{tok}' is not a parameter {c.name} accepts here. Nothing was run.",
                    failure_kind="UNKNOWN_SWITCH",
                    token=tok,
                )
            switch, takes_value = c.params[key]
            if switch:
                out.append(switch)
            if takes_value:
                if i + 1 >= len(tokens):
                    return Translation(
                        [],
                        failure=f"{tok} needs a value. Nothing was run.",
                        failure_kind="MISSING_ARG",
                        token=tok,
                    )
                plain.append(tokens[i + 1])
                i += 2
                continue
            i += 1
            continue
        plain.append(tok)
        i += 1
    if c.positional >= 0 and len(plain) > c.positional:
        return Translation(
            [],
            failure=f"{c.name} was given more than it accepts here. Nothing was run.",
            failure_kind="TOO_MANY_ARGS",
            token=plain[c.positional],
        )
    return Translation(out + plain, note=f"{c.name} → {' '.join(c.bridge)}")


def cmdlet_lines() -> list[str]:
    """Help text: which cmdlet names Bridge Mode understands and what they become."""
    lines = ["PowerShell names accepted here (same typed operations):"]
    for c in CMDLETS:
        target = " ".join(c.bridge) if c.bridge else "explains only"
        params = " ".join(k for k in c.params) if c.params else ""
        lines.append(f"  {c.name:<22}{target}{('  ' + params) if params else ''}")
    lines.append("  Real PowerShell: type powershell (opens an installed pwsh).")
    return lines
