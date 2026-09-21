# Trier Bridge Test Strategy

**Task:** SCOPE-05  
**Status:** Design. No test has been run against product code because no product code exists.  
**Governing:** `VALIDATION.md` (evidence states and records), `SECURITY.md` section 37, TB-INV-228 to 233, DEC-016, DEC-017 (rejected: no WSL)  
**Fixture policy:** no synthetic fixtures, accepted as DEC-021 on 2026-09-21 under owner delegation.

## 1. Principles

1. **The oracle is a real system.** Tests run against real Linux services in the project VM. Nothing is simulated: no fake D-Bus services, no stubbed adapters, no recorded responses, no mocked filesystems. This is the project's global no-mock rule applied to testing.
2. **Fixtures are real objects created for the test.** A dummy systemd unit, a loopback filesystem image, a NetworkManager dummy interface, or a locally built test `.deb` is a real thing the real service manages. Creating such objects inside the VM is allowed; pretending a service answered is not.
3. **If the owner ever approves a synthetic fixture,** it is named in this document with the single scenario it serves and the reason no real object can produce that scenario. None exist today.
4. **Evidence is per environment.** A result belongs to the exact VM profile and checkpoint it ran on (`VALIDATION.md` section 2). One VM proves one profile.
5. **Failure paths are first-class.** Every mutation feature ships with denial, cancel, missing-backend, stale-target, interruption, and partial-result tests (TB-INV-229).

## 2. Environments

| Environment | Use | Evidence level reachable |
|---|---|---|
| `tb-ubuntu-desktop-2404` (Hyper-V, Ubuntu 24.04.5, Wayland GNOME 46) restored to `clean-install` before each qualification run | everything for the first target | UNIT, INTEGRATION, FAILURE, DISTRO, DESKTOP, ACCESSIBILITY (with Orca), NOVICE (with a person at the console) |
| Additional `tb-` VMs per derivative or desktop (created by the same script with a different ISO) | derivative and desktop matrix (ARC-09/10) | DISTRO, DESKTOP |
| Owner-authorized physical hardware | USB, printers, Bluetooth, real GPU | PHYSICAL |
| Developer host (Windows) | pure-logic unit tests only, tooling | UNIT |

WSL is not used (DEC-017 rejected). The SSH session into the VM is not a desktop session; anything about the desktop runs in the console Wayland session and says so (TB-INV-023).

## 3. Test layers

### 3.1 Unit tests (pure logic)

Parser and grammar, typed operation schema validation, state machines, path normalization, identity comparison, result-to-message mapping, concept catalog loading. No system access. Inputs are literal values; no mocks are needed because nothing external is involved. These run on any machine.

### 3.2 Integration tests, read-only

Against the VM's live services: capability discovery reports the real backends; process, service, journal, network, storage, device, and package inventories match what `systemctl`, `nmcli`, `udisksctl`, `journalctl`, and `apt` report for the same moment. Assertions compare two real observations, not an observation to a canned answer.

### 3.3 Mutation tests with real test objects

| Feature | Real object created in the VM | Verified postcondition |
|---|---|---|
| service start/stop/restart/enable/disable | a user-visible `tb-test.service` unit installed for the test (a sleep process) | `ActiveState`, `UnitFileState` re-read from systemd |
| process terminate | a child process the test started | process gone, PID reuse detected when the test deliberately reuses one |
| mount/unmount | a loopback image with a real filesystem attached through udisks2 (`loop-setup`) | mount point present/absent, identity checked |
| network profile edit | a NetworkManager `dummy` device and a throwaway connection profile | connection state and settings `Version` |
| package install/remove | a tiny locally built `.deb` served from a file-based apt source inside the VM | PackageKit resolves it; dpkg state re-read |
| default application change | a per-user `mimeapps.list` change for a test MIME type | `xdg-mime query default` |

Each mutation test also runs its negative cases: polkit denial (cancel the prompt), backend stopped mid-operation, target replaced between preview and execute, and interruption (kill the app between commit and verify), each ending in the exact expected state (Denied, Failed, Partial, OutcomeUnknown, RecoveryRequired).

### 3.4 Fault injection

Only inside the VM, from a checkpoint, never on the host (TB-INV-230):

- disk full: a small loopback filesystem filled with `fallocate`, state directory pointed at it;
- read-only filesystem: remount the loopback read-only;
- permission loss: `chmod` on the state directory during a write;
- backend restart: `systemctl restart NetworkManager` during a network preview;
- session events: lock, log out, suspend/resume where the hypervisor allows;
- hostile text: file names with control characters, RTL marks, emoji, and shell metacharacters, created for real in a test directory;
- oversized output: a process that never stops writing, started by the test;
- clock change inside the guest during a timeout.

### 3.5 Security tests

The whole of `SECURITY.md` section 37: injection strings into the Bridge Terminal, path traversal and symlink escape in a test tree, stale targets, privilege boundary (no root process ever appears), secret exclusion from logs and history, and the seven North-Star tests of section 45.

### 3.6 Acceptance and usability

The 30 cases in `VALIDATION.md` section 6, performed by a person on the console session, recorded with steps and observations. Accessibility runs use Orca, large text, high contrast, and keyboard-only, on the same session.

### 3.7 Package tests

Install, upgrade, and remove from `clean-install`, with a file-system diff and a check that no process, unit, autostart, or `/etc` change appeared (`PACKAGING.md` section 6).

## 4. Running tests in the VM

Until the repository lives in the guest, the tree is pushed with `git archive HEAD` over SSH and run there; results are copied back through `tb-pad` or `scp`. Once the stack is chosen, TOOL-06 adds result normalization so each run becomes a `VALIDATION.md` entry with candidate revision, checkpoint name, and environment profile filled in automatically.

Discipline for a qualification run:

1. `Restore-VMCheckpoint clean-install` (host, elevated or Hyper-V Administrators).
2. Push the exact candidate revision; record its hash.
3. Run the selected layers; capture logs.
4. Record the entry; classify with the `VALIDATION.md` vocabulary; never write PASS.
5. Restore the checkpoint again before the next candidate.

## 5. Mapping to invariants

Every `TB-INV-###` has a default test identity `TB-T###` (INVARIANTS.md section 2). ARC-14 freezes the planned matrix: which layer covers each invariant, on which environment, with which real object. Until then, the invariant index tool (`tb inv`) reports which invariants no test references, so coverage gaps stay visible rather than assumed.

## 6. What this strategy refuses

- a green unit suite as proof of Linux behavior;
- a mock D-Bus service standing in for systemd, NetworkManager, udisks2, or PackageKit;
- tests that need root on the developer host;
- destructive tests on any machine that is not a `tb-` VM restored from a checkpoint;
- reusing one distro's results for another (TB-INV-231).
