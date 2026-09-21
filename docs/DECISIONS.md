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
| DEC-016 | Ubuntu 24.04 LTS is the first-release qualification target. Ubuntu-based derivatives (for example Linux Mint, Zorin OS, Pop!_OS) are the next targets because the adapters carry over, but each derivative still receives its own evidence before any support claim (TB-INV-017, TB-INV-231). Owner accepted 2026-09-20. | Accepted |
| DEC-019 | Delivery model: Trier Bridge ships as one integrated build containing the application (launcher/search, familiar file entry points, settings routing, system tools, Bridge Terminal) and every desktop integration it provides. Which integrations are active is decided by user intent: on first launch after package installation a setup screen lists every integration, organized into named groups (feature subsets) so the user can select a whole group or individual items and integrate as much or as little as they want. Nothing is activated before that choice. Every integration is cleanly reversible and can be changed at any time from the application. Otherwise the product stays out of sight: a simple tray icon (a plain "T") opens the options. Integrations use only each desktop's standard extension points and augment the native file manager rather than replacing it. Global key/mouse rebinding and file-association changes are individual items, never part of a default group. Privileged operations run in a small separate system service registered with polkit, started on demand, exiting when idle. Sandboxed package formats that block system access are not candidates for the core. Owner direction 2026-09-20. | Accepted |

| DEC-020 | Implementation stack (ARC-01/ARC-02): Python 3.12 with PyGObject; GTK 4 with libadwaita; per `docs/STACK-SELECTION.md`. Owner delegated the choice on 2026-09-21 ("that is in your area of expertise; I stated the outcome and you make it happen as safe and secure as possible"). Accepted under that delegation; alternatives remain recorded for revisit with new evidence. | Accepted |
| DEC-021 | Testing uses only real systems and real test objects in the project VM; no synthetic fixtures, mocks, or stubbed services. A fixture may exist only if the owner names it and its single scenario in `docs/TEST-STRATEGY.md`. Accepted under the same delegation, consistent with the owner's global no-mock rule. | Accepted |
| DEC-022 | Updates are deferred for the first release: Trier Bridge updates arrive through the same package channel as installation; no self-update mechanism; a signed repository is a later, owner-gated step (`docs/PACKAGING.md` section 5). Closes ARC-12. | Accepted |
| DEC-023 | Implementation is authorized. On 2026-09-21 the owner set the goal "continue working until the project is done or I ask you to stop." Foundation 01 may begin; every later foundation still requires its prerequisites and evidence (ledger completion rules). Publication remains owner-gated (AGENTS.md section 14). | Accepted |
| DEC-024 | First-release scope of network and package mutations (IMP-06.06): none. Trier Bridge reads network and package facts and opens the desktop's own tools for changes (GNOME Settings panels, App Center); it does not install, remove, or reconfigure packages or connections itself. Rationale: every such change is class C with a large failure surface (SECURITY.md sections 37.6 and 37.8), the desktop already has qualified tools for it, and the non-invasive directive (DEC-018) favours routing over reimplementing. Revisit after the acceptance cases with a separate qualification plan. Proposed 2026-09-21 for the owner. | Proposed |

## Rejected decisions

| ID | Decision | Status |
|---|---|---|
| DEC-017 | Use a WSL2 Ubuntu instance for tool/unit/parser testing. Rejected by owner 2026-09-20: all Linux testing uses the disposable Hyper-V Ubuntu Desktop VM (`tb-ubuntu-desktop-2404`). The rules that survive: never touch the owner's work-production Hyper-V VM or the pre-existing WSL distro; VM creation/removal is an owner-run step; evidence names the exact environment. | Rejected |

## Open decisions

- DEC-024 (package and network mutations: none in the first release) awaits the owner
- (closed 2026-09-21) name: Trier Bridge is part of Trier OS, whose trademark the owner holds (SCOPE-12)
- localization: English only until decided (`docs/ACCESSIBILITY.md` TB-A11Y-09)

Decided since the list was written: first-release desktop and distro (ARC-09/10, `PLATFORMS.md` section 10), package format (ARC-11), persistence engine (ARC-07), native integration mechanisms and file-manager and launcher depth (SCOPE-14, `DELIVERY-MODEL.md` section 3).
- first-release destructive storage scope
- exact privilege helper design

Open decisions must not be silently resolved in implementation.
