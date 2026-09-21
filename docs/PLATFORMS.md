# Trier Bridge Platforms, Capability Discovery, and Adapters

**Status:** Design contract. No distro/desktop combination is qualified.

## 1. Rule

There is no single "Linux" target.

Support is qualified by the combination of operating environment and the feature being tested.

## 2. Environment identity

Track as applicable:

- distribution
- distribution version
- derivative/base family
- CPU architecture
- kernel
- desktop environment
- display protocol (Wayland/X11/headless)
- init/service manager
- network backend
- package backends
- storage service/backend
- authorization mechanism
- session type
- Trier Bridge package format

## 3. Target families

First-release qualification target (DEC-016): **Ubuntu 24.04 LTS**.

Next candidates, in the order the adapters carry over; each needs its own evidence before any claim:

- Ubuntu
- Linux Mint
- Debian
- Fedora
- Zorin OS
- AnduinOS

## 4. Support state

Each feature/environment combination is one of:

- `QUALIFIED`
- `PARTIAL`
- `UNSUPPORTED`
- `UNKNOWN`
- `BLOCKED`

## 5. Generic fallback

Unknown distributions should still receive safe capabilities that can be established from stable cross-distro mechanisms.

Generic fallback prefers:

- read-only discovery
- user-level functions
- native standards
- no destructive mutation

## 6. Capability discovery

### Goal

Discover what the current machine can actually do without mutating it.

### Required discovery areas

- distro and version
- architecture
- desktop/session
- init/service manager
- network backend
- package systems
- authorization mechanism
- journaling/log source
- storage integration
- printers
- Bluetooth
- display APIs
- optional PowerShell availability

### Rules

- Discovery is side-effect free.
- Branding is not capability.
- Binary presence alone is not support.
- A successful probe does not prove every operation.
- Capability results expire or invalidate when relevant backends restart/change.
- Unknown remains Unknown.

### Capability record

Each discovered capability includes:

```text
capability
state
backend
backend version if relevant
evidence source
freshness
read operations
mutation operations
required privilege
known limitations
```

## 7. Platform adapters

Adapters isolate Linux implementation diversity from the Trier Bridge domain model.

### Candidate adapter families

- process inventory/control
- service management
- journal/log access
- network management
- storage/mount management
- package inventory/mutation
- device discovery
- desktop integration
- printing
- Bluetooth
- display configuration
- user/session information
- authorization
- power/session operations

### Adapter contract

Every adapter declares:

- identity
- supported environments/versions
- discovery method
- operations supported
- operations unsupported
- privilege requirements (read, preview, and mutate separately)
- target identity rules
- timeouts/cancellation
- result types
- stale-state behavior
- recovery behavior
- tests

### Rule

No adapter exposes arbitrary command execution to the domain layer.

If the system cannot establish a qualified route, the feature remains unavailable or read-only.

## 8. Hardware and environment profiles

Profiles help qualify behavior; they are not allowlists.

Profile fields:

- CPU architecture
- RAM
- GPU/vendor/driver if observable
- display count
- display protocol
- input devices
- storage topology
- removable storage
- network adapters
- Bluetooth
- printer/scanner availability
- distro/version
- desktop environment
- service manager
- network backend
- package systems
- authorization mechanism

Rules:

- Unknown hardware must still receive safe generic behavior.
- User choices outrank catalog suggestions.
- No profile may be used to justify unsupported privileged behavior.

## 9. Release rule

A release note must never say simply "supports Linux" unless the project intentionally defines that phrase and links to the exact tested matrix.

Prefer:

> Service inspection and bounded service control verified on Ubuntu 26.04 / GNOME / systemd under native package build.
