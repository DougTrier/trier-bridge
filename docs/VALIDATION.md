# Trier Bridge Validation and Evidence

**Status:** All runtime evidence is NOT RUN. No implementation candidate exists.

This document defines evidence states, evidence records, qualification automation limits, the pre-implementation checklist, interaction acceptance cases, and the templates for test reports and task evidence. The existence of any template here is not evidence of PASS.

## 1. Evidence states

- `DESIGN`
- `IMPLEMENTED`
- `UNIT_VERIFIED`
- `INTEGRATION_VERIFIED`
- `FAILURE_VERIFIED`
- `DISTRO_VERIFIED`
- `DESKTOP_VERIFIED`
- `PHYSICAL_VERIFIED`
- `ACCESSIBILITY_VERIFIED`
- `NOVICE_VERIFIED`
- `RELEASE_VERIFIED`
- `NOT_RUN`
- `BLOCKED`
- `UNSUPPORTED`
- `NOT_APPLICABLE`

Do not collapse these into one PASS.

`NOT_RUN` means evidence is missing, not PASS or FAIL. `BLOCKED` means a prerequisite, capability, environment, decision, or verification requirement is unresolved.

## 2. Evidence record

Every consequential verification records:

- task/test ID
- candidate revision
- package/build identity
- environment profile
- fixture
- steps
- expected result
- observed result
- logs/artifacts
- limitations
- timestamp (America/Chicago)

## 3. Claim boundary

A passing unit test cannot prove:

- distro compatibility
- real privilege UX
- Wayland behavior
- physical USB/printing/Bluetooth
- novice usability
- release packaging

Evidence belongs to the exact claim.

## 4. Qualification automation

Purpose: automate evidence collection without automating approval.

Safe automation may:

- inspect Git scope
- identify affected invariant families
- identify protected areas
- validate docs/headers/license inventory
- check environment profile
- run reviewed non-destructive tests
- run destructive tests only in disposable authorized profiles
- collect machine-readable results
- bind results to candidate/environment

Automation may not:

- mark an invariant PASS without its procedure
- widen support claims
- modify source to make tests pass
- suppress findings automatically
- run destructive tests on the user's workstation
- authorize privilege
- publish a release
- change product scope

Readiness failure produces BLOCKED/NOT_RUN with a reason, not a fake PASS.

## 5. Pre-implementation checklist

No item implies implementation or runtime PASS.

**Product**

- [ ] Product North Star reviewed
- [ ] everyday-office-user flows defined
- [ ] power-user/admin layers separated from everyday UX
- [ ] MVP scope frozen
- [ ] non-goals reviewed

**Architecture**

- [ ] implementation stack selected
- [ ] module boundaries frozen
- [ ] platform adapter contract frozen
- [ ] typed operation model frozen
- [ ] privilege architecture reviewed
- [ ] persistence ownership frozen
- [ ] capability state model frozen
- [ ] recovery model frozen

**UX**

- [ ] screen inventory reviewed
- [ ] file/app/search/settings everyday flows designed
- [ ] loading/empty/unknown/denied/error/recovery states designed
- [ ] accessibility flows reviewed
- [ ] Familiar/Bridge/native-detail behavior reviewed

**Security**

- [ ] SECURITY.md review complete
- [ ] privileged API contains no generic root execution
- [ ] Bridge Terminal grammar/security frozen
- [ ] path/identity/stale-state strategy reviewed
- [ ] update trust design selected before enabling updates

**Platform**

- [ ] first-release distro candidates chosen
- [ ] desktop/session matrix chosen
- [ ] packaging candidates chosen
- [ ] capability-discovery research complete for MVP subsystems

**Evidence**

- [ ] affected invariants mapped to planned tests
- [ ] destructive fault tests use disposable environments
- [ ] no support claim exceeds planned qualification

## 6. Interaction acceptance cases

**Status:** Design cases, NOT RUN.

Required evidence for each case: environment, steps, expected result, observed result, failures/limitations.

| ID | Case |
|---|---|
| TB-IA-01 | Office user finds and opens a downloaded PDF without knowing a Linux path. |
| TB-IA-02 | Office user copies a document to a USB drive and safely ejects it. |
| TB-IA-03 | Office user connects to Wi-Fi and verifies connection status. |
| TB-IA-04 | Office user opens a familiar network share without using mount commands. |
| TB-IA-05 | Office user prints a document and views/cancels the queue. |
| TB-IA-06 | Office user changes the default application for PDFs. |
| TB-IA-07 | Office user finds an installed application and launches it. |
| TB-IA-08 | Office user uninstalls an application while its package provenance remains clear. |
| TB-IA-09 | Office user changes display arrangement/resolution through a familiar route. |
| TB-IA-10 | Office user connects Bluetooth headphones and selects them for audio. |
| TB-IA-11 | Office user takes a screenshot using familiar interaction. |
| TB-IA-12 | Office user finds disk usage without understanding mount points. |
| TB-IA-13 | User closes a frozen user application through Task Manager. |
| TB-IA-14 | User searches for "Task Manager" and lands on the correct Linux-backed feature. |
| TB-IA-15 | User searches for "Add or Remove Programs" and reaches Installed Apps. |
| TB-IA-16 | User opens Event Viewer after an application failure and gets useful filtered logs. |
| TB-IA-17 | Power user inspects startup applications without learning systemd first. |
| TB-IA-18 | Power user identifies a network adapter and current IP address. |
| TB-IA-19 | Power user inspects hardware in Device Manager. |
| TB-IA-20 | Power user inspects disks/partitions without destructive action. |
| TB-IA-21 | Advanced user restarts a qualified service with explicit authorization. |
| TB-IA-22 | Advanced user enters `ipconfig` in Bridge Terminal and receives Linux-backed output. |
| TB-IA-23 | Advanced user enters an unsupported Windows command and nothing executes. |
| TB-IA-24 | Bridge Terminal rejects command injection/metacharacter abuse. |
| TB-IA-25 | Permission denial is explained without suggesting an insecure bypass. |
| TB-IA-26 | Backend unavailable degrades only the affected capability. |
| TB-IA-27 | System state changes outside Trier Bridge and the UI refreshes rather than fighting it. |
| TB-IA-28 | Large-text/keyboard-only user completes an everyday task. |
| TB-IA-29 | Non-English user searches a familiar system concept without changing backend identity. |
| TB-IA-30 | Internet disconnected: core local experience and system tools remain usable. |

## 7. Foundation test report template

**Current status:** NOT RUN.

When foundation testing begins, record: candidate revision, build/package identity, host environment, tested distro/session profiles, toolchain versions, source verification, build result, unit result, integration result, fault result, package install/uninstall result, known gaps, exact artifacts.

Persistence-specific coverage is listed in `STATE-AND-PERSISTENCE.md` section 13.

## 8. Task evidence ledger

**Status:** Empty baseline. Use only for observed evidence once implementation work begins.

Entry template:

```text
### <Task ID> — <Title>

- Timestamp:
- Candidate revision:
- Environment/profile:
- Files/modules:
- Invariant impact:
- Expected result:
- Observed result:
- Tests/checks:
- Artifacts/logs:
- Failures/limitations:
- Evidence state: DESIGN / IMPLEMENTED / UNIT_VERIFIED / INTEGRATION_VERIFIED /
  FAILURE_VERIFIED / DISTRO_VERIFIED / PHYSICAL_VERIFIED / RELEASE_VERIFIED /
  NOT_RUN / BLOCKED
```

Do not record planned behavior as observed evidence.

## Entries

(none)
