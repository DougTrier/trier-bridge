# Trier Bridge Context

**Last updated:** 2026-09-21 12:05 AM CDT  
**Owner:** Doug Trier  
**Project state:** FOUNDATIONS 06/07 SLICES DONE; SETUP/INTEGRATIONS NEXT  
**Implementation:** AUTHORIZED 2026-09-21 (DEC-023)  
**CQS:** NOT MEASURED  

---

## Current objective

Establish a complete, internally consistent engineering foundation for Trier Bridge before production implementation begins.

Trier Bridge targets **typical Windows office/home users through advanced Windows users**.

The primary product requirement is:

> **Everything a Windows user already knows how to do should have a familiar place to go on Linux.**

Everyday productivity comes first.

Administration and command translation are deeper layers.

---

## Current checkpoint

### Completed design foundation

- corrected product concept and target audience
- Product North Star
- engineering architecture baseline
- security architecture
- 233 numbered invariants
- Apache-2.0 licensing model
- NOTICE/provenance model
- contributor policy
- code-quality/CQS model
- platform/capability design
- persistence/recovery design
- interaction and screen inventories
- qualification/evidence model
- roadmap and implementation sequencing
- eight implementation baseline documents
- document pack consolidated from 75 root files to 26 (root control files plus `docs/`); links and authority order reconciled
- read-only engineering tools created under `tools/` and verified on Windows (`tb all` exit 0, 2026-09-20 09:55 PM CDT)
- owner decisions 2026-09-20: DEC-016 accepted (Ubuntu 24.04 LTS first, derivatives next with their own evidence); DEC-017 rejected (no WSL; Hyper-V VM only); DEC-019 accepted (one integrated build, integrations are part of the product)
- Hyper-V desktop VM scripts and autoinstall seed written under `tools/env/`; ISO download started (2026-09-20 10:25 PM CDT); VM creation is an owner-run elevated step
- local Git repository initialized on `main` with no remote (2026-09-20)
- test VM `tb-ubuntu-desktop-2404` created by owner and profiled in-guest; tools verified on Linux (ENV-02, TOOL-05, 2026-09-20 11:10 PM CDT)
- SCOPE-01..05 written from an in-guest research probe: delivery model, privilege model (no helper needed), packaging, research plan with findings, test strategy (2026-09-20 11:55 PM CDT)
- live research R2/R17/R18 done in the VM session; stack proposal `docs/STACK-SELECTION.md` written as DEC-020 (proposed) (2026-09-21 12:05 AM CDT)
- R1 Nautilus extension load and R12 PowerShell-on-Linux verified after the owner enabled sudo in the VM (2026-09-21 12:20 AM CDT)
- Services control (user scope verified, system denial verified) and Bridge Terminal read-only vocabulary verified live (2026-09-21 03:15 AM CDT)
- Foundation 05 complete with loopback fault tests; End task (first typed mutation) verified live (2026-09-21 03:05 AM CDT)
- Foundation 04 complete: Task Manager, Event Viewer, Network, Disks, Devices, Startup read-only tools verified live (2026-09-21 02:55 AM CDT)
- Foundation 03 read-only slice complete: 39-concept catalog, Home search, Files places, Installed Apps with provenance, Settings routing; 11 integration tests in the session (2026-09-21 02:40 AM CDT)
- Foundation 01 complete: typed core, atomic config, redacted logging, Adw shell with AT-SPI labels, reproducible `.deb` (identical hashes), install/purge clean; candidate cd3ef65 (2026-09-21 12:15 AM CDT)
- pre-implementation gap review recorded as SCOPE-01..13; non-invasive directive DEC-018 accepted; delivery model DEC-019 proposed (2026-09-20)

### Not yet done

- implementation-language/runtime decision
- desktop framework decision
- package format decision
- first-release derivative matrix beyond Ubuntu 24.04 LTS
- first-release desktop/session matrix freeze
- persistence-engine decision
- privilege-helper implementation design freeze
- exact file-manager/desktop integration strategy
- build tooling
- production code
- runtime tests
- distro qualification
- novice-user qualification
- packaging qualification
- release

---

## Evidence state

All implementation/test claims remain one of:

- DESIGN
- NOT_RUN
- BLOCKED

unless exact observed evidence exists.

No document existence implies runtime PASS.

---

## Important owner direction

1. Target the everyday Windows office/home user through advanced Windows users.
2. Everyday tasks should feel familiar and require little thought.
3. The user should be able to use existing Windows knowledge on Linux.
4. Linux remains Linux underneath.
5. Core functionality should be local-first.
6. Do not weaken security to create familiarity.
7. Design to prevent failure; when failure occurs, fail gracefully.
8. Use America/Chicago / Central Time for project timestamps.
9. Local Git only: commit locally, no remotes, nothing touches GitHub until explicitly instructed (2026-09-20).
10. Non-invasive: never invasive, never mistaken for a virus; the owner defines outcomes and delegates the engineering approach (2026-09-20, DEC-018).
11. Ship every integration; user intent decides at first-run setup via grouped options; all reversible, changeable any time; otherwise out of sight behind a plain "T" tray icon (2026-09-20, DEC-019).

---

## Next bounded work

Before implementation:

0. take the `clean-install` checkpoint of the test VM (ENV-03)
1. review root/project documents for alignment (ALN-12)
1a. SCOPE-14: integration catalog with groups, first-run setup screen, integration ledger with exact reversal; ship search provider, tray icon, Files extension in the package
2. decide implementation stack
3. research desktop integration mechanisms for the selected first-release environments
4. select first-release distro/desktop qualification matrix
5. freeze Foundation 01 toolchain and package skeleton
6. only then create executable production source

---

## Do not infer

- documentation completion is not implementation authorization
- one distro working is not Linux support
- build success is not feature qualification
- a command executing is not verified success
- a Windows-looking interface does not justify copying protected assets
- normal Linux users are not expected to learn Linux administration just to be productive

---

## Resume protocol

At a new work session, read in this order:

1. latest owner direction
2. `AGENTS.md`
3. `tools\tb context` output (status, unreviewed changes, ledger digest)
4. this `CONTEXT.md`
5. only the files `tb changes` lists, using `tb outline` / `tb section` for large ones
6. affected `docs/DECISIONS.md`
7. affected `docs/INVARIANTS.md` (via `tb inv show` / `tb inv find`)
8. affected subsystem documents

Then state:

- active task
- authority
- invariant impact
- unresolved blockers
- next bounded action

before consequential work.
