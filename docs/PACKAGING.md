# Trier Bridge Packaging

**Task:** SCOPE-03  
**Status:** Design constraints and recommendation. Formal freeze is ledger task ARC-11, after the stack is chosen.  
**Governing:** DEC-016, DEC-018, DEC-019; TB-INV-024 to 030, 168, 172, 219 to 225  
**Evidence base:** `tb-ubuntu-desktop-2404` probe, 2026-09-20: apt 2.8.3 with `ubuntu.sources`; snapd 2.76 with 11 snaps including Firefox, Thunderbird, and the App Center (`snap-store`); `gnome-software` absent; Flatpak absent

## 1. Constraints that decide the format

1. **System integration needs.** The application talks to the system D-Bus (systemd, NetworkManager, udisks2, PackageKit, polkit), registers a GNOME Shell search provider, and loads a Nautilus extension. Sandboxes built to prevent exactly that access are the wrong tool.
2. **Non-invasive (DEC-018).** The package must be visible in Installed Apps, uninstall cleanly, and never enable a daemon or touch user homes.
3. **Ubuntu first (DEC-016).** The format must be native to Ubuntu 24.04 and its derivatives.
4. **Trust stays native (TB-INV-168).** Installation goes through the distribution's package trust; no curl-pipe-shell installers, no unsigned tarballs.

## 2. Formats considered

| Format | Verdict | Reason |
|---|---|---|
| **Native `.deb`** | **Core format** | Full system access, first-class in apt and the App Center, standard ownership and uninstall semantics, lintian and dpkg tooling, per-file ownership tracking satisfies TB-INV-026. |
| Snap, strict confinement | Not a candidate for the core | Strict confinement blocks Nautilus extensions and much system-bus access; polkit prompts and search providers need interfaces that are not granted automatically. |
| Snap, classic confinement | Deferred | Would work technically but classic snaps require Canonical review, and the App Center is a secondary distribution channel for a system tool. Revisit only if Ubuntu users demand it. |
| Flatpak | Excluded | Absent on the first target and sandboxed by design; portals do not cover service, network, or package control. |
| AppImage | Excluded | No uninstall tracking, no dependency declaration, no update trust, and it would look like the kind of drop-in binary DEC-018 exists to avoid. |
| Distribution-hosted (Ubuntu archive) | Long-term goal, not first release | Requires a stable, reviewed package; pursue after qualification. |

## 3. What the `.deb` contains

| Path | Contents | Owner |
|---|---|---|
| `/usr/bin/trier-bridge` | launcher for the Bridge window | package |
| `/usr/lib/trier-bridge/` | application code and adapters | package |
| `/usr/share/applications/` | one visible launcher; the familiar-tool entries with `NoDisplay=true` until a user enables them (`DELIVERY-MODEL.md` section 3) | package |
| `/usr/share/gnome-shell/search-providers/` | not used; the search provider is enabled per user under `~/.local/share/` so setup choice controls it | — |
| `/usr/share/trier-bridge/integrations/` | the Files extension source (`tb_nautilus.py`), inert until the user turns the integration on; it is then copied under the user's home and removed from there when turned off | package |
| `/usr/share/trier-bridge/` | concept catalog data, help content, integration catalog, icons (original assets only) | package |
| `/usr/share/doc/trier-bridge/` | `copyright` (Apache-2.0), `NOTICE`, changelog | package |
| `/usr/share/man/man1/trier-bridge.1` | man page | package |
| `~/.config/trier-bridge/`, `~/.local/share/trier-bridge/` | preferences, integration ledger, operation journal, audit | user (created by the app, never by the package) |

Not in the package: polkit rules (never), a systemd system service (none in the first release), autostart entries (per user, by setup only), shell hooks, cron jobs, or anything under `/etc`.

## 4. Install, upgrade, and remove behavior

- **postinst** only refreshes caches the distribution expects (desktop database, icon cache). It never starts a process, never enables a unit, never writes to `/home`.
- **prerm / postrm** remove only files the package owns. `purge` additionally removes package configuration; it still does not touch user homes. Users are told, inside the app and in the man page, how to remove per-user state (TB-INV-026).
- **Upgrade** keeps per-user state; schema migrations are performed by the app on next launch, forward-only with a backup of the previous state file (TB-INV-028, TB-INV-029). A downgrade opens the state read-only if the schema is newer (TB-INV-029).
- **Failed install** leaves the system exactly as before; dpkg's own transaction semantics cover this, and postinst does nothing that can half-complete (TB-INV-027).
- **Architecture** is declared (`amd64` first); dpkg refuses mismatches (TB-INV-030).
- **Dependencies** are declared explicitly and kept minimal. Every runtime dependency is justified in the dependency inventory (`CODE-QUALITY.md` section 21). A dependency already present on Ubuntu Desktop by default costs nothing; one that pulls a new stack onto the machine is a review item.

## 4a. Clean build

A clean build uses `sbuild` with a `noble` buildd chroot that carries **main and universe** (`pybuild-plugin-pyproject` is in universe): `sudo sbuild-createchroot noble /srv/chroot/noble-amd64-sbuild http://archive.ubuntu.com/ubuntu`, then add `universe` to the chroot's `/etc/apt/sources.list`, then `dpkg-buildpackage -S -us -uc -d` and `sbuild -d noble trier-bridge_<version>.dsc`. The result must match `dpkg-buildpackage -us -uc -b` from the same tree byte for byte; it does when the top `debian/changelog` entry is not dated in the future (`SOURCE_DATE_EPOCH` comes from that date and only clamps mtimes newer than it). Evidence: `VALIDATION.md` entry IMP-08.01.

## 5. Updates

First release: updates arrive the same way the package did. Until a signed repository exists, that means a new `.deb` installed by the user. No self-update mechanism is built (ARC-12: deferred by this document). When a repository is introduced, it is signed with a project key, the key handling is an owner-gated release step (TB-INV-219), and the app's Updates view shows Trier Bridge updates through PackageKit like any other package.

## 6. Build and release requirements

- Reproducible build from a clean checkout of a tagged revision; the build records the source revision, toolchain versions, and the resulting package hash (TB-INV-223).
- `lintian` clean or with each override justified.
- Package contents diffed against the ownership table above before release.
- Install, upgrade, and remove tested on the VM from the `clean-install` checkpoint, with a file-system diff before and after (TB-INV-025 to 027).
- License files present in the package; source headers verified by `tb headers`.
- Nothing is published: builds stay local until the owner authorizes release (AGENTS.md section 14).

## 7. Derivatives

An Ubuntu 24.04 `.deb` is expected to install unchanged on derivatives that track that base (Linux Mint 22, Zorin OS 17, Pop!_OS 24.04). Expected is not qualified: each derivative gets its own install/upgrade/remove run and its own evidence entry before any support statement (DEC-016, TB-INV-231).

## 8. Stack dependency

The stack decision changes the package's runtime dependencies, not its shape. A Python application depends on `python3` and `python3-gi` (both preinstalled on Ubuntu Desktop) plus `python3-nautilus` if the Files integration uses it; a compiled application depends on GTK/libadwaita shared libraries (also preinstalled) and ships its own binary. Both fit the layout above. ARC-11 freezes the exact control file after ARC-01.
