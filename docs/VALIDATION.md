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
