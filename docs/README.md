# Trier Bridge Documentation

**Updated:** 2026-09-21 12:05 AM CDT  
**Status:** Design foundation. Every runtime, test, or evidence statement in this pack is a design contract or template until observed evidence is recorded.

## Authority order

When documents conflict, use the order in the root `AGENTS.md`:

1. latest explicit Doug Trier instruction
2. `AGENTS.md`
3. `CONTEXT.md`
4. `Engine Spec Tasklist 01.MD`
5. `docs/PRODUCT-NORTH-STAR.md`
6. `docs/SECURITY.md` and `docs/INVARIANTS.md` (stricter rule controls between them)
7. `docs/DECISIONS.md`
8. `docs/ENGINEERING.md`
9. affected subsystem documents
10. roadmap/task indexes
11. historical reports

Do not silently choose a weaker interpretation. If documents conflict, stop and reconcile.

## Governing documents

| Document | Purpose |
|---|---|
| `PRODUCT-CONCEPT.md` | Full product concept: thesis, audience, every experience surface, MVP phases, success criteria. |
| `PRODUCT-NORTH-STAR.md` | Governing product direction, UX priority order, decision test, owner product directive. |
| `DECISIONS.md` | Accepted decisions DEC-001 to DEC-028 and the explicit list of open decisions. |
| `SECURITY.md` | Security architecture, trust boundaries, TB-SEC invariants, threat model, testing strategy, release gate. |
| `INVARIANTS.md` | The 258 binding TB-INV invariants, fault-injection catalog, graceful-failure hierarchy, research baseline. |
| `ENGINEERING.md` | Architecture rules, layers, domain boundaries, build contract, automation, optimization, good first issues. |
| `CODE-QUALITY.md` | CQS standard, hard gates, quality vocabulary, review questions. |
| `LICENSING.md` | Apache-2.0 policy, headers, NOTICE, third-party and asset provenance. |

## Subsystem and process documents

| Document | Purpose |
|---|---|
| `PLATFORMS.md` | Environment identity, support states, capability discovery, adapter contract, hardware profiles. |
| `STATE-AND-PERSISTENCE.md` | Capability/authorization/operation/recovery state models and what Trier Bridge may persist. |
| `EXPERIENCE.md` | Interaction rules, screen inventory, search, connectivity, displays, Manual, localization, theming. |
| `VALIDATION.md` | Evidence states, evidence records, qualification automation, pre-implementation checklist, acceptance cases, evidence ledger. |
| `ROADMAP.md` | Product phases, the eight implementation foundations, and the baseline protocol. |
| `RESEARCH.md` | Research plan with exit criteria (R1 to R18), in-guest findings, reference policy. |
| `DELIVERY-MODEL.md` | SCOPE-01: what Trier Bridge is on the desktop, first-run setup, integration catalog seed, non-invasive checklist. |
| `PRIVILEGE-MODEL.md` | SCOPE-02: no privileged helper in the first release; polkit-mediated services, identity and lifecycle on D-Bus. |
| `PACKAGING.md` | SCOPE-03: native `.deb` core, excluded formats, package contents and lifecycle behavior. |
| `TEST-STRATEGY.md` | SCOPE-05: real-VM oracle, real test objects, layers, fault injection, run discipline. |
| `STACK-SELECTION.md` | ARC-01/02 proposal (DEC-020): Python + PyGObject, GTK 4 + libadwaita; candidates, evidence, costs, what Foundation 01 pins. |

## Root control files

| File | Purpose |
|---|---|
| `README.md` | Public overview. |
| `AGENTS.md` | Operating rules for agents and automated contributors; authority order. |
| `CONTEXT.md` | Current checkpoint and resume protocol. |
| `Engine Spec Tasklist 01.MD` | The single operational task/completion ledger. |
| `CONTRIBUTING.md` | Human contribution policy and review levels. |
| `CODE-QUALITY-REPORT.md` | Current CQS report (94 / 100, measured). |
| `ACCESSIBILITY.md` | Accessibility criteria TB-A11Y-01..09 and their evidence state. |
| `FEATURE-INVARIANT-MAP.md` | Generated map from every evidence entry to the invariants it cites (`tools/dev.py map`). |
| `KNOWN-LIMITATIONS.md` | Generated known-limitations report: the failures/limitations and evidence state of every entry (`tools/dev.py limitations`, IMP-08.09). |
| `LICENSE`, `NOTICE`, `SOURCE-HEADER.txt` | Apache-2.0 text, attribution, canonical source header. |
| `tools/` | Read-only engineering tools (`tb context`, `tb all`, `tb section`, ...). See `tools/README.md`. |

## How the documents are organized

Design documents state commitments; `VALIDATION.md` records what has been shown true, entry by entry, with the commit hash it was shown on; the ledger tracks what is done and what is not. The security design in `SECURITY.md` is stated as Trier Bridge's own principles, and whether the code honors each one is a question for the invariants and the evidence, never for the prose.

## Consolidation record — 2026-09-20

The original pack of 75 root files was condensed. Content was merged, not dropped, except where noted.

| Former file(s) | Now in |
|---|---|
| `Trier_Bridge_Concept_Revised.md` | Deleted; byte-identical duplicate of `PRODUCT-CONCEPT.md`. |
| `OWNER-PRODUCT-DIRECTIVE.md` | `PRODUCT-NORTH-STAR.md` (owner directive section). |
| `TRIER-BRIDGE-CODE-QUALITY.md` | Renamed `CODE-QUALITY.md`. |
| `BUILDING.md`, `ENGINEERING-AUTOMATION.md`, `OPTIMIZATION.md`, `RESOURCE-EFFICIENCY.md`, `GOOD-FIRST-ISSUES.md`, `ROOT-FILE-MAP.md` | `ENGINEERING.md` |
| `PLATFORM-ADAPTERS.md`, `CAPABILITY-DISCOVERY.md`, `HARDWARE-PROFILES.md` | `PLATFORMS.md` |
| `STATE-MODEL.md`, `PERSISTENCE.md`, `PERSISTENCE-DESIGN.md`, `DATABASE-DESIGN.md`, `PERSISTENCE-TEST-REPORT.md` | `STATE-AND-PERSISTENCE.md` |
| `INTERACTION-RULES.md`, `SCREEN-FLOW-INVENTORY.md`, `SEARCH-AND-IDENTIFICATION.md`, `CONNECTIVITY.md`, `DISPLAYS.md`, `MANUAL.md`, `LOCALIZATION.md`, `THEMING.md`, `DEFAULT-VISUAL-ASSETS.md`, `DESIGN-AND-REUSE.md` | `EXPERIENCE.md` |
| `INTERACTION-ACCEPTANCE.md`, `QUALIFICATION-AUTOMATION.md`, `PREIMPLEMENTATION-CHECKLIST.md`, `FOUNDATION-TEST-REPORT.md`, `TASK-EVIDENCE.md` | `VALIDATION.md` |
| `FOUNDATION-SEQUENCING.md`, `IMPLEMENTATION-BASELINE-01.md` through `-08.md`, `TASKS.md` | `ROADMAP.md` |
| `REFERENCE-POLICY.md` | `RESEARCH.md` |
| `SECURITY-DESIGN.md`, `SECURITY-THREAT-REVIEW.md`, `SECURITY-VERIFICATION.md`, `RELEASE-SECURITY.md` | `SECURITY.md` (sections 5, 6.3, 37, 40 already covered them; the threat-review record fields were added as 6.3). |
| `README-DOCS.md`, `DOCUMENT-MAP.md`, `DOCUMENT-ALIGNMENT.md` | This file. The Goldenage per-file mapping table was dropped as historical. |

Authority-order drift between `AGENTS.md` and the former `DOCUMENT-ALIGNMENT.md` was resolved in favor of `AGENTS.md`. Phase numbering drift between the concept, roadmap, and foundation sequencing was reconciled in `ROADMAP.md`.

Originals were backed up outside the project before deletion.
