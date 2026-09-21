# Trier Bridge Research Ledger, Plan, and Reference Policy

**Task:** SCOPE-04 (research plan with exit criteria)  
**Updated:** 2026-09-20

## 1. Current conclusion

Adjacent projects exist, but research to date has not identified one mature installable project whose central contract is:

> Windows mental model → familiar interaction/command → typed Linux operation → native authorization → verified result → optional Linux teaching.

This is a research conclusion, not proof that no similar project exists anywhere. The detailed survey, design lessons, and reference URLs from September 20, 2026 are in `INVARIANTS.md` section 1.

Adjacent categories: Windows-familiar distributions (Zorin OS, AnduinOS, Linux Mint, Lindows); system monitors (Mission Center, SysMonTask, System Monitoring Center); graphical administration (Cockpit); journal viewers (GNOME Logs); command familiarity experiments (Unix cmd.exe reimplementations, command translators); migration-readiness tools and guides.

## 2. Research plan

Each track has a question, an exit criterion, and the decision it feeds. A track is closed only by a written finding with in-VM evidence, recorded in section 4.

| Track | Question | Exit criterion | Feeds |
|---|---|---|---|
| R1 File manager integration | How can Trier Bridge add right-click actions and open Files at familiar places on GNOME, then KDE, Cinnamon, XFCE? | A Nautilus extension loads on the target and shows a menu item; scripts-folder fallback verified; other desktops listed with their mechanism. | DELIVERY-MODEL, SCOPE-14, DOC-02 |
| R2 Launcher and search | Can Windows terms resolve in Activities search? | A `SearchProvider2` provider registered per user returns results for "Task Manager". | DELIVERY-MODEL, DOC-03 |
| R3 Settings routing | Which familiar categories map to GNOME Settings panels, and which need a Trier Bridge view? | Panel list captured from a console session; mapping table drafted. | DOC-03 |
| R4 Default applications | Per-user default changes through `mimeapps.list` and `xdg-mime`; scheme handlers. | Change and revert verified without touching system files. | DOC-03 |
| R5 Printing and scanning | CUPS status, queue, cancel, add-printer routes; scanner discovery. | Read-only queue view against CUPS on the VM; add-printer route decided (GNOME panel versus own view). | DOC-04 |
| R6 Network shares | SMB browse and mount through GVfs/GIO versus udisks. | A share from the host mounted via GIO from the VM, credentials scope understood. | DOC-04 |
| R7 Package aggregation | apt plus snap inventory with provenance; PackageKit versus native. | PackageKit `GetPackages` and `snap list` reconciled for the same app; plan preview fields available. | DOC-05, IMP-04.07 |
| R8 Notifications | Portal versus GNOME notifications for operation results. | One notification shown from a test process via the portal. | SCOPE-14 |
| R9 Devices and Bluetooth | udev/sysfs inventory, UPower, bluez routes. | Device Manager categories mapped to real sources on the VM. | DOC-05 |
| R10 Wayland constraints | Screenshots, global shortcuts, window control. | Screenshot portal call works; shortcut route confirmed (gsettings, since the GlobalShortcuts portal is absent). | DELIVERY-MODEL, IMP-03.08 |
| R11 polkit boundaries | Which actions the MVP needs and their defaults; agent behavior in local versus remote sessions. | Table in PRIVILEGE-MODEL complete; denial and cancel observed live. | PRIVILEGE-MODEL, IMP-06 |
| R12 PowerShell on Linux | `pwsh` availability, execution policy behavior, cmdlet gaps. | `pwsh` snap installed in the VM; behavior notes for SCOPE-08. | SCOPE-08, IMP-07.06 |
| R13 Packaging | `.deb` build, lintian, install/upgrade/remove diff. | A test package built and diffed on the VM. | PACKAGING, ARC-11 |
| R14 Distro settings APIs | Ubuntu-specific settings surfaces (netplan renderer, App Center). | Documented where Ubuntu differs from upstream GNOME. | PLATFORMS |
| R15 Tray icon | AppIndicator availability on the target and on other desktops. | Closed for Ubuntu 24.04 (finding F5). Others pending. | SCOPE-14 |
| R16 First-run trigger | How the setup screen appears after a silent package install. | Decided: first launch, no autostart (DELIVERY-MODEL section 2). | DELIVERY-MODEL |
| R17 UI toolkit accessibility | AT-SPI on Wayland for GTK4/libadwaita versus alternatives. | Orca reads a sample window of each candidate toolkit on the VM. | SCOPE-09, ARC-02 |
| R18 D-Bus client libraries | Maturity of D-Bus, polkit-flag, and signal support per candidate stack. | A read of systemd, NetworkManager, and udisks2 properties plus one polkit-prompting call from each candidate. | ARC-01 |
| (status 2026-09-21) | R1 extension load verified (F18), menu item visual pending; R2 provider verified at the D-Bus level (F16), Shell listing pending a console check; R12 closed (F19); R17 and R18 closed for candidate A (F17, F15). | | |

Tracks R1, R2, R11, R17, R18 gate ARC-01/ARC-02.

## 3. Reference policy

External projects and documentation are evidence and research references, not hidden implementation authority.

- Record source URL, project/version/date, and what was learned.
- Separate public API behavior from private/internal implementation observations.
- Do not claim Trier Bridge support because another project supports a platform.
- Do not copy source/assets without license/provenance review.
- Prefer official Linux subsystem documentation for behavioral contracts.
- Community reports are useful leads, not qualification evidence.
- Historical results do not certify the current Trier Bridge build.

High-value reference families: freedesktop specifications, systemd documentation, D-Bus, NetworkManager, udisks, polkit, PackageKit where used, desktop environment documentation, distribution packaging policies, accessibility standards.

## 4. Findings

Evidence source unless stated otherwise: read-only probe of `tb-ubuntu-desktop-2404` (Ubuntu 24.04.5 LTS, GNOME Shell 46.0, Nautilus 46.4) on 2026-09-20, run over SSH as user `tb`.

**F1 (R1) File manager.** Nautilus 46.4 loads extensions from `/usr/lib/x86_64-linux-gnu/nautilus/extensions-4` (`libnautilus-extension.so.4` present). `python3-nautilus` 4.0 is in the archive but not installed. The per-user scripts folder `~/.local/share/nautilus/scripts` exists and needs no dependency. The Desktop Icons extension (`ding`) is active, so launcher files on `~/Desktop` are shown. Open: load a real extension and verify a menu item (exit criterion).

**F2 (R2) Search.** GNOME Shell ships 8 system search providers and the interface definition `org.gnome.ShellSearchProvider2.xml`. Per-user providers under `~/.local/share/gnome-shell/search-providers` are supported, which lets setup control the integration without system files. Open: register one and query it.

**F3 (R4) Defaults.** Defaults resolve through `xdg-mime`; the VM has no user `mimeapps.list` yet and the system one is `gnome-mimeapps.list`. Observed defaults: PDF opens in LibreOffice Draw, plain text in LibreOffice Writer, PNG in Shotwell Viewer, and no `http` handler is registered on a fresh install (Firefox is a snap and registers on first run). Consequence: "change the default PDF application" (TB-IA-06) is a real, valuable everyday task on this target.

**F4 (R10) Wayland.** The `xdg-desktop-portal` 1.18 on the target exposes Screenshot, OpenURI, Trash, Notification, Settings, Secret, Background, DynamicLauncher, and others, with GNOME and GTK backends. `GlobalShortcuts` is absent, so keyboard shortcuts must use per-user GNOME custom keybindings through gsettings. Xwayland is running (one process).

**F5 (R15) Tray icon.** `ubuntu-appindicators@ubuntu.com` (gnome-shell-extension-appindicator 58) is enabled by default alongside `ubuntu-dock`, `ding`, and `tiling-assistant`. A StatusNotifier tray icon is viable on the first target. Closed for Ubuntu 24.04.

**F6 (R11) polkit.** 156 actions under the relevant prefixes, 16 rule files under `/usr/share/polkit-1/rules.d`, none under `/etc`. Defaults for an active local user: `systemd1.manage-units` auth_admin_keep; `NetworkManager.settings.modify.system` auth_admin_keep; `udisks2.filesystem-mount` yes; `packagekit.package-install` auth_admin_keep; `packagekit.package-remove` auth_admin; `login1.reboot` yes. Consequence: no Trier Bridge privileged helper is needed for the first release (`PRIVILEGE-MODEL.md`). Open: observe denial and cancel live from a candidate stack.

**F7 (R7, R14) Packages.** apt 2.8.3 with the deb822 `ubuntu.sources`; snapd 2.76.3 with 11 snaps including Firefox 155, Thunderbird 155, `snap-store` (the App Center), `firmware-updater`; `gnome-software` absent; Flatpak absent; PackageKit 1.2.8 activatable on the system bus. Consequence: Installed Apps on the first target aggregates apt and snap and must preserve which is which (TB-INV-072).

**F8 (R14) Network.** NetworkManager 1.46 manages `eth0` through a netplan-generated profile (`netplan-eth0`); netplan files `01-network-manager-all.yaml` and `50-cloud-init.yaml` present. The NetworkManager checkpoint/rollback API is present on the bus (TB-INV-151 can be honored). Ubuntu-specific: persistent changes made through NetworkManager are stored by NetworkManager, while netplan owns the initial configuration; the two must not be edited concurrently (TB-INV-178).

**F9 (R9, R11) System bus.** Active: NetworkManager, UDisks2, PolicyKit1, login1, systemd1, UPower, Avahi, CUPS. Activatable: PackageKit, hostname1, timedate1, bluez, fwupd. udisks2 exposes 19 block objects on the VM (mostly snap loop devices), which is a realistic "many mounts" case for Disk Management.

**F10 (R11) Journal and processes.** User `tb` is in `adm`, so `journalctl` reads the system journal without elevation; a user outside `adm` will not, and the UI must show restricted rather than empty (TB-INV-145). `/proc` is fully readable (`hidepid` off), so Task Manager needs no privilege for inventory.

**F11 (R12) PowerShell.** `pwsh` is not in the apt archive on 24.04; the `powershell` snap 7.6.5 is available. Trier Bridge invokes an installed `pwsh` and never bundles one (DEC-008).

**F12 (R17, R18) Toolchain presence on the target.** Preinstalled: `python3` 3.12.3, `python3-gi` 3.48, GTK 4.14.5, libadwaita 1.5.0. In the archive, not installed: Rust 1.75, Go 1.22, Qt 6.4, Node 18, `libgtk-4-dev`. Consequence for ARC-01: a Python plus GTK4/libadwaita application adds no runtime dependency to Ubuntu Desktop; a compiled GTK application adds only its own binary; Qt or web-view stacks add runtime libraries the target does not have.

**F13 (R16) First-run trigger.** Decided by design rather than probe: packages install silently, so setup appears on first launch (`DELIVERY-MODEL.md` section 2).

**F15 (R18) D-Bus from the Python candidate.** `python3-gi` (GLib 2.80) read systemd (522 units; `ssh.service` ActiveState/UnitFileState by object path), NetworkManager (version, state, connectivity, per-device state and managed flag), UDisks2 (18 block objects, 3 drives with stable `Id`/`Serial`/`Size`), PackageKit (1.2.8, backend `apt`, distro `ubuntu;24.04;x86_64`), and login1, all without shelling out, and read `/proc/self/stat` for PID plus start time. polkit `CheckAuthorization` with no interaction flag returned `challenge` for every action without prompting, including `udisks2.filesystem-mount` and `login1.reboot` that are `yes` for an active local session: the probe ran from an SSH session, so polkit applied its stricter inactive-session defaults. This is the TB-INV-023 distinction observed live. Closed for candidate A.

**F16 (R2) Search provider.** A per-user provider prototype (`~/.local/share/gnome-shell/search-providers/*.ini`, a D-Bus session service file, a hidden `.desktop`) was installed with no system files. D-Bus activation started the service on the first call; `GetInitialResultSet` returned `tb.taskmanager` for "task manager" and `tb.installedapps` for "add or remove"; `GetResultMetas` returned name and description. The service exits after 60 s idle. Still open: confirmation that GNOME Shell lists it in Activities search (needs the console session; expected on the next search after the desktop database refresh). The word matcher is loose ("task manager" also matched Device Manager) and will be replaced by the concept catalog.

**F17 (R17) Accessibility on Wayland.** A GTK 4.14 / libadwaita 1.5 window from `python3-gi`, launched into the console Wayland session, appeared on the AT-SPI bus (inspected with the same `Atspi` library Orca uses): application, frame, label, push button `Task Manager` with its description, and the switch labelled `Tray icon at login` were all exposed. Note: the AT-SPI application name comes from the program name, so `GLib.set_prgname` must be set. Closed for candidate A. Other candidates unverified.

**F18 (R1) Nautilus extension loads.** With `python3-nautilus` 4.0 installed (it pulls `gir1.2-nautilus-4.0`), a per-user extension placed in `~/.local/share/nautilus-python/extensions/` was imported by Nautilus 46.4 and its `MenuProvider` constructed on the next launch (`nautilus -q` then open), with no system files touched and no session restart. The extension adds one context-menu item on files and on the folder background. Visual confirmation of the item is pending a console check; reversal is deleting one file. Consequence: the Files integration in `DELIVERY-MODEL.md` is viable with one declared dependency; the scripts-folder fallback remains for a zero-dependency mode.

**F19 (R12) PowerShell on Linux.** `powershell` snap 7.6.5 (classic confinement) installed and ran: `$PSVersionTable.OS` reports Ubuntu 24.04.5, execution policy is `Unrestricted` (Linux has no policy enforcement; explain rather than simulate, SECURITY section 11), `Get-Process` exists (229 processes seen). Absent: `Get-Service`, `Get-NetIPAddress`, `Get-EventLog`, `Get-WmiObject`, `Get-CimInstance`. Available modules are the cross-platform core set (Management, Utility, Security, Archive, ThreadJob, PSResourceGet, PackageManagement, PowerShellGet, PSReadLine). Consequence for SCOPE-08: Trier compatibility cmdlets fill exactly those gaps through the typed-operation layer (TB-INV-103, TB-INV-104), never by reimplementing Windows semantics.

**F14 Session identity caveat.** `loginctl` lists both the console session (Type=wayland, from the ENV-02 profile) and SSH sessions (Type=tty) for user `tb`. Evidence scripts must select the graphical session explicitly rather than the first match.

## 5. Open research tracks (not yet started)

R3 settings panels (needs a console session), R5 printing, R6 SMB shares, R8 notifications, R9 device categories, R13 package build, and the desktop-specific halves of R1, R2, R15 for KDE, Cinnamon, and XFCE.
