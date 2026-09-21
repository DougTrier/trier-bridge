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
| **Active task** | IMP-05 — Foundation 05: durable state, operation journal, restart reconciliation |
| **Last completed** | Foundation 04 read-only tools verified live; 22 integration tests (2026-09-21 02:55 AM CDT) |
| **Implementation** | Foundations 01, 02, 04 complete; 03 read-only slice complete (2026-09-21); Foundation 05 starting |
| **Invariant baseline** | 233 design invariants; runtime evidence NOT RUN |
| **Security** | Design baseline exists; implementation evidence NOT RUN |
| **CQS** | NOT MEASURED (7 of 8 categories assessed, see CODE-QUALITY-REPORT.md) |
| **Platform support** | No product feature qualified; test environment Ubuntu 24.04.5 / Wayland GNOME 46 / Hyper-V profiled (ENV-02) |
| **Release** | Locked; local Git only, no remote, no GitHub (owner direction 2026-09-20) |
| **Next bounded step** | IMP-05.01 preferences durability → IMP-05.02 operation journal → IMP-05.03 restart reconciliation → IMP-05.06 fault tests in the VM |

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
- [ ] **TOOL-06** Stack-dependent tools: lint/static-analysis orchestration, test-result normalization, dependency inventory, CQS evidence collection. Blocked until ARC-01 and IMP-01.01.
- [ ] **ENV-01** CANCELLED 2026-09-20: WSL instance scratched by owner (DEC-017 rejected). All Linux testing uses the Hyper-V VM under ENV-02.
- [x] **ENV-02** Create the Hyper-V Ubuntu Desktop VM `tb-ubuntu-desktop-2404` (`tb-` prefix, Default Switch, storage on G:, isolated from the work-production VM) for desktop and backend qualification. Evidence: created by owner via `New-TbDesktopVm.ps1` 2026-09-20 10:39 PM CDT (ISO VERIFIED); in-guest profile recorded 11:10 PM CDT in `docs/VALIDATION.md` entry ENV-02 (Ubuntu 24.04.5, Wayland GNOME 46, systemd 255, NM 1.46, udisks 2.10, polkit 124).
  - 2026-09-20 10:25 PM CDT: owner approved. `tools/env/New-TbDesktopVm.ps1`, `Remove-TbDesktopVm.ps1`, and autoinstall seed written and parse-checked; Ubuntu 24.04.5.1 Desktop ISO download to `G:\tb-vms\iso` started with SHA256 verification. Remaining: owner runs the create script from an elevated PowerShell, answers the single installer confirmation, then records the in-guest environment profile.
- [ ] **ENV-03** Baseline `clean-install` checkpoint taken after first login and restore verified; removal procedure (`tools/env/Remove-TbDesktopVm.ps1`) kept available but the owner intends to keep the VM for other uses (2026-09-20).
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
- [ ] **SCOPE-06** Typed operation model: schema (ID, stable target identity, preview, authorization state, result taxonomy) and the rule that turns each result into "did anything change / what stopped it / safest next step".
- [ ] **SCOPE-07** Windows-to-Linux concept catalog: data schema for every Windows-labeled concept with route, backend, and equivalence class (exact / approximate / none) per TB-INV-065; drives search, help, Show Me the Linux Way, and Bridge commands.
- [ ] **SCOPE-08** Bridge Terminal grammar and MVP command list with class A to E, flags, and typed operation per command.
- [ ] **SCOPE-09** Accessibility acceptance criteria as a stack-selection gate (AT-SPI on Wayland across candidate frameworks, keyboard-only, screen reader, large text).
  - 2026-09-21: gate evidence for the proposed framework recorded (F17: GTK4/libadwaita exposes names, descriptions, and switch labels on Wayland). Full criteria document still to write.
- [ ] **SCOPE-10** Backend runtime topology: session service versus in-process core, UI-to-backend IPC, relationship to the privileged service.
- [ ] **SCOPE-11** Local pre-commit gate convention (`tools\tb all` before every commit; optional local git hook), since there is no CI.
- [ ] **SCOPE-12** Name and trademark check on "Trier Bridge" before any public step.
- [ ] **SCOPE-13** Observability specification: log location, levels, redaction, audit placement (SECURITY.md section 26 fields).
- [ ] **SCOPE-14** Integration catalog and setup flow: the list of every shippable integration, its named group (feature subset), its desktop extension point, its activation/reversal mechanism, and the first-run setup screen plus tray-icon options flow that presents them (DEC-019). Includes the Ubuntu GNOME tray/AppIndicator research item.

---

# Product and UX freeze

- [ ] **DOC-01** Freeze MVP user journeys for typical office/home users.
- [ ] **DOC-02** Freeze familiar file/navigation behavior and desktop integration boundary.
- [ ] **DOC-03** Freeze app-launch/search/settings/default-app routing.
- [ ] **DOC-04** Freeze printers/scanners/USB/network-share everyday journeys.
- [ ] **DOC-05** Freeze Task Manager/Startup/Network/Device/Disk/Event Viewer familiar-tool scope.
- [ ] **DOC-06** Freeze Services/Bridge Terminal/PowerShell advanced scope.
- [ ] **DOC-07** Freeze Familiar/Bridge/native-detail progressive disclosure.
- [ ] **DOC-08** Complete loading/empty/unknown/unsupported/denied/error/partial/recovery designs.
- [ ] **DOC-09** Review accessibility, large text, keyboard-only, screen-reader, and localization behavior.

---

# Platform and architecture freeze

- [x] **ARC-01** Select implementation language/runtime with documented alternatives and rationale. Evidence: `docs/STACK-SELECTION.md`; DEC-020 accepted under owner delegation 2026-09-21.
- [x] **ARC-02** Select desktop/UI framework with Wayland/X11/accessibility/package implications. Evidence: GTK 4 + libadwaita, AT-SPI on Wayland verified (F17); DEC-020.
- [ ] **ARC-03** Freeze module/dependency direction.
- [ ] **ARC-04** Freeze typed operation model.
- [ ] **ARC-05** Freeze capability-discovery contract.
- [ ] **ARC-06** Freeze platform-adapter interfaces.
- [ ] **ARC-07** Freeze persistence engine and schema ownership.
- [ ] **ARC-08** Freeze privilege helper / authorization model.
- [ ] **ARC-09** Select first-release distro families.
- [ ] **ARC-10** Select first-release desktop/session matrix.
- [ ] **ARC-11** Select package formats.
- [x] **ARC-12** Freeze update mechanism or explicitly defer updates. Evidence: deferred, DEC-022 (2026-09-21), `docs/PACKAGING.md` section 5.
- [ ] **ARC-13** Map every selected MVP feature to applicable `TB-INV-###`.
- [ ] **ARC-14** Freeze planned test/failure matrix.

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
- [ ] **IMP-03.03** Right-click/copy/move/paste/rename/delete/properties behavior.
- [ ] **IMP-03.04** Drag-and-drop behavior.
- [ ] **IMP-03.05** Installed apps/default apps.
  - 2026-09-21: read-only half done (inventory with provenance, defaults read; entry IMP-03). Uninstall and default changes are mutations and wait for Foundation 06.
- [x] **IMP-03.06** Printer/device entry points. Evidence: Printers page routes to the GNOME Settings printers panel; Bluetooth/devices via catalog (entry IMP-03). Live status is Foundation 04.
- [x] **IMP-03.07** Wi-Fi/network entry points. Evidence: Network page routes to wifi/network panels (entry IMP-03).
- [ ] **IMP-03.08** Screenshot/clipboard/common shortcut support.
  - 2026-09-21: teaching entries in the catalog (Print Screen, clipboard differences); keyboard shortcut integration waits for the setup screen (SCOPE-14).
- [ ] **IMP-03.09** Everyday office-user interaction tests.

---

# Foundation 04 — Read-only familiar system tools

- [x] **IMP-04.01** Task Manager observation. Evidence: `docs/VALIDATION.md` entry IMP-04.01 (live procfs sampler, identity, Unknown-not-zero, page verified in session).
- [x] **IMP-04.02** Startup Apps observation. Evidence: `docs/VALIDATION.md` entry IMP-04 (Foundation 03 entry for provenance).
- [x] **IMP-04.03** Event Viewer / journal presentation. Evidence: `docs/VALIDATION.md` entry IMP-04.03 (native sd-journal, cross-checked with journalctl, page verified in session).
- [x] **IMP-04.04** Device Manager inventory. Evidence: `docs/VALIDATION.md` entry IMP-04 (Foundation 03 entry for provenance).
- [x] **IMP-04.05** Disk/storage inventory. Evidence: `docs/VALIDATION.md` entry IMP-04 (Foundation 03 entry for provenance).
- [x] **IMP-04.06** Network Connections inventory. Evidence: `docs/VALIDATION.md` entry IMP-04 (Foundation 03 entry for provenance).
- [x] **IMP-04.07** Installed software provenance inventory. Evidence: `docs/VALIDATION.md` entry IMP-04 (Foundation 03 entry for provenance).
- [x] **IMP-04.08** Verify missing metrics remain Unknown/Unavailable, not zero. Evidence: processes (first-sample CPU, unreadable memory), storage (free space when unmounted), devices (driver unknown), network (Unknown layers), discovery records; entries IMP-02, IMP-04.01, IMP-04.

---

# Foundation 05 — Durable state, journals, and recovery

- [ ] **IMP-05.01** Implement Trier Bridge-owned preference durability.
- [ ] **IMP-05.02** Implement operation IDs and state journal.
- [ ] **IMP-05.03** Implement crash/restart reconciliation.
- [ ] **IMP-05.04** Implement atomic configuration writes.
- [ ] **IMP-05.05** Implement recovery records/retention.
- [ ] **IMP-05.06** Run disk-full/read-only/permission-loss/process-kill/stale-revision tests.

---

# Foundation 06 — Privilege and typed system mutation

- [ ] **IMP-06.01** Implement finite privileged-operation schema; no generic root execution.
- [ ] **IMP-06.02** Implement explicit authorization binding to current user intent.
- [ ] **IMP-06.03** Implement stable target identity and revalidation.
- [ ] **IMP-06.04** Implement selected user-process termination.
- [ ] **IMP-06.05** Implement selected service control.
- [ ] **IMP-06.06** Implement selected network/package mutations only if separately qualified.
- [ ] **IMP-06.07** Verify denial/cancel/expiry/stale-target/backend-restart behavior.
- [ ] **IMP-06.08** Run security/failure regression set.

---

# Foundation 07 — Bridge Terminal and PowerShell continuity

- [ ] **IMP-07.01** Implement strict Bridge Terminal mode and parser.
- [ ] **IMP-07.02** Implement initial read-only Windows-command vocabulary.
- [ ] **IMP-07.03** Map commands to existing typed operation authority.
- [ ] **IMP-07.04** Reject unknown/unparsed syntax without shell fallback.
- [ ] **IMP-07.05** Implement bounded output/history/redaction.
- [ ] **IMP-07.06** Integrate real `pwsh` where selected/available.
- [ ] **IMP-07.07** Implement selected compatibility cmdlets only through typed operations.
- [ ] **IMP-07.08** Run injection/quoting/path/Unicode/timeout/cancellation tests.

---

# Foundation 08 — Integrated qualification and packaging

- [ ] **IMP-08.01** Build selected native packages/installers.
- [ ] **IMP-08.02** Verify clean install/upgrade/uninstall and ownership.
- [ ] **IMP-08.03** Run selected distro/desktop matrix.
- [ ] **IMP-08.04** Run office-user usability acceptance.
- [ ] **IMP-08.05** Run Windows power-user continuity acceptance.
- [ ] **IMP-08.06** Run accessibility/localization acceptance.
- [ ] **IMP-08.07** Run security/recovery/fault qualification.
- [ ] **IMP-08.08** Run performance/resource qualification.
- [ ] **IMP-08.09** Produce exact release CQS and known-limitations report.

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
