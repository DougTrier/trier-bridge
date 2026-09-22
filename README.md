# Trier Bridge
## Everything You Know. Linux Underneath.

**Version:** 1.0.0  
**Author:** Doug Trier  
**License:** Apache License 2.0

> **Trier Bridge is designed so a Windows user can move to Linux without feeling like they have to relearn how to use a computer.**

Trier Bridge is an installable **Windows-to-Linux experience compatibility layer** for Ubuntu Desktop.

It is not another Linux distribution and it is not a Windows emulator.

The goal is to preserve the useful knowledge Windows users already have:

- files and folders
- right-click
- drag and drop
- copy / cut / paste
- application launching
- search
- printers
- USB devices
- network shares
- Wi-Fi
- common settings
- default applications
- installed applications
- updates
- screenshots
- task switching
- familiar troubleshooting

Power users and advanced Windows users should additionally find familiar paths for:

- Task Manager
- Startup Apps
- Device Manager
- Disk Management
- Network Connections
- Event Viewer
- Services
- Command Prompt
- PowerShell

Linux remains authoritative underneath.

---

## Product North Star

> **Everything a Windows user already knows how to do should have a familiar place to go on Linux.**

The primary target is the normal office/home Windows user through advanced Windows users.

The experience priority is:

1. **Everyday continuity**
2. **Familiar troubleshooting**
3. **Advanced Windows continuity**
4. **Optional Linux learning**

**Learning Linux is optional. Productivity is not.**

---

## Example

A normal user should not need to know:

```bash
ip addr
journalctl
systemctl
lsblk
```

just to perform tasks they already understood on Windows.

Trier Bridge can expose familiar concepts such as:

```text
Network Connections
Event Viewer
Services
Disk Management
```

and translate those actions through qualified Linux-native mechanisms.

Advanced users can optionally see the native Linux details.

---

## Bridge Terminal

A Windows user enters familiar commands:

```text
C:\Users\You> ipconfig
```

Trier Bridge does **not** perform unsafe text substitution into Bash.

The architecture is:

```text
Windows-style input
        ↓
strict parser
        ↓
typed Trier Bridge operation
        ↓
capability + security validation
        ↓
Linux-native adapter
        ↓
verified result
        ↓
familiar output
```

If no safe or faithful equivalent exists, Trier Bridge says so and performs no hidden substitution.

---

## Engineering Philosophy

Trier Bridge was designed before it was built, around several permanent principles:

- **local first**
- **Linux remains authoritative**
- **no destructive guessing**
- **least privilege**
- **typed operations instead of shell-string translation**
- **capability detection instead of distro assumptions**
- **stable target identity before mutation**
- **failure containment**
- **explicit recovery**
- **truthful support claims**
- **progressive disclosure**
- **accessibility**
- **evidence before PASS**

If Trier Bridge cannot prove that it knows what it is about to do, to exactly what target, with the right authority, and with a defined recovery path, it does not do it.

---

## Install

Trier Bridge ships as one Debian package for Ubuntu 24.04 Desktop: `trier-bridge_1.0.0_all.deb` (about 140 KB; it depends only on what Ubuntu Desktop already has: Python 3, GTK 4, libadwaita).

**Without a terminal.** Right-click the `.deb` in Files → *Open With* → **App Center**, tick *Always use for this file type*, then press Install. From then on a double-click installs. (On a stock Ubuntu 24.04 the archive viewer is the default for `.deb` files, so the first time needs that one choice; once Trier Bridge is installed, *Apps → Default apps → Software installers (.deb)* offers the same choice inside the app.)

**With a terminal**, if you prefer:

```bash
sudo apt install ./trier-bridge_1.0.0_all.deb
```

Everything Trier Bridge writes lives in your home folder (`~/.config/trier-bridge`, `~/.local/state/trier-bridge`); removing the package leaves those, like a Windows uninstall leaves AppData. It never installs or removes other software, never runs as root, and asks Linux (polkit) for permission each time a change needs it.

## Screenshot

![Home: the accent-framed shell, the goal paragraph, the Windows-vocabulary search, and the Start-here cards](docs/screenshots/home.png)

Rendered from the installed 1.0.0 package on my Ubuntu 24.04 test VM (960×640, the default window size).

## What's in 1.0.0

- **Everyday:** Home — type what you would look for on Windows and go to the Linux place for it; Files, with an in-app browser and drive letters (`C:`, `D:`) shown as labels next to the real Linux paths; Apps, with where each program came from and a Default apps chooser; Settings, routed to the desktop's own panels; Printers; Network, as a translation layer over NetworkManager.
- **Troubleshooting:** Task Manager (End task, live Performance graphs for CPU, memory, every disk and adapter); Event Viewer; Device Manager; Startup Apps; Disk Management.
- **Advanced:** Services (changes go through Linux's own permission prompt); Command Prompt and PowerShell names, turned into typed operations — nothing is ever passed to a shell; System Information.
- **Integrations you choose at setup, each reversible:** tray icon, desktop search that understands Windows words, familiar launchers in the app grid, a Files context-menu entry, Ctrl+Shift+Esc.

## How it is built

- **Typed operations, never shell text.** A Windows-style command becomes a parsed, typed operation with a fixed argument list; nothing you type is ever handed to a shell. If there is no faithful Linux equivalent, Trier Bridge says so and does nothing.
- **Linux stays in charge.** Nothing runs as root. Any change that needs permission (a service, a network setting, ending a system process) goes through Linux's own prompt, every time.
- **Honest about what it knows.** A value it cannot read shows as Unknown, never as zero. An action interrupted mid-way is shown to you afterward, never silently repeated.
- **Verified on the real thing.** Every change is gated on a real Ubuntu 24.04 desktop — tests run against real files, real processes, real services, with no mocks. The package is reproducible and lintian-clean. The **258 invariants** in `docs/INVARIANTS.md` each trace to evidence tied to a commit hash in `docs/VALIDATION.md`, and the code-quality score in `CODE-QUALITY-REPORT.md` is measured, not asserted.

## What's next

- Builds for Linux Mint and Zorin.
- A package repository, so updates arrive the normal Ubuntu way.
- More of the Windows vocabulary in Home search.

---

## Documentation

Core project documentation is intended to live under `docs/`.

Start with [`docs/README.md`](docs/README.md), then:

- [`docs/PRODUCT-CONCEPT.md`](docs/PRODUCT-CONCEPT.md)
- [`docs/PRODUCT-NORTH-STAR.md`](docs/PRODUCT-NORTH-STAR.md)
- [`docs/ENGINEERING.md`](docs/ENGINEERING.md)
- [`docs/SECURITY.md`](docs/SECURITY.md)
- [`docs/INVARIANTS.md`](docs/INVARIANTS.md)
- [`docs/DECISIONS.md`](docs/DECISIONS.md)
- [`docs/CODE-QUALITY.md`](docs/CODE-QUALITY.md)
- [`docs/PLATFORMS.md`](docs/PLATFORMS.md)
- [`docs/EXPERIENCE.md`](docs/EXPERIENCE.md)
- [`docs/VALIDATION.md`](docs/VALIDATION.md)

Repository-root control documents:

- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`AGENTS.md`](AGENTS.md)
- [`CONTEXT.md`](CONTEXT.md)
- [`Engine Spec Tasklist 01.MD`](Engine%20Spec%20Tasklist%2001.MD)
- [`CODE-QUALITY-REPORT.md`](CODE-QUALITY-REPORT.md)
- [`LICENSE`](LICENSE)
- [`NOTICE`](NOTICE)

---

## What Trier Bridge Is Not

Trier Bridge is not:

- another Linux distribution
- a Windows emulator
- Wine replacement
- a Windows application compatibility runtime
- a theme pack
- a collection of shell aliases
- a product that requires terminal knowledge
- a Linux administration course
- a reason to weaken Linux security

It is:

> **A Windows-to-Linux experience compatibility layer.**

---

## License

Apache License 2.0.

Copyright © 2026 Doug Trier.

See `LICENSE`, `NOTICE`, and `docs/LICENSING.md`.
