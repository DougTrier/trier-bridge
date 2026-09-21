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
"""Catalog records, loading, validation, and search."""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum, unique
from pathlib import Path

SCHEMA_VERSION = 1


@unique
class Equivalence(Enum):
    """How faithful the Linux counterpart is (TB-INV-003, TB-INV-065)."""

    EXACT = "exact"  # same task, same outcome
    APPROXIMATE = "approximate"  # same task, different shape or scope; the UI says so
    NONE = "none"  # no faithful counterpart; educational only (TB-INV-105)


@unique
class RouteKind(Enum):
    SECTION = "section"  # a Trier Bridge view
    GNOME_SETTINGS = "gnome-settings"  # a GNOME Settings panel
    FOLDER = "folder"  # an XDG special folder or URI in the file manager
    APP = "app"  # a desktop application by desktop id
    TEACH = "teach"  # nothing to open; explanation only
    ACTION = "action"  # something the Bridge window does through the desktop (screenshot)


@dataclass(frozen=True)
class Route:
    kind: RouteKind
    target: str = ""  # section key, panel name, folder key or URI, desktop id


@dataclass(frozen=True)
class Concept:
    id: str
    title: str
    windows_terms: tuple[str, ...]
    route: Route
    linux: str  # what actually does this on Linux, in plain words
    equivalence: Equivalence
    group: str
    note: str = ""  # what is different, when equivalence is not exact
    linux_terms: tuple[str, ...] = field(default_factory=tuple)

    @property
    def can_open(self) -> bool:
        return self.route.kind is not RouteKind.TEACH and self.equivalence is not Equivalence.NONE

    def mapping_note(self) -> str:
        """The mapping note TB-INV-065 requires for every Windows-labelled concept."""
        base = {
            Equivalence.EXACT: "Same task on Linux.",
            Equivalence.APPROXIMATE: "Similar on Linux, with differences.",
            Equivalence.NONE: "No direct equivalent on Linux.",
        }[self.equivalence]
        return f"{base} {self.note}".strip()


class CatalogError(ValueError):
    """The catalog file is malformed. The catalog is data the product ships, so this is a bug."""


def _fold(text: str) -> str:
    """Case- and accent-insensitive comparison key; punctuation becomes spaces."""
    norm = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in norm if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", stripped.lower()).strip()


@dataclass(frozen=True)
class Match:
    concept: Concept
    score: int  # higher is better
    matched_term: str


class Catalog:
    def __init__(self, concepts: tuple[Concept, ...]) -> None:
        ids = [c.id for c in concepts]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise CatalogError(f"duplicate concept ids: {sorted(dupes)}")
        self.concepts = concepts
        self._by_id = {c.id: c for c in concepts}
        self._index: list[tuple[str, str, Concept]] = []
        for c in concepts:
            for term in c.windows_terms + (c.title,) + c.linux_terms:
                self._index.append((_fold(term), term, c))

    @classmethod
    def load(cls, path: Path) -> "Catalog":
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CatalogError(f"cannot read catalog {path}: {exc}") from exc
        if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_VERSION:
            raise CatalogError(f"catalog schema must be {SCHEMA_VERSION}")
        concepts: list[Concept] = []
        for raw in doc.get("concepts", []):
            try:
                route = raw["route"]
                concepts.append(
                    Concept(
                        id=str(raw["id"]),
                        title=str(raw["title"]),
                        windows_terms=tuple(str(t) for t in raw["windows"]),
                        route=Route(RouteKind(route["kind"]), str(route.get("target", ""))),
                        linux=str(raw["linux"]),
                        equivalence=Equivalence(raw["equivalence"]),
                        group=str(raw["group"]),
                        note=str(raw.get("note", "")),
                        linux_terms=tuple(str(t) for t in raw.get("linux_terms", [])),
                    )
                )
            except (KeyError, ValueError, TypeError) as exc:
                raise CatalogError(f"bad concept entry {raw.get('id', '?')!r}: {exc}") from exc
        for c in concepts:
            if c.equivalence is not Equivalence.EXACT and not c.note:
                raise CatalogError(f"{c.id}: non-exact mappings must carry a note (TB-INV-065)")
            if c.route.kind is RouteKind.TEACH and c.route.target:
                raise CatalogError(f"{c.id}: teach routes have no target")
            if c.route.kind is not RouteKind.TEACH and not c.route.target:
                raise CatalogError(f"{c.id}: route needs a target")
        return cls(tuple(concepts))

    def get(self, concept_id: str) -> Concept | None:
        return self._by_id.get(concept_id)

    def search(self, query: str, limit: int = 10) -> list[Match]:
        """Rank: exact term > term starts with query > query starts a word > substring."""
        q = _fold(query)
        if not q:
            return []
        best: dict[str, Match] = {}
        for folded, term, concept in self._index:
            score = 0
            if folded == q:
                score = 100
            elif folded.startswith(q):
                score = 80
            elif any(w.startswith(q) for w in folded.split()):
                score = 60
            elif q in folded:
                score = 40
            elif all(any(w.startswith(qw) for w in folded.split()) for qw in q.split()):
                score = 30
            if score and (concept.id not in best or best[concept.id].score < score):
                best[concept.id] = Match(concept, score, term)
        ranked = sorted(best.values(), key=lambda m: (-m.score, m.concept.title))
        return ranked[:limit]

    def by_group(self) -> dict[str, list[Concept]]:
        out: dict[str, list[Concept]] = {}
        for c in self.concepts:
            out.setdefault(c.group, []).append(c)
        return out
