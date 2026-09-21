# Trier Bridge Roadmap and Implementation Foundations

**Status:** Planning only. Nothing in this document is authorized or implemented.

The operational task ledger is the root `Engine Spec Tasklist 01.MD`. This document explains the phases and foundations that ledger's task IDs belong to.

## 1. Product phases

The product view, from `PRODUCT-CONCEPT.md` section 22:

| Phase | Name | Scope |
|---|---|---|
| 0 | Product and engineering freeze | Concept, North Star, invariants, security, licensing, code quality, platform research, stack selection. |
| 1 | Everyday continuity MVP | Familiar launcher/search, files and navigation entry points, removable drives, right-click, drag and drop, common shortcuts, task switching, settings routing, default apps, printers, network/Wi-Fi entry, installed apps. |
| 2 | Familiar troubleshooting | Task Manager, startup applications, Network Connections, storage overview, Device Manager, Event Viewer. |
| 3 | Safe system mutation | Selected service/process/package/network operations through typed privileged APIs. |
| 4 | Advanced Windows continuity | Services, Bridge Terminal, Windows command translation, PowerShell integration, deeper diagnostics. |
| 5 | Cross-distro hardening | Adapter expansion, distro/desktop qualification, package formats. |
| 6 | Usability and accessibility qualification | Office users, home users, power users, advanced Windows users. |
| 7 | Release | Security, provenance, packaging, signed artifacts, documented compatibility matrix. |

"Show Me the Linux Way" and other optional-learning features are cross-cutting and ship alongside the surface they explain, never as a prerequisite for using it.

The advanced layers must never make the everyday experience dependent on them.

## 2. Implementation foundations

The engineering view. The project builds from low-risk observation toward higher-risk mutation.

| Foundation | Name | Objective | Supports phase |
|---|---|---|---|
| 01 | Toolchain, package skeleton, and unprivileged shell | Build/package skeleton, logging, config, accessibility baseline. No privileged mutation. | 0 |
| 02 | Environment profile and capability discovery | Distro/session/backend detection and adapters, read-only only. | 0–1 |
| 03 | Everyday Windows-continuity experience | Files, routes, search, apps, settings, printers, USB, network-share entry points with minimal mutation. | 1 |
| 04 | Read-only familiar system tools | Task Manager observation, logs, devices, network, storage, installed apps. | 2 |
| 05 | Durable state, journals, and recovery | Preferences, operation IDs, journals, state model, restart reconciliation. | prerequisite for 3 |
| 06 | Privilege boundary and typed system mutation | Finite privileged operations; service/user-process/network/package mutations only as individually reviewed. | 3 |
| 07 | Bridge Terminal and PowerShell continuity | Parser and typed operations, read-only first; mutation later through existing authority. | 4 |
| 08 | Integrated qualification, packaging, and release | Cross-distro testing, accessibility, performance, security review, release gates. | 5–7 |

Rule: a later foundation may prototype against interfaces before prior integrated qualification is complete, but no dependent production claim may bypass missing prerequisite evidence.

Foundation 01 prerequisites: ledger tasks ARC-01 through ARC-03 and the relevant quality/licensing decisions.

## 3. Baseline protocol for every foundation

Each foundation is a bounded baseline that must not weaken `SECURITY.md`, `INVARIANTS.md`, `PRODUCT-NORTH-STAR.md`, or any prior baseline.

Before work on a foundation begins, record:

- exact task/objective
- authority/scope confirmation
- affected files/modules
- applicable `TB-INV-###`
- invariant delta
- Must remain true
- tests/failure injection
- rollback/recovery
- environment/profile

A foundation is complete only when its stated implementation and required verification evidence exist. Build success alone is insufficient.

Current evidence for every foundation: **NOT RUN / NOT IMPLEMENTED**.

## 4. Qualification tracks

Tracked in the ledger under Foundation 08 and Release:

- distro/desktop matrix
- office-user usability
- power-user continuity
- accessibility and localization
- security
- recovery/fault injection
- performance/resource
- package/install/uninstall
