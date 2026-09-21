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
| DEC-018 | Trier Bridge is non-invasive. Owner direction 2026-09-20: it must not be invasive or ever be mistaken for a virus. Engineering meaning: (a) installs as an ordinary desktop application through the distribution's normal package mechanism, visible in Installed Apps, and uninstalls cleanly (TB-INV-026); (b) never replaces the desktop shell, file manager, display manager, login, or terminal; (c) no background process runs unless a user-enabled feature needs it, and any such process is visible under its own name; (d) no autostart, global key/mouse rebinding, or file-association takeover by default; integrations are opt-in, individually toggleable, and reversible (TB-INV-025, TB-INV-077); (e) no hidden privileged component: privileged work goes through a named, packaged, polkit-registered service with documented actions, never a setuid binary or persistent root daemon (TB-SEC-002, TB-INV-107); (f) no telemetry and no network activity outside a feature the user invoked (TB-INV-216, TB-SEC-017); (g) writes only to its own XDG config/data/cache locations; other applications' configuration is touched only with explicit consent; (h) no code injection, LD_PRELOAD, kernel modules, shell-startup hooks, or process tampering; (i) everything it does is inspectable: audit record, plain "what changed" reporting, Show Me the Linux Way, signed releases. | Accepted |

## Proposed decisions

Recorded from owner direction on 2026-09-20. A proposed decision becomes Accepted only when Doug Trier confirms it; until then the related open decision stays open.

| ID | Decision | Status |
|---|---|---|
| DEC-016 | Ubuntu LTS (currently 24.04) is the first-release qualification target distro family. Other families follow only with their own evidence. | Proposed |
| DEC-019 | Delivery model: Trier Bridge ships as one standalone application (launcher/search, familiar file entry points, settings routing, system tools, Bridge Terminal) plus optional desktop integrations delivered only through each desktop's standard extension points (file-manager context-menu entries, desktop search provider, `.desktop` launchers). Files, right-click, and drag-and-drop route to and augment the native file manager rather than replacing it. Privileged operations run in a small separate system service registered with polkit, started on demand by D-Bus activation, exiting when idle. Sandboxed package formats that block system access (Flatpak, strict Snap) are not candidates for the core application. Recorded under owner delegation of approach (2026-09-20); confirmed at ALN-12 review. | Proposed |
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
