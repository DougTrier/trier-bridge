# Trier Bridge Test Environments

Project-owned Linux environment for tool, unit, and qualification work; kept or removed at owner discretion. Governing rules: `docs/DECISIONS.md` DEC-016 (Ubuntu 24.04 LTS first), DEC-017 (rejected: WSL is not used), and `AGENTS.md` section 15. Nothing here touches any VM that does not carry the `tb-` prefix.

## Environment profile

| Profile | Use it for | Cannot prove |
|---|---|---|
| Hyper-V Ubuntu Desktop 24.04 (`tb-ubuntu-desktop-2404`) | tools, unit tests, Bridge Terminal parser, capability discovery, GNOME desktop integration, NetworkManager, udisks, polkit prompts, package flows, usability runs | physical hardware behavior (USB, printers, Bluetooth, real GPU); other desktops and distros until each has its own VM |

Evidence from this profile is recorded with the profile named, per `docs/VALIDATION.md`. WSL is deliberately not used (DEC-017 rejected): it has no desktop session, NetworkManager, udisks, or polkit agent and would prove the wrong things.

Run the tools inside the VM once it is up (paths assume the repo is shared or cloned into the guest):

```bash
python3 tools/tb.py all
```

## Hyper-V desktop VM

Files:

- `New-TbDesktopVm.ps1` creates the VM. Elevated PowerShell required.
- `Remove-TbDesktopVm.ps1` turns it off, unregisters it, and deletes its folder. Elevated PowerShell required.
- `tb-pad.py` / `tb-pad.cmd` shared notepad and file drop between host and VM (see below).
- `autoinstall/user-data`, `autoinstall/meta-data` are the unattended-install answers. They are copied onto a 64 MB seed disk labeled `CIDATA`, which the Ubuntu installer reads as a cloud-init NoCloud datasource.

Storage: `G:\tb-vms\iso\` holds the ISO and `SHA256SUMS`; `G:\tb-vms\<vm-name>\` holds the disks. Nothing is placed in the Hyper-V default path on C:.

Create and start:

```bash
powershell -ExecutionPolicy Bypass -File "G:\0001 Trier Bridge\tools\env\New-TbDesktopVm.ps1" -Start
```

Defaults: Generation 2, 4 vCPU, 8 GB dynamic memory (4 to 12), 64 GB dynamic disk, Default Switch, Secure Boot with the Microsoft UEFI Certificate Authority template, manual checkpoints allowed but automatic checkpoints off, no automatic start on host boot. All are parameters.

What the script verifies before creating anything: name has the `tb-` prefix, no VM or VHDX of that name exists, the switch exists, the seed files exist, and the ISO SHA256 matches `SHA256SUMS` when that file sits beside the ISO. A hash mismatch aborts.

Install flow: open the console with `vmconnect.exe localhost tb-ubuntu-desktop-2404`. The installer detects the autoinstall data and asks once whether to proceed; answer yes. Installation then runs unattended, reboots, and lands on the GNOME login screen.

Baseline checkpoint (recommended, elevated PowerShell, after the first login and before any Trier Bridge work):

```bash
Checkpoint-VM -Name tb-ubuntu-desktop-2404 -SnapshotName clean-install
```

Restore it between qualification runs with `Restore-VMCheckpoint -VMName tb-ubuntu-desktop-2404 -Name clean-install -Confirm:$false` so every evidence run starts from the same known state. Checkpoints apply only to this `tb-` VM; project rules forbid checkpointing any other VM.

Lifetime: the VM is owned by the project but the owner may keep it after Trier Bridge work for other builds. Removal is at owner discretion; the remove script exists for when it is wanted.

Guest account, test-only and documented on purpose: user `tb`, password `trierbridge`, hostname `tb-ubuntu-desktop`, timezone America/Chicago. The `user-data` file carries only a SHA-512 crypt hash of that password, which is why the secret-literal term rule excludes `tools/env/autoinstall/`.

Remove:

```bash
powershell -ExecutionPolicy Bypass -File "G:\0001 Trier Bridge\tools\env\Remove-TbDesktopVm.ps1"
```

The ISO folder is kept for reuse; delete it by hand if no longer wanted.

## Shared notepad and file drop (tb-pad)

Hyper-V has no clipboard for Linux guests, so `tb-pad.py` serves a small page reachable from both the host and the VM. No guest changes, no RDP, no sudo.

Start it on the host, which also opens the page (closing the console window or Ctrl+C stops it):

```bash
tools\env\tb-pad --open
```

The Windows desktop folder `Trier Bridge` holds a shortcut that does exactly that, plus shortcuts for the VM console and the project. The Ubuntu desktop has a `tb-pad` launcher that opens the same page; it finds the host through the VM's default gateway, so it keeps working if the switch subnet changes after a host reboot.

The server binds only to the host's address on the Default Switch (read from `ipconfig`, normally `172.20.240.1`), so nothing off that switch can reach it, and it has no login by design. Page: textarea, Save, Ctrl+S, `raw`, `files`.

From a shell (host has `curl`; Ubuntu Desktop ships `wget`, not `curl`):

| Action | Host (curl) | VM (wget) |
|---|---|---|
| read the note | `curl -s http://172.20.240.1:8000/text` | `wget -qO- http://172.20.240.1:8000/text` |
| run the note as a script | | `wget -qO- http://172.20.240.1:8000/text \| sh` |
| replace the note from a file | `curl --data-binary @f http://172.20.240.1:8000/text` | `wget -qO- --post-file=f http://172.20.240.1:8000/text` |
| upload a file | `curl -T f http://172.20.240.1:8000/files/f` | `wget -qO- --method=PUT --body-file=f http://172.20.240.1:8000/files/f` |
| download a file | `curl -O http://172.20.240.1:8000/files/f` | `wget http://172.20.240.1:8000/files/f` |
| list files | open `/files/` | open `/files/` |

State (the note and dropped files) lives under `reports/local/pad/`, which is gitignored so pasted commands and files never enter history; `--state DIR` keeps it elsewhere. Other options: `--port`, `--peer`, `--bind`, `--allow-any`. File names are restricted to a safe character set, path escapes are rejected, uploads are capped at 64 MB, and chunked uploads (piped `curl -T -`) are accepted.

## Guest state beyond the clean-install checkpoint (2026-09-21)

Owner-approved for this test VM: passwordless sudo for `tb` (`/etc/sudoers.d/tb`). Research additions: `python3-nautilus`, `powershell` snap, a per-user search-provider prototype (`~/.local/{bin/tb-search-provider,share/dbus-1/services,share/gnome-shell/search-providers,share/applications}`), a per-user Nautilus extension prototype, and the `tb-pad` launcher. All are reversible per user; take a new checkpoint (for example `research-baseline`) once they are wanted as the new starting point, or restore `clean-install` to drop them.

## Evidence

Each create and remove writes a JSON record to `reports/local/env-<name>*.json` with the parameters and ISO hash state. Copy the relevant facts into the environment-profile field of any `docs/VALIDATION.md` evidence entry that used the VM.

## Not done by these scripts

- No virtual switch is created or altered. The VM uses the existing Default Switch (NAT).
- No Windows optional feature is enabled or disabled.
- No other VM is enumerated, started, stopped, exported, or checkpointed.
- No in-guest changes beyond the autoinstall answers. Trier Bridge itself is installed and tested by later foundation work.
