# CODE-QUALITY-REPORT.md
# Trier Bridge Code Quality Report

**Candidate:** commit `cd3ef65` (Foundation 01)  
**Timestamp:** 2026-09-21 12:20 AM CDT  
**CQS:** **NOT MEASURED**  
**Assessed weight:** 85 / 100 (seven of eight categories have current evidence)  
**Observed on assessed weight:** 76 of 85 (not normalized to 100 by rule)  
**Release quality:** NOT ASSESSED (no release candidate)

Rubric: `docs/CODE-QUALITY.md` section 1. Each criterion is 0, 0.5, or 1 with evidence. A category with any unmeasured criterion is NOT MEASURED as a whole; a numeric CQS exists only when all eight categories are measured.

---

## Scope and tools

| Item | Value |
|---|---|
| Source scope | `trier_bridge/` (1,338 lines, 11 files), `tests/unit/` (369 lines, 5 files), `tools/dev.py` |
| Environment | `tb-ubuntu-desktop-2404` (Ubuntu 24.04.5) and Windows host `.venv` with identical tool versions |
| Tools | black 24.2.0, flake8 7.0.0 (pyflakes 3.2.0, pycodestyle 2.11.1, mccabe 0.7.0), mypy 1.9.0 `--strict`, pytest 7.4.4, lintian 2.117.0 |
| Commands | `python3 tools/dev.py all`; `flake8 --select=C901 --max-complexity=1 trier_bridge`; `dpkg-buildpackage -us -uc -b`; `lintian` |

---

## CQS categories

| Category | Weight | Criteria (0 / 0.5 / 1) | Score | State |
|---|---:|---|---:|---|
| Architecture / boundaries | 20 | purposes and dependency direction documented in package docstrings and `docs/ENGINEERING.md` (1); acyclic: `core` imports only the standard library, `ui` imports `core`, `__main__` imports `config`, `logging_setup`, `ui`, verified by reading every import (1); single mutable-state authority: only `config.py` writes state, UI holds none (1); explicit domain/interfaces/adapters: `StableIdentity` protocol exists, adapters do not yet (0.5); cohesive responsibilities, no generic managers (1) | 18 | MEASURED |
| Readability / naming | 15 | Trier Bridge vocabulary (Operation, CapabilityState, StableIdentity, PrivilegeClass) (1); accurate names (1); understandable control flow, largest function reviewed below (1); consistent state/result terms matching `docs/STATE-AND-PERSISTENCE.md` (1); coherent module scope (1) | 15 | MEASURED |
| Complexity | 15 | cyclomatic: 21 functions above 1, maximum 10 in `config.atomic_write_bytes`, next highest 5; outlier dispositioned below (1); cognitive complexity: no tool in the pinned toolchain, not measured (NM); nesting review: deepest nesting three levels, in the same function (1); function/module/parameter scope: largest module `ui/window.py` 225 lines, no function over 45 lines (1); duplicated decision review: one state machine, one identity comparison per kind, one redaction function (1) | — | **NOT MEASURED** (one criterion) |
| Documentation / rationale | 15 | API ownership/errors/side effects in module and class docstrings (1); privilege/security assumptions stated (`logging_setup`, `config`, `ui/__init__`) (1); persistence/recovery documented in `config.py` (1); concurrency/lifecycle: none exists yet, GLib main loop only, not yet documented as a contract (0.5); compatibility decisions cite `TB-INV-###` and decision IDs (1) | 13.5 | MEASURED |
| Testing / regression | 15 | tests map to invariants by `TB-T###` in docstrings (1); 33 meaningful unit tests on real files, no mocks (1); integration/negative tests against live services: none yet, nothing integrates yet (0); failure/lifecycle/recovery cases: state-machine refusals, failed-validation keeps original, newer-schema refusal, corrupt-file refusal (0.5); candidate-specific regression evidence: identical results on host and VM for this revision (1) | 10.5 | MEASURED |
| Static-analysis health | 10 | build diagnostics: package builds with no warnings (1); lint and type analysis: flake8 and mypy strict clean (1); security/safety findings: no dedicated security analyzer in the toolchain; manual grep shows zero subprocess/shell/os.system in the product (0.5); suppression inventory: 7, all listed below with reasons (1); resource/nullability/unsafe/boundary warnings: mypy strict with `warn_unreachable` clean (1) | 9 | MEASURED |
| Dependency hygiene | 5 | necessity: no runtime dependency beyond Ubuntu Desktop defaults (1); pins: `docs/TOOLCHAIN.md` and `debian/control` version floors (1); license/provenance: all first-party Apache-2.0 plus Ubuntu packages (1); maintenance/security/platform: Ubuntu 24.04 LTS set (1); transitive/package cost: 19 KB `.deb`, zero new packages pulled (1) | 5 | MEASURED |
| Dead code / duplication | 5 | unused paths: pyflakes clean (1); unreachable branches: mypy `warn_unreachable` clean (1); exact duplicates: none found by reading (1); semantic duplicates / state authority: one authority each for state transitions, identity, redaction, atomic writes (1); standalone foundations distinguished: `core` types precede their consumers by design and are labelled as such in `trier_bridge/__init__.py` (1) | 5 | MEASURED |

**Why NOT MEASURED:** the complexity category has no cognitive-complexity evidence because no such analyzer is in the pinned Ubuntu toolchain. Adding one is a toolchain change (`docs/TOOLCHAIN.md` section 5); until then this report lists the observed criteria separately, as the standard requires.

---

## Complexity outlier disposition

`trier_bridge/config.py: atomic_write_bytes` (cyclomatic 10). It is the whole atomic-write protocol: temp file, flush, fsync, optional validation, replace, directory fsync where the platform allows, cleanup on any failure with the original untouched. Splitting it would spread one recovery guarantee across several functions with shared failure state. Reviewed and kept; six unit tests cover success, replacement, failed validation, and round-trips. Re-review if it grows.

---

## Suppression inventory (7)

| Location | Suppression | Reason |
|---|---|---|
| `ui/app.py` 30, 32, 33; `ui/window.py` 31, 33 | `# noqa: E402` | PyGObject requires `gi.require_version()` before importing `gi.repository`; imports after it are the documented pattern |
| `ui/app.py` 38; `ui/window.py` 90 | `# type: ignore[misc]` | mypy strict forbids subclassing an untyped base; `gi` has no complete stubs on the target |

No baseline files, no disabled rules, no lowered thresholds.

---

## Hard-gate status

| Gate | State | Evidence |
|---|---|---|
| Invariant violations | none known | tests cite TB-T IDs; `tb inv` reports no undefined references |
| Privilege boundary | no privileged code exists | `docs/PRIVILEGE-MODEL.md`; package installs no helper, unit, or polkit file |
| Shell injection | no shell use | zero subprocess/shell/os.system matches in `trier_bridge/` |
| Path traversal / symlink safety | writes only under XDG app dirs | `config.py`; unit tests |
| Data-loss / recovery | atomic writes verified | `test_config.py` |
| Stale-target mutation | identities implemented, no mutation exists yet | `core/identity.py`; `test_identity.py` |
| Package/update trust | native `.deb`; no update mechanism (DEC-022) | reproducible build, lintian silent |
| Dependency security | no third-party runtime dependency | `tools/dev.py inventory` |
| Cross-distro compatibility | one profile only | Ubuntu 24.04.5 GNOME Wayland (ENV-02) |
| Release provenance | reproducible: two builds, identical SHA256 | `docs/VALIDATION.md` entry IMP-01 |

---

## Remediation tasks

| ID | Priority (CODE-QUALITY section 7) | Task |
|---|---|---|
| CQ-01 | 8 compatibility | Integration tests against live services begin with Foundation 02 discovery (read-only). |
| CQ-02 | 10 complexity | Decide whether to add a cognitive-complexity analyzer to `docs/TOOLCHAIN.md` (candidate: none in the Ubuntu archive; would need a pinned, recorded source). |
| CQ-03 | 11 documentation | Document the concurrency/lifecycle contract once anything runs off the main loop. |
| CQ-04 | 2 security | Evaluate `python3-bandit` from the Ubuntu archive as the security analyzer. |

---

## Current result

> **CQS: NOT MEASURED** (assessed weight 85 of 100; observed 76 of 85; complexity category incomplete)

This is the truthful result for the Foundation 01 candidate.
