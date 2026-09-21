# Trier Bridge Delivery Model

**Task:** SCOPE-01  
**Status:** Design. No implementation exists.  
**Governing decisions:** DEC-018 (non-invasive), DEC-019 (one integrated build, user intent decides integrations), DEC-016 (Ubuntu 24.04 LTS first)  
**Governing invariants:** TB-INV-001, 005, 008, 010, 021, 022, 025, 026, 064, 074, 075, 076, 077, 106  
**Evidence base:** in-guest probe of `tb-ubuntu-desktop-2404`, 2026-09-20 (see `RESEARCH.md` section 4)

## 1. What Trier Bridge is on the desktop

Trier Bridge is one installed application plus a set of desktop integrations that the user switches on at setup. It never replaces the shell, the file manager, the login screen, or the terminal. Everything below runs as the signed-in user; nothing runs as root (see `PRIVILEGE-MODEL.md`).

| Component | What it is | Runs when |
|---|---|---|
| **Bridge window** | The application: launcher/search home, familiar file entry points, settings routing, system tools (Task Manager, Installed Apps, Network Connections, Device Manager, Disk Management, Event Viewer, Services), Bridge Terminal, Help, and the Integrations page. One unprivileged process per user session. | When the user opens it. |
| **Tray icon "T"** | A StatusNotifier/AppIndicator icon whose menu opens the window, the Integrations page, and Quit. | Only if the user selected it at setup; then it starts at login through a per-user XDG autostart entry. |
| **Integrations** | Small, individually reversible hooks into the desktop's own extension points (section 3). | Only those the user selected. |
| **Typed operation core** | The trusted logic that turns intent into typed operations, validates, authorizes through Linux, executes through adapters, and verifies. | Inside the Bridge window process (topology finalized in SCOPE-10). |

The user who installs the package and then opens Trier Bridge has expressed the opt-in that TB-INV-077 requires. Nothing is activated before that user clicks Apply on the setup screen.

## 2. First-run setup

Native packages install silently (apt has no UI), so the setup screen appears on the first launch of the Bridge window, not during package installation.

1. Package installs files under `/usr` only. No daemon is enabled, no autostart is written, no user home is touched (TB-INV-025).
2. The user opens Trier Bridge from the application grid (its `.desktop` entry is the one visible entry the package provides).
3. The setup screen shows every integration, organized into groups. A recommended group is preselected but nothing is applied until the user clicks Apply. Each item states in one line what it changes and how it is undone.
4. Apply writes only per-user files under `~/.config/trier-bridge/`, `~/.local/share/`, and `~/.config/autostart/`, and records what it wrote in an integration ledger so removal is exact.
5. The same page is reachable any time from the tray icon and from the window. Toggling an item off removes exactly what it added. "Remove all integrations" restores the pre-setup state.

Uninstalling the package removes everything under `/usr`. Per-user files are the user's; the package cannot safely walk every home directory, so Trier Bridge offers "Remove all integrations" before uninstall and documents the per-user paths (TB-INV-026).

## 3. Integration catalog (seed for SCOPE-14)

Every entry names its desktop extension point, the exact reversal, and the evidence that the extension point exists on the first target. Global key/mouse rebinding and file-association changes are individual items and never part of a default group (DEC-019).

| Group | Item | Extension point | Reversal | Evidence (Ubuntu 24.04.5 GNOME 46) |
|---|---|---|---|---|
| **Essentials** (recommended) | Tray icon at login | `~/.config/autostart/trier-bridge-tray.desktop`; StatusNotifier via the AppIndicator extension | delete the autostart entry | `ubuntu-appindicators` enabled by default |
| Essentials | Familiar tool names in the app grid and Activities search (Task Manager, Event Viewer, Device Manager, Disk Management, Services, Network Connections, Installed Apps, Command Prompt) | package-provided `.desktop` entries hidden by default; setup unhides them per user via `~/.local/share/applications/` overrides | restore the override files | 113 system `.desktop` entries; user overrides directory present |
| Essentials | Windows-term search in Activities ("Add or Remove Programs" finds Installed Apps) | GNOME Shell `SearchProvider2` D-Bus interface plus a provider `.ini` | remove the user provider `.ini` | 8 providers installed; interface XML present |
| **Files** | "Trier Bridge" actions in the Files right-click menu (Open Command Prompt here, familiar Properties, Send to) | Nautilus extension API (libnautilus-extension 4; `python3-nautilus` in the archive) or, with no dependency, the Nautilus scripts folder | remove the extension or script files | `libnautilus-extension.so.4` present; `python3-nautilus` 4.0 available; scripts dir exists |
| Files | "This Computer" and familiar places on the desktop | desktop launcher files shown by the Desktop Icons extension | delete the launchers | `ding` extension active |
| **Shortcuts** (individual items) | Ctrl+Shift+Esc opens Task Manager | per-user GNOME custom keybinding via gsettings | remove the keybinding entry | GlobalShortcuts portal absent on 24.04; gsettings route is the supported one |
| Shortcuts | Super+E opens the file entry | same mechanism; only bound if free | same | conflict check required before binding (TB-INV-076) |
| **Notifications** | Operation results as desktop notifications | Notification portal / GNOME notifications | disable in preferences | portal present |
| **Advanced** | PowerShell entry uses real `pwsh` | invokes an installed `pwsh`; never bundled | nothing to undo | `powershell` 7.6.5 available as a snap |

Explicitly not offered, ever: global mouse behavior changes, theme changes, replacing the default file manager, terminal, or browser, shell startup file edits, kernel modules, system-wide polkit rules (TB-INV-077, TB-INV-112, DEC-018).

## 4. How the everyday layer works without replacing anything

- **Files, right-click, drag and drop** stay in Nautilus. Trier Bridge adds menu actions and provides familiar entry points that open Nautilus at the right place. It does not draw its own file manager.
- **Launcher and search** stay GNOME's. The search provider makes Windows vocabulary resolve to Trier Bridge routes and native destinations; the Bridge window's own search does the same for users who prefer one place.
- **Settings** are routed: a familiar category opens the right GNOME Settings panel or, where GNOME has no panel, a Trier Bridge view (for example Services). Default applications are changed through the standard per-user `mimeapps.list` route (`xdg-mime`), never system-wide.
- **Screenshots and clipboard** use the Screenshot portal and GNOME's own tools; Trier Bridge only teaches the keys.
- **Installed Apps** aggregates apt and snap on the first target (Flatpak is absent there) while preserving provenance (TB-INV-072).

## 5. Session and user model

- One Bridge window per user session; a second launch focuses the first.
- Preferences and integration state are per user. System-wide policy, if ever added, is a separate opt-in for administrators (TB-INV-215).
- The application is a Wayland-native client on the first target. It never grabs global input, never sets itself as a compositor plugin, and leaves window management to GNOME (TB-INV-022). X11 sessions are treated as a distinct capability surface with their own evidence.

## 6. Non-invasive checklist (DEC-018 mapped to this model)

| DEC-018 clause | How the delivery model satisfies it |
|---|---|
| (a) ordinary package, visible, clean uninstall | native package under `/usr`; one visible launcher; per-user files documented and removable from inside the app |
| (b) never replaces shell, file manager, login, terminal | integrations only through Nautilus extension points, search providers, launchers, gsettings |
| (c) no background process unless chosen | tray icon is a setup item; no daemon, no system service of its own for the first release |
| (d) no autostart, rebinding, or association takeover by default | autostart only with the tray item; shortcuts are individual items; defaults changed only by explicit user action |
| (e) no hidden privileged component | no helper at all in the first release; polkit-mediated system services only (`PRIVILEGE-MODEL.md`) |
| (f) no telemetry, no network outside invoked features | none; package metadata refresh only when the user opens Updates |
| (g) writes only to its own XDG locations | integration ledger records every written path |
| (h) no injection, preload, modules, shell hooks | none |
| (i) inspectable | integration ledger, audit journal, "what changed" on every operation, Show Me the Linux Way |

## 7. Inputs to stack selection (ARC-01/ARC-02)

The delivery model needs a stack that can, on Ubuntu 24.04 without adding runtime dependencies the target lacks:

- talk to the session and system D-Bus, including polkit-mediated calls and signals;
- implement a GNOME Shell search provider (a D-Bus service) and a StatusNotifier item;
- provide a Nautilus extension (Python through `python3-nautilus`, or a native shared object through `libnautilus-extension`);
- render a libadwaita-styled, accessible (AT-SPI on Wayland) window so it blends with Ubuntu's own settings and tools;
- package cleanly as a `.deb`.

Observed on the target: `python3-gi`, GTK 4.14, and libadwaita 1.5 are preinstalled; Rust 1.75, Go 1.22, Qt 6.4, and Node 18 are available in the archive but not installed. The recommendation is made in ARC-01 with alternatives and rationale.

## 8. Open items

- SCOPE-14: full integration catalog with group definitions and the setup/tray UI flow.
- DOC-02/DOC-03: exact familiar-file and search/settings routing behavior.
- ARC-10: whether X11 sessions are in the first-release matrix.
- Evidence still needed on the first target: a search provider registration and a Nautilus extension load, each verified live before either integration is claimed.
