# Trier Bridge Privilege Model

**Task:** SCOPE-02  
**Status:** Design. No implementation exists.  
**Governing:** `SECURITY.md` sections 4.5, 8, 22; TB-SEC-002, 005, 006, 013, 020, 021, 022; TB-INV-106 to 113, 121, 129, 188  
**Evidence base:** polkit action defaults and system-bus services observed on `tb-ubuntu-desktop-2404`, 2026-09-20 (`RESEARCH.md` section 4)

> Observed on systemd 255 / polkit 124 (entry IMP-06.07): a prompt the user dismisses comes back from systemd as the same access-denied error as a refusal, so service control reports both as "Linux did not grant permission for this change" and changes nothing. The CANCELLED state is used where a backend reports dismissal distinctly.

## 1. Design decision: no privileged helper in the first release

Every mutation in the first-release scope already has a Linux system service that owns the operation and asks polkit for authorization. Trier Bridge calls those services as the signed-in user; polkit and the desktop's own authentication agent handle the prompt; the service performs the change under its own authority. Trier Bridge never runs as root and ships no component that does.

| Operation family | System service (system bus) | polkit action (observed default for an active local user) |
|---|---|---|
| Service start / stop / restart / reload / enable / disable | `org.freedesktop.systemd1` | `org.freedesktop.systemd1.manage-units` — auth_admin_keep |
| Network profile changes | `org.freedesktop.NetworkManager` | `org.freedesktop.NetworkManager.settings.modify.system` — auth_admin_keep (per-user profiles: `settings.modify.own`) |
| Mount / unmount removable media | `org.freedesktop.UDisks2` | `org.freedesktop.udisks2.filesystem-mount` — yes (no prompt); other udisks actions have their own defaults |
| Package install / remove / update | `org.freedesktop.PackageKit` | `package-install` — auth_admin_keep; `package-remove` — auth_admin |
| Reboot / power off | `org.freedesktop.login1` | `org.freedesktop.login1.reboot` — yes |
| Hostname, time zone, locale | `hostname1`, `timedate1`, `locale1` | their own actions (auth_admin) |

Operations that need no privilege at all: terminating the user's own processes (signals from the user's process), reading `/proc` (visible to the user; `hidepid` is off on the target), reading the journal (user `tb` is in `adm`, so the system journal is readable; users outside `adm` see their own entries and the UI shows "restricted", TB-INV-145), reading device, storage, and network state over D-Bus properties, and all per-user settings.

Consequences:

- DEC-018 (e) is satisfied in the strongest way: there is no hidden privileged component because there is no privileged component.
- Authorization scope is whatever polkit grants for that action on that machine. Trier Bridge never ships polkit rules and never asks for a broader action than the one the operation needs (TB-INV-110, TB-INV-112).
- If a system service is absent or the action is denied, the operation is Unsupported or Denied, never re-attempted through another path (TB-SEC-007, TB-INV-126).

## 2. Where a helper would become necessary

A privileged helper is required only for an operation that no polkit-mediated service owns. Known candidates, all outside the first release:

- editing files under `/etc` that have no D-Bus owner (deferred by design; TB-INV-177 prefers structured APIs);
- kernel module or driver changes (deferred, TB-INV-174);
- reading another user's process environment or private files (never; TB-INV-132, TB-INV-214);
- disk formatting and partitioning beyond what udisks2 exposes (deferred; udisks2 already covers most, with its own actions).

If one is ever approved, it is a separate, named D-Bus system service (`org.triertech.TrierBridge.Helper1` or similar) with:

- a systemd service unit activated on demand by D-Bus and exiting after a short idle period (TB-INV-188);
- its own polkit `.policy` file with one action per operation, defaults no weaker than the closest native action;
- a finite, versioned, schema-validated method list; no method takes a command string, a free path, or a mode/owner triple (TB-SEC-002, TB-INV-107);
- target identity captured by the caller and revalidated by the helper before mutation (TB-SEC-021);
- structured results and an audit record per call (TB-INV-129);
- fault-injection tests for denial, cancel, expiry, caller mismatch, replay, and stale target (SECURITY section 37.2).

Adding such a helper is a scope change requiring owner approval (CONTRIBUTING, "new privileged operation").

## 3. Authorization semantics Trier Bridge relies on

- **Interactive prompts are polkit's.** The desktop authentication agent (GNOME's `polkitd` agent on the target) shows the dialog. Trier Bridge passes the interaction flag only for operations the user just initiated; background refreshes call read-only methods that never prompt (TB-INV-109).
- **`auth_admin_keep` caching is polkit's policy, not Trier Bridge's.** Trier Bridge keeps no credentials, no tokens, and no memory of a prior grant (TB-INV-111, TB-INV-124). If polkit re-prompts, the user sees the prompt.
- **Remote and non-local sessions** get whatever polkit's "inactive/any" defaults say, which is usually stricter. The UI shows Requires authorization rather than guessing (TB-INV-023).
- **Denial is a result, not an error to route around.** Denied, Cancelled, and Expired are distinct terminal states (`STATE-AND-PERSISTENCE.md` section 3).

## 4. Operation lifecycle on D-Bus

```text
observe            read properties and objects; capture stable identity + revision
preview            human-readable plan from the typed operation
revalidate         re-read the target by identity immediately before the call
execute            one D-Bus method on the owning service (polkit prompts if needed)
verify             re-read the postcondition (ActiveState, connection state, mount point, package state)
audit              operation ID, target identity, result, verification state, no secrets
```

Stable identities on the first target:

| Target | Identity captured | Revalidation |
|---|---|---|
| systemd unit | unit name plus object path plus `LoadState`/`ActiveState` generation at preview | `GetUnit` again; abort if the unit vanished or was reloaded incompatibly (TB-INV-053) |
| NetworkManager connection | connection UUID plus device interface plus `Version` of the settings object | re-read by UUID; stale `Version` requires reconfirmation (TB-INV-052) |
| udisks block device | object path plus `Id`, `Serial`/`WWN` where present, `Size`, filesystem UUID | re-read by identity, not by `/dev/sdX` (TB-INV-051, TB-INV-158) |
| package | PackageKit package ID (name;version;arch;repo) from the plan | resolve again; a changed candidate reopens the preview (TB-INV-054) |
| process | PID plus start time from `/proc/PID/stat`, executable path, UID | re-read; a changed start time means a reused PID, abort (TB-INV-050) |

Process termination sends SIGTERM first; SIGKILL is a separate, explicit action (TB-INV-134). Processes of other users, kernel threads, and PID 1 are non-actionable in the UI (TB-INV-136).

## 5. Trust boundaries

```text
Bridge window UI  --(typed intent, untrusted)-->  operation core (validates, plans)
operation core    --(D-Bus method, user creds)-->  system service  --(polkit)-->  authorization
system service    --(its own authority)-------->  Linux
operation core    <--(structured result)--------  system service
```

The UI never constructs D-Bus calls itself; it submits typed intent to the core (TB-INV-114, TB-INV-116). Whether the core is in-process or a session D-Bus service is decided in SCOPE-10; either way it runs as the user.

## 6. Test obligations (feeds `TEST-STRATEGY.md`)

Run on the real VM, no synthetic fixtures:

- authorization granted, denied, cancelled, and timed out for each action family;
- `auth_admin_keep` expiry observed and re-prompt handled;
- system service stopped or restarted mid-operation (NetworkManager restart, PackageKit exit);
- target replaced between preview and execute (unit reloaded, connection profile edited outside, USB device reinserted, PID reused);
- restart that stops but fails to start is reported as Partial (TB-INV-143);
- no `sudo`, `pkexec`, or root process ever appears in the process list during any operation.

## 7. Inputs to stack selection

The chosen stack must have a mature D-Bus client that supports proxies, properties, signals, and the polkit interaction flag on the system bus, and must be able to read `/proc` without shelling out. Every candidate under consideration meets this through GLib/GDBus bindings (Python via `python3-gi`, which is preinstalled) or a native library (for example `zbus` in Rust).

## 8. What is implemented (2026-09-21)

The schema of privileged operations is finite and small. Every operation is an `Operation` with a `kind` drawn from a fixed vocabulary (`trier_bridge/core/operations.py`); the only kinds that can require privilege are `service.start`, `service.stop`, `service.restart`, `service.enable`, and `service.disable`, each on one named systemd unit identified by name, object path, and fragment path. They are executed by one method call on `org.freedesktop.systemd1` over the system bus with `ALLOW_INTERACTIVE_AUTHORIZATION`. polkit decides per call and binds any grant to the calling process, its session, and the `org.freedesktop.systemd1.manage-units` action. Trier Bridge never holds a credential, never caches an authorization, never runs a helper, never calls `sudo`, and never runs a shell. The same plan is used whether the request came from the Services page or from `sc stop <name>` in the Bridge Terminal, and it is shown to the user and confirmed before the call is made (TB-INV-094, TB-INV-104, TB-INV-109, TB-INV-110).

Every other mutation (end task, file operations, default apps, integrations) is class B: it changes only what the signed-in user already owns, needs no privilege, and is confirmed and journaled the same way. Evidence: `docs/VALIDATION.md` entries IMP-06.04, IMP-06.05, IMP-06.07, IMP-06.08.
