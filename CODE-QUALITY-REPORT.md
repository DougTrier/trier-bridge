# CODE-QUALITY-REPORT.md
# Trier Bridge Code Quality Report

**Candidate:** commit `078048d` (Foundations 01–05, 06/07 partial, SCOPE-14 integrations)  
**Timestamp:** 2026-09-21 04:05 AM CDT  
**CQS:** **NOT MEASURED**  
**Assessed weight:** 85 / 100 (seven of eight categories have current evidence)  
**Observed on assessed weight:** 78.5 of 85 (not normalized to 100 by rule)  
**Release quality:** NOT ASSESSED (no release candidate; release locked)

Rubric: `docs/CODE-QUALITY.md` section 1. Each criterion is 0, 0.5, or 1 with evidence. A category with any unmeasured criterion is NOT MEASURED as a whole; a numeric CQS exists only when all eight categories are measured.

---

## Scope and tools

| Item | Value |
|---|---|
| Source scope | `trier_bridge/` (9,782 lines, 57 files), `tests/` (2,203 lines, 28 files: unit and integration), `tools/dev.py`, `data/integrations/tb_nautilus.py` |
| Environment | `tb-ubuntu-desktop-2404` (Ubuntu 24.04.5, GNOME 46 Wayland) and Windows host `.venv` with identical tool versions |
| Tools | black 24.2.0, flake8 7.0.0 (pyflakes 3.2.0, pycodestyle 2.11.1, mccabe 0.7.0), mypy 1.9.0 `--strict`, pytest 7.4.4, lintian 2.117.0 |
| Commands | `python3 tools/dev.py all`; `flake8 --select=C901 --max-complexity=10 trier_bridge`; `dpkg-buildpackage -us -uc -b`; `lintian`; a read-only metrics script (line counts, suppression and broad-catch inventory, longest functions) |
| Test results | host: 94 unit passed, 3 skipped (2 need `gi`, 1 needs POSIX permission bits); VM: 102 unit passed, 38 integration passed, 1 skipped |

---

## CQS categories

| Category | Weight | Criteria (0 / 0.5 / 1) | Score | State |
|---|---:|---|---:|---|
| Architecture / boundaries | 20 | purposes and dependency direction documented in package docstrings and `docs/ENGINEERING.md` (1); acyclic: `core` imports only the standard library; `system`, `state`, `operations`, `bridge`, `integrations` import `core`/`config`; `ui` imports all of them; nothing imports `ui` except `__main__` (1); single mutable-state authority per kind: `config.py` writes files, `state/journal.py` owns operation records, `state/preferences.py` owns preferences, `integrations/ledger.py` owns the integration record; UI holds none (1); explicit domain/interfaces/adapters: typed `Operation`/`OperationResult`, `StableIdentity` protocol, adapters `system/*` behind `Bus` (1); cohesive responsibilities, no generic managers (1) | 20 | MEASURED |
| Readability / naming | 15 | Trier Bridge vocabulary throughout (Operation, CapabilityState, ProcessIdentity, UnitIdentity, TerminatePlan, Integration, AppliedIntegration) (1); accurate names, two renamed during review (`has_ended`, `_remove_compiled_copies`) (1); understandable control flow: the fourteen functions above cyclomatic 10 are dispositioned below; one (`execute_service`, 131 lines) is flagged for splitting (0.5); consistent state/result terms matching `docs/STATE-AND-PERSISTENCE.md` (1); coherent module scope (1) | 13.5 | MEASURED |
| Complexity | 15 | cyclomatic: 14 functions above 10, maximum 18 (`execute_service`, `MainWindow._build_page`), all dispositioned below; `read_devices` reduced from 30 to below 11 this candidate (0.5); cognitive complexity: no tool in the pinned toolchain, not measured (NM); nesting review: deepest nesting four levels in `execute_service` (0.5); function/module scope: longest function 131 lines (`execute_service`), largest module `ui/window.py` 430 lines (0.5); duplicated decision review: one state machine, one identity comparison per kind, one redaction function, one atomic write, one ledger (1) | — | **NOT MEASURED** (one criterion) |
| Documentation / rationale | 15 | API ownership/errors/side effects in module and class docstrings (1); privilege/security assumptions stated (`operations/*`, `integrations/*`, `bridge/*`) (1); persistence/recovery documented (`config.py`, `state/journal.py`, `integrations/ledger.py`) (1); concurrency/lifecycle: background sampling threads in `ui/taskmanager.py`, `ui/sysinfo.py`, and page loaders hand results to the main loop through `GLib.idle_add`; the contract is stated in those modules but not yet in `docs/ENGINEERING.md` (0.5); compatibility decisions cite `TB-INV-###` and decision IDs (1) | 13.5 | MEASURED |
| Testing / regression | 15 | tests map to invariants by `TB-T###` in docstrings (1); 94 unit tests on real files and real child processes, no mocks (1); integration/negative tests against live services: 38 in the VM (systemd, NetworkManager, udisks2, journald, sysfs, D-Bus activation, loopback ext4 faults, denial paths) (1); failure/lifecycle/recovery cases: state-machine refusals, disk-full and kill-mid-write journal recovery, stale target cancel, PARTIAL restart, denied system-scope call, read-only ledger (1); candidate-specific regression evidence: same revision run on host and VM, plus the installed `.deb` exercised through AT-SPI (1) | 15 | MEASURED |
| Static-analysis health | 10 | build diagnostics: package builds with no warnings; lintian silent (1); lint and type analysis: flake8 and mypy strict clean (1); security/safety findings: no dedicated analyzer; manual grep shows zero subprocess/shell/os.system in the product, the single match is a docstring saying so (0.5); suppression inventory: 108, all of two documented kinds, listed below (1); resource/nullability/unsafe/boundary warnings: mypy strict with `warn_unreachable` clean (1) | 9 | MEASURED |
| Dependency hygiene | 5 | necessity: no runtime dependency beyond Ubuntu Desktop defaults; `python3-nautilus` is a Recommends used only if the user turns the Files integration on (1); pins: `docs/TOOLCHAIN.md` and `debian/control` version floors (1); license/provenance: all first-party Apache-2.0 plus Ubuntu packages (1); maintenance/security/platform: Ubuntu 24.04 LTS set (1); transitive/package cost: 86 KB `.deb`, zero new packages pulled (1) | 5 | MEASURED |
| Dead code / duplication | 5 | unused paths: pyflakes clean (1); unreachable branches: mypy `warn_unreachable` clean (1); exact duplicates: none found by reading; the `Paths` name exists in both `config.py` (XDG app dirs) and `integrations/catalog.py` (user home dirs) and should be renamed (0.5); semantic duplicates / state authority: one authority each (1); standalone foundations distinguished and labelled (1) | 4.5 | MEASURED |

**Why NOT MEASURED:** the complexity category has no cognitive-complexity evidence because no such analyzer is in the pinned Ubuntu toolchain. Adding one is a toolchain change (`docs/TOOLCHAIN.md` section 5); until then this report lists the observed criteria separately, as the standard requires.

---

## Complexity outlier disposition (cyclomatic > 10)

| Function | CC | Disposition |
|---|---:|---|
| `operations/service.py: execute_service` | 18 | One function holds validate → revalidate identity → authorize → call → verify for five service actions and every error class. Kept correct but too long (131 lines, four nesting levels). **CQ-05: split into per-action verification helpers** without moving the failure classification. |
| `ui/window.py: _build_page` | 18 | A flat `if section.key == ...` dispatch that constructs one page per sidebar section. No nesting, no shared state; reads as a table. Kept; a dict of constructors would only move the branching. |
| `capability/discovery.py: Discovery.environment` | 17 | Reads a dozen independent facts (os-release, session, desktop, display server, init, package managers), each guarded so one missing source never hides the others. Kept; each branch is one fact with one fallback. |
| `system/processes.py: ProcessSampler.sample` | 16 | procfs parsing for every process with per-field tolerance. Kept; splitting per field would repeat the error handling. |
| `system/storage.py: read_storage` | 15 | udisks2 object walk with filters for loop/squashfs/EFI. Candidate for the same per-object helper split as `read_devices`. **CQ-06.** |
| `integrations/catalog.py: apply` | 14 | Dispatch by integration id plus rollback on any failure and on an unrecordable ledger. Kept; the rollback must see every step. |
| `bridge/grammar.py: tokenize`, `parse` | 13, 13 | The CMD-style tokenizer and parser; every branch is one grammar rule, each with a unit test. Kept. |
| `operations/process.py: execute_terminate` | 13 | Same shape as `execute_service` for TERM/KILL with zombie handling. Kept; shorter (83 lines). |
| `config.py: atomic_write_bytes` | 12 | The whole atomic-write protocol including temp-file creation failure (product defect found in Foundation 05). Kept; six unit tests plus disk-full and kill tests. |
| `ui/window.py: _on_row_selected` | 12 | Starts the page's loader for the selected section. Kept; flat. |
| `system/network.py: read_network` | 12 | NetworkManager object walk. Kept; flat per-device loop. |
| `catalog/model.py: Catalog.load` | 11 | Schema validation with one error per rule. Kept. |
| `integrations/tray.py: Tray.menu_call` | 11 | dbusmenu method dispatch. Kept; one branch per protocol method. |

---

## Suppression inventory (108)

| Kind | Count | Where | Reason |
|---|---:|---|---|
| `# noqa: E402` | 83 | every module that imports `gi.repository` | PyGObject requires `gi.require_version()` before importing `gi.repository`; imports after it are the documented pattern |
| `# type: ignore[misc]` | 20 | every `Gtk`/`Adw` subclass | mypy strict forbids subclassing an untyped base; `gi` has no complete stubs on the target |
| `# type: ignore[no-untyped-def]` | 5 | D-Bus method-call handlers in `integrations/search_provider.py` and `integrations/tray.py` | Gio hands the handler eight positional values whose types come from `gi`; annotating them as `Any` eight times would say the same thing with more noise |

No baseline files, no disabled rules, no lowered thresholds. Broad `except Exception` catches: 17, all at a UI or process boundary where the failure is reported to the user or logged and the operation is marked failed (`bridge/commands.py`, `config.py` cleanup path, `integrations/catalog.py` rollback paths, `ui/*` page loaders, `ui/app.py` dev snapshot). None swallows silently.

---

## Hard-gate status

| Gate | State | Evidence |
|---|---|---|
| Invariant violations | none known | tests cite TB-T IDs; `tb inv` reports no undefined references |
| Privilege boundary | no privileged code; system-scope calls go through polkit with `ALLOW_INTERACTIVE_AUTHORIZATION` | `docs/PRIVILEGE-MODEL.md`; `operations/service.py`; denial verified (entry IMP-06.05) |
| Shell injection | no shell use; every launch is a fixed argument list through GLib | zero subprocess/shell/os.system matches; Bridge Terminal rejects metacharacters whole (entry IMP-07) |
| Path traversal / symlink safety | writes only under XDG app dirs and, for integrations, recorded per-user paths | `config.py`; `integrations/ledger.py`; unit tests |
| Data-loss / recovery | atomic writes verified under disk-full and kill | entry IMP-05 |
| Stale-target mutation | identities revalidated before every mutation; stale cancels | entries IMP-06.04, IMP-06.05 |
| Package/update trust | native `.deb`; no update mechanism (DEC-022) | reproducible build (entry IMP-01); lintian silent (entry SCOPE-14) |
| Dependency security | no third-party runtime dependency | `tools/dev.py inventory` |
| Cross-distro compatibility | one profile only | Ubuntu 24.04.5 GNOME Wayland (ENV-02) |
| Release provenance | reproducible: two builds, identical SHA256 | entry IMP-01 |

---

## Remediation tasks

| ID | Priority (CODE-QUALITY section 7) | Task | State |
|---|---|---|---|
| CQ-01 | 8 compatibility | Integration tests against live services. | done (38 in the VM) |
| CQ-02 | 10 complexity | Decide whether to add a cognitive-complexity analyzer to `docs/TOOLCHAIN.md`. | open (none in the Ubuntu archive) |
| CQ-03 | 11 documentation | Document the concurrency/lifecycle contract (worker threads hand results to the main loop through `GLib.idle_add`; no shared mutable state) in `docs/ENGINEERING.md`. | open |
| CQ-04 | 2 security | Evaluate `python3-bandit` from the Ubuntu archive as the security analyzer. | open |
| CQ-05 | 10 complexity | Split `execute_service` into per-action verification helpers. | open |
| CQ-06 | 10 complexity | Decompose `read_storage` per object kind as `read_devices` was. | open |
| CQ-07 | 11 readability | Rename `integrations.catalog.Paths` (user home dirs) so it cannot be confused with `config.Paths`. | open |

---

## Current result

> **CQS: NOT MEASURED** (assessed weight 85 of 100; observed 78.5 of 85; complexity category incomplete)

This is the truthful result for candidate `078048d`.
