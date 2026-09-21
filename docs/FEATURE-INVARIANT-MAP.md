# Feature to Invariant Map

**Generated from `VALIDATION.md` (the "Invariant impact" line of every evidence entry) by `tools/dev.py map`, 2026-09-21 12:39 PM Central Daylight Time.** Regenerate whenever an entry is added; this file is derived, not edited by hand (ARC-13).

| Evidence entry | Feature | Invariants and security rules cited |
|---|---|---|
| ENV-02 | Hyper-V Ubuntu Desktop test VM created and profiled | TB-INV-023, TB-INV-230, TB-INV-231 |
| IMP-01 | Foundation 01: toolchain, skeleton, checks, reproducible package | TB-INV-004 |
| IMP-02 | Foundation 02: environment profile and capability discovery | TB-INV-016 |
| IMP-03 | Foundation 03: everyday continuity, first slice (read-only) | TB-INV-003, TB-INV-010, TB-INV-072, TB-INV-073, TB-INV-074, TB-INV-078 |
| IMP-04.01 | Task Manager observation | TB-INV-050, TB-INV-066, TB-INV-131, TB-INV-132, TB-INV-133, TB-INV-136, TB-INV-199, TB-INV-200 |
| IMP-04.03 | Event Viewer over the journal | TB-INV-045, TB-INV-068, TB-INV-100, TB-INV-144, TB-INV-145, TB-INV-146, TB-INV-147, TB-INV-148 |
| IMP-04 | Foundation 04: read-only familiar system tools (Network, Disks, Devices, Startup, provenance) | TB-INV-052, TB-INV-070, TB-INV-071, TB-INV-072, TB-INV-131, TB-INV-149, TB-INV-157, TB-INV-158, TB-INV-162, TB-INV-173, TB-INV-174, TB-INV-175 |
| IMP-05 | Foundation 05: durable state, operation journal, restart reconciliation, fault tests | TB-INV-029, TB-INV-055, TB-INV-059, TB-INV-060, TB-INV-179, TB-INV-180, TB-INV-181, TB-INV-182, TB-INV-183, TB-INV-189, TB-INV-194, TB-INV-196 |
| IMP-06.04 | End task (user process termination) | TB-INV-006, TB-INV-050, TB-INV-078, TB-INV-121, TB-INV-132, TB-INV-134, TB-INV-136, TB-INV-192, TB-INV-193 |
| IMP-06.05 | Service control through systemd (polkit-mediated) | TB-INV-006, TB-INV-053, TB-INV-067, TB-INV-109, TB-INV-110, TB-INV-126, TB-INV-138, TB-INV-139, TB-INV-142, TB-INV-143, TB-SEC-007 |
| IMP-07 | Bridge Terminal (grammar, read-only vocabulary, taskkill via typed plan) | TB-INV-082, TB-INV-083, TB-INV-084, TB-INV-085, TB-INV-086, TB-INV-087, TB-INV-088, TB-INV-089, TB-INV-093, TB-INV-094, TB-INV-096, TB-INV-098, TB-INV-099, TB-INV-100, TB-INV-102, TB-INV-104, TB-INV-105, TB-SEC-004 |
| SCOPE-14 | Integration catalog, first-run setup, tray icon, search provider, Files extension | TB-INV-025, TB-INV-026, TB-INV-076, TB-INV-077, TB-SEC-003 |
| IMP-06.07 | Authorization paths driven end to end: granted, dismissed, backend re-exec | TB-INV-006, TB-INV-053, TB-INV-059, TB-INV-060, TB-INV-109, TB-INV-110, TB-INV-126, TB-INV-127, TB-INV-142 |
| IMP-07.06/07 | PowerShell entry through real pwsh; cmdlet names through typed operations | TB-INV-082, TB-INV-085, TB-INV-086, TB-INV-103, TB-INV-104, TB-INV-105, TB-SEC-003 |
| IMP-03.03 | Everyday file operations: copy, move, rename, Trash, folders (typed, confirmed) | TB-INV-006, TB-INV-050, TB-INV-078, TB-INV-083, TB-INV-119, TB-INV-121, TB-INV-164 |
| IMP-03.05 | Default apps: choose which listed program opens a kind of file (typed, reversible) | TB-INV-006, TB-INV-050, TB-INV-077, TB-INV-083, TB-INV-119, TB-INV-121, TB-INV-209 |
| IMP-06.08 | Security and failure regression set (with SECURITY Test B live) | TB-INV-089, TB-INV-094, TB-INV-104, TB-INV-109, TB-INV-110, TB-INV-119, TB-SEC-001 |
| IMP-08.02 | Install, upgrade in place, purge; per-user state and ownership | TB-INV-025, TB-INV-026, TB-INV-029 |
| IMP-08.08 | Performance and resource measurement (with one defect found and fixed) | TB-INV-004, TB-INV-203 |
| IMP-08.01 | Clean-chroot build (sbuild) reproduces the in-VM build bit for bit | TB-INV-004, TB-INV-027, TB-INV-028 |
| IMP-03.08 | Print Screen through the desktop portal (implemented; unverifiable in this VM) | TB-INV-004, TB-INV-065, TB-INV-078, TB-INV-119 |
| IMP-03.09 | Office-user journeys as automated interaction tests (console session) | TB-INV-078, TB-INV-082, TB-INV-105, TB-INV-209 |
| IMP-03.06/HELP | Live printer queues from CUPS; Help generated from the build | TB-INV-004, TB-INV-033, TB-INV-078, TB-INV-209 |
| IMP-06.06 | Network translation layer: adapter and IPv4 changes through NetworkManager | TB-INV-006, TB-INV-052, TB-INV-078, TB-INV-094, TB-INV-104, TB-INV-109, TB-INV-110 |
| IMP-04.07 | Drive letters: C:, D:, ... as a familiar label over Linux mounts | TB-INV-004, TB-INV-031, TB-INV-073 |
| IMP-07.08 | ping, tracert, nslookup, ipconfig /flushdns | TB-INV-004, TB-INV-078, TB-INV-083, TB-INV-119, TB-SEC-003 |
| IMP-07.09 | explorer, start, net, date, time, taskkill /IM, and the teaching entries | TB-INV-080, TB-INV-094, TB-INV-104, TB-INV-105, TB-INV-119 |
| IMP-07.10 | shutdown /s and /r through logind | TB-INV-004, TB-INV-078, TB-INV-094, TB-INV-104, TB-INV-109, TB-INV-110 |
| IMP-07.11 | findstr, find, where, set, path, tree, %VAR% expansion, exit | TB-INV-080, TB-INV-098, TB-INV-099, TB-INV-100, TB-INV-105 |
| TOOL-05 | Read-only tools run unmodified on Linux | none cited |

99 distinct invariant and security IDs are cited by 30 entries.
