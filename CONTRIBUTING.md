# Contributing to Trier Bridge

You do not need to understand the entire Trier Bridge engineering system to contribute. Start with the scope of your change. The project uses progressive review: small, isolated work should stay simple; changes that can affect the operating system, privileges, user data, recovery, compatibility, or system state require deeper review.

Trier Bridge is designed around one core idea:

> **Make existing Windows knowledge useful on Linux without weakening Linux, damaging the system, or lying about what happened.**

Contributions should preserve that contract.

---

## Start here

1. Read the [README](README.md), this page, and the relevant portion of [INVARIANTS.md](docs/INVARIANTS.md).
2. Pick a bounded change. Avoid mixing unrelated refactors, feature additions, and cleanup in one contribution.
3. Follow the established architecture and preserve copyright headers and existing notices.
4. Run the directly affected tests and verification tools available in the repository.
5. Include the exact results, limitations, and unrun checks in your pull request.
6. Open a pull request when the public contribution destination is available.

Project automation may eventually provide changed-work, invariant, licensing, and test selection. Until those tools exist, contributors must not invent passing evidence or assume a compile/build proves correctness.

`READY FOR REVIEW` means evidence is ready for human review, not approved for merge.

`NOT_RUN` means evidence is missing. It does not mean PASS or FAIL.

`BLOCKED` means a prerequisite, capability, environment, decision, or verification requirement is unresolved.

---

## How much review does your change need?

Use the highest applicable level.

**Scope and risk matter more than line count.** A five-line privilege or recovery change can require more review than a 500-line documentation improvement.

| Level | Typical changes | What you need |
| --- | --- | --- |
| **1 — Small / low risk** | Typos, documentation wording, comments, isolated tests, accessibility copy, behavior-preserving UI polish, safe refactors with no state/security/adapter impact | This page, applicable licensing rules, changed-work review, and directly affected tests. Explain any behavior change. |
| **2 — Feature / behavior** | Dashboard behavior, process views, Event Viewer presentation, settings, Windows-to-Linux terminology, Bridge Terminal read-only commands, package/application inventory, teaching/help features | Relevant subsystem design, affected invariants, adapter/capability assumptions, mapped tests, and concise PR evidence. |
| **3 — Core / high risk** | Privilege/elevation, command translation, mutation operations, filesystem writes, process termination, services, networking, storage, packages, D-Bus/IPC, update trust, distro adapters, persistence/recovery, multi-user boundaries, security architecture | Applicable security/failure/state contracts, affected invariants, explicit test/evidence mapping, negative/failure testing, broader regressions, and owner review before merge. A successful build is insufficient. |

An isolated test that changes a critical safety, security, or recovery oracle still requires the applicable protected-area review.

Small changes do not waive relevant rules. Unrelated rules do not become required reading.

---

## Scope and merge decisions

Contributions are welcome when they align with Trier Bridge's documented scope and engineering contracts.

**A feature that changes or expands project scope requires owner approval before implementation.**

Propose substantial work first when scope is uncertain, especially if it introduces:

- a new privileged operation
- a new Linux distribution or backend claim
- a new package-management route
- a new shell or command-execution mechanism
- a new update mechanism
- a new plugin/extension system
- a new destructive storage capability
- a new repository-management capability
- a new system-wide configuration authority

This prevents contributors from investing substantial effort in a design that conflicts with the project's safety model.

**No contribution is merged solely because automated checks pass.**

Merge requires:

- scope alignment
- architecture compliance
- invariant preservation
- required tests and evidence
- security review where applicable
- licensing/provenance review
- human review
- explicit project-owner approval

Doug Trier retains final merge and product-direction authority, including for technically correct and well-tested changes.

Automated or AI-assisted review may examine affected invariants, quality, licensing/provenance, static analysis, failure coverage, protected areas, and architecture boundaries. Automation assists review; it does not grant merge authority.

---

## Read only what applies

| Contributor | Reading map |
| --- | --- |
| **Everyone** | [README](README.md), this page, applicable [INVARIANTS](docs/INVARIANTS.md), and the short rules below |
| **UI / learning contributors** | Relevant Windows-to-Linux mapping, accessibility, terminology, and interaction rules |
| **Bridge Terminal contributors** | [SECURITY](docs/SECURITY.md), command-translation architecture, affected invariants, parser/failure tests |
| **System-adapter contributors** | Relevant distro/backend adapter contract, [SECURITY](docs/SECURITY.md), affected invariants, platform evidence |
| **Core / privileged contributors** | Applicable security, privilege, IPC/D-Bus, state/recovery, failure and release contracts |
| **Release maintainers** | Full release gates, [SECURITY](docs/SECURITY.md), [LICENSING](docs/LICENSING.md), dependency/SBOM evidence, supported-platform matrix, update/signing requirements |

Repository agents and automation must follow the same authority and invariant rules as human contributors.

Maintainers own the authoritative completion/evidence ledger if one is introduced. A small-contribution PR does not need to recreate the project's internal evidence-management system.

---

## Rules for every contribution

- Submit only material you have the right to contribute.
- First-party contributions intentionally submitted for inclusion use **Apache License 2.0** under [LICENSE](LICENSE), subject to its contribution terms.
- Preserve legitimate copyright, attribution, patent, trademark, and NOTICE information.
- Follow [LICENSING.md](docs/LICENSING.md) for source headers, provenance, third-party code, and asset requirements.
- Do not replace another author's valid copyright or license notice.
- Never submit credentials, private keys, tokens, passwords, personal system data, private logs, confidential reports, or material with unclear provenance.
- Use established naming, ownership, error, adapter, and recovery patterns.
- Explain non-obvious security, privilege, compatibility, or recovery decisions.
- Avoid unrelated refactors.
- Preserve applicable invariants and tests.
- Report failures and limitations honestly.
- Changed requirements require owner approval.
- Generated or AI-assisted work follows exactly the same engineering, licensing, security, and review standards as manually authored work.
- Do not claim a Linux distribution, desktop environment, backend, package manager, or system configuration is supported without corresponding evidence.
- Do not turn `UNKNOWN` into `SUPPORTED` because a fallback happened to work once.
- Do not broaden privilege, filesystem scope, package scope, service scope, or mutation scope to make implementation easier.
- Do not introduce a generic root shell, unrestricted privileged command API, or arbitrary privileged file-write mechanism.
- Do not bypass Linux security controls to make Trier Bridge behave more like Windows.

---

## Trier Bridge product boundary

Trier Bridge is a **Windows-to-Linux knowledge, workflow, and administration bridge**.

It is not intended to be:

- another Linux distribution
- a Windows clone
- a Windows emulator
- a Wine replacement
- a Windows compatibility runtime for applications
- a collection of shell aliases
- a hidden root shell
- a mechanism for bypassing Linux permissions
- a replacement for Linux package trust
- a replacement for native Linux administration

Trier Bridge translates familiar concepts into safe Linux-native operations where a qualified mapping exists.

When no faithful or safe mapping exists, Trier Bridge should explain the difference rather than fabricate compatibility.

---

## Protected architecture areas

The following areas require particular care.

### Privilege and elevation

Trier Bridge's normal application runs unprivileged.

Privileged operations must be:

- finite
- named
- schema validated
- operation scoped
- tied to deliberate user intent
- revalidated before mutation
- verified afterward where possible

Never introduce a generic API such as:

```text
RunAsRoot(command)
ExecuteShellAsRoot(script)
WriteAnythingAsRoot(path, bytes)
```

If a proposed feature appears to require such an API, stop and redesign the feature boundary.

---

### Command translation

Bridge Terminal compatibility commands must use:

```text
Windows-style input
        ↓
strict parser
        ↓
typed Trier Bridge operation
        ↓
capability and policy validation
        ↓
native Linux adapter
        ↓
structured result
```

Never implement Windows compatibility through unsafe text substitution such as:

```text
replace Windows command with shell command
→ concatenate user text
→ execute
```

Unsupported commands or flags fail without execution.

Unknown Bridge commands must not silently fall through to Bash, PowerShell, or another shell.

---

### Linux capability detection

Linux environments vary.

Do not assume:

- systemd
- NetworkManager
- PackageKit
- apt
- dnf
- rpm
- Flatpak
- Snap
- GNOME
- KDE
- Wayland
- X11
- polkit
- a specific filesystem
- a specific package layout
- a specific network configuration authority

Detect capabilities and use bounded adapters.

A missing backend should disable only the dependent capability.

---

### State and identity

Do not use unstable presentation values as mutation identity.

Examples that are insufficient by themselves:

- PID
- `/dev/sdX`
- list position
- interface display name
- package display name
- UI row
- translated Windows-style path

Capture and revalidate the strongest available stable identity before consequential operations.

---

### Recovery

A failure is not handled merely because an error message appeared.

For consequential operations, define:

- precondition
- authorization point
- commit boundary
- interruption behavior
- verification
- rollback or recovery
- partial-success reporting

If final state is uncertain, report **UNKNOWN / NEEDS REVIEW** rather than guessing.

---

## Failure-first contribution standard

For affected behavior, contributors should consider not only:

> “Does it work?”

but also:

> “What happens if every dependency fails at the worst reasonable point?”

Relevant failure cases may include:

- authorization denied
- authorization cancelled
- backend missing
- backend restarts
- target disappears
- stale target identity
- process PID reuse
- disk full
- read-only filesystem
- permission loss
- network loss
- package-manager lock
- repository outage
- invalid signature
- system suspend
- application crash
- system reboot
- operation cancellation
- partial commit
- rollback failure
- malformed input
- hostile text
- Unicode/path edge cases
- oversized output
- resource exhaustion

The required depth depends on the change, but protected-area contributions are expected to include negative/failure evidence.

---

## Graceful failure requirement

Trier Bridge's failure order is:

1. **Protect user data and system state.**
2. **Do not expand scope or privilege.**
3. **Stop before an uncertain destructive boundary.**
4. **Preserve recovery evidence.**
5. **Return control to the user.**
6. **State whether anything changed.**
7. **Classify the result accurately.**
8. **Offer the safest recovery action.**
9. **Expose technical detail progressively.**

A familiar Windows-looking success message must never hide a Linux operation that failed or could not be verified.

---

## Content and repository boundary

Do not submit:

- secrets
- credentials
- private keys
- personal logs
- `/etc/shadow` or equivalent sensitive account data
- real authentication databases
- private SSH material
- browser profiles
- private package-repository credentials
- personal home-directory fixtures
- real corporate configuration
- copied proprietary Windows assets
- Microsoft icons or screenshots without a valid usage basis
- third-party code or assets with unresolved licensing

Testing fixtures should be synthetic or sanitized.

Destructive testing belongs on disposable environments such as:

- virtual machines
- containers where appropriate
- loopback filesystem images
- synthetic D-Bus/system-service fixtures
- explicitly authorized test hardware

Do not test failure recovery by risking a contributor's real workstation.

---

## Distribution and compatibility claims

A pull request must not broaden public compatibility claims merely because the change compiled or worked on one machine.

Compatibility evidence should identify, where applicable:

- Linux distribution and version
- CPU architecture
- desktop environment
- Wayland / X11 / headless session
- init/service manager
- network backend
- package backend
- storage backend
- authorization mechanism
- Trier Bridge package format
- feature tested
- evidence level

Prefer:

> Verified on Ubuntu 26.04 / GNOME / systemd for this operation.

over:

> Works on Linux.

---

## Licensing and provenance

Trier Bridge uses **Apache License 2.0**.

See:

- [LICENSE](LICENSE)
- [NOTICE](NOTICE)
- [LICENSING.md](docs/LICENSING.md)

Qualifying first-party source should use the project's approved copyright and SPDX/header format.

Do not add Trier Bridge copyright headers to:

- third-party source
- vendored source
- generated files
- binary files
- lockfiles
- third-party license/notice files
- files whose format does not safely permit comments

Third-party dependencies and assets retain their original licenses.

Windows, Linux distribution, desktop, vendor, and product trademarks remain the property of their respective owners.

Familiarity must be achieved through original Trier Bridge design and factual terminology, not unauthorized copying of protected visual assets.

---

## Development tools and AI-assisted contributions

Trier Bridge welcomes contributions regardless of the tools used to create them.

Contributors may use:

- traditional editors and IDEs
- command-line tools
- code generators
- AI-assisted development tools
- coding agents
- manual implementation
- combinations of these approaches

Trier Bridge does not require, endorse, or prefer any particular AI provider, model, platform, agent, IDE, or development environment.

**We evaluate the resulting engineering, not the authoring method.**

Every contribution must meet the same requirements for:

- correctness
- maintainability
- architecture
- invariant preservation
- testing
- failure behavior
- security
- privilege boundaries
- licensing
- provenance
- documentation
- scope

AI-assisted code is not exempt from review, testing, or engineering requirements.

Manually written code receives the same scrutiny.

Contributors remain responsible for understanding what they submit and ensuring it contains no incorrect, unsafe, incompatible, private, or improperly licensed material.

Trier Bridge deliberately uses specifications, invariants, failure testing, and review gates so quality can be evaluated from technical evidence rather than inferred from the author's development method.

---

## Pull request evidence

A useful PR should answer, concisely:

### What changed?

Describe the bounded outcome.

### Why?

Describe the user or engineering problem.

### What protected areas are touched?

List relevant areas such as:

- privilege
- filesystem
- process
- services
- packages
- network
- storage
- command translation
- D-Bus/IPC
- persistence/recovery
- compatibility
- accessibility
- licensing

### Which invariants apply?

Reference the affected `TB-INV-###` IDs from [INVARIANTS.md](docs/INVARIANTS.md).

### What was tested?

Include:

- commands/tests run
- environment
- expected result
- observed result
- failure cases
- anything not run

### What remains uncertain?

Say so explicitly.

Do not hide missing evidence behind “works for me.”

---

## Review outcomes

Review may result in:

- **APPROVE**
- **REQUEST CHANGES**
- **BLOCKED — missing evidence**
- **BLOCKED — architecture/scope decision**
- **BLOCKED — unsupported environment**
- **BLOCKED — security concern**
- **BLOCKED — licensing/provenance**
- **NEEDS OWNER DECISION**

A blocked contribution is not necessarily rejected.

It means the project does not yet have enough evidence or authority to merge it safely.

---

## Final contribution rule

> **If Trier Bridge cannot prove that it knows what it is about to do, to exactly what target, with the right authority, and with a defined recovery path, it does not do it.**

Contributions should make the safe path easier, not make unsafe behavior easier to reach.

If guidance is missing or unclear, include that gap in your proposal or pull request so the engineering system itself can improve.
