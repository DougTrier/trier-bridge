# Trier Bridge Decisions

This file records accepted product and architecture decisions. Open questions remain explicitly open.

## Accepted decisions

| ID | Decision | Status |
|---|---|---|
| DEC-001 | Trier Bridge is an installable experience layer, not a new Linux distribution. | Accepted |
| DEC-002 | Primary audience spans typical office/home users through advanced Windows users. | Accepted |
| DEC-003 | Everyday experience continuity is higher priority than administration tooling. | Accepted |
| DEC-004 | Linux remains authoritative underneath the familiar experience. | Accepted |
| DEC-005 | Familiarity is behavioral/conceptual; do not copy protected Windows visual assets. | Accepted |
| DEC-006 | Core operation is local-first and does not require Internet, account, or subscription. | Accepted |
| DEC-007 | Windows command compatibility uses typed operations, not string-to-shell replacement. | Accepted |
| DEC-008 | PowerShell on Linux should be used where appropriate rather than recreated. | Accepted |
| DEC-009 | Unknown capability remains Unknown. No destructive guessing. | Accepted |
| DEC-010 | Normal Trier Bridge process remains unprivileged. | Accepted |
| DEC-011 | Privileged operations are finite, explicit, operation-scoped, and revalidated. | Accepted |
| DEC-012 | Failure must contain scope, preserve state/evidence, and provide safe recovery. | Accepted |
| DEC-013 | Apache License 2.0 with NOTICE and source-header provenance model. | Accepted |
| DEC-014 | Code quality is judged on engineering evidence, not authoring method. | Accepted |
| DEC-015 | Supported-platform claims require exact environment evidence, not "works on Linux." | Accepted |

## Proposed decisions

Recorded from owner direction on 2026-09-20. A proposed decision becomes Accepted only when Doug Trier confirms it; until then the related open decision stays open.

| ID | Decision | Status |
|---|---|---|
| DEC-016 | Ubuntu LTS (currently 24.04) is the first-release qualification target distro family. Other families follow only with their own evidence. | Proposed |
| DEC-017 | Development, tool, unit, and parser testing use a disposable WSL2 Ubuntu instance created for this project and removed when done. Desktop, NetworkManager, udisks, and polkit qualification use a disposable Hyper-V Ubuntu Desktop VM created for this project. Neither the pre-existing `Ubuntu-24.04-Recovered` WSL distro nor the owner's work-production Hyper-V VM is ever used, modified, exported, or checkpointed by project work. WSL evidence is recorded as its own environment profile (Ubuntu 24.04 / WSL2 / no desktop session) and is never claimed as desktop support (TB-INV-023). | Proposed |

## Open decisions

- implementation language/runtime
- desktop framework
- supported first-release distros
- first-release desktops
- package formats
- persistence engine
- exact native integration mechanisms
- file-manager integration depth
- launcher/taskbar integration depth
- update mechanism
- first-release package-management scope
- first-release destructive storage scope
- exact privilege helper design

Open decisions must not be silently resolved in implementation.
