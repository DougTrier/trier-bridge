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
| **Active task** | ROOT-01 — Root project-control document alignment |
| **Last completed** | Read-only engineering tools created and verified on Windows; `tb all` exit 0 (2026-09-20 09:55 PM CDT) |
| **Implementation** | NOT STARTED |
| **Invariant baseline** | 233 design invariants; runtime evidence NOT RUN |
| **Security** | Design baseline exists; implementation evidence NOT RUN |
| **CQS** | NOT MEASURED |
| **Platform support** | No distro/desktop combination qualified |
| **Release** | Locked; local Git only, no remote, no GitHub (owner direction 2026-09-20) |
| **Next bounded step** | Owner review (ALN-12) → SCOPE-01..05 design documents → implementation-stack selection → Foundation 01 freeze |

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

---

# Engineering tooling (read-only) and test environments

Tools are engineering automation (`docs/ENGINEERING.md` section 10), not product implementation. Evidence is the recorded tool run.

- [x] **TOOL-01** Create read-only tool entry points (`tools/tb.cmd`, `tools/tb.ps1`, `tools/tb.py`) with config and Apache headers. Evidence: all three wrappers ran 2026-09-20 09:55 PM CDT; `tb headers` 13/13 compliant.
- [x] **TOOL-02** Snapshot / changes / status / context digest. Evidence: `tb context` run 2026-09-20 09:55 PM CDT.
- [x] **TOOL-03** Ledger parser and outline/section/invariant navigation. Evidence: `tb ledger ALN-13`, `tb outline`, `tb section`, `tb inv show/find` run 2026-09-20 09:55 PM CDT.
- [x] **TOOL-04** Link, invariant cross-reference, term-rule, and header checks under `tb all`. Evidence: exit 0 on 2026-09-20 09:55 PM CDT (233 INV, 30 SEC, 30 IA indexed; 33 links; 12 term rules).
- [ ] **TOOL-05** Verify the tools run unmodified on Linux (disposable WSL2 Ubuntu 24.04, `python3`). Blocked on ENV-01.
- [ ] **TOOL-06** Stack-dependent tools: lint/static-analysis orchestration, test-result normalization, dependency inventory, CQS evidence collection. Blocked until ARC-01 and IMP-01.01.
- [ ] **ENV-01** Owner creates disposable WSL2 Ubuntu 24.04 instance `tb-ubuntu-2404`, separate from `Ubuntu-24.04-Recovered`; record `tb-env` host profile and the WSL environment profile.
- [ ] **ENV-02** Create the disposable Hyper-V Ubuntu Desktop VM `tb-ubuntu-desktop-2404` (`tb-` prefix, Default Switch, storage on G:, isolated from the work-production VM) for desktop and backend qualification.
  - 2026-09-20 10:25 PM CDT: owner approved. `tools/env/New-TbDesktopVm.ps1`, `Remove-TbDesktopVm.ps1`, and autoinstall seed written and parse-checked; Ubuntu 24.04.5.1 Desktop ISO download to `G:\tb-vms\iso` started with SHA256 verification. Remaining: owner runs the create script from an elevated PowerShell, answers the single installer confirmation, then records the in-guest environment profile.
- [ ] **ENV-03** Removal procedure for both environments verified (`wsl --unregister tb-ubuntu-2404`; delete VM) with confirmation that nothing else on the host changed.

---

# Pre-implementation scoping

Gap review 2026-09-20. Each item produces a design document or a data schema under `docs/` and is complete only when that artifact exists and cites its invariants. SCOPE-01 through SCOPE-05 block ARC-01/ARC-02.

- [ ] **SCOPE-01** Delivery model and desktop-integration boundary: what Trier Bridge is on the desktop and how it augments rather than replaces the native file manager, launcher, and settings. Direction recorded as DEC-018 (accepted) and DEC-019 (proposed); document still required.
- [ ] **SCOPE-02** Privilege helper architecture: polkit-registered on-demand system service, D-Bus interface, schema versioning, lifecycle (exits when idle; bounded to the authorized operation per TB-INV-188), packaging, and how it stays visibly non-invasive under DEC-018.
- [ ] **SCOPE-03** Packaging constraints and candidates: native package first; state why sandboxed formats are excluded for the core; install/uninstall behavior against TB-INV-025 to TB-INV-029.
- [ ] **SCOPE-04** Research plan with exit criteria per open track (Wayland portals for screenshots/global shortcuts, file-manager extension APIs on GNOME/KDE/Cinnamon/XFCE, NetworkManager and udisks2 D-Bus surfaces, PackageKit versus native apt, polkit action design). Each track yields a written finding ARC-01 can cite.
- [ ] **SCOPE-05** Test strategy: disposable VM/WSL environments are the default oracle; synthetic fixtures are prohibited unless the owner explicitly approves a named fixture for a named scenario; maps TB-T### to environments.
- [ ] **SCOPE-06** Typed operation model: schema (ID, stable target identity, preview, authorization state, result taxonomy) and the rule that turns each result into "did anything change / what stopped it / safest next step".
- [ ] **SCOPE-07** Windows-to-Linux concept catalog: data schema for every Windows-labeled concept with route, backend, and equivalence class (exact / approximate / none) per TB-INV-065; drives search, help, Show Me the Linux Way, and Bridge commands.
- [ ] **SCOPE-08** Bridge Terminal grammar and MVP command list with class A to E, flags, and typed operation per command.
- [ ] **SCOPE-09** Accessibility acceptance criteria as a stack-selection gate (AT-SPI on Wayland across candidate frameworks, keyboard-only, screen reader, large text).
- [ ] **SCOPE-10** Backend runtime topology: session service versus in-process core, UI-to-backend IPC, relationship to the privileged service.
- [ ] **SCOPE-11** Local pre-commit gate convention (`tools\tb all` before every commit; optional local git hook), since there is no CI.
- [ ] **SCOPE-12** Name and trademark check on "Trier Bridge" before any public step.
- [ ] **SCOPE-13** Observability specification: log location, levels, redaction, audit placement (SECURITY.md section 26 fields).

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

- [ ] **ARC-01** Select implementation language/runtime with documented alternatives and rationale.
- [ ] **ARC-02** Select desktop/UI framework with Wayland/X11/accessibility/package implications.
- [ ] **ARC-03** Freeze module/dependency direction.
- [ ] **ARC-04** Freeze typed operation model.
- [ ] **ARC-05** Freeze capability-discovery contract.
- [ ] **ARC-06** Freeze platform-adapter interfaces.
- [ ] **ARC-07** Freeze persistence engine and schema ownership.
- [ ] **ARC-08** Freeze privilege helper / authorization model.
- [ ] **ARC-09** Select first-release distro families.
- [ ] **ARC-10** Select first-release desktop/session matrix.
- [ ] **ARC-11** Select package formats.
- [ ] **ARC-12** Freeze update mechanism or explicitly defer updates.
- [ ] **ARC-13** Map every selected MVP feature to applicable `TB-INV-###`.
- [ ] **ARC-14** Freeze planned test/failure matrix.

---

# Foundation 01 — Toolchain and unprivileged shell

**Prerequisites:** ARC-01–ARC-03 and relevant quality/licensing decisions.

- [ ] **IMP-01.01** Pin compiler/runtime/framework/build/package tool versions.
- [ ] **IMP-01.02** Create clean module skeleton with no privileged mutation.
- [ ] **IMP-01.03** Implement source-header/provenance checks.
- [ ] **IMP-01.04** Configure build, static analysis, unit test, package-size, and dependency inventory entry points.
- [ ] **IMP-01.05** Establish accessibility/theme/logging/config foundation.
- [ ] **IMP-01.06** Verify clean reproducible build from documented environment.
- [ ] **IMP-01.07** Produce first measured code-quality baseline; CQS only if all categories are measured.

---

# Foundation 02 — Environment and capability discovery

- [ ] **IMP-02.01** Detect distro/version/architecture safely.
- [ ] **IMP-02.02** Detect desktop/session/Wayland/X11/headless facts.
- [ ] **IMP-02.03** Detect service/network/package/storage/auth backends.
- [ ] **IMP-02.04** Implement capability states Supported/Unsupported/Unknown/Degraded/Error.
- [ ] **IMP-02.05** Implement freshness/invalidation on backend/environment change.
- [ ] **IMP-02.06** Verify discovery is side-effect free.
- [ ] **IMP-02.07** Qualify generic read-only fallback on selected environments.

---

# Foundation 03 — Everyday Windows-continuity experience

- [ ] **IMP-03.01** Familiar launcher/search/settings routes.
- [ ] **IMP-03.02** Files/Documents/Downloads/Desktop/removable/network-location experience.
- [ ] **IMP-03.03** Right-click/copy/move/paste/rename/delete/properties behavior.
- [ ] **IMP-03.04** Drag-and-drop behavior.
- [ ] **IMP-03.05** Installed apps/default apps.
- [ ] **IMP-03.06** Printer/device entry points.
- [ ] **IMP-03.07** Wi-Fi/network entry points.
- [ ] **IMP-03.08** Screenshot/clipboard/common shortcut support.
- [ ] **IMP-03.09** Everyday office-user interaction tests.

---

# Foundation 04 — Read-only familiar system tools

- [ ] **IMP-04.01** Task Manager observation.
- [ ] **IMP-04.02** Startup Apps observation.
- [ ] **IMP-04.03** Event Viewer / journal presentation.
- [ ] **IMP-04.04** Device Manager inventory.
- [ ] **IMP-04.05** Disk/storage inventory.
- [ ] **IMP-04.06** Network Connections inventory.
- [ ] **IMP-04.07** Installed software provenance inventory.
- [ ] **IMP-04.08** Verify missing metrics remain Unknown/Unavailable, not zero.

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
