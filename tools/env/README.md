# Trier Bridge Test Environments

Disposable Linux environments for tool, unit, and qualification work. Governing rules: `docs/DECISIONS.md` DEC-016/DEC-017 (proposed) and `AGENTS.md` section 15. Nothing here touches any VM or WSL distro that does not carry the `tb-` prefix.

## Environment profiles

| Profile | Use it for | Cannot prove |
|---|---|---|
| WSL2 Ubuntu 24.04 (`tb-ubuntu-2404`) | tools, unit tests, Bridge Terminal parser, capability discovery negative cases | desktop, NetworkManager, udisks, polkit, Wayland/X11 (TB-INV-023) |
| Hyper-V Ubuntu Desktop 24.04 (`tb-ubuntu-desktop-2404`) | GNOME desktop integration, NetworkManager, udisks, polkit prompts, package flows, usability runs | physical hardware behavior (USB, printers, Bluetooth, real GPU) |

Evidence from either profile is recorded with the profile named, per `docs/VALIDATION.md`.

## WSL2 instance

Owner-run creation (WSL 2.6.3 is installed):

```bash
wsl --install -d Ubuntu-24.04 --name tb-ubuntu-2404 --no-launch
```

Run the tools inside it:

```bash
wsl -d tb-ubuntu-2404 -- python3 "/mnt/g/0001 Trier Bridge/tools/tb.py" all
```

Remove:

```bash
wsl --unregister tb-ubuntu-2404
```

## Hyper-V desktop VM

Files:

- `New-TbDesktopVm.ps1` creates the VM. Elevated PowerShell required.
- `Remove-TbDesktopVm.ps1` turns it off, unregisters it, and deletes its folder. Elevated PowerShell required.
- `autoinstall/user-data`, `autoinstall/meta-data` are the unattended-install answers. They are copied onto a 64 MB seed disk labeled `CIDATA`, which the Ubuntu installer reads as a cloud-init NoCloud datasource.

Storage: `G:\tb-vms\iso\` holds the ISO and `SHA256SUMS`; `G:\tb-vms\<vm-name>\` holds the disks. Nothing is placed in the Hyper-V default path on C:.

Create and start:

```bash
powershell -ExecutionPolicy Bypass -File "G:\0001 Trier Bridge\tools\env\New-TbDesktopVm.ps1" -Start
```

Defaults: Generation 2, 4 vCPU, 8 GB dynamic memory (4 to 12), 64 GB dynamic disk, Default Switch, Secure Boot with the Microsoft UEFI Certificate Authority template, checkpoints disabled, no automatic start on host boot. All are parameters.

What the script verifies before creating anything: name has the `tb-` prefix, no VM or VHDX of that name exists, the switch exists, the seed files exist, and the ISO SHA256 matches `SHA256SUMS` when that file sits beside the ISO. A hash mismatch aborts.

Install flow: open the console with `vmconnect.exe localhost tb-ubuntu-desktop-2404`. The installer detects the autoinstall data and asks once whether to proceed; answer yes. Installation then runs unattended, reboots, and lands on the GNOME login screen.

Guest account, test-only and documented on purpose: user `tb`, password `trierbridge`, hostname `tb-ubuntu-desktop`, timezone America/Chicago. The `user-data` file carries only a SHA-512 crypt hash of that password, which is why the secret-literal term rule excludes `tools/env/autoinstall/`.

Remove:

```bash
powershell -ExecutionPolicy Bypass -File "G:\0001 Trier Bridge\tools\env\Remove-TbDesktopVm.ps1"
```

The ISO folder is kept for reuse; delete it by hand if no longer wanted.

## Evidence

Each create and remove writes a JSON record to `reports/local/env-<name>*.json` with the parameters and ISO hash state. Copy the relevant facts into the environment-profile field of any `docs/VALIDATION.md` evidence entry that used the VM.

## Not done by these scripts

- No virtual switch is created or altered. The VM uses the existing Default Switch (NAT).
- No Windows optional feature is enabled or disabled.
- No other VM is enumerated, started, stopped, exported, or checkpointed.
- No in-guest changes beyond the autoinstall answers. Trier Bridge itself is installed and tested by later foundation work.
