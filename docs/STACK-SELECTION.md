# Trier Bridge Implementation Stack Selection

**Tasks:** ARC-01 (language/runtime), ARC-02 (desktop framework)  
**Status:** ACCEPTED as DEC-020 on 2026-09-21 under owner delegation. Frozen for Foundation 01.  
**Inputs:** `DELIVERY-MODEL.md` section 7, `PRIVILEGE-MODEL.md` section 7, `PACKAGING.md` section 8, `RESEARCH.md` findings F12, F15, F16, F17  
**Date:** 2026-09-21 (evidence gathered 2026-09-20 in `tb-ubuntu-desktop-2404`)

## 1. What the stack must do

From the accepted decisions and the delivery model, the first-release stack must, on Ubuntu 24.04 without adding runtime dependencies the desktop lacks:

1. speak session and system D-Bus fluently (proxies, properties, signals, polkit interaction flags);
2. render an accessible, libadwaita-styled window on Wayland that Orca can read;
3. provide a GNOME Shell search provider and a StatusNotifier tray item;
4. provide a Nautilus extension;
5. read `/proc`, `/sys`, and the journal without shelling out;
6. package as a native `.deb` with a small, justified dependency list;
7. be reviewable by contributors who are not systems specialists (CONTRIBUTING levels 1 and 2).

## 2. Candidates

| Candidate | Runtime already on target | D-Bus | AT-SPI on Wayland | Nautilus extension | Package footprint | Assessment |
|---|---|---|---|---|---|---|
| **A. Python 3.12 + PyGObject + GTK 4 / libadwaita** | yes: `python3` 3.12.3, `python3-gi` 3.48, GTK 4.14, libadwaita 1.5 preinstalled | Gio/GDBus, verified live (F15) | verified live (F17) | `python3-nautilus` 4.0 in the archive | architecture-independent `.deb`; one optional dependency | **Recommended** |
| B. Rust + gtk4-rs / libadwaita-rs + zbus | GTK/libadwaita yes; Rust toolchain no (archive has 1.75, older than current gtk4-rs needs) | zbus, mature | expected equal to A (same GTK), not yet verified | native `.so` via C ABI; bindings immature | compiled binary; build needs a pinned rustup toolchain and vendored crates | Strong runtime, higher build and contributor cost; keep as the path for any hotspot |
| C. C or Vala + GTK 4 | yes | GDBus | same as A | native, the reference way | compiled binary | Slowest to develop and review for this project's contributor profile |
| D. Web-view stacks (Tauri, Electron) | no: webkitgtk or bundled Chromium runtime | via native side only | weaker; web content trees are not native AT-SPI | no | tens to hundreds of MB, foreign look | Conflicts with DEC-018 and with blending into GNOME |
| E. Qt 6 / PySide6 | no: Qt libraries absent on Ubuntu GNOME | QtDBus | qt-at-spi, good | no | adds Qt runtime | Right choice for a KDE-first product; the first target is GNOME |

## 3. Recommendation

**ARC-01: Python 3.12 with PyGObject. ARC-02: GTK 4 with libadwaita.**

Why:

- **Zero added runtime on the first target.** Every library is already installed on Ubuntu Desktop 24.04 (F12). The package adds Trier Bridge and, if the Files integration is selected, `python3-nautilus`. That is the most literal form of DEC-018 clause (a).
- **Every gate verified live, not assumed.** D-Bus reads of systemd, NetworkManager, UDisks2, PackageKit, login1, and a non-prompting polkit check (F15); a D-Bus-activated search provider answering Windows terms (F16); AT-SPI exposure of button, description, and switch on Wayland (F17).
- **It blends in.** libadwaita is what GNOME Settings and Ubuntu's own tools use, so familiar-looking Trier Bridge views look like they belong, which matters for "not mistaken for a virus."
- **Reviewability.** Python plus typed operation schemas is readable by the widest contributor pool; the invariants demand review depth on privilege and recovery paths, and readable code makes that review real.
- **The system boundary is D-Bus either way.** The language does not change the security model: no shell, no root, typed operations, polkit-mediated services (`PRIVILEGE-MODEL.md`).

Known costs, and how they are handled:

| Cost | Mitigation |
|---|---|
| Interpreter start-up and per-widget overhead | Measure against the budgets in `ENGINEERING.md` section 11 from Foundation 01 onward; the Bridge window is a single long-lived process per session, so start-up is paid once. |
| Monitoring cost (Task Manager sampling) | Read `/proc` directly with adaptive sampling (TB-INV-199, 200); pause when hidden. If a hotspot proves too slow, a small compiled helper library (Rust or C) sits behind the same adapter interface; no rewrite. |
| Dynamic typing | `mypy --strict` on the operation core and adapters; typed schemas for every operation and result; no `Any` at trust boundaries. |
| Python versions across derivatives | Minimum is Ubuntu 24.04's 3.12 and PyGObject 3.48; derivatives are qualified individually (DEC-016). |
| Source is readable in the package | The project is Apache-2.0; readability is a feature, and provenance headers ride along (`LICENSING.md`). |

Rejected alternatives are recorded above so the decision can be revisited with new evidence rather than re-argued from memory.

## 4. Rules that come with the stack

- No `subprocess` with a shell; fixed argv only where a native API truly does not exist, and each such case reviewed (`CODE-QUALITY.md` section 12).
- All system interaction through Gio D-Bus or direct file reads; no parsing of localized CLI output where an API exists (TB-INV-045).
- No third-party Python packages at runtime beyond what Ubuntu ships; development-only tools (formatter, linter, type checker, test runner) are pinned in Foundation 01.
- Nautilus integration prefers the `python3-nautilus` extension; the scripts-folder route stays as the dependency-free fallback.

## 5. What Foundation 01 pins if this is accepted

- Python 3.12.x, PyGObject 3.48.x, GTK 4.14.x, libadwaita 1.5.x as minimum versions (the Ubuntu 24.04 set).
- Development tools: `ruff` (lint and format), `mypy` (strict), `pytest` (with real objects only, per `TEST-STRATEGY.md`), `lintian` for packages.
- Module skeleton following `ENGINEERING.md` section 4; source headers verified by `tb headers`.
- The first measured baseline for `CODE-QUALITY-REPORT.md`.

## 6. Decision requested

Accept ARC-01 and ARC-02 as above (recorded as DEC-020, proposed), or name the alternative to evaluate further. Evaluating candidate B live in the VM is possible once a Rust toolchain can be installed there (requires sudo in the guest).
