# Trier Bridge Validation and Evidence

**Status:** All runtime evidence is NOT RUN. No implementation candidate exists.

This document defines evidence states, evidence records, qualification automation limits, the pre-implementation checklist, interaction acceptance cases, and the templates for test reports and task evidence. The existence of any template here is not evidence of PASS.

## 1. Evidence states

- `DESIGN`
- `IMPLEMENTED`
- `UNIT_VERIFIED`
- `INTEGRATION_VERIFIED`
- `FAILURE_VERIFIED`
- `DISTRO_VERIFIED`
- `DESKTOP_VERIFIED`
- `PHYSICAL_VERIFIED`
- `ACCESSIBILITY_VERIFIED`
- `NOVICE_VERIFIED`
- `RELEASE_VERIFIED`
- `NOT_RUN`
- `BLOCKED`
- `UNSUPPORTED`
- `NOT_APPLICABLE`

Do not collapse these into one PASS.

`NOT_RUN` means evidence is missing, not PASS or FAIL. `BLOCKED` means a prerequisite, capability, environment, decision, or verification requirement is unresolved.

## 2. Evidence record

Every consequential verification records:

- task/test ID
- candidate revision
- package/build identity
- environment profile
- fixture
- steps
- expected result
- observed result
- logs/artifacts
- limitations
- timestamp (America/Chicago)

## 3. Claim boundary

A passing unit test cannot prove:

- distro compatibility
- real privilege UX
- Wayland behavior
- physical USB/printing/Bluetooth
- novice usability
- release packaging

Evidence belongs to the exact claim.

## 4. Qualification automation

Purpose: automate evidence collection without automating approval.

Safe automation may:

- inspect Git scope
- identify affected invariant families
- identify protected areas
- validate docs/headers/license inventory
- check environment profile
- run reviewed non-destructive tests
- run destructive tests only in disposable authorized profiles
- collect machine-readable results
- bind results to candidate/environment

Automation may not:

- mark an invariant PASS without its procedure
- widen support claims
- modify source to make tests pass
- suppress findings automatically
- run destructive tests on the user's workstation
- authorize privilege
- publish a release
- change product scope

Readiness failure produces BLOCKED/NOT_RUN with a reason, not a fake PASS.

## 5. Pre-implementation checklist

No item implies implementation or runtime PASS.

**Product**

- [ ] Product North Star reviewed
- [ ] everyday-office-user flows defined
- [ ] power-user/admin layers separated from everyday UX
- [ ] MVP scope frozen
- [ ] non-goals reviewed

**Architecture**

- [ ] implementation stack selected
- [ ] module boundaries frozen
- [ ] platform adapter contract frozen
- [ ] typed operation model frozen
- [ ] privilege architecture reviewed
- [ ] persistence ownership frozen
- [ ] capability state model frozen
- [ ] recovery model frozen

**UX**

- [ ] screen inventory reviewed
- [ ] file/app/search/settings everyday flows designed
- [ ] loading/empty/unknown/denied/error/recovery states designed
- [ ] accessibility flows reviewed
- [ ] Familiar/Bridge/native-detail behavior reviewed

**Security**

- [ ] SECURITY.md review complete
- [ ] privileged API contains no generic root execution
- [ ] Bridge Terminal grammar/security frozen
- [ ] path/identity/stale-state strategy reviewed
- [ ] update trust design selected before enabling updates

**Platform**

- [ ] first-release distro candidates chosen
- [ ] desktop/session matrix chosen
- [ ] packaging candidates chosen
- [ ] capability-discovery research complete for MVP subsystems

**Evidence**

- [ ] affected invariants mapped to planned tests
- [ ] destructive fault tests use disposable environments
- [ ] no support claim exceeds planned qualification

## 6. Interaction acceptance cases

**Status:** Design cases, NOT RUN.

Required evidence for each case: environment, steps, expected result, observed result, failures/limitations.

| ID | Case |
|---|---|
| TB-IA-01 | Office user finds and opens a downloaded PDF without knowing a Linux path. |
| TB-IA-02 | Office user copies a document to a USB drive and safely ejects it. |
| TB-IA-03 | Office user connects to Wi-Fi and verifies connection status. |
| TB-IA-04 | Office user opens a familiar network share without using mount commands. |
| TB-IA-05 | Office user prints a document and views/cancels the queue. |
| TB-IA-06 | Office user changes the default application for PDFs. |
| TB-IA-07 | Office user finds an installed application and launches it. |
| TB-IA-08 | Office user uninstalls an application while its package provenance remains clear. |
| TB-IA-09 | Office user changes display arrangement/resolution through a familiar route. |
| TB-IA-10 | Office user connects Bluetooth headphones and selects them for audio. |
| TB-IA-11 | Office user takes a screenshot using familiar interaction. |
| TB-IA-12 | Office user finds disk usage without understanding mount points. |
| TB-IA-13 | User closes a frozen user application through Task Manager. |
| TB-IA-14 | User searches for "Task Manager" and lands on the correct Linux-backed feature. |
| TB-IA-15 | User searches for "Add or Remove Programs" and reaches Installed Apps. |
| TB-IA-16 | User opens Event Viewer after an application failure and gets useful filtered logs. |
| TB-IA-17 | Power user inspects startup applications without learning systemd first. |
| TB-IA-18 | Power user identifies a network adapter and current IP address. |
| TB-IA-19 | Power user inspects hardware in Device Manager. |
| TB-IA-20 | Power user inspects disks/partitions without destructive action. |
| TB-IA-21 | Advanced user restarts a qualified service with explicit authorization. |
| TB-IA-22 | Advanced user enters `ipconfig` in Bridge Terminal and receives Linux-backed output. |
| TB-IA-23 | Advanced user enters an unsupported Windows command and nothing executes. |
| TB-IA-24 | Bridge Terminal rejects command injection/metacharacter abuse. |
| TB-IA-25 | Permission denial is explained without suggesting an insecure bypass. |
| TB-IA-26 | Backend unavailable degrades only the affected capability. |
| TB-IA-27 | System state changes outside Trier Bridge and the UI refreshes rather than fighting it. |
| TB-IA-28 | Large-text/keyboard-only user completes an everyday task. |
| TB-IA-29 | Non-English user searches a familiar system concept without changing backend identity. |
| TB-IA-30 | Internet disconnected: core local experience and system tools remain usable. |

## 7. Foundation test report template

**Current status:** NOT RUN.

When foundation testing begins, record: candidate revision, build/package identity, host environment, tested distro/session profiles, toolchain versions, source verification, build result, unit result, integration result, fault result, package install/uninstall result, known gaps, exact artifacts.

Persistence-specific coverage is listed in `STATE-AND-PERSISTENCE.md` section 13.

## 8. Task evidence ledger

**Status:** Empty baseline. Use only for observed evidence once implementation work begins.

Entry template:

```text
### <Task ID> — <Title>

- Timestamp:
- Candidate revision:
- Environment/profile:
- Files/modules:
- Invariant impact:
- Expected result:
- Observed result:
- Tests/checks:
- Artifacts/logs:
- Failures/limitations:
- Evidence state: DESIGN / IMPLEMENTED / UNIT_VERIFIED / INTEGRATION_VERIFIED /
  FAILURE_VERIFIED / DISTRO_VERIFIED / PHYSICAL_VERIFIED / RELEASE_VERIFIED /
  NOT_RUN / BLOCKED
```

Do not record planned behavior as observed evidence.

## Entries

### ENV-02 — Hyper-V Ubuntu Desktop test VM created and profiled

- **Timestamp:** 2026-09-20 11:10 PM CDT
- **Candidate revision:** bbd29fa (tools/env scripts)
- **Environment/profile:** Environment profile `tb-ubuntu-desktop-2404` observed 2026-09-20 11:10 PM CDT (in-guest, over SSH): Ubuntu 24.04.5 LTS (ID ubuntu, like debian), kernel 7.0.0-31-generic x86_64, virt microsoft (Hyper-V Gen2); session: GDM, Type=wayland, Class=user, local (Remote=no); GNOME Shell 46.0; systemd 255 (pid 1); NetworkManager 1.46.0 running; udisks2 2.10.1; polkit 124 (polkitd); apt 2.8.3; PackageKit 1.2.8; snap 2.76.3; Flatpak absent; CUPS 2.4.7; xdg-desktop-portal 1.18.4 with gnome backend 46.2; AppArmor enabled; Python 3.12.3; git 2.43.0; pwsh absent; GNOME extensions enabled by default: ubuntu-appindicators, ubuntu-dock, ding, tiling-assistant (gnome-shell-extension-appindicator 58); Hyper-V: hv_balloon and vmbus kernel workers present, linux-cloud-tools daemons absent; 4 vCPU, 8.3 GiB, 62 GB root (48 GB free). Guest changes beyond autoinstall: openssh-server installed and enabled; host SSH public key authorized for user tb.
- **Files/modules:** `tools/env/New-TbDesktopVm.ps1`, `tools/env/autoinstall/*`
- **Invariant impact:** TB-INV-023 (session type recorded, not conflated), TB-INV-230 (disposable environment), TB-INV-231 (exact environment identity)
- **Expected result:** VM created by script with verified ISO; unattended install completes; guest reachable.
- **Observed result:** Create script evidence `reports/local/env-tb-ubuntu-desktop-2404.json` (ISO SHA256 VERIFIED, created 2026-09-20 10:39 PM CDT); autoinstall completed (marker `/etc/tb-environment` present); guest at 172.20.252.59 on Default Switch.
- **Tests/checks:** in-guest profile script (read-only) over SSH.
- **Artifacts/logs:** profile output recorded above; create-script JSON in `reports/local/` (untracked).
- **Failures/limitations:** vmconnect basic session has no clipboard for Linux guests; bootstrap used a temporary host HTTP server on the switch address. Profile is one VM, one desktop; proves nothing about other desktops or physical hardware.
- **Evidence state:** DISTRO_VERIFIED (environment identity only; no product behavior claimed)

### IMP-01 — Foundation 01: toolchain, skeleton, checks, reproducible package

- **Timestamp:** 2026-09-21 12:15 AM CDT
- **Candidate revision:** cd3ef65
- **Environment/profile:** tb-ubuntu-desktop-2404 (Ubuntu 24.04.5, Wayland GNOME 46, Hyper-V Gen2; see ENV-02 profile); guest deviates from `clean-install` by sudo, python3-nautilus, powershell snap, dev toolchain packages
- **Files/modules:** `pyproject.toml`, `.flake8`, `trier_bridge/` (core, config, logging_setup, ui, __main__), `tests/unit/`, `tools/dev.py`, `data/`, `debian/`, `docs/TOOLCHAIN.md`
- **Invariant impact:** TB-INV-004, 006, 029, 049 to 054, 057, 078, 105, 106, 107, 121, 123, 181, 182, 192 to 195, 209, 223, 225 (implemented in core/config/logging/ui and covered by unit tests where marked TB-T###); no system mutation exists in this candidate
- **Expected result:** all checks clean on host and VM; the window runs in the Wayland session with accessible labels; the package builds reproducibly, validates, installs, runs, and removes cleanly; no daemon, unit, autostart, or /etc change.
- **Observed result:** `python3 tools/dev.py all` clean in the VM (black, flake8, mypy --strict, 33 unit tests, 35/35 headers). Window launched in the console Wayland session and exited 0; AT-SPI walk found the application `trier-bridge` with 14 list items carrying labels and descriptions, group headers, and status text (RESEARCH F17 method). Self-snapshot 960x640 reviewed. `dpkg-buildpackage -us -uc -b` twice with `SOURCE_DATE_EPOCH` = commit time gave identical SHA256 `8ac8408f2435b03cc3fa6bde19afaa2d02441f218ec5a47a8f58f83d0250b4d1`; lintian silent; `desktop-file-validate` valid; `appstreamcli validate` warns only `url-homepage-missing` (no public homepage exists by decision). `apt-get install ./trier-bridge_0.1.0~dev0_all.deb` succeeded; `trier-bridge --version` printed 0.1.0.dev0; no `trier-bridge` process, no system unit, no system autostart entry, no `/etc` change after install; `apt-get purge` left nothing under /usr; per-user state under `~/.local/state/trier-bridge` kept by design (TB-INV-026 documented in the man page).
- **Tests/checks:** unit tests against real temporary files (no mocks, DEC-021); AT-SPI inspection in the live session; package lifecycle in the VM.
- **Artifacts/logs:** snapshot `tb-shot.png` (scratchpad, not tracked); build logs `/tmp/b1.log`, `/tmp/b2.log` in the guest; session transcript.
- **Failures/limitations:** one desktop, one distro, one VM; no integration or mutation tests exist yet (nothing mutates); the Hyper-V guest has no GPU so GTK used software rendering (libEGL warnings, harmless); AppStream homepage warning stands until a homepage exists.
- **Evidence state:** DISTRO_VERIFIED (toolchain and package lifecycle); UNIT_VERIFIED (core); DESKTOP_VERIFIED (shell launches with AT-SPI exposure on Ubuntu 24.04 GNOME Wayland)

### IMP-02 — Foundation 02: environment profile and capability discovery

- **Timestamp:** 2026-09-21 12:25 AM CDT
- **Candidate revision:** 07320ae
- **Environment/profile:** tb-ubuntu-desktop-2404 (Ubuntu 24.04.5, kernel 7.0.0-31, Hyper-V; ENV-02), checks run over SSH (tty, remote) and the window run in the console Wayland session
- **Files/modules:** `trier_bridge/capability/` (model, facts, discovery), `trier_bridge/ui/sysinfo.py`, `tests/unit/test_facts.py`, `tests/unit/test_capability_model.py`, `tests/integration/test_discovery_vm.py`
- **Invariant impact:** TB-INV-016, 017, 018, 019, 020, 021, 022, 023, 035, 036, 037, 040, 041, 044, 046, 145 (implemented: identity from os-release; session facts from logind; five distinct states; evidence and freshness on every record; bounded D-Bus timeouts; structured errors; no side effects)
- **Expected result:** discovery reports the real distro, kernel, architecture, virtualization, session type and remoteness, and one record per backend with a state, backend, version, and evidence; creates no files; the view renders the records.
- **Observed result:** SSH run reported Ubuntu 24.04.5 LTS / 24.04 / like debian / x86_64 / kernel 7.0.0-31-generic / virtualization microsoft / session tty (user), remote yes; 16 records: systemd 255.4 SUPPORTED, NetworkManager 1.46.0 SUPPORTED, udisks2 2.10.1 SUPPORTED, polkit 124 SUPPORTED, logind SUPPORTED, PackageKit (apt backend) SUPPORTED, apt/dpkg SUPPORTED, snapd SUPPORTED, Flatpak UNSUPPORTED (absent), journal SUPPORTED (readable), CUPS SUPPORTED, BlueZ SUPPORTED (activatable), UPower SUPPORTED, portals SUPPORTED, GNOME Shell SUPPORTED, procfs SUPPORTED. Six integration tests passed, each comparing discovery with an independent live read (os-release, /proc, direct D-Bus property reads, filesystem facts), plus the side-effect test (no file created under a fresh XDG home). 43 unit tests passed on host and VM.
- **Tests/checks:** `python3 tools/dev.py all`; `python3 -m pytest tests/integration -m integration`; discovery dump over SSH; System Information view opened in the console session.
- **Artifacts/logs:** session transcript; snapshot `tb-shot2.png` (scratchpad).
- **Failures/limitations:** one environment only; IMP-02.07 (generic fallback on other environments) has unit evidence for the unknown-distro path on real file text but no second live environment yet; `desktop` is taken from the session environment variable, so it reads Unknown over SSH by design.
- **Evidence state:** INTEGRATION_VERIFIED and DISTRO_VERIFIED (Ubuntu 24.04.5 profile); IMP-02.07 NOT_RUN elsewhere

### IMP-03 — Foundation 03: everyday continuity, first slice (read-only)

- **Timestamp:** 2026-09-21 02:40 AM CDT
- **Candidate revision:** f9299ac
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); checks over SSH; page runs and the launch test in the console Wayland session bus
- **Files/modules:** `data/catalog/concepts.json`, `trier_bridge/catalog/`, `trier_bridge/desktop/launch.py`, `trier_bridge/apps/`, `trier_bridge/resources.py`, `trier_bridge/ui/pages.py`, `tests/unit/test_catalog.py`, `test_provenance.py`, `test_resources.py`, `tests/integration/test_desktop_vm.py`
- **Invariant impact:** TB-INV-003, 065, 105 (catalog: 39 concepts, every non-exact mapping carries a note, no-equivalent concepts cannot open); TB-INV-072, 024 (installed apps keep provenance by real entry path); TB-INV-073 (real Linux paths shown under familiar names); TB-INV-074 (only openable actions get an Open button); TB-INV-078, 192 (every result plain, failures say nothing was changed); TB-INV-010 (desktop tools opened, never replaced)
- **Expected result:** Windows terms resolve to the right route; folders open in Files through FileManager1; Settings panels open through org.gnome.Settings actions; installed apps list snap and system entries with correct provenance; no markup or crash on any page.
- **Observed result:** catalog search: "add remove" → Installed Apps, "control panel" → Settings, "recycle" → Recycle Bin, "ipconfig" → Network Connections, "regedit" → Registry Editor (no equivalent, cannot open), "wifi" → Network Connections and Wi-Fi settings. Inventory: 47 apps (41 system, 5 snap: App Center, Firefox, Firmware Updater, PowerShell, Thunderbird; 1 user). Defaults read: PDF → Document Viewer, http → nothing set (reported as empty, not guessed). Integration: 11 passed, including `test_launcher_opens_the_downloads_folder_in_files` (FileManager1.ShowFolders returned without error in the session). Home, Apps, Settings pages ran with 0 markup errors and 0 tracebacks; Home snapshot reviewed. Unit: 53 passed on host and VM.
- **Tests/checks:** `python3 tools/dev.py all`; `pytest tests/integration -m integration` in the session; AT-SPI walk (search entry exposed with its label).
- **Artifacts/logs:** `tb-shot3.png` (scratchpad); session transcript.
- **Failures/limitations:** two defects found and fixed during the run (snap entries invisible to `Gio.AppInfo.get_all` outside a graphical session; Adw rows parsed `&` as markup). Not yet: right-click integration (needs the Nautilus extension and the setup screen, SCOPE-14), uninstall and default-app changes (mutations, Foundation 06), printer/network live status (Foundation 04), office-user acceptance (IMP-03.09, needs a person at the console).
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED for the read-only slice on Ubuntu 24.04.5 GNOME Wayland

### IMP-04.01 — Task Manager observation

- **Timestamp:** 2026-09-21 02:45 AM CDT
- **Candidate revision:** 888e679
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); unit and integration checks over SSH; page run in the console Wayland session
- **Files/modules:** `trier_bridge/system/processes.py`, `trier_bridge/ui/taskmanager.py`, `tests/unit/test_processes.py`, `tests/integration/test_processes_vm.py`
- **Invariant impact:** TB-INV-050 (PID plus start time identity, revalidation helper), TB-INV-131 (Unknown never 0: first-sample CPU, unreadable memory), TB-INV-132/133 (native visibility respected; command line only in tooltip, truncated), TB-INV-136 (PID 1 and kernel threads non-actionable), TB-INV-199/200 (one procfs pass per 2 s, only while the page is visible), TB-INV-066 (apps, background, kernel kept distinct)
- **Expected result:** sampler matches independent /proc reads; kernel threads and PID 1 classified critical; CPU percent unknown on the first sample then measured; page renders live rows with the observation-only banner and no crash.
- **Observed result:** 4 live integration tests passed (this process found with the kernel start time and uid; PID 1 critical, kernel threads present with empty cmdline; CPU unknown then measured within bounds; system processes report memory or not-readable). Page in the session: banner exposed over AT-SPI, rows for python3, gnome-shell, firefox, systemd; 0 tracebacks, 0 markup errors. Unit: 58 passed on host and VM; integration total 15 passed.
- **Tests/checks:** `python3 tools/dev.py all`; `pytest tests/integration -m integration`; AT-SPI walk.
- **Artifacts/logs:** session transcript (self-snapshot did not render for this page; AT-SPI walk is the evidence).
- **Failures/limitations:** APP versus USER classification is not yet distinguished (no window/desktop-entry correlation); no End task (Foundation 06); Startup tab not yet present (IMP-04.02).
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED on Ubuntu 24.04.5 GNOME Wayland

### IMP-04.03 — Event Viewer over the journal

- **Timestamp:** 2026-09-21 02:50 AM CDT
- **Candidate revision:** 73e2fc0
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); user `tb` is in `adm` so the system journal is readable; page run in the console Wayland session
- **Files/modules:** `trier_bridge/system/journal.py` (ctypes binding to libsystemd sd-journal), `trier_bridge/ui/eventviewer.py`, `tests/unit/test_journal.py`, `tests/integration/test_journal_vm.py`
- **Invariant impact:** TB-INV-045 (native API, no CLI parsing in the product), TB-INV-068/147 (familiar views are filters; native fields preserved), TB-INV-100/144 (ANSI and control characters stripped; text is data), TB-INV-145 (restricted access stated as restricted), TB-INV-146 (bounded to 500, cancellable), TB-INV-148 (nothing in a message is a link or executed)
- **Expected result:** newest entries agree with an independent journalctl read; access state matches group membership; cancellation returns early; page renders with the access banner, view drop-down, and level badges.
- **Observed result:** 3 integration tests passed (access matches `id -Gn`; at least 25 of the newest 50 messages matched `journalctl -o json`, all sanitized; cancel returned an empty list). Sample of 200 entries: System 195, Application 5, Security 81, Errors 0, Boot 0 (views overlap by design). Page in session: banner, combo box 'All events', '500 of the newest 500 entries', Information badges; 0 tracebacks, 0 markup errors. Unit 61 passed on host and VM; integration total 18 passed.
- **Tests/checks:** `python3 tools/dev.py all`; `pytest tests/integration -m integration`; AT-SPI walk.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** the restricted-account path (user outside `adm`) is implemented but not yet exercised live; Boot view empty because the current boot's kernel messages fell outside the newest 500 (time-range and boot filters are follow-ups); the Security view is identifier-based, not audit-based.
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED on Ubuntu 24.04.5

### IMP-04 — Foundation 04: read-only familiar system tools (Network, Disks, Devices, Startup, provenance)

- **Timestamp:** 2026-09-21 02:55 AM CDT
- **Candidate revision:** e37d48a
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02; Hyper-V Gen 2, so no PCI/USB bus, devices on vmbus); checks over SSH; pages in the console Wayland session
- **Files/modules:** `trier_bridge/system/{bus,network,storage,devices,startup}.py`, `trier_bridge/ui/{network,disks,devices}.py`, `tests/unit/test_network_storage.py`, `test_devices_startup.py`, `tests/integration/test_network_storage_vm.py`, `test_devices_startup_vm.py`
- **Invariant impact:** TB-INV-071/149 (link, profile, IP, DNS, gateway, connectivity check reported as separate rows), TB-INV-052 (connection UUID + interface identity captured), TB-INV-070/157/158 (drives, partitions, filesystems, loops, mounts distinct; identity from serial/size/UUID; real mount folders shown), TB-INV-162 (free space from statvfs, Unknown when unmounted), TB-INV-173/174/175 (devices: missing fields Unknown; no driver actions; names sanitized and truncated), TB-INV-072 (installed software provenance, Foundation 03), TB-INV-131 (Unknown never zero across all tools)
- **Expected result:** each inventory agrees with an independent read of the same system; pages render without errors; package still builds, installs, and purges cleanly.
- **Observed result:** Network: NetworkManager 1.46.0, state Connected (global), connectivity Full Internet access; eth0 Ethernet Connected, profile netplan-eth0, 172.20.252.59/20, gateway and DNS 172.20.240.1, MAC matches /sys/class/net. Storage: 3 drives (two Msft Virtual Disks, one virtual DVD), volumes sda1 vfat at /boot/efi and sda2 ext4 at / with free space within 512 MB of statvfs, 13 squashfs loops hidden and counted, 0 loose. Devices: 25 devices across net, drm, sound, input, block, vmbus (eth0 hv_netvsc, hyperv_drm, atkbd keyboard, hid-hyperv mouse, sd disks, hv_balloon/hv_utils); a first run found 0 because PCI and USB do not exist on Gen 2, fixed by class and vmbus passes. Startup: 38 entries from /etc/xdg/autostart with On/Off state. Integration: 22 passed. Pages network, disks, devices, startup: 0 tracebacks, 0 markup errors, AT-SPI rows present. Unit: 68 passed on host and VM.
- **Tests/checks:** `python3 tools/dev.py all`; `pytest tests/integration -m integration`; data dumps; AT-SPI walks; package rebuild (see below).
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** one environment; Hyper-V has no PCI/USB so those passes are exercised only by unit tests on a synthetic tree; UPower reported no devices (no battery in the VM); the Startup view lists but cannot toggle (Foundation 06); Task Manager APP versus USER not yet distinguished.
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED on Ubuntu 24.04.5

### IMP-05 — Foundation 05: durable state, operation journal, restart reconciliation, fault tests

- **Timestamp:** 2026-09-21 03:05 AM CDT
- **Candidate revision:** 1c3a34a
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); fault tests on a real 4 MB ext4 loopback image mounted through the kernel (sudo used by the test harness only, fixed argv); app runs in the console Wayland session
- **Files/modules:** `trier_bridge/state/{journal,preferences}.py`, `trier_bridge/config.py` (fix), `trier_bridge/__main__.py`, `trier_bridge/ui/{app,window}.py`, `tests/unit/test_state_journal.py`, `tests/integration/test_persistence_faults_vm.py`
- **Invariant impact:** TB-INV-055/183 (operation ID, one atomic record per state change with history), TB-INV-059/060/189 (restart: non-terminal records become OUTCOME_UNKNOWN + NEEDS_REVIEW, surfaced in a banner, never replayed), TB-INV-179/180 (preferences: declared defaults, versioned, non-durable writes reported and reverted, unknown keys preserved), TB-INV-181/182 (atomic writes survive disk full, read-only remount, permission loss; original kept, no temp file left), TB-INV-029 (newer schema opened read-only or left alone), TB-INV-194 (corrupt records quarantined, not guessed), TB-INV-196 (unresolved records never pruned)
- **Expected result:** every fault leaves the last known-good state; an interrupted operation is flagged on the next start and shown to the user; the last section is restored.
- **Observed result:** disk full: the write failed with a plain not-changed result, prefs.json kept bridge, no temp file remained, and the write succeeded again after space returned; read-only remount and permission loss: StateWriteError raised, record still DRAFT; child process killed with SIGKILL while EXECUTING: flagged OUTCOME_UNKNOWN on reconcile. Seeded EXECUTING record on the real app: log line about interrupted operations needing review, banner text 'An earlier action was interrupted: service.restart on cups.service...' exposed over AT-SPI on two consecutive starts; last_section disks persisted and restored. A product defect was found and fixed: temp-file creation errors escaped as raw OSError instead of StateWriteError. Unit 77 passed (host and VM); integration 30 passed.
- **Tests/checks:** `python3 tools/dev.py all`; `pytest tests/integration -m integration`; AT-SPI walk; journal dump.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** power loss during a write is approximated by SIGKILL of the writer, not by cutting VM power; two concurrent instances (TB-INV-063) not yet tested; suspend/resume not exercised.
- **Evidence state:** FAILURE_VERIFIED and INTEGRATION_VERIFIED on Ubuntu 24.04.5

### IMP-06.04 — End task (user process termination)

- **Timestamp:** 2026-09-21 03:05 AM CDT
- **Candidate revision:** 1c3a34a
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); real child processes started by the tests; page in the console session
- **Files/modules:** `trier_bridge/operations/process.py`, `trier_bridge/ui/taskmanager.py` (End task button, confirmation dialog), `tests/integration/test_terminate_vm.py`
- **Invariant impact:** TB-INV-050/121 (revalidation by PID plus start time immediately before the signal; stale identity cancels and the replacement process is untouched), TB-INV-134 (End and Force end are separate operations with separate confirmations), TB-INV-132/136 (PID 1, kernel threads, system and other-user processes, and Trier Bridge itself refused before any signal), TB-INV-006 (success only when the process is observed gone; zombies count as ended), TB-INV-193 (PARTIAL enumerates what happened), TB-INV-078/192 (plain results with nothing-was-changed); journaled through Foundation 05
- **Expected result:** a cooperative child ends and is VERIFIED; a child ignoring SIGTERM yields PARTIAL with Force end as the next step, then Force end VERIFIES; a stale identity CANCELS without touching the live process; protected targets are UNSUPPORTED.
- **Observed result:** all four integration tests passed on the VM; the journal record history ends committed, verifying, verified; Task Manager shows End task only on the user's own rows with a spoken description, banner text updated; 0 tracebacks. Two defects found and fixed during the run: a zombie (exited, unreaped) child was still counted as present, and the PARTIAL result lacked its step lists.
- **Tests/checks:** `pytest tests/integration/test_terminate_vm.py`; AT-SPI walk.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** the confirmation dialog path was not driven end to end by automation (button present, dialog not clicked); Force end is reachable only after a PARTIAL result (no separate button yet).
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED on Ubuntu 24.04.5

### IMP-06.05 — Service control through systemd (polkit-mediated)

- **Timestamp:** 2026-09-21 03:15 AM CDT
- **Candidate revision:** 05a2971
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); user-scope tests on a real transient unit created with systemd-run; system-scope denial exercised over SSH where no polkit agent exists; page in the console session
- **Files/modules:** `trier_bridge/system/services.py`, `trier_bridge/operations/service.py`, `trier_bridge/ui/services.py`, `tests/integration/test_services_vm.py`
- **Invariant impact:** TB-INV-053/142 (unit revalidated by name, object path, fragment path; a replaced unit cancels), TB-INV-067/138/139 (Running and Start-at-boot are separate facts; start/stop/restart/enable/disable are separate operations; static and masked units cannot be enabled), TB-INV-143 (restart that stops but fails to start is PARTIAL), TB-INV-006 (success is the observed ActiveState/UnitFileState), TB-SEC-007/TB-INV-126 (denial is a DENIED result; no fallback), TB-INV-109/110 (system-scope calls use ALLOW_INTERACTIVE_AUTHORIZATION so polkit prompts only from a user action; Trier Bridge holds no privilege)
- **Expected result:** stopping a user unit is VERIFIED and matches systemctl; a stale identity cancels without touching the unit; a system-scope restart without an agent is DENIED with the unit unchanged; enable on a static unit is UNSUPPORTED.
- **Observed result:** all five service integration tests passed: tb-test-service.service stopped and VERIFIED (systemctl --user is-active reported inactive), stale fragment path CANCELLED with the unit still active, cups.service restart over SSH DENIED with ActiveState unchanged, static unit enable UNSUPPORTED, listing kept ssh.service Running/Manual distinct. Services page in session: banner, scope drop-down, 168 of 168 services, per-row action menus; 0 tracebacks.
- **Tests/checks:** `pytest tests/integration/test_services_vm.py`; AT-SPI walk.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** the interactive polkit prompt on the console (grant path) was not driven by automation; enable/disable on a real unit file was not mutated in the test (only planned); PARTIAL restart path not provoked live.
- **Evidence state:** INTEGRATION_VERIFIED (user scope, denial path) and DESKTOP_VERIFIED on Ubuntu 24.04.5

### IMP-07 — Bridge Terminal (grammar, read-only vocabulary, taskkill via typed plan)

- **Timestamp:** 2026-09-21 03:15 AM CDT
- **Candidate revision:** 05a2971
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); commands run against live NetworkManager, systemd, procfs; page in the console session
- **Files/modules:** `trier_bridge/bridge/{grammar,commands}.py`, `trier_bridge/ui/terminal.py`, `tests/unit/test_grammar.py`, `tests/unit/test_bridge_commands.py`, `tests/integration/test_bridge_vm.py`
- **Invariant impact:** TB-INV-082/102 (Bridge Mode only, mode label always visible, no shell fall-through), TB-INV-083/084 (grammar, typed commands), TB-INV-085/086/087/088 (unknown commands, unknown switches, residue, and any shell metacharacter rejected as a whole), TB-INV-089 (CMD quoting and Unicode preserved), TB-INV-093 (read-only commands never elevate), TB-INV-094/104 (taskkill returns the same typed plan as Task Manager and requires confirmation), TB-INV-096 (no fabricated fields; Unknown shown), TB-INV-098 (sensitive lines excluded from history), TB-INV-099/100 (bounded output, no escape interpretation), TB-INV-105 (regedit and format are educational only), TB-SEC-004
- **Expected result:** SECURITY.md test A (tasklist, ipconfig, sc query useful without root) and test C (injection strings rejected, nothing executes).
- **Observed result:** ipconfig /all showed eth0 with the MAC from sysfs and the connectivity check; tasklist listed the test's own PID; sc query ssh reported Running/Manual with the unit file; hostname, whoami, systeminfo, getmac, netstat matched independent facts; euid stayed non-root. Five injection lines (redirect, chaining, backticks, $()) all parsed to nothing and no marker file appeared. taskkill /PID returned a TerminatePlan without killing; /PID 1 refused; unknown switch parsed to nothing. type on /etc/shadow reported Access is denied. Terminal page: banner, Mode: Bridge label, command entry, bounded output view, Run button; 0 tracebacks. Unit 95 passed; integration 39 passed.
- **Tests/checks:** `python3 tools/dev.py all`; `pytest tests/integration -m integration`; AT-SPI walk; sample runs (ver, ipconfig, sc query cups, injection, regedit).
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** Bash and PowerShell modes are not offered yet (IMP-07.06); no persistent history file; netstat parses /proc/net directly and shows listening sockets only by default.
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED on Ubuntu 24.04.5

### SCOPE-14 — Integration catalog, first-run setup, tray icon, search provider, Files extension

- **Timestamp:** 2026-09-21 03:55 AM CDT
- **Candidate revision:** 078048d
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02), package built from the tree and installed with apt (`trier-bridge_0.1.0~dev0_all.deb`); GNOME session unlocked so the Ubuntu AppIndicator extension is active (session-mode extensions are inactive while the screen is locked, which is why the StatusNotifier host was first missing)
- **Files/modules:** `trier_bridge/integrations/{catalog,ledger,search_provider,tray}.py`, `trier_bridge/ui/integrations.py`, `trier_bridge/ui/app.py` (single-instance launch actions), `data/integrations/tb_nautilus.py`, `data/trier-bridge-{tray,search-provider}.1`, `tests/unit/test_integrations.py`
- **Invariant impact:** TB-INV-025/026 (package touches `/usr` only; the setup screen writes only under the user's home and records every file), TB-INV-077 (each integration individually reversible; removal deletes exactly the recorded files, including the compiled copy Files makes of the extension), TB-INV-076 (shortcut is an individual item, never in a group), TB-SEC-003 (search provider, tray, and Files extension launch the window with fixed argument lists, no shell), DEC-018 c (tray and search provider exit when idle or turned off; no daemon), DEC-019 (groups Essentials, Files, Shortcuts; whole-group or single-item choice; changeable any time; tray icon "T" with a three-entry menu)
- **Expected result:** first launch shows the setup screen; Apply with the recommended group writes the tray autostart entry, the search-provider `.ini` and D-Bus service file, and eight launcher entries, and records them; every switch on the Integrations page reverses exactly; the tray registers with the StatusNotifier host and its menu reaches the window; the search provider answers Windows words and opens the running window at the right place; the Files extension is loaded by Nautilus.
- **Observed result:** setup screen appeared on the first run (AT-SPI: groups, "Whole group" checks, five items, Not now, Apply); Apply recorded 3 integrations and 11 files, all under `/home/tb`. Tray: process `trier-bridge-tray` registered as `org.kde.StatusNotifierItem-<pid>-1`, the panel exposed a `menu: 'Trier Bridge'` with `Open Trier Bridge`; dbusmenu `GetLayout` returned the four entries; `Event 4 clicked` turned the tray off from its own menu (process gone, autostart entry deleted, ledger updated) and the open Integrations page then showed the switch off (ledger re-reads the shared file; found and fixed live). Switch toggles: Ctrl+Shift+Esc wrote the custom keybinding and its removal restored `custom-keybindings` to the recorded previous value (`[]`); Files extension copied to `~/.local/share/nautilus-python/extensions`, Nautilus compiled it on load (pyc appeared), removal took both. Search provider: D-Bus activation started it, `GetInitialResultSet(['add','remove'])` returned `tb.installedapps`, `GetResultMetas` carried the mapping note, `ActivateResult('tb.taskmanager')` switched the running window to Task Manager (0 → 136 End task buttons). Launch options: `trier-bridge --section integrations` from a second process reached the running window (remote action) and exited 0. Package: lintian silent after man pages were added; `man -w` finds both. Unit 94 passed on the host (3 skipped: gi absent, Windows permission bits), 102 in the VM; integration 38 passed, 1 skipped.
- **Tests/checks:** `python3 tools/dev.py all` (host and VM); `pytest tests/integration -m integration`; `dpkg-buildpackage -us -uc -b`; `lintian`; AT-SPI walks and actions (`a11y_walk.py`, `a11y_do.py`, test aids kept outside the repo); `gdbus`/`busctl` calls against the live provider, watcher, and menu.
- **Artifacts/logs:** session transcript; `~/.config/trier-bridge/integrations.json` in the VM.
- **Failures/limitations:** the Files context-menu item was verified as loaded, not clicked (needs a person or a Nautilus AT-SPI driver, TB-IA acceptance); the shortcut was not pressed on a keyboard; GNOME Shell reads new search providers at login, so Activities search itself was exercised over D-Bus, not typed into the overview; the pre-existing per-user search-provider files from the F16 research were overwritten by the integration and are now recorded by it; the AppIndicator host is absent while the screen is locked, so a locked session shows no icon until unlocked.
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED on Ubuntu 24.04.5

### IMP-06.07 — Authorization paths driven end to end: granted, dismissed, backend re-exec

- **Timestamp:** 2026-09-21 04:30 AM CDT
- **Candidate revision:** c31be9d
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02), over SSH (logind session of type tty); polkit 124; systemd 255. Prompts answered by a real polkit authentication agent registered for the test's own session (`tests/integration/polkit_agent.py`): it either dismisses the prompt or runs the system's setuid `polkit-agent-helper-1` with the test account's password taken from `TRIER_BRIDGE_TEST_PASSWORD` (never stored in the repository), exactly as graphical agents do.
- **Files/modules:** `trier_bridge/operations/service.py`, `trier_bridge/system/services.py`, `tests/integration/polkit_agent.py`, `tests/integration/test_authorization_vm.py`
- **Invariant impact:** TB-INV-109/110 (the product never holds privilege; polkit decides per action, `manage-units` was the one action asked), TB-INV-126/127 (denied or dismissed: plain result, unit untouched, no fallback), TB-INV-006 (granted: success is the observed ActiveState, VERIFIED), TB-INV-053/142 (identity revalidated after the user manager re-executed), TB-INV-059/060 (journal left no unresolved record after the granted operation)
- **Expected result:** dismissed prompt leaves cups.service in its prior state and says so; granted prompt stops a transient system unit and verifies it; a `systemctl --user daemon-reexec` between reading a user unit and stopping it does not break the operation.
- **Observed result:** all three tests passed. Dismissed: polkit asked the agent exactly once for `org.freedesktop.systemd1.manage-units`, the agent returned `Cancelled`, systemd answered with an access-denied error, the product reported DENIED with "Linux did not grant permission for this change. cups.service was not changed." and ActiveState was unchanged; polkitd logged "FAILED to authenticate". Granted: the helper printed `SUCCESS`, polkit authorized, the stop was VERIFIED (ActiveState inactive), the product's euid stayed 1000, and the journal had no unresolved record. Re-exec: the stop after `daemon-reexec` was VERIFIED.
- **Tests/checks:** `TRIER_BRIDGE_TEST_PASSWORD=<account password> pytest tests/integration/test_authorization_vm.py -m integration`; `journalctl` polkitd lines; a one-off probe printing the dismissed result.
- **Artifacts/logs:** session transcript; polkitd journal lines quoted above.
- **Failures/limitations:** systemd 255 reports a dismissed polkit prompt as `AccessDenied`, so the product cannot tell "cancelled" from "denied" for service control and says "did not grant permission" for both; the wording is accurate in both cases and nothing changes either way, but the CANCELLED state is reachable only where the backend distinguishes (documented in `docs/PRIVILEGE-MODEL.md`). Authorization expiry (`auth_admin_keep`) is polkit's own cache and was not exercised. The grant test skips when the password variable is absent, so an unattended run without it proves only the dismissed and re-exec paths.
- **Evidence state:** INTEGRATION_VERIFIED on Ubuntu 24.04.5

### IMP-07.06/07 — PowerShell entry through real pwsh; cmdlet names through typed operations

- **Timestamp:** 2026-09-21 04:50 AM CDT
- **Candidate revision:** 3a59f1f
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); `powershell` snap 7.6.5 installed (F19); GUI session env for the launch check
- **Files/modules:** `trier_bridge/bridge/cmdlets.py`, `trier_bridge/bridge/grammar.py` (translation hook, `powershell` command), `trier_bridge/bridge/commands.py` (`cmd_powershell`, help), `trier_bridge/ui/terminal.py` (PowerShell button), `tests/unit/test_cmdlets.py`
- **Invariant impact:** TB-INV-103/104 (cmdlet names run the same typed operations as the Bridge commands and show the translation; `Stop-Process -Id` yields the same TerminatePlan and confirmation as taskkill), TB-INV-085/086 (unknown parameters and extra arguments refuse the whole line), TB-INV-105 (Get-EventLog and Get-WmiObject teach; nothing is simulated), DEC-008 (PowerShell is never bundled; `powershell` opens an installed `pwsh`), TB-SEC-003/TB-INV-082 (the launch is a fixed program path handed to the desktop's terminal handler; Bridge Mode stays shell-free; `$PSVersionTable` is refused as shell syntax), SECURITY section 11 (execution policy explained, not simulated)
- **Expected result:** `Get-Service ssh`, `Get-Process`, `gip` produce the sc query, tasklist, and ipconfig /all output with a "PowerShell X → Y" first line; `Get-Process -Name` refuses; `Get-EventLog` teaches; `powershell` opens pwsh in the user's terminal when installed and explains how to get it when not.
- **Observed result:** live in the VM: `Get-Service ssh` → "PowerShell Get-Service → sc query" then ssh.service Running; `Get-Process` → tasklist table; `gip` → ipconfig /all; `Get-EventLog System` → PARSE_ERROR with the Event Viewer explanation, nothing run; `Get-Process -Name bash` → PARSE_ERROR naming the parameter; `help Get-Service` shows the mapping and `-name`. `powershell` reported OK with the snap path; a `gnome-terminal-server` window titled Terminal appeared (AT-SPI) and `/snap/powershell/405/opt/powershell/pwsh` was running; closed afterwards. Unit 99 passed on the host, 107 in the VM; integration 41 passed, 1 skipped.
- **Tests/checks:** `tools/dev.py all` (host, VM); `pytest tests/integration -m integration`; `vm_pwsh_probe.py` (test aid outside the repo) in the GUI session; AT-SPI walk of the terminal.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** the "not installed" branch was not exercised (pwsh is installed in the VM); the PowerShell button in the Terminal page was verified by the same command path, not clicked; cmdlet coverage is the listed set only (Get-Process, Stop-Process -Id/-Force, Get-Service, Get-NetIPConfiguration, Get-NetIPAddress, Get-NetTCPConnection, Get-ComputerInfo, Get-ChildItem, Set-Location, Get-Location, Get-Content, Clear-Host, Write-Output, Get-Help, plus teaching entries for Get-EventLog and Get-WmiObject); PowerShell pipelines and variables are refused as shell syntax by design.
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED (launch) on Ubuntu 24.04.5

### IMP-03.03 — Everyday file operations: copy, move, rename, Trash, folders (typed, confirmed)

- **Timestamp:** 2026-09-21 07:40 AM CDT
- **Candidate revision:** 910961d
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); unit tests on real files under the repository checkout (ext4, same filesystem as the home Trash); UI driven through AT-SPI in the console session
- **Files/modules:** `trier_bridge/operations/files.py`, `trier_bridge/bridge/grammar.py` (copy, move, ren, del, md, rd; Linux paths starting with / are arguments for these), `trier_bridge/bridge/commands.py`, `trier_bridge/bridge/cmdlets.py` (Copy-Item, Move-Item, Rename-Item, Remove-Item), `trier_bridge/ui/terminal.py` (confirmation dialog for file plans), `tests/unit/test_file_operations.py`
- **Invariant impact:** TB-INV-006 (success is the observed result: destination exists, source gone, folder present), TB-INV-050/121 (identity is device, inode, and inode change time, revalidated right before acting; ext4 reuses an inode number immediately after delete-and-recreate, found by the test and covered by ctime), TB-INV-083 (a plan performs nothing until confirmed), TB-INV-164 (no recursive delete, no permanent delete: del means the Trash; rd removes only an empty folder), TB-INV-078 (plain results with the three answers), TB-INV-119 (paths are data; Windows separators accepted, no shell)
- **Expected result:** copy/move/rename verified on real files and never overwrite; del moves to the Trash where Files can restore it; md/rd create and remove folders (rd refuses non-empty); an identity change between plan and execution cancels; Bridge commands and cmdlet names only plan until the dialog confirms.
- **Observed result:** unit: 5 tests passed in the VM (copy verified and refused on an existing name; move into a folder; rename with a Windows separator; del landed in `trash:///` with `trash::orig-path` equal to the original; mkdir/rmdir; non-empty rmdir refused; folder copy refused with the Files hint; recreated file with the same path cancelled; `Remove-Item -Recurse` refused; `copy a.txt /tmp` treated /tmp as a path). Live UI: typed `copy report.txt copy-of-report.txt` in the Bridge Terminal, the dialog read "Copy report.txt to /home/tb/tb-files-demo/copy-of-report.txt?" with Cancel and Copy; Copy produced the file (20 bytes, same as the source); `del copy-of-report.txt` showed "Move to Trash?"; confirming removed it from the folder and `gio trash --list` showed it with its original path. 112 unit tests passed in the VM.
- **Tests/checks:** `python3 tools/dev.py all` (host: file tests skip without gi; VM: run); AT-SPI aids `a11y_type.py` (set the command entry text) and `a11y_do.py` (Run, Copy, Move to Trash) kept outside the repo.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** folders are not copied (Files does that; refused with a hint); the terminal's output view text was not read back over AT-SPI in this run (the dialog and the filesystem were the evidence); the Trash listing in the VM still holds the test file; the Files page itself offers no file operations (it routes to Files), so these operations are reachable from the Bridge Terminal and PowerShell names only.
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED on Ubuntu 24.04.5

### IMP-03.05 — Default apps: choose which listed program opens a kind of file (typed, reversible)

- **Timestamp:** 2026-09-21 08:10 AM CDT
- **Candidate revision:** 9f779ce
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); the tb user's own `~/.config/mimeapps.list`; two programs registered per common type in this VM
- **Files/modules:** `trier_bridge/operations/defaults.py`, `trier_bridge/ui/pages.py` (Apps page: a program drop-down and Set button per kind of file, confirmation dialog), `trier_bridge/bridge/grammar.py` and `commands.py` (`assoc`/`ftype` read-only listing), `tests/unit/test_default_apps.py`
- **Invariant impact:** TB-INV-006 (success is the re-read default), TB-INV-050/121 (MimeIdentity = kind of file plus the current default; a change made elsewhere between plan and execution cancels), TB-INV-077 (reversible: the previous program is recorded in the journal and offered in the result; choosing it again undoes the change), TB-INV-119 (only programs the desktop already lists for the type are accepted; no free-form commands), TB-INV-083 (nothing changes until the dialog confirms), TB-INV-209 (drop-downs are announced by the selected program with the description "Program for <kind>")
- **Expected result:** setting Text files to the other registered program is VERIFIED and reads back; the same choice again is refused as a no-op; choosing the previous program restores it; an unlisted program is refused; `assoc` lists the defaults without changing anything.
- **Observed result:** unit in the VM: set text/plain from LibreOffice Writer to Text Editor VERIFIED, refusal on repeat, revert VERIFIED, journal resolved; unlisted program UNSUPPORTED; `assoc` OK and read-only; the concurrent-change case skipped honestly (no common type has three programs in this VM). Live Apps page: eight Set buttons (one per kind of file with candidates) and eight combo boxes named after the selected program found over AT-SPI; no tracebacks. Full unit run 114 passed, 1 skipped; integration 41 passed, 1 skipped.
- **Tests/checks:** `python3 tools/dev.py all` (host and VM); `pytest tests/unit/test_default_apps.py`; `xdg-mime query default text/plain` before and after (unchanged: libreoffice-writer.desktop); AT-SPI walk of the Apps page.
- **Artifacts/logs:** session transcript; the VM's `~/.config/mimeapps.list` now pins text/plain explicitly to the same program it had before.
- **Failures/limitations:** the Set flow was not driven through the dialog over AT-SPI (drop-down selection is not exposed as an action; the same plan/execute path is covered by the unit test); the stale-default cancel path is untested where fewer than three programs exist; uninstalling programs (the other half of IMP-03.05) is a package mutation and stays with IMP-06.06.
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED (controls) on Ubuntu 24.04.5

### IMP-06.08 — Security and failure regression set (with SECURITY Test B live)

- **Timestamp:** 2026-09-21 08:45 AM CDT
- **Candidate revision:** fe28c25
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); host `.venv` for the platform-independent part
- **Files/modules:** `docs/TEST-STRATEGY.md` section 7 (the mapping), `trier_bridge/bridge/commands.py` (`sc start|stop|restart|enable|disable` through the terminal), `trier_bridge/ui/terminal.py` (service confirmation dialog), `tests/integration/test_authorization_vm.py` (Test B), `tests/unit/test_file_operations.py` (hostile filenames)
- **Invariant impact:** TB-SEC-001..030 as mapped in the table; TB-INV-094/104 (`sc stop` in the terminal is the same ServicePlan as the Services page, confirmed the same way), TB-INV-109/110 (Test B: one polkit request for one unit, product euid unchanged), TB-INV-089/119 (hostile filenames are data)
- **Expected result:** SECURITY section 37 and Tests A–D each map to an automated test or an honest gap; the whole suite passes on host and VM; Test B passes end to end from the typed command through polkit.
- **Observed result:** host `tools/dev.py all` clean, 99 unit passed (5 skipped without gi or POSIX bits); VM `tools/dev.py all` clean, 115 unit passed (1 skipped: fewer than three programs for any common type); integration 42 passed, 1 skipped (console-only desktop test over SSH). Test B: `sc stop tb-test-system` returned NEEDS_CONFIRMATION with a ServicePlan naming that unit and "Linux will ask for administrator permission for this one action"; the unit was still active before confirmation; executing with the real polkit agent produced exactly one `manage-units` prompt and a VERIFIED stop; euid stayed 1000. Hostile filenames (space, leading dash, apostrophe, umlauts and ß, semicolon) copied VERIFIED through the typed path; the terminal refused the semicolon line whole; `del ../../etc/passwd` failed as not found in the working folder.
- **Tests/checks:** as listed in `docs/TEST-STRATEGY.md` section 7.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** gaps stay listed in the table: symlink escape and mount boundary (no recursive operation exists yet), dependency failure and live PARTIAL restart, packages and network (no mutation exists), expiry/replay (polkit's own), keyboard-driven Cancel paths exercised by hand only.
- **Evidence state:** INTEGRATION_VERIFIED on Ubuntu 24.04.5; gaps recorded

### IMP-08.02 — Install, upgrade in place, purge; per-user state and ownership

- **Timestamp:** 2026-09-21 09:40 AM CDT
- **Candidate revision:** fdc7569 (package versions 0.1.0~dev0 → 0.1.0~dev1)
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); apt on the `.deb` files built from the tree in the VM
- **Files/modules:** `debian/*`, `data/org.triertech.TrierBridge.metainfo.xml` (release entries), `data/*.1`, `pyproject.toml`, `trier_bridge/__init__.py`
- **Invariant impact:** TB-INV-025/026 (the package touches `/usr` only; per-user files are the user's and survive purge and upgrade), TB-INV-029 (a newer build read the dev0 ledger and preferences unchanged; no schema bump was needed), DEC-018 g/DEC-019 (integrations kept across the upgrade; no setup screen shown again)
- **Expected result:** purge removes every packaged path and nothing under the home; reinstall restores the commands; upgrading dev0 → dev1 over a running tray keeps the ledger and preferences byte-identical, the window opens without the setup screen, and the Integrations page shows the same switches.
- **Observed result:** purge: 113 owned paths gone, 0 left under `/usr`, 7 per-user entries kept, the running tray kept running; reinstall restored three commands and the existing autostart entry started the tray as login would. Upgrade: `Unpacking trier-bridge (0.1.0~dev1) over (0.1.0~dev0)` then `Setting up`; `trier-bridge --version` reported dev1; `integrations.json` and `preferences.json` SHA-256 identical before and after; the dev1 window showed no setup screen and the Integrations page read tray-icon, search provider, and launchers as on; the old tray process (dev0 code) kept running until the next login. lintian silent on dev1.
- **Tests/checks:** `apt-get purge`, `apt-get install`, `dpkg -L`, `sha256sum`, AT-SPI walk of the Integrations page.
- **Artifacts/logs:** session transcript; `/tmp/upgrade.log` in the VM.
- **Failures/limitations:** downgrade dev1 → dev0 was not exercised (the dev0 file had been removed before the attempt); an upgrade across a state-schema change has not happened yet (no schema change exists); a second environment is still missing (IMP-08.03).
- **Evidence state:** DISTRO_VERIFIED on Ubuntu 24.04.5

### IMP-08.08 — Performance and resource measurement (with one defect found and fixed)

- **Timestamp:** 2026-09-21 09:40 AM CDT
- **Candidate revision:** fdc7569
- **Environment/profile:** tb-ubuntu-desktop-2404: 4 vCPU, 10 GB RAM, Hyper-V without GPU acceleration (`hyperv_drm`; GTK falls back to software rendering, so memory figures are an upper bound for this stack), installed package for the window and tray, checkout for the after-fix Task Manager run
- **Files/modules:** `trier_bridge/ui/taskmanager.py` (row reuse), measurement aid `vm_perf.sh` (outside the repo)
- **Invariant impact:** TB-INV-203 (no background indexing exists; the only periodic work is the Task Manager sampler while its page is visible), TB-INV-004 (measurements reported as observed; no budget document exists yet, so no pass/fail claim is made)
- **Expected result:** the window opens in about a second, is idle when idle, and each background process is small and quiet; any page that burns CPU while idle is a defect.
- **Observed result:** launch to window frame 0.93–0.95 s (three runs, installed command). Window RSS 257 MB on Home, 268 MB Task Manager, 286 MB Event Viewer, 296 MB Services, 280 MB Device Manager; 16 threads; idle CPU 0 ticks in 10 s on Home, Event Viewer, Services, Device Manager. **Defect:** the Task Manager page used 941 ticks in 10 s (94% of a core) because the list rebuilt every row every 2 s; after reusing rows it uses 25 ticks in 10 s with 230 processes (sampler alone 9 ms per sample). Tray icon: 24.8 MB RSS, 0 CPU over 10 s, 4 hours up. Search provider: 42 ms cold (D-Bus activation to first answer), 4 ms warm, 23 MB, exits after 60 s idle. Package: 87,748 bytes, Installed-Size 469 KB; per-user state 1.8 KB config, 12.6 KB state (logs and journal).
- **Tests/checks:** `vm_perf.sh` (timestamps around launch, AT-SPI poll for the frame, `/proc/<pid>/stat` utime+stime deltas, `ps` RSS); `tools/dev.py all` after the fix; AT-SPI walk of the fixed page (140 End task buttons, no tracebacks).
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** no performance budget is written down yet (candidate for `docs/ENGINEERING.md`); figures come from one VM under software rendering, not from hardware with a GPU; the after-fix number was taken from the checkout run, the installed package is rebuilt from the same revision next.
- **Evidence state:** DISTRO_VERIFIED (measured) on Ubuntu 24.04.5; defect fixed and re-measured

### IMP-08.01 — Clean-chroot build (sbuild) reproduces the in-VM build bit for bit

- **Timestamp:** 2026-09-21 10:30 AM CDT
- **Candidate revision:** d689fb6 (package 0.1.0~dev1)
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02) as the build host; a fresh `noble` buildd chroot created with `sbuild-createchroot` from archive.ubuntu.com (main and universe; `pybuild-plugin-pyproject` lives in universe); `sbuild` 0.85 as shipped by Ubuntu 24.04
- **Files/modules:** `debian/*`, `debian/source/format` (`3.0 (native)`), `debian/changelog`
- **Invariant impact:** TB-INV-027/028 (build provenance: the same source yields the same package in a clean environment), TB-SEC release-provenance gate (`CODE-QUALITY-REPORT.md`), TB-INV-004 (the earlier mismatch is reported and explained, not hidden)
- **Expected result:** the source package builds in a clean chroot with only declared build dependencies; the resulting `.deb` is identical to two consecutive in-VM builds of the same tree; lintian is silent; the chroot-built package installs.
- **Observed result:** `dpkg-buildpackage -S` produced `trier-bridge_0.1.0~dev1.dsc` and `.tar.xz`; `sbuild -d noble` installed the five declared build dependencies inside the chroot and built the package. SHA-256 of in-VM build 1, in-VM build 2 (two seconds later), and the chroot build: all `d2d599d0…507e49`. lintian silent; `apt-get install --reinstall` of the chroot build succeeded and `trier-bridge --version` reports 0.1.0.dev1. **Found on the way:** the first chroot build differed from the in-VM build only in file mtimes because the dev1 changelog entry carried a time later than the build itself, so `SOURCE_DATE_EPOCH` clamping did nothing; dating the entry at its real time fixed it (commit d689fb6). File contents had been identical throughout (`diff -r` of the unpacked trees was empty).
- **Tests/checks:** `dpkg-buildpackage -S -us -uc -d`; `sbuild -d noble --no-run-lintian`; `dpkg-buildpackage -us -uc -b` twice; `sha256sum`; `dpkg-deb -R` + `diff -r`; `lintian`; `apt-get install`.
- **Artifacts/logs:** `/tmp/sbuild3.log`, `/tmp/b1.log`, `/tmp/b2.log` in the VM; session transcript.
- **Failures/limitations:** one build host (the VM) and one chroot; a build on a different machine has not been compared yet. The chroot was created with `--components=main` first and needed universe added; `docs/PACKAGING.md` should say so for the next person.
- **Evidence state:** DISTRO_VERIFIED on Ubuntu 24.04.5; reproducible across environment

### IMP-03.08 — Print Screen through the desktop portal (implemented; unverifiable in this VM)

- **Timestamp:** 2026-09-21 11:50 AM CDT
- **Candidate revision:** 941e5d7
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02): `xdg-desktop-portal` 1.18 with the GNOME backend (`gnome.portal` lists `org.freedesktop.impl.portal.Screenshot`); the VM has no GPU and `xdg-desktop-portal-gnome` logs an EGL initialisation failure at start
- **Files/modules:** `trier_bridge/desktop/screenshot.py`, `trier_bridge/catalog/model.py` (route kind `action`), `data/catalog/concepts.json` (`tb.screenshot`), `trier_bridge/ui/pages.py` (Router actions), `trier_bridge/ui/window.py`, `tests/unit/test_screenshot_route.py`
- **Invariant impact:** TB-INV-119 (Trier Bridge captures nothing itself; the desktop's own tool does, after the user acts in it), TB-INV-004 (no claim that the tool appeared: the toast says it should, and a 60-second watchdog reports "no answer" and closes the request rather than waiting forever), TB-INV-078 (plain results for saved, cancelled, failed, no answer), TB-INV-065 (Screenshot stays an exact-equivalence concept with a real action)
- **Expected result:** choosing Screenshot (Home search "Print Screen", "Snipping Tool", or the search provider) sends one `org.freedesktop.portal.Screenshot.Screenshot` request with `interactive=true`; GNOME's screenshot UI appears; the Response carries a file URI or a cancellation; the product reports it.
- **Observed result:** the route, the Home "Take" button, the remote `--open tb.screenshot` path, and the request all work: the portal accepted the call and returned a request handle (`/org/freedesktop/portal/desktop/request/1_574/trierbridge…`). **In this VM the GNOME backend never answers:** the shell's screenshot UI nodes (Area Selection, Screen Selection, Window Selection, Capture) stayed hidden in the accessibility tree, no permission dialog appeared from `xdg-desktop-portal-gnome`, no Response arrived within 20 s for a direct portal call from the session either, and `Request.Close` returned without effect. This correlates with the backend's EGL failure in a GPU-less VM (the same environment in which the earlier research call timed out). Unit tests pass (100 host, 116 VM).
- **Tests/checks:** `tools/dev.py all`; direct portal call (`vm_portal_diag.sh`, test aid) with a 20-second wait; AT-SPI state probe of the shell's screenshot UI before, during, and after; product log lines.
- **Artifacts/logs:** session transcript; `~/tb-run14.log` in the VM.
- **Failures/limitations:** after these requests `xdg-desktop-portal-gnome` crashed with SIGSEGV (08:23:31, `/var/crash/_usr_libexec_xdg-desktop-portal-gnome.1000.crash`; Ubuntu offered to send the report and the owner declined), so in this VM the backend not only stays silent but falls over; the request Trier Bridge sends is the documented portal call, and the same call from a plain script behaved the same way. The screenshot itself is NOT VERIFIED anywhere yet; it needs a desktop with a working compositor capture path (real hardware or a VM with GPU acceleration) and is added to the TB-IA acceptance list. Clipboard stays teaching only (Ctrl+C/V are the same; there is no built-in clipboard history on GNOME). The watchdog wording was verified by reading; its firing was exercised in the VM.
- **Evidence state:** UNIT_VERIFIED for the route and request; the desktop behaviour is NOT VERIFIED (environment limitation)

### IMP-03.09 — Office-user journeys as automated interaction tests (console session)

- **Timestamp:** 2026-09-21 01:40 PM CDT
- **Candidate revision:** 4c2daa6
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02), console session (`WAYLAND_DISPLAY` set), the product started as a real process by the test
- **Files/modules:** `tests/integration/test_journeys_vm.py`
- **Invariant impact:** TB-INV-209 (every step is an accessible action: set text in the search entry, activate a button, read labels and the terminal text), TB-INV-105 (Registry Editor answered as No equivalent with no Open button), TB-INV-078/082 (a Windows command answered with this computer's facts and the Linux equivalent shown)
- **Expected result:** three journeys pass without a pointer or keyboard: Home search "Add or Remove Programs" then Show leads to Installed Apps; "regedit" is said to have no equivalent; the Command Prompt answers `hostname` with the machine name.
- **Observed result:** all three PASSED. Lessons kept in the test: search fields are role `entry`, plain entries role `text`; libatspi caches children and a test process must pump the GLib main context and clear the cache between polls; the sidebar rows carry no action, so the journey reaches Command Prompt through the same `--section` forwarding a launcher uses.
- **Tests/checks:** `WAYLAND_DISPLAY=wayland-0 ... python3 -m pytest tests/integration/test_journeys_vm.py -m integration` in the VM session (skips without a console session).
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** these are interaction tests, not usability acceptance: whether an office user finds the flow natural is IMP-08.04 and needs a person; the journeys run only where a console session is available (they skip over plain SSH).
- **Evidence state:** DESKTOP_VERIFIED on Ubuntu 24.04.5

### IMP-03.06/HELP — Live printer queues from CUPS; Help generated from the build

- **Timestamp:** 2026-09-21 02:20 PM CDT
- **Candidate revision:** 45f9f34
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); `cups-daemon` 2.4.7 running with no printers configured; `python3-cups` 2.0.1 present as Ubuntu Desktop ships it
- **Files/modules:** `trier_bridge/system/printers.py`, `trier_bridge/ui/printers.py`, `trier_bridge/help.py`, `trier_bridge/ui/help.py`, `trier_bridge/ui/window.py`, `debian/control` (Recommends `python3-cups`), `tests/unit/test_help_and_printers.py`
- **Invariant impact:** TB-INV-033 (pycups is optional: without it only the Printers page says printers are managed in Settings), TB-INV-004 (Help is generated from the catalog, the command table, and the integration catalog, so it cannot describe an absent feature), TB-INV-078 (printer state, reasons, and queue in plain words), TB-INV-209 (every row named; the Settings button described)
- **Expected result:** the Printers page reports the print service, the default, each printer with state and waiting jobs, and opens the GNOME Settings printers panel; Help lists how the product works, every Windows word by group, every Bridge command with its class, the PowerShell names, the integrations, and the three folders the product writes, with Open buttons for the folders.
- **Observed result:** Printers page over AT-SPI: "0 printers known to the print service", "No printers yet", the Printers settings button with its description; no warnings after the ampersand in the description was removed. Help page: 429 nodes, groups How Trier Bridge works, Windows words (Troubleshooting, Everyday, Advanced, Files), Command Prompt, PowerShell names, Integrations, Where Trier Bridge keeps its files. Unit: the Help test asserts every command row carries its class text and that the file rows point inside the given home; the printers test read CUPS live (`available`, zero printers). Full suites: host 101 passed, VM 118 passed, integration 46 passed with the console session (journeys included).
- **Tests/checks:** `tools/dev.py all` (host, VM); `pytest tests/integration -m integration` in the VM session; AT-SPI walks of both pages.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** no printer is attached to the VM, so a printer with a queue was not observed; job listing is read-only (cancelling a job is a later class B operation); the Help search field filters rows by plain text only.
- **Evidence state:** DESKTOP_VERIFIED on Ubuntu 24.04.5 (no printer present)

### IMP-06.06 — Network translation layer: adapter and IPv4 changes through NetworkManager

- **Timestamp:** 2026-09-21 04:10 PM CDT
- **Candidate revision:** afa244c
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); NetworkManager 1.46.0; polkit 124; a dummy connection `tb-dummy` on `tbdummy0` created with `nmcli` as the test object; the VM's uplink `eth0` never touched (checked before and after)
- **Files/modules:** `trier_bridge/operations/network.py`, `trier_bridge/bridge/grammar.py` and `commands.py` (`netsh`), `trier_bridge/ui/network.py` (Disconnect/Connect and IPv4 dialog per adapter), `trier_bridge/ui/terminal.py` (network confirmation), `tests/unit/test_network_ops.py`, `tests/integration/test_network_vm.py`
- **Invariant impact:** TB-INV-109/110 (each change is one D-Bus call under polkit with ALLOW_INTERACTIVE_AUTHORIZATION; the product never holds privilege), TB-INV-052 (connection revalidated by UUID and interface right before acting; a change made elsewhere cancels), TB-INV-006 (success is the observed device state or the re-read profile), TB-INV-094/104 (`netsh` yields the same NetworkPlan as the page and needs the same confirmation), TB-INV-078 (plain previews and results), DEC-024 (translation, not hand-off)
- **Expected result:** `netsh interface set interface <name> disable|enable`, `netsh interface ip set address <name> static <ip> <mask> [gateway] | dhcp`, `netsh interface ip set dns <name> static <ip> | dhcp` and the page's buttons become NetworkManager changes that are verified; invalid addresses and masks are refused before any plan exists.
- **Observed result:** four integration tests passed on the dummy interface with the real polkit agent granting: disconnect VERIFIED (NetworkManager removes a disconnected virtual adapter entirely, which the layer now treats as disconnected), connect from the saved profile VERIFIED with 192.0.2.10/24 back on the adapter, fixed address 192.0.2.11/24 with DNS 192.0.2.53 saved in the profile and visible on the adapter (VERIFIED), DNS back to automatic VERIFIED, a connection changed underneath by `nmcli` cancelled the plan, the loopback adapter refused, `netsh ... static 192.0.2.12 ...` returned a plan without acting, an unknown adapter failed plainly. `eth0` stayed connected throughout. Unit: masks, prefixes, address forms, and the netsh grammar. Lint, types, bandit clean; VM unit 125 passed.
- **Tests/checks:** `TRIER_BRIDGE_TEST_PASSWORD=... pytest tests/integration/test_network_vm.py -m integration`; `tools/dev.py all`.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** the Network page buttons and the IPv4 dialog were not driven over AT-SPI in this entry (the same plan and execute path is exercised by the tests; a page walk is queued behind the owner's open window); IPv6 and Wi-Fi profile creation are not offered; `auto` on the dummy adapter cannot get a DHCP lease, so that verb was verified only as a saved setting.
- **Evidence state:** INTEGRATION_VERIFIED on Ubuntu 24.04.5

### IMP-04.07 — Drive letters: C:, D:, ... as a familiar label over Linux mounts

- **Timestamp:** 2026-09-21 04:10 PM CDT
- **Candidate revision:** afa244c
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02): `/` ext4, `/boot/efi` vfat, `/media/tb/CIDATA` vfat
- **Files/modules:** `trier_bridge/system/driveletters.py`, `trier_bridge/operations/files.py` (paths), `trier_bridge/bridge/commands.py` (cd, dir, type accept Windows spellings and show them), `trier_bridge/ui/disks.py` (letters next to volumes, a Drive letters group), `trier_bridge/ui/pages.py` (Drives on the Files page), `tests/unit/test_driveletters.py`
- **Invariant impact:** TB-INV-031/073 (the letter is a label; the real path is always shown and is what every operation uses), TB-INV-004 (an unknown letter is refused plainly, never invented)
- **Expected result:** C: is /, D: and later letters follow fixed then removable mounts in a stable order; plumbing mounts (EFI, snaps, tmpfs) get no letter; `C:\Users\<name>` is `/home/<name>`; Windows spellings work in the Command Prompt and file operations.
- **Observed result:** in the VM: letters C: (/) and D: (/media/tb/CIDATA); `cd` prints `/home/tb  (C:\Users\tb)`; `cd C:\Users\tb` lands in /home/tb; `dir D:\` lists /media/tb/CIDATA; `cd Q:\` answers "There is no drive Q: on this computer."; `type C:\etc\hostname` reads /etc/hostname; `dir C:\Users` lists /home; `/tmp` shows as C:\tmp. Unit tests cover ordering, plumbing exclusion, escapes in the mount table, and both directions of the spelling. Unit 125 passed in the VM.
- **Tests/checks:** `tools/dev.py all`; `vm_letters_probe.py` (test aid) against the live mount table.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** the Disk Management and Files pages were not walked over AT-SPI yet (queued behind the owner's open window); letters can shift when removable media come and go, exactly as on Windows, and that is stated on the page.
- **Evidence state:** INTEGRATION_VERIFIED (terminal and operations) on Ubuntu 24.04.5; page walks pending

### IMP-07.08 — ping, tracert, nslookup, ipconfig /flushdns

- **Timestamp:** 2026-09-21 05:30 PM CDT
- **Candidate revision:** eb139b7
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02); `net.ipv4.ping_group_range = 1 0` (unprivileged ICMP sockets disabled, `/usr/bin/ping` carries `cap_net_raw`); systemd-resolved with DNS 172.20.240.1; `tracepath` present, `traceroute` absent
- **Files/modules:** `trier_bridge/system/netdiag.py`, `trier_bridge/bridge/grammar.py`, `commands.py` (`ping`, `tracert`, `nslookup`, `ipconfig /flushdns|/renew|/release`, `ActionPlan`), `cmdlets.py` (Test-Connection, Test-NetConnection, Resolve-DnsName, Clear-DnsClientCache), `trier_bridge/ui/terminal.py` (action confirmation), `tests/unit/test_netdiag.py`, `tests/integration/test_netdiag_vm.py`
- **Invariant impact:** TB-INV-119 (a host is validated as a name or address before anything runs; shell characters are refused whole), TB-SEC-003 (ping and tracert run the system's own programs through the desktop terminal with a fixed argument list; no shell of ours), TB-INV-004 (the answer says why ping opens a window instead of pretending to send ICMP), TB-INV-078/083 (flushdns asks first, then is verified against the resolver's cache statistics)
- **Expected result:** `nslookup localhost` answers with the resolver's servers and 127.0.0.1; an unknown name is reported as not found; `ipconfig /flushdns` returns a plan, and running it empties systemd-resolved's cache; `ping -n 1 127.0.0.1` opens the system ping in a terminal window in the desktop session; `ping ubuntu.com; rm -rf /` is refused as shell syntax; `ipconfig /renew` explains the Linux way.
- **Observed result:** three integration tests passed in the VM: nslookup (Server: 172.20.240.1, Address: 127.0.0.1; `no-such-host.invalid` reported "Can't find"), flushdns (plan returned, run gave "Successfully flushed the DNS Resolver Cache.", cache size 0 afterwards), ping (terminal window opened with `ping -c 1 127.0.0.1`). Unit tests on the host cover host validation (names, IPv4, IPv6, refusals for spaces, semicolons, `$(x)`, over-long names), the `-n` count bounds, and the cmdlet mappings. `tools/dev.py all` clean on host and VM (VM unit 128 passed).
- **Tests/checks:** `pytest tests/integration/test_netdiag_vm.py -m integration` in the VM session; `tools/dev.py all`.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** ping replies appear in the terminal window, not in the Bridge Terminal (an in-process ping would need CAP_NET_RAW, which the product will not carry); tracert uses `tracepath` (no ICMP mode); `ipconfig /release` and `/renew` teach the reconnect route instead of acting.
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED (ping window) on Ubuntu 24.04.5

### IMP-07.09 — explorer, start, net, date, time, taskkill /IM, and the teaching entries

- **Timestamp:** 2026-09-21 06:15 PM CDT
- **Candidate revision:** 9630a12
- **Environment/profile:** tb-ubuntu-desktop-2404 (ENV-02), console session for the launches
- **Files/modules:** `trier_bridge/bridge/grammar.py`, `commands.py`, `trier_bridge/desktop/launch.py` (`open_uri`), `tests/unit/test_familiar_commands.py`, `tests/integration/test_familiar_vm.py`
- **Invariant impact:** TB-INV-080 (each familiar word answers with the Linux place: Files, the default application, Settings), TB-INV-105 (sfc, chkdsk, xcopy, robocopy, gpedit explain and never run), TB-INV-094/104 (`net start|stop` is the same ServicePlan as `sc`; `taskkill /IM` is the same TerminatePlan as `/PID`, and only when exactly one of the user's programs carries the name), TB-INV-119 (paths and addresses are data; a Linux path is never read as a switch for these commands)
- **Expected result:** `explorer <folder>` opens Files there (Windows or Linux spelling); `start <url|file|folder|notepad|calc|explorer|control>` opens the right thing and says so; `start cmd` answers that this is the Command Prompt; `start mspaint` explains; `date`/`time` show the clock and point to Settings; `net user|use|share|view` explain; `taskkill /IM name` plans for a single match, lists PIDs for several, reports not found otherwise.
- **Observed result:** integration in the VM: `taskkill /IM sleep` planned for the test's own child (or listed PIDs when other sleeps existed) and the child kept running; `explorer <tmp folder>` reported "Opened in Files" with the folder and its `C:\...` spelling and a Nautilus window existed; a missing folder failed plainly; `start calc` started Calculator ("Started Calculator."), `start cmd` answered, `start mspaint` explained, an unknown name failed with the Apps hint. Unit: classes and parse results for every new spec, teaching entries as NO_EQUIVALENT, date/time output, net teaching and arity, taskkill by unknown name. Host and VM `tools/dev.py all` clean; VM unit 131 passed.
- **Tests/checks:** `pytest tests/integration/test_familiar_vm.py -m integration` in the session; `tools/dev.py all`.
- **Artifacts/logs:** session transcript.
- **Failures/limitations:** `start` knows six program names; anything else must be a path or address; `net start|stop` targets system services only (like `sc`); the Files window opened by `explorer` stays open after the test.
- **Evidence state:** INTEGRATION_VERIFIED and DESKTOP_VERIFIED on Ubuntu 24.04.5

### TOOL-05 — Read-only tools run unmodified on Linux

- **Timestamp:** 2026-09-20 11:10 PM CDT
- **Candidate revision:** bbd29fa
- **Environment/profile:** as ENV-02 above; Python 3.12.3.
- **Files/modules:** `tools/tb.py`, `tools/tbtools/*`
- **Invariant impact:** none (engineering tooling)
- **Expected result:** `python3 tools/tb.py all` exits 0 with the same counts as on Windows; navigation commands work; timestamps are Central.
- **Observed result:** links 0/0/0 (33 links, 87 mentions); invariants 233 INV / 30 SEC / 30 IA, 0 findings; terms 0 error 0 warn 5 info; headers 15/15; exit 0. `tb status`, `tb inv show 023`, `tb section`, `tb snapshot` worked; stamp `2026-09-20 11:10 PM CDT` (zoneinfo path).
- **Tests/checks:** tree exported with `git archive HEAD`, extracted to `~/tb` in the guest, commands run over SSH, copy removed afterwards.
- **Artifacts/logs:** command output captured in session transcript; counts identical to the Windows run of the same revision.
- **Failures/limitations:** `tb.ps1` and `tb-env.ps1` not exercised in the guest (pwsh absent). No git repository in the guest copy, so `git:` reported none.
- **Evidence state:** DISTRO_VERIFIED
