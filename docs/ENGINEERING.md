# Trier Bridge Engineering

**Status:** Architecture baseline  
**Date:** September 20, 2026

This document covers architecture, build contract, engineering automation, optimization, resource efficiency, and contributor on-ramps. Security detail lives in `SECURITY.md`; invariants in `INVARIANTS.md`; platform and adapter contracts in `PLATFORMS.md`; state and persistence in `STATE-AND-PERSISTENCE.md`; evidence rules in `VALIDATION.md`.

## 1. Engineering objective

Trier Bridge is an installable Linux experience layer that preserves the learned workflows of Windows users while executing through Linux-native mechanisms.

The engineering problem is not "make Linux look like Windows."

It is:

> **Preserve familiar intent while safely adapting to a heterogeneous Linux platform.**

## 2. Architectural rules

- Linux remains authoritative.
- Presentation is not a security authority.
- Everyday experience is first-class; administration is a deeper layer.
- Windows-like commands normalize to typed operations before execution.
- Platform/distro differences remain behind bounded adapters.
- Capability is detected, never guessed.
- Unsupported and Unknown remain distinct.
- Normal operation is unprivileged.
- Privileged actions are explicit, narrow, temporary, and verifiable.
- Core use is local-first and Internet-independent.
- System mutation requires stable identity, current authorization, and recovery semantics.
- A failed operation must not widen scope or fall back to a weaker mechanism.
- No code-quality or performance goal may weaken invariants.

## 3. Conceptual layers

```text
Experience Layer
    familiar shell / files / search / settings / system tools
        ↓
Intent Layer
    user action / Windows term / Bridge command
        ↓
Domain Operation Layer
    typed operations and state machines
        ↓
Capability + Policy Layer
    supported / unsupported / unknown / privilege / safety
        ↓
Adapter Interfaces
    process / service / network / storage / package / desktop / device
        ↓
Linux Implementations
    systemd / D-Bus / NetworkManager / udisks / procfs / sysfs / package backends
```

Privileged execution is a side boundary reached only through named typed operations.

## 4. Suggested domain boundaries

Names are provisional until implementation stack freeze.

- `experience`
- `files`
- `apps`
- `search`
- `settings`
- `devices`
- `display`
- `printing`
- `network`
- `process`
- `services`
- `journal`
- `storage`
- `packages`
- `bridge-command`
- `powershell`
- `capability`
- `platform-profile`
- `privilege`
- `recovery`
- `audit`
- `help`

Avoid generic `Manager`, `Utils`, or `System` modules that become hidden authority.

## 5. Dependency direction

Domain logic must not depend directly on a particular distro, desktop, package manager, or shell.

Linux-specific code implements adapter contracts.

UI code may request typed intent but must not:

- construct privileged shell commands
- infer system capability
- bypass backend validation
- convert Unknown into Supported
- own authoritative mutable system state

## 6. Environment plurality

Support claims must bind to actual facts such as:

- distro/version
- architecture
- desktop environment
- Wayland/X11/headless
- init/service manager
- network backend
- package backends
- authorization mechanism
- package form used to install Trier Bridge

"Linux" is not one runtime profile. See `PLATFORMS.md`.

## 7. Failure philosophy

Before implementation, every consequential operation defines:

- identity
- precondition
- privilege
- preview
- commit boundary
- cancellation boundary
- verification
- partial outcome
- recovery
- retry/idempotency

Unknown final state is valid. False success is not.

## 8. Evidence

Use the evidence states defined in `VALIDATION.md`.

Implementation, testing, qualification, and release evidence remain separate.

## 9. Build contract

**Status:** Toolchain not selected. No build commands are invented before the implementation stack is frozen.

When the stack is chosen, establish and document:

- supported host build environments
- compiler/runtime versions
- package manager versions
- dependency locks
- reproducible build inputs
- debug/release profiles
- package formats
- source verification
- code-quality checks
- unit/integration tests
- package validation
- artifact hashes

Documented build commands must be tested from a clean checkout.

No undocumented Internet dependency may be required for normal end-user runtime.

Stack-specific root files (build manifests, lockfiles, tool configs, CI entry points) are added only after the stack freeze, and only what the selected stack actually requires. Creating them earlier would silently make architecture decisions the project has not approved.

## 10. Engineering automation

Automation should reduce repetitive engineering work while preserving human authority and exact evidence.

Candidate automation:

- source/provenance checks
- changed-area detection
- invariant mapping
- static-analysis orchestration
- package/dependency inventory
- environment-profile capture
- test selection
- result normalization
- docs link checking
- release-input verification

Safety classes:

| Class | Rule |
|---|---|
| Read-only | Safe by default. |
| Build/test | Allowed only in known local/disposable contexts. |
| System-mutating | Requires explicit task authorization and a disposable/authorized target. |
| Publication | Always owner-gated. |

Automation cannot infer authority from a green test suite. Qualification-specific automation limits are in `VALIDATION.md`.

## 11. Optimization and resource efficiency

Optimization occurs only after correctness and evidence.

Order of work:

1. data-loss/security/recovery defects
2. false success / unknown-state defects
3. user-visible latency
4. unnecessary polling
5. memory growth
6. I/O/storage growth
7. startup
8. package/install size
9. local micro-optimizations

Rules:

- measure before optimizing
- preserve invariants
- no cache may own user data
- no performance fix may remove verification
- no batching may merge distinct authorization scopes
- no retry optimization may weaken idempotency
- no faster shell shortcut may replace a safer native API
- re-run affected regression/failure tests after optimization

Resource-efficiency principles:

- monitoring work is bounded
- hidden views reduce/pause sampling
- no busy polling when event-driven APIs exist
- lists are streamed/paged/virtualized as needed
- cache, logs, and audit are bounded, with unresolved recovery records protected
- optional network work never blocks startup
- low memory/storage stops optional work first
- user data is never deleted as cache cleanup

Release measurements to define after implementation: cold/warm startup, idle CPU and memory, active dashboard CPU/memory, process-list scale, journal query scale, package inventory scale, device inventory scale, cache/storage growth, low-space behavior, suspend/resume activity, screen-hidden activity, installer size and dependency growth.

Numeric targets remain **NOT MEASURED** until the stack and baseline hardware profiles are chosen.

## 12. Good first issues

Examples only; actual issues are created after the repository exists.

Low-risk candidates:

- improve a Manual topic
- add reviewed Windows/Linux search synonyms
- add a synthetic test fixture
- add accessibility labels to an isolated non-privileged control
- improve error copy without changing error state
- add a distro-detection fixture
- add a read-only environment-profile test
- improve documentation links
- add license/provenance metadata
- add a non-mutating system-information field with explicit Unknown behavior

Not good first issues: privileged helper, command execution, filesystem deletion, package installation/removal, network mutation, service mutation, update mechanism, disk partitioning/formatting, security policy changes, new distro support claims.

## 13. Current state

Architecture is design-only. Toolchain, runtime, language, packaging, and module graph are not yet frozen.
