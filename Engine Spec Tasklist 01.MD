# Engine Spec Tasklist 01
## Trier Bridge

**Revision:** 0.1  
**Last updated:** 2026-09-20 9:17 PM CDT  
**Owner:** Doug Trier  

**This root file is the single operational task/completion ledger unless Doug later designates another ledger.**

No unchecked task is implied complete.

Documentation completion does not imply implementation, qualification, or release.

---

## Resume dashboard

| Field | Current checkpoint |
|---|---|
| **Active phase** | Design / engineering foundation |
| **Active task** | Page walks for drive letters and the interrupted-operation banner (queued behind the owner's open window); otherwise waiting on the owner's console acceptance |
| **Last completed** | IMP-07.12 closed: shutdown timer/cancel, familiar tool names open pages, findstr /R and /L, Event Viewer Boot view; CODE-QUALITY-REPORT refreshed for candidate 28f6988 (2026-09-21 01:20 PM CDT) |
| **Implementation** | Foundations 01–07 closed except IMP-03.08/09 and IMP-06.06; integrations shipped and reversible; Foundation 08: 01, 02, 07, 08 closed, 03 one cell, 04/05/06 need a person, 09 waits for release (2026-09-21) |
| **Invariant baseline** | 233 design invariants; runtime evidence NOT RUN |
| **Security** | Design baseline exists; implementation evidence NOT RUN |
| **CQS** | 94 / 100, unchanged on refresh for candidate 28f6988 (cognitive outliers 33 → 31, cyclomatic and suppressions unchanged; see CODE-QUALITY-REPORT.md) |
| **Platform support** | No product feature qualified; test environment Ubuntu 24.04.5 / Wayland GNOME 46 / Hyper-V profiled (ENV-02) |
| **Release** | Locked; local Git only, no remote, no GitHub (owner direction 2026-09-20) |
| **Next bounded step** | IMP-02.07 generic read-only fallback qualification; owner: TB-IA acceptance at the console, screenshot on hardware, decision on IMP-06.06, whether the VM window can close for the queued page walks |

---

## Completion rules

1. `[ ]` means incomplete, active, blocked, deferred, or not verified.
2. `[x]` means the exact stated outcome has evidence.
3. Documentation can be complete while implementation remains not started.
4. A compile is not runtime qualification.
5. One distro test is not Linux qualification.
6. Unsupported / Unknown / NOT_RUN are not PASS.
7. If evidence is invalidated, reopen the task.
8. Scope/invariant changes require explicit owner approval.

---

# Alignment / project-control foundation

- [x] **ALN-01** Define Trier Bridge product concept and Windows-to-Linux experience thesis.
- [x] **ALN-02** Correct target audience to typical Windows office/home user through advanced Windows users.
- [x] **ALN-03** Define Product North Star and everyday-continuity priority.
- [x] **ALN-04** Research adjacent Linux/Windows-transition projects and identify the differentiated product gap.
- [x] **ALN-05** Create security architecture baseline.
- [x] **ALN-06** Create 233 numbered design invariants and graceful-failure doctrine.
- [x] **ALN-07** Select Apache License 2.0, NOTICE, and source-provenance model.
- [x] **ALN-08** Create contribution policy.
- [x] **ALN-09** Create code-quality/CQS policy with current status NOT MEASURED.
- [x] **ALN-10** Recreate relevant Goldenage-style documentation architecture for Trier Bridge.
- [x] **ALN-11** Create root README/CONTEXT/AGENTS/task ledger/quality-report templates.
- [ ] **ALN-12** Owner review of complete document foundation and corrections.
- [ ] **ALN-13** Verify links/names/authority order across root and `docs/`.
  - 2026-09-20 9:36 PM CDT: document pack consolidated (75 → 26 files), `docs/` created, links repaired, authority order reconciled to `AGENTS.md`. See `docs/README.md` consolidation record. Awaiting owner confirmation under ALN-12.
- [ ] **ALN-14** Freeze first documentation revision for implementation planning.
- [x] **ALN-15** TB-INV-077 amendment question closed 2026-09-20: owner direction (DEC-019, user selects integrations at setup) satisfies the existing wording. No invariant change made.

---

# Engineering tooling (read-only) and test environments

Tools are engineering automation (`docs/ENGINEERING.md` section 10), not product implementation. Evidence is the recorded tool run.

- [x] **TOOL-01** Create read-only tool entry points (`tools/tb.cmd`, `tools/tb.ps1`, `tools/tb.py`) with config and Apache headers. Evidence: all three wrappers ran 2026-09-20 09:55 PM CDT; `tb headers` 13/13 compliant.
- [x] **TOOL-02** Snapshot / changes / status / context digest. Evidence: `tb context` run 2026-09-20 09:55 PM CDT.
- [x] **TOOL-03** Ledger parser and outline/section/invariant navigation. Evidence: `tb ledger ALN-13`, `tb outline`, `tb section`, `tb inv show/find` run 2026-09-20 09:55 PM CDT.
- [x] **TOOL-04** Link, invariant cross-reference, term-rule, and header checks under `tb all`. Evidence: exit 0 on 2026-09-20 09:55 PM CDT (233 INV, 30 SEC, 30 IA indexed; 33 links; 12 term rules).
- [x] **TOOL-05** Verify the tools run unmodified on Linux inside the Hyper-V VM (`python3 tools/tb.py all`). Evidence: 2026-09-20 11:10 PM CDT in `tb-ubuntu-desktop-2404`, exit 0, counts identical to Windows; see `docs/VALIDATION.md` entry TOOL-05.
- [x] **TOOL-06** Stack-dependent tools: lint/static-analysis orchestration (`dev.py all`), test-result normalization (`dev.py results`), dependency inventory (`dev.py inventory`), CQS evidence collection (`dev.py evidence`), derived docs (`dev.py map`, `dev.py limitations`). Evidence: `docs/VALIDATION.md` entry TOOL-06.
- [ ] **ENV-01** CANCELLED 2026-09-20: WSL instance scratched by owner (DEC-017 rejected). All Linux testing uses the Hyper-V VM under ENV-02.
- [x] **ENV-02** Create the Hyper-V Ubuntu Desktop VM `tb-ubuntu-desktop-2404` (`tb-` prefix, Default Switch, storage on G:, isolated from the work-production VM) for desktop and backend qualification. Evidence: created by owner via `New-TbDesktopVm.ps1` 2026-09-20 10:39 PM CDT (ISO VERIFIED); in-guest profile recorded 11:10 PM CDT in `docs/VALIDATION.md` entry ENV-02 (Ubuntu 24.04.5, Wayland GNOME 46, systemd 255, NM 1.46, udisks 2.10, polkit 124).
  - 2026-09-20 10:25 PM CDT: owner approved. `tools/env/New-TbDesktopVm.ps1`, `Remove-TbDesktopVm.ps1`, and autoinstall seed written and parse-checked; Ubuntu 24.04.5.1 Desktop ISO download to `G:\tb-vms\iso` started with SHA256 verification. Remaining: owner runs the create script from an elevated PowerShell, answers the single installer confirmation, then records the in-guest environment profile.
- [ ] **ENV-03** Baseline `clean-install` checkpoint taken after first login and restore verified;
  - 2026-09-21 12:40 PM CDT: `Get-VMCheckpoint` (read-only) lists one checkpoint, `clean-install`, created 2026-09-20 11:12:55 PM CDT. A restore was not exercised: it would discard the owner's open window and the installed product; the owner decides when. removal procedure (`tools/env/Remove-TbDesktopVm.ps1`) kept available but the owner intends to keep the VM for other uses (2026-09-20).
  - 2026-09-21 12:20 AM CDT: owner enabled passwordless sudo for `tb` in the VM (`/etc/sudoers.d/tb`). Installed for research: `python3-nautilus` 4.0 (+ `gir1.2-nautilus-4.0`), `powershell` snap 7.6.5. Nautilus extension prototype at `~/.local/share/nautilus-python/extensions/tb_nautilus_probe.py` (log in `~/.local/share/tb-nautilus-probe.log`), reversible. None of this is in `clean-install`; a fresh baseline checkpoint should be taken once the morning checks are done.
  - 2026-09-21 12:05 AM CDT: research prototypes left in the guest for the morning check: per-user search provider under `~/.local/share/{dbus-1/services,gnome-shell/search-providers,applications}` and `~/.local/bin/tb-search-provider` (reversible with the recorded uninstall script). `~/tb-research` removed. Not part of `clean-install`.
  - 2026-09-20 11:40 PM CDT: `tools/env/tb-pad.py` shared notepad/file drop added and verified in both directions (host curl, guest wget); desktop launchers created on both sides. Guest deviation from baseline: `~/.local/bin/tb-pad-open.sh`, `~/Desktop/tb-pad.desktop` (not in the `clean-install` checkpoint).
  - 2026-09-20 11:12 PM CDT: VM checkpoint type set to Standard (automatic checkpoints off); baseline checkpoint `clean-install` taken while running, after openssh-server + host key were added and all bootstrap files removed. Restore verification still open (would interrupt the owner session).

---

# Pre-implementation scoping

Gap review 2026-09-20. Each item produces a design document or a data schema under `docs/` and is complete only when that artifact exists and cites its invariants. SCOPE-01 through SCOPE-05 block ARC-01/ARC-02.

- [x] **SCOPE-01** Delivery model and desktop-integration boundary: what Trier Bridge is on the desktop and how it augments rather than replaces the native file manager, launcher, and settings. Governed by DEC-018 and DEC-019 (accepted 2026-09-20: one integrated build; first-run setup screen with grouped integration presets; user intent decides what activates; all reversible and changeable any time; tray icon "T" otherwise). Evidence: `docs/DELIVERY-MODEL.md` written 2026-09-20 11:55 PM CDT from the in-guest probe; live search-provider and Nautilus-extension checks remain open under R1/R2.
- [x] **SCOPE-02** Privilege model. Evidence: `docs/PRIVILEGE-MODEL.md` 2026-09-20. Finding: every first-release mutation has a polkit-mediated system service (systemd1, NetworkManager, UDisks2, PackageKit, login1), so no Trier Bridge privileged helper exists in the first release; the helper design is specified only as a future, owner-approved scope change.
- [x] **SCOPE-03** Packaging constraints and candidates. Evidence: `docs/PACKAGING.md` 2026-09-20: native `.deb` core, snap classic deferred, Flatpak and AppImage excluded, ownership table, install/upgrade/remove behavior, updates deferred to ARC-12. Formal control-file freeze stays ARC-11.
- [x] **SCOPE-04** Research plan with exit criteria. Evidence: `docs/RESEARCH.md` sections 2 and 4, 2026-09-20: 18 tracks with exit criteria; first in-guest probe produced findings F1 to F14 (R15 and R16 closed; R1, R2, R11, R17, R18 gate ARC-01/02 and stay open until their live checks run).
- [x] **SCOPE-05** Test strategy. Evidence: `docs/TEST-STRATEGY.md` 2026-09-20: real VM as the only oracle, real test objects instead of fixtures, layers, fault injection, run discipline from the `clean-install` checkpoint. Owner assumption recorded: no synthetic fixtures (awaiting explicit confirmation).
- [x] **SCOPE-06** (Evidence: `trier_bridge/core/operations.py` and `core/state.py`; `OperationResult.three_answers()`; `docs/STATE-AND-PERSISTENCE.md`; entries IMP-05, IMP-06.04.) Typed operation model: schema (ID, stable target identity, preview, authorization state, result taxonomy) and the rule that turns each result into "did anything change / what stopped it / safest next step".
- [x] **SCOPE-07** (Evidence: `data/catalog/concepts.json` schema 1 with route, equivalence, note, terms; `trier_bridge/catalog/model.py`; entries IMP-03, SCOPE-14 search provider.) Windows-to-Linux concept catalog: data schema for every Windows-labeled concept with route, backend, and equivalence class (exact / approximate / none) per TB-INV-065; drives search, help, Show Me the Linux Way, and Bridge commands.
- [x] **SCOPE-08** Bridge Terminal grammar and MVP command list with class A to E, flags, and typed operation per command. Evidence: `trier_bridge/bridge/grammar.py` (COMMANDS table with class, switches, arity, Linux equivalent), `bridge/cmdlets.py`; entries IMP-07, IMP-07.06/07, IMP-03.03.
- [x] **SCOPE-09** Accessibility acceptance criteria as a stack-selection gate (AT-SPI on Wayland across candidate frameworks, keyboard-only, screen reader, large text). Evidence: `docs/ACCESSIBILITY.md` (TB-A11Y-01..09; 01–05 verified by AT-SPI, 06–08 need a person and stay NOT RUN).
  - 2026-09-21: gate evidence for the proposed framework recorded (F17: GTK4/libadwaita exposes names, descriptions, and switch labels on Wayland). Full criteria document still to write.
- [x] **SCOPE-10** Backend runtime topology: session service versus in-process core, UI-to-backend IPC, relationship to the privileged service. Evidence: `docs/ENGINEERING.md` section 14 (in-process core, no privileged service, two optional small processes, single instance).
- [x] **SCOPE-11** Local pre-commit gate convention (`tools\tb all` before every commit; optional local git hook), since there is no CI. Evidence: `CONTRIBUTING.md` section "Local gate before every commit"; `tools/git-hooks/pre-commit`.
- [x] **SCOPE-12** Name and trademark check on "Trier Bridge" before any public step. Closed by the owner 2026-09-21: Trier Bridge is part of Trier OS, whose trademark the owner holds; the product name is used under that mark. The preliminary search below found no conflicting product.
  - 2026-09-21: preliminary web search only: no software product or registered mark named "Trier Bridge" surfaced; unrelated marks exist for "Bridge" software names (a dead 1986 BRIDGE SOFTWARE LTD. mark, THE BRIDGE mobile-app mark filed 2018, Bridgemate) and "Trier Software Inc." owns LIST-IT!. Not a clearance: a USPTO/EUIPO database search and the owner's decision are still required before any public step.
- [x] **SCOPE-13** Observability specification: log location, levels, redaction, audit placement (SECURITY.md section 26 fields). Evidence: `docs/ENGINEERING.md` section 15; `trier_bridge/logging_setup.py`; `state/journal.py`; entries IMP-01, IMP-05.
- [x] **SCOPE-14** Integration catalog and setup flow: the list of every shippable integration, its named group (feature subset), its desktop extension point, its activation/reversal mechanism, and the first-run setup screen plus tray-icon options flow that presents them (DEC-019). Includes the Ubuntu GNOME tray/AppIndicator research item. Evidence: `docs/VALIDATION.md` entry SCOPE-14; catalog in `trier_bridge/integrations/catalog.py` and `docs/DELIVERY-MODEL.md` section 3 (shipped set marked). Roadmap items (desktop places, Super+E, notifications, pwsh entry) stay in the delivery model as unshipped.

---

# Product and UX freeze

- [ ] **DOC-01** Freeze MVP user journeys for typical office/home users.
  - 2026-09-21 12:40 PM CDT: journeys are implemented and exercised (entry IMP-03.09; `docs/EXPERIENCE.md`); freeze is the owner's call under ALN-12/ALN-14. Awaiting owner freeze.
- [ ] **DOC-02** Freeze familiar file/navigation behavior and desktop integration boundary.
  - 2026-09-21 12:40 PM CDT: boundary as built: Files places and operations in `docs/DELIVERY-MODEL.md` section 3 and entry IMP-03.03; nothing outside the user's home or the desktop's own extension points. Awaiting owner freeze.
- [ ] **DOC-03** Freeze app-launch/search/settings/default-app routing.
  - 2026-09-21 12:40 PM CDT: routing as built: `data/catalog/concepts.json` (search, Settings routes), entries IMP-03 and IMP-03.05 (default apps). Awaiting owner freeze.
- [ ] **DOC-04** Freeze printers/scanners/USB/network-share everyday journeys.
  - 2026-09-21 12:40 PM CDT: printers live from CUPS (entry IMP-03.06/HELP); scanners, USB, and network shares route to the desktop's own tools (catalog) and are not reimplemented. Awaiting owner freeze.
- [ ] **DOC-05** Freeze Task Manager/Startup/Network/Device/Disk/Event Viewer familiar-tool scope.
  - 2026-09-21 12:40 PM CDT: scope as built: entries IMP-04, IMP-04.01, IMP-04.03, IMP-04.07 (drive letters), IMP-06.06 (network translation layer, DEC-024). Awaiting owner freeze.
- [ ] **DOC-06** Freeze Services/Bridge Terminal/PowerShell advanced scope.
  - 2026-09-21 12:40 PM CDT: scope as built: entries IMP-06.05 (Services), IMP-07 and IMP-07.06..07.11 (Bridge Terminal, PowerShell names). Awaiting owner freeze.
- [ ] **DOC-07** Freeze Familiar/Bridge/native-detail progressive disclosure.
  - 2026-09-21 12:40 PM CDT: disclosure as built: Familiar pages, Bridge Mode terminal with `linux` column, native detail through the desktop's own tools (`docs/EXPERIENCE.md`). Awaiting owner freeze.
- [ ] **DOC-08** Complete loading/empty/unknown/unsupported/denied/error/partial/recovery designs.
  - 2026-09-21 12:40 PM CDT: designs as built: `OperationState` and `CommandOutput` cover previewed/denied/partial/unknown/unsupported; empty and unknown views are truthful placeholders (entry IMP-01); recovery banner with Mark reviewed (entry IMP-05). Awaiting owner freeze.
- [ ] **DOC-09** Review accessibility, large text, keyboard-only, screen-reader, and localization behavior.
  - 2026-09-21 12:40 PM CDT: `docs/ACCESSIBILITY.md` TB-A11Y-01..05 verified over AT-SPI; keyboard-only, Orca, large text need a person (IMP-08.06); no localization yet. Awaiting owner freeze.

---

# Platform and architecture freeze

- [x] **ARC-01** Select implementation language/runtime with documented alternatives and rationale. Evidence: `docs/STACK-SELECTION.md`; DEC-020 accepted under owner delegation 2026-09-21.
- [x] **ARC-02** Select desktop/UI framework with Wayland/X11/accessibility/package implications. Evidence: GTK 4 + libadwaita, AT-SPI on Wayland verified (F17); DEC-020.
- [x] **ARC-03** Freeze module/dependency direction. Evidence: `docs/ENGINEERING.md` sections 5 and 14; `CODE-QUALITY-REPORT.md` architecture row (acyclic, verified by reading every import).
- [x] **ARC-04** Freeze typed operation model. Evidence: SCOPE-06; four identity kinds and four plan kinds share one plan → confirm → execute → verify shape (`trier_bridge/operations/`).
- [x] **ARC-05** Freeze capability-discovery contract. Evidence: `trier_bridge/capability/{model,facts,discovery}.py`; `docs/PLATFORMS.md` section 6; entry IMP-02.
- [x] **ARC-06** Freeze platform-adapter interfaces. Evidence: `trier_bridge/system/bus.py` and the `system/*` adapters (procfs, sysfs, journald, systemd, NetworkManager, udisks2, UPower); `docs/PLATFORMS.md` section 7; entries IMP-04, IMP-06.05.
- [x] **ARC-07** Freeze persistence engine and schema ownership. Evidence: JSON files under XDG dirs with atomic replace and schema versions (`config.py`, `state/*`, `integrations/ledger.py`); `docs/STATE-AND-PERSISTENCE.md`; entry IMP-05.
- [x] **ARC-08** Freeze privilege helper / authorization model. Evidence: no helper; `docs/PRIVILEGE-MODEL.md` section 8; entries IMP-06.05, IMP-06.07.
- [x] **ARC-09** Select first-release distro families. Evidence: Ubuntu 24.04 LTS only (DEC-016); `docs/PLATFORMS.md` section 10.
- [x] **ARC-10** Select first-release desktop/session matrix. Evidence: GNOME 46 on Wayland, Ubuntu session; `docs/PLATFORMS.md` section 10 (X11 and other desktops not claimed).
- [x] **ARC-11** Select package formats. Evidence: native `.deb` only; `docs/PACKAGING.md`; `debian/`; entries IMP-01, IMP-08.02.
- [x] **ARC-12** Freeze update mechanism or explicitly defer updates. Evidence: deferred, DEC-022 (2026-09-21), `docs/PACKAGING.md` section 5.
- [x] **ARC-13** Map every selected MVP feature to applicable `TB-INV-###`. Evidence: `docs/FEATURE-INVARIANT-MAP.md`, generated from the Invariant impact line of every evidence entry.
- [x] **ARC-14** Freeze planned test/failure matrix. Evidence: `docs/TEST-STRATEGY.md` section 7 (SECURITY section 37 and Tests A–D mapped, gaps named); `docs/SECURITY.md` section 37.

---

# Foundation 01 — Toolchain and unprivileged shell

**Prerequisites:** ARC-01–ARC-03 and relevant quality/licensing decisions.

- [x] **IMP-01.01** Pin compiler/runtime/framework/build/package tool versions. Evidence: `docs/TOOLCHAIN.md` (Ubuntu 24.04 archive versions observed in the VM, host venv mirrors), 2026-09-21.
- [x] **IMP-01.02** Create clean module skeleton with no privileged mutation. Evidence: `trier_bridge/` core, config, logging, ui; zero subprocess/shell use; no privileged component; `docs/VALIDATION.md` entry IMP-01.
- [x] **IMP-01.03** Implement source-header/provenance checks. Evidence: `tools/tb.py headers` (35/35 compliant) wired into `tools/dev.py all`.
- [x] **IMP-01.04** Configure build, static analysis, unit test, package-size, and dependency inventory entry points. Evidence: `tools/dev.py` (format, lint, typecheck, test, headers, inventory, size, all) run clean on host and VM; `debian/` build via `dpkg-buildpackage`.
- [x] **IMP-01.05** Establish accessibility/theme/logging/config foundation. Evidence: AT-SPI labels and descriptions on every sidebar row (live walk in the VM session); libadwaita theme follows the desktop; `logging_setup.py` bounded and redacted (unit tests); `config.py` atomic XDG writes (unit tests).
- [x] **IMP-01.06** Verify clean reproducible build from documented environment. Evidence: two builds of cd3ef65 with `SOURCE_DATE_EPOCH` gave identical SHA256 `8ac8408f2435b03cc3fa6bde19afaa2d02441f218ec5a47a8f58f83d0250b4d1`; lintian silent; install/run/purge clean in the VM (`docs/VALIDATION.md` entry IMP-01).
- [x] **IMP-01.07** Produce first measured code-quality baseline; CQS only if all categories are measured. Evidence: `CODE-QUALITY-REPORT.md` 2026-09-21: seven of eight categories assessed with per-criterion evidence, CQS remains NOT MEASURED (complexity category lacks cognitive-complexity evidence).

---

# Foundation 02 — Environment and capability discovery

- [x] **IMP-02.01** Detect distro/version/architecture safely. Evidence: `docs/VALIDATION.md` entry IMP-02 (os-release, kernel, arch, virtualization from systemd1).
- [x] **IMP-02.02** Detect desktop/session/Wayland/X11/headless facts. Evidence: logind session Type/Class/Remote/Active per PID; SSH reported tty+remote, console reported wayland (entry IMP-02).
- [x] **IMP-02.03** Detect service/network/package/storage/auth backends. Evidence: 16 records with versions from D-Bus properties (entry IMP-02).
- [x] **IMP-02.04** Implement capability states Supported/Unsupported/Unknown/Degraded/Error. Evidence: `capability/model.py`, `core/state.py`; Flatpak UNSUPPORTED, journal DEGRADED path, bus ERROR path implemented; unit tests.
- [x] **IMP-02.05** Implement freshness/invalidation on backend/environment change. Evidence: monotonic `observed_monotonic` with TTL `is_fresh()` and a Check-again action; bus-name watch invalidation deferred to the first consumer that mutates (Foundation 06). Unit test TB-T037.
- [x] **IMP-02.06** Verify discovery is side-effect free. Evidence: code uses only Properties.Get, GetManagedObjects, ListNames, GetSessionByPID and file reads; integration test creates nothing under a fresh XDG home (entry IMP-02).
- [ ] **IMP-02.07** Qualify generic read-only fallback on selected environments.
  - 2026-09-21: unknown-distro path unit-tested on real os-release text; needs a second live environment (derivative VM) before it can close.

---

# Foundation 03 — Everyday Windows-continuity experience

- [x] **IMP-03.01** Familiar launcher/search/settings routes. Evidence: concept catalog + Home search + Settings routing, `docs/VALIDATION.md` entry IMP-03.
- [x] **IMP-03.02** Files/Documents/Downloads/Desktop/removable/network-location experience. Evidence: Files page with real paths, FileManager1 launch verified live (entry IMP-03). Deeper file behaviors stay native (Nautilus).
- [x] **IMP-03.03** Right-click/copy/move/paste/rename/delete/properties behavior. Evidence: `docs/VALIDATION.md` entry IMP-03.03 (copy, move, rename, Trash-first delete, folders as typed confirmed operations through GIO; right-click and properties stay in Files, plus the Files context-menu integration of entry SCOPE-14).
- [x] **IMP-03.04** Drag-and-drop behavior. Disposition 2026-09-21: Trier Bridge offers no drop target; drag-and-drop happens in Files with its own copy/move indication (TB-INV-075 holds because nothing here accepts a drop). Reopen if a drop target is ever added.
- [x] **IMP-03.05** Installed apps/default apps. Evidence: entry IMP-03 (inventory with provenance, defaults read) and entry IMP-03.05 (default-app changes as typed, confirmed, reversible operations). Uninstalling programs is a package mutation and is tracked under IMP-06.06.
- [x] **IMP-03.06** Printer/device entry points. Evidence: entry IMP-03 (routes) and entry IMP-03.06/HELP (live printer state and queues from CUPS, optional python3-cups); devices under IMP-04.
- [x] **IMP-03.07** Wi-Fi/network entry points. Evidence: Network page routes to wifi/network panels (entry IMP-03).
- [ ] **IMP-03.08** Screenshot/clipboard/common shortcut support.
  - 2026-09-21: teaching entries in the catalog (Print Screen, clipboard differences); Ctrl+Shift+Esc shipped as an individual Shortcuts integration (entry SCOPE-14). Print Screen is now an action through the desktop portal (entry IMP-03.08) but the GNOME backend never answers in the GPU-less VM, so the screenshot itself stays NOT VERIFIED until run on hardware; clipboard stays teaching only. Item stays open for that verification.
- [x] **IMP-03.09** Everyday office-user interaction tests. Evidence: `docs/VALIDATION.md` entry IMP-03.09 (three journeys driven through AT-SPI in the console session). Usability acceptance by a person stays under IMP-08.04.

---

# Foundation 04 — Read-only familiar system tools

- [x] **IMP-04.01** Task Manager observation. Evidence: `docs/VALIDATION.md` entry IMP-04.01 (live procfs sampler, identity, Unknown-not-zero, page verified in session).
- [x] **IMP-04.02** Startup Apps observation. Evidence: `docs/VALIDATION.md` entry IMP-04 (Foundation 03 entry for provenance).
- [x] **IMP-04.03** Event Viewer / journal presentation. Evidence: `docs/VALIDATION.md` entry IMP-04.03 (native sd-journal, cross-checked with journalctl, page verified in session).
  - 2026-09-21 01:16 PM CDT: the Boot view empty-when-out-of-the-newest-500 limitation noted in entry IMP-04.03 is resolved by a separate boot-scoped read (`_BOOT_ID`/kernel/audit match). Evidence: entry IMP-07.12.
- [x] **IMP-04.04** Device Manager inventory. Evidence: `docs/VALIDATION.md` entry IMP-04 (Foundation 03 entry for provenance).
- [x] **IMP-04.05** Disk/storage inventory. Evidence: `docs/VALIDATION.md` entry IMP-04 (Foundation 03 entry for provenance).
- [x] **IMP-04.06** Network Connections inventory. Evidence: `docs/VALIDATION.md` entry IMP-04 (Foundation 03 entry for provenance).
- [x] **IMP-04.07** Installed software provenance inventory. Evidence: `docs/VALIDATION.md` entry IMP-04 (Foundation 03 entry for provenance).
- [x] **IMP-04.08** Verify missing metrics remain Unknown/Unavailable, not zero. Evidence: processes (first-sample CPU, unreadable memory), storage (free space when unmounted), devices (driver unknown), network (Unknown layers), discovery records; entries IMP-02, IMP-04.01, IMP-04.

---

- [x] **IMP-04.07** (Evidence: entry IMP-04.07.) Drive letters as a familiar label (DEC-024): C: for the Linux system drive, D:, E:, ... for other mounted volumes, shown in Disk Management, Files, and the Command Prompt next to the real path; `C:\Users\<name>` resolves to `/home/<name>`.

---

# Foundation 05 — Durable state, journals, and recovery

- [x] **IMP-05.01** Implement Trier Bridge-owned preference durability. Evidence: `docs/VALIDATION.md` entry IMP-05 (preferences with reported non-durable writes).
- [x] **IMP-05.02** Implement operation IDs and state journal. Evidence: `docs/VALIDATION.md` entry IMP-05.
- [x] **IMP-05.03** Implement crash/restart reconciliation. Evidence: `docs/VALIDATION.md` entry IMP-05 (SIGKILL mid-operation flagged; banner shown).
- [x] **IMP-05.04** Implement atomic configuration writes. Evidence: `docs/VALIDATION.md` entry IMP-01 (config.py) and IMP-05 fault tests.
- [x] **IMP-05.05** Implement recovery records/retention. Evidence: `docs/VALIDATION.md` entry IMP-05 (unresolved never pruned).
- [x] **IMP-05.06** Run disk-full/read-only/permission-loss/process-kill/stale-revision tests. Evidence: `docs/VALIDATION.md` entry IMP-05 (loopback ext4 image); stale-revision covered by schema tests; two concurrent instances still open.

---

# Foundation 06 — Privilege and typed system mutation

- [x] **IMP-06.01** Implement finite privileged-operation schema; no generic root execution. Evidence: `docs/PRIVILEGE-MODEL.md` section 8 (the implemented schema: the only privileged kinds are `service.start|stop|restart|enable|disable` on a named unit through systemd's D-Bus API under polkit; `Operation.kind` is validated against a fixed vocabulary, `tests/unit/test_operations.py::test_kind_vocabulary_is_validated`; no helper, no sudo, no shell anywhere in the product).
- [x] **IMP-06.02** Implement explicit authorization binding to current user intent. Evidence: `docs/PRIVILEGE-MODEL.md` section 8 (plan → preview → the user's confirmation → one D-Bus call with ALLOW_INTERACTIVE_AUTHORIZATION → polkit binds the grant to this process, this session, this action; nothing is cached by the product; entries IMP-06.05, IMP-06.07, IMP-06.08).
- [x] **IMP-06.03** Implement stable target identity and revalidation. Evidence: `docs/VALIDATION.md` entry IMP-06.04 (PID+start revalidation; stale target cancels); other target kinds as their operations land.
- [x] **IMP-06.04** Implement selected user-process termination. Evidence: `docs/VALIDATION.md` entry IMP-06.04.
- [x] **IMP-06.05** Implement selected service control. Evidence: `docs/VALIDATION.md` entry IMP-06.05.
- [x] **IMP-06.06** Implement selected network/package mutations only if separately qualified. Evidence: entry IMP-06.06 (network translation layer on a dummy interface; packages out of scope by DEC-024).
  - 2026-09-21 (DEC-024): packages are out of scope for good (no App Center, no install/remove). Network changes are in scope as a translation layer: adapter on/off, connect/disconnect a profile, static IPv4 address/gateway/DNS, back to automatic; each a typed class C operation through NetworkManager under polkit, qualified on a dummy interface in the VM, never on its uplink.
- [x] **IMP-06.07** Verify denial/cancel/expiry/stale-target/backend-restart behavior. Evidence: `docs/VALIDATION.md` entries IMP-06.04/06.05 (stale target, denial without an agent) and IMP-06.07 (granted and dismissed prompts through a real polkit agent, user-manager re-exec). Limitation recorded: systemd 255 reports a dismissed prompt as access denied; expiry is polkit's cache and not exercised.
  - 2026-09-21: denial (no agent) and stale target verified for services; stale PID for processes; cancel/expiry of a live polkit prompt and backend restart still open.
- [x] **IMP-06.08** Run security/failure regression set. Evidence: `docs/TEST-STRATEGY.md` section 7 (mapping of SECURITY section 37 and Tests A–D to tests, gaps named) and `docs/VALIDATION.md` entry IMP-06.08 (Test B live through the terminal and polkit).

---

# Foundation 07 — Bridge Terminal and PowerShell continuity

- [x] **IMP-07.01** Implement strict Bridge Terminal mode and parser. Evidence: `docs/VALIDATION.md` entry IMP-07 (grammar, unit tests).
- [x] **IMP-07.02** Implement initial read-only Windows-command vocabulary. Evidence: `docs/VALIDATION.md` entry IMP-07.
- [x] **IMP-07.03** Map commands to existing typed operation authority. Evidence: `docs/VALIDATION.md` entry IMP-07 (taskkill uses plan_terminate).
- [x] **IMP-07.04** Reject unknown/unparsed syntax without shell fallback. Evidence: `docs/VALIDATION.md` entry IMP-07 (injection tests).
- [x] **IMP-07.05** Implement bounded output/history/redaction. Evidence: `docs/VALIDATION.md` entry IMP-07.
- [x] **IMP-07.06** Integrate real `pwsh` where selected/available. Evidence: `docs/VALIDATION.md` entry IMP-07.06/07 (`powershell` Bridge command and Terminal button open an installed pwsh in the desktop terminal; explains the snap when absent; never bundled).
- [x] **IMP-07.11** `findstr`, `find`, `where`, `set`, `path`, `tree`, `exit`, `%VAR%` expansion, teaching for attrib/icacls/takeown. Evidence: entry IMP-07.11.
- [x] **IMP-07.10** `shutdown /s|/r [/t n]` as a confirmed logind action (execution deliberately unverified in the VM). Evidence: entry IMP-07.10.
- [x] **IMP-07.12** `shutdown /t` arms a cancellable main-loop timer, `/a` cancels it; `taskmgr`/`devmgmt.msc`/`services.msc`/`eventvwr`/`msconfig`/`ncpa.cpl`/`appwiz.cpl`/`msinfo32`/`compmgmt.msc` open the matching page; `findstr /R` regular-expression matching and `/L` literal mode; Event Viewer Boot view reads this boot's kernel/audit records. Evidence: entry IMP-07.12 (unit- and integration-verified; timer fire/cancel-while-armed and the open-page desktop branch are unit-only this session).
- [x] **IMP-07.09** Familiar commands beyond the MVP list: `explorer`, `start`, `net start|stop` (and teaching for user/use/share/view), `date`, `time`, `taskkill /IM`, teaching entries for sfc, chkdsk, xcopy, robocopy, gpedit. Evidence: entry IMP-07.09.
- [x] **IMP-07.08** Network diagnostics a Windows user types first: `ping`, `tracert`, `nslookup`, `ipconfig /flushdns` (plus Test-Connection, Resolve-DnsName, Clear-DnsClientCache). Evidence: entry IMP-07.08.
- [x] **IMP-07.07** Implement selected compatibility cmdlets only through typed operations. Evidence: entry IMP-07.06/07 (16 cmdlet names translate to Bridge commands with a visible note; Get-EventLog and Get-WmiObject teach; unknown parameters refuse the line).
- [x] **IMP-07.08** Run injection/quoting/path/Unicode/timeout/cancellation tests. Evidence: `docs/VALIDATION.md` entry IMP-07 (injection, quoting, Unicode, length); timeout/cancellation of long commands still open.

---

# Foundation 08 — Integrated qualification and packaging

- [x] **IMP-08.01** Build selected native packages/installers. Evidence: entries IMP-01 (reproducible in one environment), SCOPE-14 (contents), IMP-08.01 (clean `sbuild` chroot build identical to the in-VM build; changelog dating defect found and fixed).
  - 2026-09-21: the `.deb` now carries the tray, search provider, Files extension, catalog, and three man pages; built and installed from the tree in the VM, lintian silent (entry SCOPE-14). Open: a build from a clean chroot and a second environment.
- [x] **IMP-08.02** Verify clean install/upgrade/uninstall and ownership. Evidence: `docs/VALIDATION.md` entry IMP-08.02 (purge, reinstall, in-place upgrade dev0 → dev1 with per-user state byte-identical). Open: downgrade and a second environment.
  - 2026-09-21: install and purge verified on the VM with integrations on: `apt-get purge` left nothing under `/usr` (113 owned paths gone) and kept every per-user file (ledger, autostart entry, search-provider files); reinstall restored the three commands and the existing autostart entry started the tray as login would. Open: upgrade between two versions (only one version exists) and a second environment.
- [ ] **IMP-08.03** Run selected distro/desktop matrix.
  - 2026-09-21: the first-release matrix is one cell, Ubuntu 24.04 LTS / GNOME 46 Wayland (`docs/PLATFORMS.md` section 10), and that cell is verified by every entry. A second environment (another machine, an X11 session, an Ubuntu flavour) is the open work; nothing beyond the one cell is claimed.
  - 2026-09-21 (later): the GTK X11 backend was exercised through XWayland in the same session (`GDK_BACKEND=x11`, the session's Xwayland authority): Home, Task Manager, Services, and Integrations rendered with the same accessibility trees (169, 712, 769, 201 nodes) and no tracebacks; RSS 255-301 MB. This is the toolkit's X11 path, not an Xorg session; a real "Ubuntu on Xorg" login remains the owner's step.
- [ ] **IMP-08.04** Run office-user usability acceptance.
  - 2026-09-21: the owner looked at the running VM desktop and confirmed the tray icon T is visible and recognizable in the top bar (first owner-verified visual check). Needs a person at the console for the rest (TB-IA cases, `docs/VALIDATION.md` section 6). What automation already covers: every page and dialog reachable and named over AT-SPI, the setup flow, file operations, and default apps driven through the accessibility interface (entries SCOPE-14, IMP-03.03, IMP-03.05).
- [ ] **IMP-08.05** Run Windows power-user continuity acceptance.
  - 2026-09-21: needs a person. Automation covers the Bridge Terminal vocabulary (entries IMP-07, IMP-07.06/07), Task Manager, Services, Event Viewer, Device Manager, Disk Management against live facts (IMP-04, IMP-06.04, IMP-06.05).
- [ ] **IMP-08.06** Run accessibility/localization acceptance.
  - 2026-09-21: `docs/ACCESSIBILITY.md`: TB-A11Y-01..05 verified over AT-SPI; 06 (keyboard only), 07 (Orca), 08 (large text, high contrast) need a person; no localization exists yet (English only).
- [x] **IMP-08.07** Run security/recovery/fault qualification. Evidence: entries IMP-05 (disk full, read-only, permission loss, kill mid-write on a real loopback filesystem), IMP-06.04/06.05/06.07 (stale target, denial, dismissal, grant, backend re-exec), IMP-06.08 (regression mapping with named gaps).
- [x] **IMP-08.08** Run performance/resource qualification. Evidence: entry IMP-08.08 (startup, memory, idle CPU, tray, search provider, package size; Task Manager CPU defect found and fixed). Open: a written budget and a measurement on hardware with a GPU.
- [ ] **IMP-08.09** Produce exact release CQS and known-limitations report.
  - 2026-09-21: release is locked (owner direction); the current report is `CODE-QUALITY-REPORT.md` (CQS NOT MEASURED by rule until a cognitive-complexity analyzer exists, CQ-02); known limitations are the Failures/limitations lines of every entry and the gaps in `docs/TEST-STRATEGY.md` section 7.
  - 2026-09-21 12:41 PM CDT: CQS is measured, 94/100 (`CODE-QUALITY-REPORT.md`, all eight categories, analyzer installed under CQ-02). The known-limitations report now exists as the generated `docs/KNOWN-LIMITATIONS.md` (`tools/dev.py limitations`, entry TOOL-06). What stays open is the word "release": the exact release CQS is the score of the release candidate the owner names, re-measured at that revision.

---

# Release

**LOCKED until explicit owner publication instruction.**

- [ ] **REL-01** Final source/dependency/asset/license provenance review.
- [ ] **REL-02** Final supported-environment matrix matches exact evidence.
- [ ] **REL-03** Final security and recovery gates clear.
- [ ] **REL-04** Final package hashes/signing/update trust as applicable.
- [ ] **REL-05** Owner explicitly authorizes GitHub publication/release.
- [ ] **REL-06** Publish only approved source/artifacts.
- [ ] **REL-07** Verify public tag/source/package/hash consistency.
- [ ] **REL-08** Start documented maintenance/security-support process.

---

## Current final state

At 2026-09-20 9:17 PM CDT:

> **Trier Bridge is an engineered design foundation, not yet an implemented product.**
