# CODE-QUALITY-REPORT.md
# Trier Bridge Code Quality Report

**Candidate:** commit `4385ef7` (Foundations 01–07 closed, SCOPE-14 integrations, Foundation 08 automated parts done, CQ-05..08 remediated; package 0.1.0~dev1)  
**Timestamp:** 2026-09-21 11:30 AM CDT  
**CQS:** **NOT MEASURED**  
**Assessed weight:** 85 / 100 (seven of eight categories have current evidence)  
**Observed on assessed weight:** 81 of 85 (not normalized to 100 by rule)  
**Release quality:** NOT ASSESSED (no release candidate; release locked)

Rubric: `docs/CODE-QUALITY.md` section 1. Each criterion is 0, 0.5, or 1 with evidence. A category with any unmeasured criterion is NOT MEASURED as a whole; a numeric CQS exists only when all eight categories are measured.

---

## Scope and tools

| Item | Value |
|---|---|
| Source scope | `trier_bridge/` (10,995 lines, 60 files), `tests/` (2,836 lines, 33 files: unit, integration, the polkit test agent), `tools/dev.py`, `data/integrations/tb_nautilus.py` |
| Environment | `tb-ubuntu-desktop-2404` (Ubuntu 24.04.5, GNOME 46 Wayland, software rendering) and Windows host `.venv` with identical tool versions |
| Tools | black 24.2.0, flake8 7.0.0 (pyflakes 3.2.0, pycodestyle 2.11.1, mccabe 0.7.0), mypy 1.9.0 `--strict`, pytest 7.4.4, lintian 2.117.0 |
| Commands | `python3 tools/dev.py all`; `flake8 --select=C901 --max-complexity=10 trier_bridge`; `dpkg-buildpackage -us -uc -b`; `lintian`; a read-only metrics script (line counts, suppression and broad-catch inventory, longest functions) |
| Test results | host: 99 unit passed, 5 skipped (need `gi` or POSIX permission bits); VM: 115 unit passed, 1 skipped (needs three programs for one file type), 42 integration passed, 1 skipped (console-only over SSH) |

---

## CQS categories

| Category | Weight | Criteria (0 / 0.5 / 1) | Score | State |
|---|---:|---|---:|---|
| Architecture / boundaries | 20 | purposes and dependency direction documented in package docstrings and `docs/ENGINEERING.md` (1); acyclic: `core` imports only the standard library; `system`, `state`, `operations`, `bridge`, `integrations`, `apps`, `desktop` import `core`/`config`; `ui` imports all of them; nothing imports `ui` except `__main__` (1); single mutable-state authority per kind: `config.py` writes files, `state/journal.py` owns operation records, `state/preferences.py` owns preferences, `integrations/ledger.py` owns the integration record and re-reads before every change (1); explicit domain/interfaces/adapters: typed `Operation`/`OperationResult`, `StableIdentity` protocol with four implementations (process, unit, file, default-app), adapters `system/*` behind `Bus` (1); cohesive responsibilities, no generic managers (1) | 20 | MEASURED |
| Readability / naming | 15 | Trier Bridge vocabulary throughout (Operation, CapabilityState, ProcessIdentity, UnitIdentity, FileIdentity, MimeIdentity, TerminatePlan, FilePlan, ServicePlan, DefaultAppPlan, Integration) (1); accurate names (1); understandable control flow: fifteen functions above cyclomatic 10 are dispositioned below; none is flagged for splitting (1); consistent state/result terms matching `docs/STATE-AND-PERSISTENCE.md` (1); coherent module scope (1) | 15 | MEASURED |
| Complexity | 15 | cyclomatic: 15 functions above 10, maximum 18 (`MainWindow._build_page`, a flat dispatch); `read_devices`, `execute_service`, `read_storage`, and `plan_file` were decomposed today (0.5); cognitive complexity: no tool in the pinned toolchain, not measured (NM); nesting review: deepest nesting three levels (0.5); function/module scope: longest function 92 lines (`Discovery.environment`), largest module `ui/window.py` 480 lines (0.5); duplicated decision review: one state machine, one identity comparison per kind, one redaction function, one atomic write, one ledger, one plan→confirm→execute shape reused by four operation kinds (1) | — | **NOT MEASURED** (one criterion) |
| Documentation / rationale | 15 | API ownership/errors/side effects in module and class docstrings (1); privilege/security assumptions stated (`operations/*`, `integrations/*`, `bridge/*`, `docs/PRIVILEGE-MODEL.md` section 8) (1); persistence/recovery documented (`config.py`, `state/journal.py`, `integrations/ledger.py`) (1); concurrency/lifecycle: worker threads hand results to the main loop through `GLib.idle_add`; the polkit test agent documents its own thread and private connection; the contract is stated in those modules but not yet in `docs/ENGINEERING.md` (0.5); compatibility decisions cite `TB-INV-###` and decision IDs (1) | 13.5 | MEASURED |
| Testing / regression | 15 | tests map to invariants by `TB-T###` in docstrings (1); 115 unit tests on real files, real child processes, the real Trash, the real mimeapps.list; no mocks (1); integration/negative tests against live services: 42 in the VM (systemd, polkit through a real agent, NetworkManager, udisks2, journald, sysfs, D-Bus activation, loopback ext4 faults) (1); failure/lifecycle/recovery cases: state-machine refusals, disk-full and kill-mid-write recovery, stale identity for four target kinds, PARTIAL restart, denied and dismissed authorization, read-only ledger (1); candidate-specific regression evidence: `docs/TEST-STRATEGY.md` section 7 maps SECURITY section 37 to tests with gaps named; same revision run on host and VM; installed `.deb` exercised through AT-SPI (1) | 15 | MEASURED |
| Static-analysis health | 10 | build diagnostics: package builds with no warnings; lintian silent (1); lint and type analysis: flake8 and mypy strict clean (1); security/safety findings: no dedicated analyzer; manual grep shows zero subprocess/shell/os.system in the product, the single match is a docstring saying so (0.5); suppression inventory: 119, all of three documented kinds, listed below (1); resource/nullability/unsafe/boundary warnings: mypy strict with `warn_unreachable` clean (1) | 9 | MEASURED |
| Dependency hygiene | 5 | necessity: no runtime dependency beyond Ubuntu Desktop defaults; `python3-nautilus` is a Recommends used only when the Files integration is on (1); pins: `docs/TOOLCHAIN.md` and `debian/control` version floors (1); license/provenance: all first-party Apache-2.0 plus Ubuntu packages (1); maintenance/security/platform: Ubuntu 24.04 LTS set (1); transitive/package cost: 86 KB `.deb`, Installed-Size 469 KB, zero new packages pulled (1) | 5 | MEASURED |
| Dead code / duplication | 5 | unused paths: pyflakes clean (1); unreachable branches: mypy `warn_unreachable` clean (1); exact duplicates: none found by reading; the two directory classes are now `config.Paths` and `integrations.catalog.UserDirs` (1); semantic duplicates / state authority: one authority each (1); standalone foundations distinguished and labelled (1) | 5 | MEASURED |

**Why NOT MEASURED:** the complexity category has no cognitive-complexity evidence because no such analyzer is in the pinned Ubuntu toolchain. Adding one is a toolchain change (`docs/TOOLCHAIN.md` section 5); until then this report lists the observed criteria separately, as the standard requires.

---

## Complexity outlier disposition (cyclomatic > 10)

| Function | CC | Disposition |
|---|---:|---|
| `ui/window.py: _build_page` | 18 | Flat dispatch constructing one page per sidebar section; reads as a table. Kept. |
| `operations/files.py: execute_file` | 17 | Revalidate → one GIO call per verb → classify errors → verify per verb. Kept; each verb is one line in the call and one line in the verify. |
| `capability/discovery.py: Discovery.environment` | 17 | A dozen independent facts, each guarded so one missing source never hides the others. Kept. |
| `system/processes.py: ProcessSampler.sample` | 16 | procfs parsing with per-field tolerance. Kept. |
| `bridge/grammar.py: parse` | 14 | Grammar rules plus the PowerShell translation hook; each branch has a unit test. Kept. |
| `integrations/catalog.py: apply` | 14 | Dispatch by integration id plus rollback on any failure and on an unrecordable ledger. Kept; the rollback must see every step. |
| `bridge/grammar.py: tokenize` | 13 | The CMD-style tokenizer. Kept. |
| `operations/process.py: execute_terminate` | 13 | Same shape as `execute_service` for TERM/KILL with zombie handling (83 lines). Kept. |
| `config.py: atomic_write_bytes` | 12 | The whole atomic-write protocol including temp-file creation failure. Kept; covered by disk-full and kill tests. |
| `ui/window.py: _on_row_selected`, `system/network.py: read_network` | 12, 12 | Flat per-section start and per-device walk. Kept. |
| `bridge/cmdlets.py: translate`, `catalog/model.py: Catalog.load`, `integrations/tray.py: Tray.menu_call`, `operations/defaults.py: execute_default` | 11 each | One branch per parameter form, per schema rule, per protocol method, per verify outcome. Kept. |

---

## Suppression inventory (119)

| Kind | Count | Where | Reason |
|---|---:|---|---|
| `# noqa: E402` | 94 | every module that imports `gi.repository` | PyGObject requires `gi.require_version()` before importing `gi.repository`; imports after it are the documented pattern |
| `# type: ignore[misc]` | 20 | every `Gtk`/`Adw` subclass | mypy strict forbids subclassing an untyped base; `gi` has no complete stubs on the target |
| `# type: ignore[no-untyped-def]` | 5 | D-Bus method-call handlers in `integrations/search_provider.py` and `integrations/tray.py` | Gio hands the handler eight positional values whose types come from `gi`; annotating them as `Any` eight times would say the same thing with more noise |

No baseline files, no disabled rules, no lowered thresholds. Broad `except Exception` catches: 17, all at a UI or process boundary where the failure is reported to the user or logged and the operation is marked failed (`bridge/commands.py`, `config.py` cleanup path, `integrations/catalog.py` rollback paths, `ui/*` page loaders, `ui/app.py` dev snapshot). None swallows silently.

---

## Hard-gate status

| Gate | State | Evidence |
|---|---|---|
| Invariant violations | none known | tests cite TB-T IDs; `tb inv` reports no undefined references |
| Privilege boundary | no privileged code; system-scope calls go through polkit with `ALLOW_INTERACTIVE_AUTHORIZATION`; granted, dismissed, and denied paths verified with a real agent | `docs/PRIVILEGE-MODEL.md` section 8; entries IMP-06.05, IMP-06.07, IMP-06.08 |
| Shell injection | no shell use; every launch is a fixed argument list through GLib; hostile filenames are data | zero subprocess/shell/os.system matches; entries IMP-07, IMP-06.08 |
| Path traversal / symlink safety | writes only under XDG app dirs and recorded per-user paths; file operations never recurse and never overwrite | `config.py`; `integrations/ledger.py`; `operations/files.py`; entry IMP-03.03 |
| Data-loss / recovery | atomic writes verified under disk-full and kill; delete means the Trash | entries IMP-05, IMP-03.03 |
| Stale-target mutation | identities revalidated before every mutation for processes, units, files, and default apps; stale cancels | entries IMP-06.04, IMP-06.05, IMP-03.03, IMP-03.05 |
| Package/update trust | native `.deb`; no update mechanism (DEC-022); upgrade in place verified | reproducible build (entry IMP-01); lintian silent; entry IMP-08.02 |
| Dependency security | no third-party runtime dependency | `tools/dev.py inventory` |
| Cross-distro compatibility | one profile only | Ubuntu 24.04.5 GNOME Wayland (ENV-02) |
| Release provenance | reproducible: two builds, identical SHA256 (dev0); clean-chroot build in progress (IMP-08.01) | entry IMP-01 |
| Resource use | measured; one idle-CPU defect found and fixed | entry IMP-08.08 |

---

## Remediation tasks

| ID | Priority (CODE-QUALITY section 7) | Task | State |
|---|---|---|---|
| CQ-01 | 8 compatibility | Integration tests against live services. | done (42 in the VM) |
| CQ-02 | 10 complexity | Decide whether to add a cognitive-complexity analyzer to `docs/TOOLCHAIN.md`. | open (none in the Ubuntu archive) |
| CQ-03 | 11 documentation | Document the concurrency/lifecycle contract (worker threads hand results to the main loop through `GLib.idle_add`; no shared mutable state) in `docs/ENGINEERING.md`. | open |
| CQ-04 | 2 security | Evaluate `python3-bandit` from the Ubuntu archive as the security analyzer. | open |
| CQ-05 | 10 complexity | Split `execute_service` into per-action verification helpers. | done (revalidate, call, per-kind verify) |
| CQ-06 | 10 complexity | Decompose `read_storage` per object kind as `read_devices` was. | done |
| CQ-07 | 11 readability | Rename `integrations.catalog.Paths` (user home dirs) so it cannot be confused with `config.Paths`. | done (`UserDirs`) |
| CQ-08 | 10 complexity | Split `plan_file` per verb. | done (mkdir, rmdir, trash, transfer) |
| CQ-09 | 9 performance | Write a performance budget (startup, idle CPU, memory per page) into `docs/ENGINEERING.md` and measure on hardware with a GPU. | open |

---

## Current result

> **CQS: NOT MEASURED** (assessed weight 85 of 100; observed 81 of 85; complexity category incomplete)

This is the truthful result for candidate `4385ef7`.
