# Trier Bridge Context

**Last updated:** 2026-09-21 11:04 PM CDT  
**Owner:** Doug Trier  
**Project state:** FOUNDATIONS 01–07 CLOSED; FOUNDATION 08 AUTOMATED PARTS DONE; FILE BROWSER, PERFORMANCE GRAPHS, SHELL RESTYLE, AND FINAL POLISH BUILT (DEC-025–028); OWNER ACCEPTANCE OF CANDIDATE `208a257` IS WHAT REMAINS  
**Implementation:** AUTHORIZED 2026-09-21 (DEC-023)  
**CQS:** 94 / 100 (all eight categories measured 2026-09-21, refreshed for candidate `208a257` at 11:04 PM CDT, `CODE-QUALITY-REPORT.md`; release still locked)  

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

- Evening of 2026-09-21, at the owner's direction and mostly owner-confirmed live as it went: the in-app file browser (DEC-025, `DOC-02.01`; a real `Adw.ActionRow` activation bug found on first click and fixed); session-critical processes and services protected after the owner was force-logged-out twice (IMP-06.04/06.05); a deployment gap closed — the installed package had not been rebuilt since 7:30 AM, so nothing tested that day had been what was written — with rebuild+reinstall+relaunch now part of every cycle; Task Manager's Performance tab with live per-disk/per-adapter graphs (DEC-026, IMP-04.01); a branded launcher icon suite (SCOPE-14); ping/tracert's terminal kept open and then reused across runs, each fix probed on the VM after a confident-but-wrong first attempt (IMP-07.14); the navy shell with a hue slider, zoom bar, and sidebar About page (DEC-027, SCOPE-15); Services' first-load lag fixed at its cause (eager per-row popovers). Then the final audit and polish pass on Fable 5.1 (DEC-028, SCOPE-16, candidate `208a257`, 11:04 PM CDT): one shared page hero for every section, the accent framing the content on three sides, Home's card grid, real app icons and status pills, zoom in 5% steps, About cut to facts with full-color support marks, and "Software installers (.deb)" as a Default apps row so App Center can be chosen once and a double-click installs — the File-Roller-wins-by-default cause verified on ENV-02 with the session's own data dirs, recorded in `docs/PACKAGING.md`. `HANDOFF.md` folded into the ledger and removed. Built, gated on both platforms, the real window constructed and exercised on the real stack, deployed; the owner's look is what remains. Invariants 258.
- After section 4 closed, kept finding and closing same-VM gaps that needed neither the owner, hardware, nor fault injection: the End task confirmation dialog (an apparent AT-SPI exposure gap turned out to be specific to this session's SSH-launched test instances, not a product defect — the owner ran the exact check himself from the console and it worked correctly end to end); the two-concurrent-instances coordination guarantee (TB-INV-063, previously untested — a second launch hands off cleanly to the first, no duplicate window); and the Terminal page's PowerShell button (clicked for real over AT-SPI, not just the same command path). One further, lower-priority AT-SPI limitation was found and documented but not escalated to the owner a second time in one session: the plain Bridge command text box cannot be driven from these SSH-launched instances, though buttons and the Task Manager search box both work fine — most likely the same SSH-launch class as the resolved dialog finding. `CODE-QUALITY-REPORT.md` refreshed for candidate `e6ad2f8` after catching that it had gone stale by one code commit (2026-09-21 03:10 PM CDT).
- All of section 4's queued AT-SPI page walks are done: Disk Management, Network (with the IPv4 dialog), and Files, plus `test_journeys_vm.py` reconfirmed 3/3 — after diagnosing and fixing an unrelated, session-specific accessibility-bus outage. `at-spi-bus-launcher`'s socket file had been deleted from the filesystem while the process kept running, so no new connection (SSH or console) could reach it — an earlier hypothesis blaming "SSH vs. console" was wrong and has been corrected in the record (`docs/VALIDATION.md` entry IMP-03.09 addendum). The owner restarted the stuck daemon trio and closed a stale single-instance window at the console; both fixes are the owner's action, not something taken unilaterally. Network page: adapter facts, Disconnect/IPv4… buttons, and the IPv4 dialog (switch, three entry fields, Cancel/Apply) all confirmed, closed with Cancel. Disk Management and Files both show C:/D: drive letters consistently with mount point, filesystem, and free space; Files additionally lists Familiar places (Desktop, Documents, Recycle Bin, Removable drives, Network) each with a real path and an Open button. Owner direction 2026-09-21 02:24 PM CDT: prove everything possible on this VM first; a second environment (IMP-08.03) waits for a real installer and the owner's own new-VM test later, not this session's job (2026-09-21 02:28 PM CDT).
- IMP-07.13: `nslookup`'s resolver calls (`socket.getaddrinfo`/`getfqdn`, the only blocking call reachable from a Bridge command with no native timeout) now bounded to 5 seconds, closing Foundation 07's last open item (TB-INV-101). Foundation 07 is fully closed, 13/13. Along the way, the owner ran the full VM integration suite from the console with the test password set and saw two failures in `test_authorization_vm.py`/`test_services_vm.py`; investigated live, both were a real but benign cause (the account's active console session carried a cached `auth_admin_keep` polkit grant from an earlier interactive authentication), confirmed by re-running the same tests over SSH where they passed cleanly; both test docstrings now state that precondition so it reads as expected next time, not a false alarm. No code defect; nothing changed in the product's privilege model (2026-09-21 01:47 PM CDT).
- IMP-07.12: shutdown timer arms a cancellable main-loop timer and `/a` cancels it; `taskmgr`/`devmgmt.msc`/`services.msc`/`eventvwr`/`msconfig`/`ncpa.cpl`/`appwiz.cpl`/`msinfo32`/`compmgmt.msc` open the matching page; `findstr /R` regular-expression matching and `/L` literal mode; Event Viewer Boot view reads this boot's kernel/audit records independently of the 500-entry general read, resolving the IMP-04.03 Boot-view limitation. CODE-QUALITY-REPORT refreshed for candidate `28f6988` (2026-09-21 01:20 PM CDT); host and VM gates clean; live checks over SSH for the shutdown preview, findstr /R and /L, and the boot-scoped read cross-checked against `journalctl -k -b`. A fuller VM integration run with the owner's test password (51 passed, 3 skipped, all needing a console) closed the initial narrower-coverage gap; the only remaining unverified pieces are the timer-fire-while-armed sequence and the taskmgr/eventvwr open-page branch while the app is actually running, both needing a live desktop session this SSH-based work does not have.
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
- Foundations 03/06/07 mutations closed (file operations, default apps, polkit grant/dismiss via a real test agent, PowerShell entry and cmdlet names, sc stop through the terminal); regression set mapped; SCOPE-06..13 and ARC-03..14 closed; upgrade in place, purge, performance measurement (Task Manager CPU defect fixed), clean sbuild chroot build identical to in-VM builds (2026-09-21 08:10 AM CDT)
- SCOPE-14 done: first-run setup screen, Integrations page (per-item switches, whole-group, Turn everything off), tray icon T (StatusNotifierItem + dbusmenu), GNOME search provider, Files context-menu extension, Ctrl+Shift+Esc shortcut; all verified live from the installed `.deb`; purge/reinstall verified; CODE-QUALITY-REPORT refreshed for candidate 078048d (2026-09-21 03:50 AM CDT)
- Services control (user scope verified, system denial verified) and Bridge Terminal read-only vocabulary verified live (2026-09-21 03:15 AM CDT)
- Foundation 05 complete with loopback fault tests; End task (first typed mutation) verified live (2026-09-21 03:05 AM CDT)
- Foundation 04 complete: Task Manager, Event Viewer, Network, Disks, Devices, Startup read-only tools verified live (2026-09-21 02:55 AM CDT)
- Foundation 03 read-only slice complete: 39-concept catalog, Home search, Files places, Installed Apps with provenance, Settings routing; 11 integration tests in the session (2026-09-21 02:40 AM CDT)
- Foundation 01 complete: typed core, atomic config, redacted logging, Adw shell with AT-SPI labels, reproducible `.deb` (identical hashes), install/purge clean; candidate cd3ef65 (2026-09-21 12:15 AM CDT)
- pre-implementation gap review recorded as SCOPE-01..13; non-invasive directive DEC-018 accepted; delivery model DEC-019 proposed (2026-09-20)

### Not yet done

- acceptance cases that need a person at the console: office-user usability (IMP-08.04), Windows power-user continuity (IMP-08.05), keyboard-only, Orca, large text (IMP-08.06, TB-A11Y-06..08)
- IMP-03.08 screenshot/clipboard behaviour beyond teaching; IMP-03.09 office-user interaction tests
- IMP-06.06 network and package mutations: deliberately not started; needs its own qualification and an owner decision
- IMP-08.03 a second environment (another machine, X11, an Ubuntu flavour); IMP-08.09 release CQS (release locked)
- SCOPE-12 name and trademark check before any public step
- quality remediation CQ-02..09 (`CODE-QUALITY-REPORT.md`)
- release (locked; local Git only)

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
