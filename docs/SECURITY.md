# SECURITY.md
# Trier Bridge Security Architecture

**Project:** Trier Bridge  
**Document:** Security Architecture, Trust Boundaries, and Security Invariants  
**Status:** Design baseline — not an implementation or certification claim  
**Revision:** 0.1  
**Date:** September 20, 2026  
**Owner:** Doug Trier  

---

## 1. Purpose

Trier Bridge exists to make Linux approachable to people whose computer knowledge was built on Windows.

That goal creates an unusual security responsibility.

The product deliberately makes powerful Linux administration concepts feel familiar:

- Task Manager
- Event Viewer
- Services
- Device Manager
- Disk Management
- Network Connections
- Installed Apps
- Command Prompt
- PowerShell-style administration

Familiarity must never become a shortcut around Linux security.

> **Trier Bridge may simplify the path to an operation. It must never silently weaken the rules governing that operation.**

This document defines the minimum security architecture for Trier Bridge before production implementation begins.

It is intentionally failure-first. A feature is not considered secure because its successful path works. It must also behave safely when:

- permissions are missing
- commands are malformed
- distributions differ
- services disappear
- paths change
- privileges expire
- processes race
- package metadata is hostile
- logs contain untrusted text
- storage is full
- the application crashes
- the system reboots
- a user misunderstands what an action will do

---

## 2. Security Design Principles

Trier Bridge's security design rests on the following principles. Each is stated here as a commitment; whether the running code honors it is a matter for the invariants (section 5 onward) and the evidence in `VALIDATION.md`, never for this list alone.

### Boundaries and authority

- explicit trust boundaries
- narrow role/operation scope
- operational authority lives behind the UI; the UI is never the system of record for a security decision
- privileged and network operations are owned by the operation layer, not by the presentation layer
- untrusted input at every boundary (IPC, D-Bus, files, typed commands) is validated on the trusted side

### Execution

- fixed executable argument arrays; no shell interpolation and no dynamic command construction, ever
- static allowlists for sensitive actions
- fail-closed behavior: malformed, unauthenticated, or unexpected input performs no operation
- trusted state is reached only through explicit state transitions
- no silent downgrade of security, and no plaintext fallback when a secure path fails
- replay and duplicate behavior are considered explicitly, not assumed away

### Secrets and records

- secrets never enter UI state
- security-relevant records are kept without raw secrets
- cryptographic trust and application trust are separate concepts

### Honesty

- validated behavior is documented separately from unverified assumptions
- recovery paths are treated separately from happy-path success
- explicit offline behavior
- deployment controls never masquerade as application guarantees
- tests never claim to prove physical or operational behavior that was not actually exercised
- dependency additions are reviewed, never silently introduced; release security is a gate, not a post-release cleanup task

---

# 3. Security North Star

Trier Bridge should preserve three things simultaneously:

1. **Linux security**
2. **user understanding**
3. **user control**

A secure system that ordinary users cannot understand will be bypassed.

A simple system that hides the consequences of privileged actions will be dangerous.

The design target is therefore:

> **Make safe actions easy, consequential actions understandable, and unsafe ambiguity impossible to execute silently.**

---

# 4. Permanent Security Principles

## 4.1 Least privilege

Every component runs with the least privilege required for its current responsibility.

The normal desktop application must run as the signed-in user.

Administrative access is requested only for the specific operation requiring it.

Trier Bridge must not remain root merely because some features occasionally require elevation.

---

## 4.2 Linux remains authoritative

Trier Bridge is an experience and translation layer.

It must not replace or bypass:

- Linux file permissions
- users and groups
- polkit authorization
- PAM
- service ownership
- package signature validation
- package-manager dependency rules
- kernel access controls
- AppArmor/SELinux policy
- filesystem mount protections
- desktop/session permissions

When Linux denies an operation, Trier Bridge reports the denial and explains the recovery path.

It must not silently search for a weaker path.

---

## 4.3 No destructive guessing

Unknown means unknown.

Trier Bridge must not guess:

- distribution
- package manager
- init/service system
- desktop environment
- display server
- filesystem
- mount policy
- authentication provider
- privilege mechanism
- network manager
- device role
- package source
- service ownership
- command meaning
- equivalent Linux operation

If the product cannot establish a safe supported operation, it does not execute one.

---

## 4.4 Typed operations, not string translation

A Windows command or GUI action is translated into a typed system intent.

Example:

```text
taskkill /PID 4271
        ↓
Windows-command parser
        ↓
TerminateProcess { pid: 4271 }
        ↓
Policy + capability validation
        ↓
Authorization
        ↓
Linux process adapter
        ↓
Structured result
```

Never:

```text
replace("taskkill", "kill")
→ build shell string
→ execute
```

The internal operation is the authority.

The Windows syntax is only one way to request it.

---

## 4.5 Explicit elevation

Privileged operations require deliberate user intent.

Elevation must be:

- operation-scoped
- visible
- short-lived
- attributable to the initiating action
- revocable
- revalidated when assumptions change

Trier Bridge must not create:

- a hidden root shell
- a permanently privileged desktop process
- a generic root RPC service
- an unrestricted "execute command as root" interface
- indefinite privilege caching for convenience

Where supported, polkit should be preferred for narrowly authorized actions.

---

## 4.6 Fail closed

Security failure must not create a weaker fallback.

Examples:

| Failure | Required behavior |
|---|---|
| privilege request denied | cancel operation |
| signature invalid | reject package/update |
| unknown command | do not guess |
| parser ambiguity | require clarification |
| invalid IPC payload | reject request |
| path escapes scope | reject path |
| package source unknown | do not install |
| certificate validation fails | do not downgrade |
| helper unavailable | do not use shell shortcut |
| distro adapter uncertain | disable mutation |
| audit write fails for critical action | block or explicitly surface degraded state according to operation policy |

---

## 4.7 User intent is authoritative

Convenience actions do not imply broader permission.

"Uninstall this application" does not automatically authorize:

- deletion of user documents
- removal of unrelated shared runtimes
- deletion of another user's data
- removal of dependencies still required elsewhere
- repository changes
- recursive cleanup outside the package's defined ownership

"Restart service" does not imply:

- enable service
- modify unit file
- reset configuration
- change dependencies
- remove overrides

The operation envelope remains narrow.

---

## 4.8 Security state must be visible

Trier Bridge should clearly distinguish:

- available
- unavailable
- unsupported
- unknown
- requires elevation
- blocked by policy
- failed
- partially completed
- requires reboot
- requires logout/login
- requires manual recovery

"Completed" must never mean "the command was dispatched."

It means the expected postcondition was verified where verification is technically possible.

---

# 5. Trust Boundaries

```text
┌─────────────────────────────────────────────────────┐
│                    Presentation                     │
│ Familiar Windows terminology / Linux learning UI   │
│ Bridge Terminal / dashboards / dialogs             │
└───────────────────────┬─────────────────────────────┘
                        │ UNTRUSTED INPUT
                        ▼
┌─────────────────────────────────────────────────────┐
│                 Intent / Domain Layer               │
│ Parse → validate → normalize → scope → authorize   │
│ Typed operations are created here                  │
└───────────────────────┬─────────────────────────────┘
                        │ TRUSTED CONTRACT
                        ▼
┌─────────────────────────────────────────────────────┐
│                  Capability Layer                   │
│ Detect actual Linux mechanisms and safe adapters   │
│ Supported / unsupported / unknown                  │
└──────────────┬───────────────────────┬──────────────┘
               │                       │
               ▼                       ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│ Unprivileged Adapters   │  │ Privileged Operations   │
│ procfs/sysfs/journal    │  │ Narrow helper / polkit  │
│ D-Bus reads / APIs      │  │ Enumerated operations   │
└─────────────┬───────────┘  └─────────────┬───────────┘
              │                            │
              └──────────────┬─────────────┘
                             ▼
┌─────────────────────────────────────────────────────┐
│                     Linux OS                        │
│ Kernel / systemd / D-Bus / udev / NM / storage    │
└─────────────────────────────────────────────────────┘
```

### Critical rule

**The UI is never a security authority.**

If the project uses Tauri/React, Rust or the equivalent trusted backend owns:

- system state
- capability detection
- validation
- authorization
- privileged-operation requests
- command parsing
- file-path validation
- service mutations
- package mutations
- network mutations
- audit decisions

The frontend mirrors state and collects intent.

---

# 6. Threat Model

Trier Bridge must defend against both hostile input and accidental misuse.

## 6.1 Primary threats

1. command injection
2. shell metacharacter injection
3. privilege escalation
4. arbitrary root command execution
5. path traversal
6. symlink escape
7. unsafe recursive file operations
8. TOCTOU races
9. malicious filenames
10. malicious service names
11. malicious package metadata
12. malicious repository definitions
13. log injection
14. malformed D-Bus/IPC payloads
15. hostile removable storage metadata
16. environment-variable manipulation
17. PATH executable substitution
18. unsafe plugin/extension execution
19. unbounded process/log/device enumeration
20. denial of service through oversized output
21. secrets written to logs
22. secrets placed in shell history
23. privilege persistence after an operation
24. update or supply-chain compromise
25. package-manager confusion across distributions
26. incorrect Windows-to-Linux command equivalence
27. destructive beginner misunderstanding
28. unsafe PowerShell compatibility behavior
29. compromised local user account
30. interrupted configuration writes
31. full disk during state change
32. partial package/service operations
33. stale state used after system topology changes
34. multi-user information disclosure
35. unsafe desktop integration
36. malicious URI/deep-link invocation
37. replayed privileged requests
38. race between preview and execution
39. stale elevation after requested target changed
40. misleading success reporting

---

## 6.2 Explicitly out of scope for application guarantees

Trier Bridge cannot guarantee protection against:

- a compromised Linux kernel
- root-level malware already controlling the host
- malicious firmware
- physical attackers with unrestricted hardware access
- compromised package repositories already trusted by the operating system
- malicious administrators intentionally bypassing the application
- security defects in the underlying Linux distribution outside Trier Bridge's control

These boundaries must be documented honestly.

---

## 6.3 Threat review record

**Current status:** DESIGN REVIEW ONLY. No implementation has been threat-qualified.

Protected boundaries that each require a review:

- UI → backend
- backend → adapter
- adapter → Linux subsystem
- unprivileged → privileged
- Bridge Terminal → typed operation
- package/update → trust
- imported file/config → parser
- system observation → mutation
- preview → commit

High-risk areas requiring a per-capability review before shipping: generic privileged execution, shell injection, path traversal/symlink escape, stale-target mutation, PID/device reuse, package/update trust, network reconfiguration, disk mutation, unsafe IPC/D-Bus, secret leakage, untrusted logs/metadata, installer/uninstaller privilege, plugin/extension authority.

For each shipped high-risk capability record:

- threat
- attack surface
- control
- failure behavior
- test
- evidence
- residual risk

---

# 7. Security Invariants

These invariants are non-negotiable unless explicitly revised before implementation.

## TB-SEC-001 — UI is untrusted

No frontend/UI value is trusted because it came from Trier Bridge itself.

Backend validation remains mandatory.

## TB-SEC-002 — No generic root execution

No public or internal API may expose arbitrary command execution with elevated privilege.

## TB-SEC-003 — No shell interpolation

Untrusted values may never be concatenated into shell command strings.

## TB-SEC-004 — Typed operation authority

All supported Windows-command translations resolve to a typed operation before execution.

## TB-SEC-005 — Explicit elevation

An elevated action must map to a current deliberate user action.

## TB-SEC-006 — No privilege persistence

Elevation ends with the bounded privileged operation unless the Linux security model independently authorizes otherwise.

## TB-SEC-007 — No security downgrade

A failed secure mechanism cannot silently fall back to a weaker mechanism.

## TB-SEC-008 — Unknown is not supported

Unknown platform capability may not be converted into an assumed compatible capability.

## TB-SEC-009 — Scope cannot expand silently

A requested target may not become a broader filesystem, service, package, device, or user scope during execution.

## TB-SEC-010 — Paths are canonicalized and bounded

Mutation paths must be canonicalized and verified against the intended scope.

## TB-SEC-011 — Symlink escape prohibited

Destructive operations must not follow links outside their approved target boundary.

## TB-SEC-012 — User files are not cache

Cleanup logic must distinguish owned cache from user data.

## TB-SEC-013 — Native trust remains authoritative

Package signatures, OS permissions, polkit decisions, MAC policy, and repository trust cannot be bypassed for convenience.

## TB-SEC-014 — No secret in UI state

Credentials, tokens, passphrases, or private keys must not enter frontend state when avoidable.

## TB-SEC-015 — No secret logging

Secrets are prohibited from logs, audit records, crash diagnostics, command previews, and telemetry.

## TB-SEC-016 — Offline means offline

If an offline mode is offered, it must actually prohibit non-local network operations except those explicitly exempted and visible to the user.

## TB-SEC-017 — No silent network access

Background network activity must be tied to a documented feature and user-controlled policy.

## TB-SEC-018 — Update trust is verified

Trier Bridge updates must be signed/verified before installation.

## TB-SEC-019 — Distribution adapters are bounded

Distro-specific logic must live behind identified capability adapters rather than scattered assumptions.

## TB-SEC-020 — Operation results are verified

Where possible, success requires observing the requested postcondition, not only a zero exit code.

## TB-SEC-021 — Stale requests cannot mutate new state

Requests capture target identity/revision and must revalidate before mutation.

## TB-SEC-022 — Privileged APIs are enumerated

Privileged helper operations must be finite, documented, versioned, and schema validated.

## TB-SEC-023 — No arbitrary plugin privilege

Third-party plugins/extensions never inherit Trier Bridge privileged authority automatically.

## TB-SEC-024 — Security-relevant action is attributable

Privileged and destructive actions record actor, operation, target, result, and reason without sensitive content.

## TB-SEC-025 — Recovery is part of security

Interrupted privileged operations must leave either the previous safe state, the intended safe state, or an explicit recoverable degraded state.

## TB-SEC-026 — Diagnostics are data-minimized

Exported diagnostics exclude secrets and unrelated personal information by default.

## TB-SEC-027 — No fabricated equivalence

If a Windows concept has no faithful Linux equivalent, Trier Bridge must say so.

## TB-SEC-028 — Learning mode cannot weaken policy

"Familiar," "Bridge," and "Native" presentation modes change terminology, not authorization.

## TB-SEC-029 — Security controls survive reboot

Operations that claim persistence must be verified through the correct Linux persistence mechanism.

## TB-SEC-030 — Security claims require evidence

Documentation must distinguish design intent, implemented controls, automated evidence, physical evidence, and unverified assumptions.

---

# 8. Privilege Architecture

## 8.1 Default application

Runs unprivileged.

Expected capabilities include:

- reading user-visible process information
- reading allowed system metrics
- displaying authorized logs
- reading network state
- reading device inventory
- inspecting package state
- invoking safe user-level actions
- requesting privileged operations

---

## 8.2 Privileged helper

If a helper is required, it must expose only narrowly defined operations.

Example interface:

```text
RestartService(ServiceIdentity)
StopService(ServiceIdentity)
SetServiceEnabled(ServiceIdentity, Enabled)
TerminateProcess(ProcessIdentity)
MountVolume(VolumeIdentity, Policy)
UnmountVolume(VolumeIdentity)
ApplyNetworkChange(NetworkChangePlan)
InstallApprovedPackage(PackagePlan)
RemoveApprovedPackage(PackagePlan)
```

Forbidden helper interfaces:

```text
RunAsRoot(command: String)
ExecuteShell(script: String)
WriteFileAsRoot(path: String, bytes: Any)
ChmodAnything(path: String, mode: String)
ChownAnything(path: String, owner: String)
```

A general root primitive defeats the architecture.

---

## 8.3 Privileged request lifecycle

```text
User action
   ↓
Capture stable target identity
   ↓
Create typed operation
   ↓
Validate current capability
   ↓
Generate human-readable preview
   ↓
Request authorization
   ↓
Revalidate target/revision
   ↓
Execute bounded operation
   ↓
Verify postcondition
   ↓
Write audit result
   ↓
Return structured status
```

If the target changes between preview and execution, the operation is cancelled or reconfirmed.

---

# 9. Bridge Terminal Security

The Bridge Terminal is one of the highest-risk components.

## 9.1 Modes must be explicit

Supported terminal modes may include:

- **Bridge Mode**
- **Bash Mode**
- **PowerShell Mode**

The current mode must always be visible.

A command entered in Bridge Mode must never silently fall through to Bash or PowerShell.

---

## 9.2 Bridge Mode grammar

Windows compatibility commands are parsed through a strict grammar.

Example:

```text
ipconfig /all
tasklist
taskkill /PID 4271
sc query
shutdown /r
```

Each recognized command maps to documented typed operations.

Unknown flags are rejected.

Extra unparsed input is rejected.

---

## 9.3 No raw shell fallback

If a Windows command is unsupported:

```text
Unsupported compatibility command.
No operation was performed.

Closest Linux concept:
...
```

The product may teach the user the Linux equivalent.

It does not guess and execute.

---

## 9.4 Output safety

Terminal output must be bounded.

Controls include:

- maximum captured bytes
- streaming limits
- cancellation
- timeout
- binary-output rejection/handling
- control-character sanitization for rendering
- safe ANSI parsing if ANSI is supported

A hostile process must not freeze the UI by producing unlimited output.

---

## 9.5 History

Command history must not retain:

- passwords
- tokens
- private keys
- commands explicitly marked sensitive
- privilege-response material

History clearing must be easy and scoped.

---

# 10. Windows Command Compatibility Policy

Commands fall into security classes.

## Class A — Read-only

Examples:

- `ipconfig`
- `systeminfo`
- `tasklist`
- `netstat`
- `whoami`
- `getmac`
- `dir`

Normally no elevation.

## Class B — User-scoped mutation

Examples:

- user-owned file copy/move/delete
- user application process termination

Requires target validation and may require confirmation.

## Class C — Administrative mutation

Examples:

- service start/stop/restart
- package install/remove
- network configuration
- mount policy
- shutdown/reboot

Requires explicit authorization.

## Class D — High-risk/destructive

Examples:

- filesystem formatting
- partition deletion
- recursive permission/ownership changes
- account deletion
- repository trust changes
- firewall policy replacement

These require stronger preview/confirmation and may remain intentionally unsupported in early releases.

## Class E — No faithful Linux equivalent

The product explains the difference and performs no hidden substitution.

---

# 11. PowerShell Security

PowerShell on Linux is a real execution environment and should not be reimplemented unnecessarily.

Rules:

1. Native `pwsh` executes under normal Linux user permissions.
2. Trier-provided compatibility cmdlets call typed Trier operations.
3. Windows-only cmdlets are never destructively approximated.
4. Remote module installation is not automatic.
5. Script execution never inherits privileged helper access automatically.
6. Elevation is operation-specific.
7. secrets are excluded from history/logs.
8. compatibility output clearly indicates when behavior differs from Windows.
9. execution policy differences between Windows PowerShell and PowerShell on Linux are explained rather than simulated deceptively.

---

# 12. Filesystem Security

## 12.1 Read versus mutate

Filesystem browsing and mutation are separate capabilities.

Read permission does not imply write permission.

Write permission does not imply recursive permission.

---

## 12.2 Path validation

Before mutation:

1. normalize path representation
2. identify intended root
3. resolve canonical target where appropriate
4. evaluate symlinks
5. identify mount boundary
6. verify ownership/scope
7. revalidate immediately before mutation

Special files require explicit handling:

- devices
- FIFOs
- sockets
- procfs
- sysfs
- virtual filesystems

---

## 12.3 Recursive operations

Recursive delete/chmod/chown are high-risk.

Trier Bridge must provide:

- explicit target
- estimated scope where possible
- mount-boundary awareness
- symlink policy
- cancellation behavior
- error accounting
- partial-completion reporting

---

## 12.4 Atomic configuration writes

Trier Bridge-owned configuration should use atomic replacement:

```text
write temporary
→ flush
→ validate
→ fsync where required
→ atomic rename/replace
→ verify
```

Do not overwrite a known-good file with an unvalidated partial write.

---

# 13. Process and Task Manager Security

Process information may reveal sensitive command lines or environment data.

Default UI should avoid unnecessary disclosure.

Rules:

- do not display environment variables containing secrets
- redact known credential patterns
- respect Linux process visibility restrictions
- distinguish same-user and other-user processes
- do not elevate merely to display more process information
- process termination captures stable PID plus additional identity when possible to reduce PID-reuse races
- revalidate process identity before sending a signal
- escalating from TERM to KILL requires explicit policy and presentation
- kernel threads/system-critical processes receive stronger warnings or are protected where appropriate

---

# 14. Event Viewer / Journal Security

Logs are untrusted text.

A log entry may contain:

- terminal control characters
- HTML-like content
- malicious URLs
- misleading severity text
- secrets accidentally logged by another application

Trier Bridge must:

- render logs as data, not executable markup
- sanitize control characters
- never interpret log content as commands
- avoid auto-opening URLs
- respect journal permissions
- avoid elevating solely to increase log visibility unless explicitly requested
- redact Trier Bridge-owned secrets at source
- bound query size/time
- support cancellation
- distinguish missing access from "no events"

---

# 15. Services Security

Service administration must use stable service identity.

Actions:

- inspect
- start
- stop
- restart
- enable
- disable

must remain distinct.

Editing a unit/service definition is a different, higher-risk capability.

Rules:

- no user-controlled service name becomes a shell string
- verify the target still exists before mutation
- display dependencies/impact where available
- distinguish service failure from authorization failure
- do not auto-disable a repeatedly failing service
- do not convert "stop" into "disable"
- do not reset service configuration as a recovery shortcut
- show actual post-operation state

---

# 16. Device Manager Security

Hardware metadata is untrusted input.

Trier Bridge should avoid requiring privilege merely to enumerate devices.

Actions that change devices/drivers are separate capabilities.

Early versions should strongly prefer:

- inspection
- troubleshooting
- identification
- linking to native supported mechanisms

over custom driver mutation.

Kernel-module installation/removal is high-risk and must not be hidden behind a casual Windows-like button.

---

# 17. Disk Management Security

Storage management has the highest destructive potential in the GUI.

Read-only inventory should be broadly available.

Operations should be classified.

## Lower-risk

- mount
- unmount
- label where supported
- show filesystem details
- show health/status

## High-risk

- format
- resize
- partition creation
- partition deletion
- filesystem repair
- encryption changes

High-risk operations require:

- explicit device identity
- human-readable before-state
- intended after-state
- mounted/in-use checks
- data-loss warning
- privilege confirmation
- revalidation immediately before commit
- no "best guess" target selection

Trier Bridge must never select a destructive disk target based only on device ordering such as `/dev/sda`.

---

# 18. Network Security

Network operations should prefer supported APIs such as NetworkManager/D-Bus when available rather than editing arbitrary files.

Rules:

- detect actual networking backend
- preserve unknown configurations
- never replace config files globally because one adapter is being edited
- distinguish runtime versus persistent configuration
- verify adapter identity
- validate IP/prefix/gateway/DNS values
- preview connectivity-impacting changes
- provide recovery guidance
- do not disable remote connectivity without warning when Trier Bridge is used remotely
- no certificate-validation bypass
- no silent DNS/proxy modification

---

# 19. Package Management Security

Trier Bridge must use the distribution's native trust system.

It must not create a weaker package-install mechanism simply to provide a consistent UI.

## 19.1 Package plans

Before mutation, construct a package plan containing as available:

- package identity
- requested version
- source/repository
- architecture
- install/remove action
- dependency additions
- dependency removals
- replacements/conflicts
- download size
- disk impact
- signature/trust result
- reboot/restart requirement

The user approves the plan, not an ambiguous package name alone.

---

## 19.2 Repository changes

Adding or changing package repositories is security-sensitive.

Show:

- repository URL
- distribution/release
- signing key/fingerprint where applicable
- trust scope
- packages potentially affected

No repository is added silently.

---

## 19.3 Cross-format package handling

APT, DNF/RPM, Flatpak, Snap, AppImage, and other mechanisms are not interchangeable.

Trier Bridge may provide a unified user experience while preserving:

- package type
- trust model
- update mechanism
- sandbox model
- removal semantics
- system versus user installation scope

The UI must not imply stronger isolation than the package type actually provides.

---

# 20. Authentication, Users, and Groups

User management is security-critical.

Trier Bridge must not store Linux account passwords itself.

Authentication should remain with Linux/PAM/native facilities.

Rules:

- password entry goes only to the required native authorization path
- passwords are not logged
- passwords are not retained
- creating/deleting users requires explicit scope
- group membership changes display the security impact where practical
- administrative groups such as `sudo`/`wheel` receive stronger warnings
- deleting a user and deleting that user's home directory are separate choices
- multi-user visibility follows OS permissions

---

# 21. Secrets and Credential Handling

If Trier Bridge ever stores credentials, tokens, or private keys:

Preferred order:

1. Linux Secret Service / libsecret or appropriate OS-bound secret store
2. another reviewed platform-bound mechanism
3. encrypted local fallback only if explicitly designed and threat-reviewed

Secrets must never appear in:

- frontend state
- URL query strings
- logs
- audit details
- crash reports
- command history
- clipboard automatically
- support bundles

Memory lifetime should be minimized.

---

# 22. IPC / D-Bus / Backend Boundary

Every cross-process or frontend-to-backend call is a trust boundary.

Requirements:

- versioned message schema
- operation allowlist
- bounded input lengths
- enum validation
- path validation
- numeric range checks
- stable identity/revision
- caller authorization where applicable
- replay resistance for privileged requests if the transport permits replay
- structured errors
- no frontend-supplied executable strings

Unknown message types are rejected.

---

# 23. Desktop Integration Security

Trier Bridge may integrate with:

- file managers
- launchers
- context menus
- URI handlers
- drag and drop
- desktop notifications

All external inputs are untrusted.

URI/deep-link handlers must:

- define an explicit scheme
- parse strictly
- prohibit arbitrary command execution
- require confirmation for consequential actions
- validate file paths and origins
- avoid embedding secrets

Drag-and-drop must never execute files automatically.

---

# 24. Update Security

Trier Bridge update behavior must be explicit and cryptographically verifiable.

Required principles:

- signed releases
- checksum verification
- trusted update origin
- anti-rollback policy where appropriate
- atomic update staging
- failure recovery
- version display
- release notes
- no hidden downgrade
- no unsigned fallback

Automatic download and automatic installation are separate user choices.

The application must remain usable offline even if update services are unreachable.

---

# 25. Local-First and Network Policy

Trier Bridge core system-management functionality should not require an internet connection.

Core features such as:

- Task Manager
- Services
- Event Viewer
- Device inventory
- storage inventory
- network status
- Bridge Terminal translation
- "Show Me the Linux Way"

should operate locally.

If future features use the network:

- network purpose must be documented
- destinations must be visible
- data sent must be minimized
- failures must not disable unrelated local features
- TLS validation cannot be bypassed
- telemetry is opt-in if introduced at all

No account should be required merely to use local Trier Bridge functionality.

---

# 26. Audit Architecture

Security-relevant operations should create structured audit events.

Suggested fields:

```text
timestamp
session/user identity
operation ID
operation type
target type
target stable identity
privilege required
authorization result
execution result
verification result
error category
application version
adapter/version
correlation ID
```

Do not include:

- passwords
- tokens
- private keys
- full sensitive command lines
- unrelated file content

For high-assurance modes, an append-only hash chain may be considered, following the established Trier governance pattern.

Audit existence does not prove the underlying operation was correct.

---

# 27. Error Handling

Security errors should be understandable to non-technical users.

Bad:

> EPERM

Better:

> Trier Bridge was not permitted to restart this system service.  
> Nothing was changed.

Then optionally:

> **Show technical details**

Technical detail remains available without replacing the plain-language explanation.

Errors must distinguish:

- permission denied
- unsupported
- unknown
- target disappeared
- target changed
- operation failed
- verification failed
- partial completion
- recovery required

---

# 28. Recovery Security

Recovery is part of the security model.

For consequential changes, define before implementation:

- precondition
- commit boundary
- interruption behavior
- rollback possibility
- recovery artifact
- postcondition verification

A crash during:

- package installation
- network reconfiguration
- service mutation
- storage mutation
- settings update

must not be treated as ordinary success on restart.

Trier Bridge should surface unresolved operations rather than silently repeat destructive actions.

---

# 29. Race and Stale-State Protection

The product frequently shows a state before the user acts.

That state can become stale.

Therefore consequential operations capture:

- target identity
- relevant revision/version
- observed state
- requested operation

Immediately before mutation, the backend revalidates the target.

Examples:

- PID may now belong to another process
- device path may refer to a different removable drive
- service may have been replaced
- package candidate may have changed after metadata refresh
- network interface may have disappeared
- mount point may have changed

Stale state must not mutate a newly different target.

---

# 30. Dependency and Supply-Chain Policy

Every runtime dependency increases attack surface.

Requirements:

- direct dependency justification
- lockfiles committed
- reproducible dependency inventory
- security audit before release
- license/provenance review
- transitive-risk review for security-critical dependencies
- no silent dependency additions
- SBOM generation for release candidates where practical

Severity alone does not prove exploitability, but unresolved serious reachable vulnerabilities block release unless explicitly documented and accepted.

---

# 31. Extension and Plugin Policy

Trier Bridge should not introduce an unrestricted plugin system early.

If extensibility is added later:

- plugins declare capabilities
- privileged capabilities require explicit approval
- plugins do not inherit root access
- plugins do not receive secrets by default
- plugin origin/version is visible
- plugin failure cannot corrupt core Trier Bridge state
- unsigned/untrusted code is clearly labeled
- native executable plugins receive additional review

"Customizable" must never mean "arbitrary code runs with Trier Bridge authority."

---

# 32. Data Minimization

Trier Bridge should collect only the data required to perform the requested system-management function.

It should not create a surveillance database of the user's machine merely because system information is available.

Avoid persistent collection of:

- full process command histories
- unrelated file paths
- browsing history
- document names
- clipboard contents
- shell history
- network payload contents

unless a feature explicitly requires it and the user understands the scope.

---

# 33. Diagnostics and Support Bundles

Support bundles are potentially sensitive.

Default exports must redact or omit:

- usernames where unnecessary
- home-directory details
- IP addresses where unnecessary
- Wi-Fi secrets
- tokens
- repository credentials
- environment secrets
- private keys
- full command histories
- unrelated logs

Before export, present a manifest of included categories.

---

# 34. AppArmor / SELinux / MAC Policy

Mandatory access control is not an obstacle to bypass.

Trier Bridge should detect relevant policy when practical and surface meaningful denial information.

It must not recommend disabling SELinux/AppArmor globally as an ordinary troubleshooting step.

Any required policy integration should be narrowly scoped and documented.

---

# 35. Safe UX for Novice Users

Security UX is part of security architecture.

The application must avoid two extremes:

1. hiding dangerous consequences
2. overwhelming the user until they click through blindly

For consequential operations, answer plainly:

- **What will happen?**
- **What could be affected?**
- **Does this require administrator permission?**
- **Can it be undone?**
- **Will this interrupt applications or networking?**

Advanced technical detail is progressively disclosed.

---

# 36. "Show Me the Linux Way" Security Rule

Educational output is informational only.

The displayed Linux command must correspond to the operation Trier Bridge actually performed or would perform conceptually.

Never show a dangerous oversimplified command merely because it is short.

If the safe implementation uses D-Bus, a library API, or structured system interface instead of a shell command, say so.

Example:

> Trier Bridge used the systemd D-Bus interface.  
> A common terminal equivalent is: `systemctl restart ...`

The teaching layer must not falsify the implementation.

---

# 37. Security Testing Strategy

Security qualification must include positive and negative cases.

## 37.1 Command translation

Test:

- valid commands
- invalid flags
- extra tokens
- quoting
- Unicode
- control characters
- shell metacharacters
- command substitution
- redirection tokens
- path traversal
- extremely long input
- repeated execution
- cancellation

## 37.2 Privilege

Test:

- authorization accepted
- denied
- expired
- cancelled
- helper missing
- caller mismatch
- replayed request
- stale target after authorization
- privilege boundary after completion

## 37.3 Filesystem

Test:

- symlink escape
- mount boundary
- disappearing target
- read-only filesystem
- full disk
- permission loss
- hostile filenames
- interrupted atomic write

## 37.4 Processes

Test:

- PID reuse
- process exits before action
- same-user process
- other-user process
- protected system process
- TERM timeout
- explicit KILL escalation

## 37.5 Services

Test:

- service absent
- masked
- failed
- dependency failure
- auth denied
- state changes during preview
- restart fails after stop
- enable versus start distinction

## 37.6 Packages

Test:

- bad signature
- repo unavailable
- metadata stale
- dependency conflict
- removal cascade
- interrupted transaction
- low disk
- package-manager lock
- unknown package source

## 37.7 Logs

Test:

- hostile ANSI
- HTML/script-like content
- huge logs
- binary content
- restricted journal
- malformed timestamps

## 37.8 Network

Test:

- interface disappears
- DHCP/static transition
- invalid gateway
- DNS failure
- rollback/recovery
- remote-session warning
- NetworkManager unavailable
- alternate backend detected

---

# 38. Security Evidence Model

Every security requirement should eventually have an evidence classification:

- **DESIGN** — documented but not implemented
- **IMPLEMENTED** — code exists
- **UNIT VERIFIED**
- **INTEGRATION VERIFIED**
- **FAILURE VERIFIED**
- **DISTRO VERIFIED**
- **PHYSICAL VERIFIED**
- **RELEASE VERIFIED**
- **NOT APPLICABLE**
- **BLOCKED**
- **UNKNOWN**

Do not collapse these into one "PASS."

This follows the established Trier principle that evidence belongs to the exact claim.

---

# 39. Cross-Distribution Security

"Works on Linux" is too broad to be a security claim.

Support must be expressed as qualified combinations.

Examples:

```text
Ubuntu + systemd + NetworkManager + GNOME
Fedora + systemd + NetworkManager + GNOME
Mint + systemd + NetworkManager + Cinnamon
```

Adapters must expose:

- capability
- implementation route
- required privilege
- known limitations
- tested distribution/version
- fallback state

Unsupported does not mean broken.

Unknown does not mean supported.

---

# 40. Release Security Gate

A release candidate cannot ship merely because it builds.

Before release:

- [ ] all privileged operations enumerated
- [ ] no generic root execution API
- [ ] no shell interpolation with untrusted input
- [ ] IPC schemas reviewed
- [ ] path traversal tests pass
- [ ] symlink tests pass
- [ ] stale-state tests pass
- [ ] privilege denial tests pass
- [ ] package trust tests pass where applicable
- [ ] network certificate validation has no production bypass
- [ ] secrets excluded from logs
- [ ] production debug surfaces disabled or justified
- [ ] dependency audits reviewed
- [ ] SBOM generated/reviewed where supported
- [ ] update signing verified
- [ ] diagnostic export reviewed
- [ ] supported distro matrix reflects actual evidence
- [ ] known limitations documented
- [ ] recovery behavior tested for consequential mutations
- [ ] exact release artifacts hashed
- [ ] security policy and private reporting route present

---

# 41. Vulnerability Disclosure

When Trier Bridge becomes public, the repository should provide private vulnerability reporting.

Preferred route:

**GitHub Private Vulnerability Reporting / Security Advisories**

Reports should include:

- affected version
- distribution/version
- desktop environment when relevant
- reproduction steps
- security impact
- whether privilege is required
- disposable test evidence
- proposed narrow mitigation if known

Do not request real credentials or personal files.

A public issue should not be required for confidential disclosure.

Response commitments should only be published when Doug is prepared to maintain them.

---

# 42. Security Versus Compatibility

Compatibility is not a reason to weaken security.

Trier Bridge must refuse a Windows behavior if reproducing it safely would require an unacceptable Linux security compromise.

Examples:

- running everything as root to reduce prompts
- disabling SELinux
- bypassing package signatures
- accepting invalid TLS certificates
- treating a Windows administrator mental model as permission for unrestricted Linux root operations
- silently executing unknown commands through Bash
- exposing a generic elevated PowerShell session from the GUI

When compatibility and safety conflict:

> **Safety wins, and the user gets a plain-language explanation.**

---

# 43. Architectural Non-Goals

Trier Bridge security architecture does not require:

- inventing a new authentication system
- inventing a new package trust model
- replacing PAM
- replacing polkit
- replacing systemd security
- replacing SELinux/AppArmor
- storing Linux passwords
- implementing a root shell
- intercepting arbitrary terminal commands globally
- modifying the user's existing Bash/PowerShell configuration without explicit consent
- disabling native Linux security to make the Windows analogy easier

---

# 44. Initial MVP Security Scope

The MVP should prove the architecture with a deliberately limited mutation surface.

Recommended first-release security scope:

## Read-mostly capabilities

- System Dashboard
- Task Manager inspection
- Event Viewer/journal inspection
- Services inspection
- Network status
- device inventory
- disk/storage inventory
- installed-app inventory
- Bridge Terminal read-only commands
- "Show Me the Linux Way"

## Carefully bounded mutation

- terminate a user process
- start/stop/restart a service
- enable/disable a service with explicit privilege
- safe user-file operations
- possibly package install/remove only after package-plan architecture is complete

## Intentionally defer

- partition formatting
- partition deletion
- recursive ownership changes
- firewall replacement
- user deletion
- driver/kernel-module mutation
- arbitrary repository modification
- arbitrary root shell
- unrestricted scripting with privileged authority

This creates a small enough security surface to verify rigorously before expansion.

---

# 45. Security North-Star Tests

Before Trier Bridge can claim the core architecture is sound, it should prove at minimum:

### Test A — Windows knowledge without root leakage

A user can enter:

```text
tasklist
ipconfig
sc query
```

and receive useful Linux-backed results without Trier Bridge becoming root.

### Test B — Explicit elevation

A user requests:

```text
sc stop <service>
```

and receives an explicit privilege request tied only to stopping that service.

### Test C — Injection rejection

Inputs such as:

```text
taskkill /PID 1234; rm -rf /
```

are rejected as invalid syntax.

No shell fragment executes.

### Test D — Stale target

A process exits and its PID is reused between preview and confirmation.

Trier Bridge detects the identity change and refuses to kill the replacement process.

### Test E — Security downgrade resistance

A privileged helper or secure API fails.

Trier Bridge reports failure and does not retry using an unrestricted shell.

### Test F — Linux remains authoritative

SELinux/AppArmor/polkit denies an action.

Trier Bridge reports the denial and does not recommend globally disabling the protection as its default fix.

### Test G — Offline survivability

Disconnect the internet.

All core local administration and translation functions continue working.

---

# 46. Product Security Promise

Trier Bridge should be able to state truthfully:

> **Trier Bridge helps you use Linux with concepts you already understand, but it does not weaken Linux to make that familiarity possible.**

And technically:

> **The interface translates intent. The trusted backend validates it. Linux authorizes it. The result is verified.**

That sentence should guide the security architecture throughout the project.

---

# 47. Future Security Documents

As Trier Bridge moves from concept to implementation, this baseline should split into supporting documents rather than becoming an unmanageable monolith.

Recommended future documents:

- `THREAT-MODEL.md`
- `PRIVILEGE-MODEL.md`
- `COMMAND-TRANSLATION.md`
- `DISTRO-ADAPTERS.md`
- `PACKAGE-SECURITY.md`
- `FILESYSTEM-SAFETY.md`
- `UPDATE-TRUST.md`
- `SECURITY-TESTS.md`
- `SECURITY-EVIDENCE.md`
- `RELEASE-SECURITY-CHECKLIST.md`

`SECURITY.md` remains the governing security policy and navigation point.

---

# 48. Current Status

This document defines architecture and intent only.

No control should be described publicly as implemented, verified, hardened, certified, or secure until corresponding code and evidence exist.

**Current evidence state: DESIGN ONLY.**

---

## Final Rule

> **Familiarity may reduce cognitive load. It may never reduce security.**

**Trier Bridge — Your Windows knowledge. Linux underneath.**
