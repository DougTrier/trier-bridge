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

## 7. Security and failure regression set (IMP-06.08)

The regression set is the whole automated suite (`python3 tools/dev.py all` on the host and in the VM, then `TRIER_BRIDGE_TEST_PASSWORD=<account password> python3 -m pytest tests/integration -m integration` in the VM) plus the manual probes named in `docs/VALIDATION.md`. This table maps `docs/SECURITY.md` section 37 and its Tests A–D to what covers them today; a gap is a gap, not a pass.

| SECURITY item | Covered by | State |
|---|---|---|
| 37.1 valid commands, invalid flags, extra tokens, quoting, Unicode, control characters, shell metacharacters, command substitution, redirection, long input | `tests/unit/test_grammar.py`, `tests/unit/test_cmdlets.py` | covered |
| 37.1 path traversal | `tests/integration/test_bridge_vm.py::test_type_and_dir_stay_inside_real_paths`, `test_file_operations.py::test_hostile_filenames_are_data_not_syntax` (`del ../../etc/passwd` fails as not found in the working folder; no traversal is interpreted) | covered |
| 37.1 repeated execution, cancellation | every plan is a fresh identity check; dialog Cancel paths in the terminal are exercised by hand (entries IMP-03.03, IMP-06.04) | partly manual |
| 37.2 authorization accepted, denied, cancelled, stale target after authorization, privilege boundary after completion | `tests/integration/test_authorization_vm.py` (granted, dismissed, Test B), `test_services_vm.py` (denied without an agent, stale unit), euid checked after grant | covered; dismissed reports as denied on systemd 255 |
| 37.2 expired, helper missing, caller mismatch, replayed request | no privileged helper exists (docs/PRIVILEGE-MODEL.md); polkit's own cache and caller binding are Linux's, not reimplemented | not applicable / not testable from the product |
| 37.3 symlink escape, mount boundary | not covered: file operations act on the path given and never recurse; a symlink is trashed as a link. Add when a recursive operation exists | gap (bounded) |
| 37.3 disappearing target, read-only filesystem, full disk, permission loss, interrupted atomic write | `test_file_operations.py::test_identity_change_between_plan_and_execute_cancels`, `tests/integration/test_persistence_faults_vm.py` (loopback ext4: disk full, read-only, permission loss, kill mid-write) | covered |
| 37.3 hostile filenames | `test_file_operations.py::test_hostile_filenames_are_data_not_syntax` | covered |
| 37.4 PID reuse, exits before action, same-user, other-user, protected, TERM timeout, KILL escalation | `tests/integration/test_terminate_vm.py`, `tests/unit/test_processes.py` | covered |
| 37.5 service absent, auth denied, state changes during preview, restart fails after stop, enable versus start | `tests/integration/test_services_vm.py`, `test_authorization_vm.py`; the PARTIAL result shape is unit-level (`tests/unit/test_operations.py::test_partial_result_must_enumerate`); restart-fails-after-stop is not provoked live | covered except live PARTIAL |
| 37.5 masked, failed, dependency failure | listing shows masked and failed units; mutation on them refused (static/masked enable UNSUPPORTED). Dependency failure not provoked | partly |
| 37.6 packages | no package mutation exists (IMP-06.06 not started); read-only provenance only | not applicable yet |
| 37.7 hostile ANSI, HTML/script-like content, binary content, malformed timestamps, restricted journal | `trier_bridge/system/journal.py` strips escapes and control characters (`tests/unit/test_journal.py::test_sanitize_strips_ansi_and_control_but_keeps_text`); Event Viewer renders text only; restricted journal reported as such (entry IMP-04.03) | covered |
| 37.7 huge logs | bounded reads (entry IMP-04.03) | covered |
| 37.8 network | read-only network view only; no network mutation exists (IMP-06.06) | not applicable yet |
| Test A (Windows knowledge without root) | `test_bridge_vm.py::test_north_star_a_windows_commands_without_root` | covered |
| Test B (explicit elevation for one service) | `test_authorization_vm.py::test_security_test_b_sc_stop_asks_linux_for_this_one_action` | covered |
| Test C (injection rejection) | `test_bridge_vm.py::test_north_star_c_injection_is_rejected_and_nothing_runs` | covered |
| Test D (stale target) | `test_terminate_vm.py::test_stale_identity_cancels_instead_of_killing_a_replacement` | covered |

Every future mutation adds its rows here before its ledger item closes.
