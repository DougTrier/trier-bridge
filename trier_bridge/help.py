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
"""Help content, generated from what this build actually contains.

The Manual is optional (docs/EXPERIENCE.md): a normal user should never need
it. What Help shows is derived from the catalog, the Bridge command table, and
the integration catalog, so it can never describe a feature that is not there
(TB-INV-004).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import __version__
from .bridge.cmdlets import CMDLETS
from .bridge.grammar import specs
from .catalog.model import Catalog, Equivalence
from .config import Paths
from .core.state import PrivilegeClass
from .integrations.catalog import CATALOG as INTEGRATIONS

CLASS_TEXT = {
    PrivilegeClass.A_READ_ONLY: "reads only",
    PrivilegeClass.B_USER_MUTATION: "changes something of yours; asks first",
    PrivilegeClass.C_ADMIN_MUTATION: "asks Linux for administrator permission",
    PrivilegeClass.D_HIGH_RISK: "not available",
    PrivilegeClass.E_NO_EQUIVALENT: "explains only; nothing runs",
}


@dataclass(frozen=True)
class HelpSection:
    title: str
    description: str
    rows: tuple[tuple[str, str], ...] = field(default_factory=tuple)  # (title, subtitle)


def sections(catalog: Catalog, paths: Paths) -> list[HelpSection]:
    out = [
        HelpSection(
            "How Trier Bridge works",
            f"Version {__version__}. Everything you know from Windows has a place here; Linux "
            "stays underneath and does the work.",
            (
                (
                    "Nothing changes without asking",
                    "Every change shows what it will do and waits for you. Reading never "
                    "changes anything.",
                ),
                (
                    "Linux decides permissions",
                    "When a change needs administrator rights, Linux itself asks for your "
                    "password for that one action. Trier Bridge never holds it.",
                ),
                (
                    "Everything it adds can be removed",
                    "Integrations write only inside your home folder and are listed under "
                    "Integrations, where each can be turned off exactly.",
                ),
                (
                    "When something is different on Linux, it says so",
                    "Search results and pages tell you when a Windows idea has no exact match "
                    "here, instead of pretending.",
                ),
            ),
        )
    ]
    for group, concepts in catalog.by_group().items():
        rows = []
        for c in concepts:
            words = ", ".join(c.windows_terms[:3])
            tag = {
                Equivalence.EXACT: "",
                Equivalence.APPROXIMATE: " (similar, with differences)",
                Equivalence.NONE: " (no equivalent)",
            }[c.equivalence]
            rows.append((f"{c.title}{tag}", f"Windows: {words}. Linux: {c.linux}"))
        out.append(
            HelpSection(
                f"Windows words: {group}",
                "What each familiar name means here. Type any of them on the Home page.",
                tuple(rows),
            )
        )
    command_rows = tuple(
        (
            s.name + (f" ({', '.join(s.aliases)})" if s.aliases else ""),
            f"{s.summary} {CLASS_TEXT[s.privilege]}. Linux: {s.linux}",
        )
        for s in specs()
    )
    out.append(
        HelpSection(
            "Command Prompt (Bridge Mode)",
            "Windows commands typed here become typed Linux operations. Nothing is passed to "
            "a shell, and unknown commands do nothing.",
            command_rows,
        )
    )
    out.append(
        HelpSection(
            "PowerShell names",
            "These cmdlet names are accepted in the Command Prompt and run the same "
            "operations. Type powershell to open an installed real PowerShell.",
            tuple(
                (
                    c.name + (f" ({', '.join(c.aliases)})" if c.aliases else ""),
                    ("becomes " + " ".join(c.bridge)) if c.bridge else c.teach,
                )
                for c in CMDLETS
            ),
        )
    )
    out.append(
        HelpSection(
            "Integrations",
            "Chosen at first start and changeable any time under Integrations. Each one says "
            "what it changes and how it is undone.",
            tuple(
                (f"{i.title} ({i.group})", f"{i.changes} Off: {i.reversal}") for i in INTEGRATIONS
            ),
        )
    )
    out.append(
        HelpSection(
            "Where Trier Bridge keeps its files",
            "Only these folders, all inside your home. Removing the package leaves them; "
            "delete them yourself if you want nothing left.",
            (
                (str(paths.config), "Preferences and the integration ledger"),
                (str(paths.log_dir), "Log files (bounded, with passwords and keys masked)"),
                (
                    str(paths.journal_dir),
                    "The record of every change, used to recover after a crash",
                ),
            ),
        )
    )
    return out
