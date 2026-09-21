# Trier Bridge Toolchain Pins

**Task:** IMP-01.01  
**Status:** Frozen for Foundation 01 on 2026-09-21 (DEC-020).  
**Rule:** the product runs on what Ubuntu 24.04 Desktop already ships; development tools come from the Ubuntu 24.04 archive; the host virtualenv mirrors those exact versions. No `pip install` for the product, ever (AGENTS.md section 4).

## 1. Runtime (present on Ubuntu Desktop 24.04.5 by default)

| Component | Package | Pinned minimum | Observed in `tb-ubuntu-desktop-2404` |
|---|---|---|---|
| Python | `python3` | 3.12 | 3.12.3-0ubuntu2.1 |
| PyGObject | `python3-gi` | 3.48 | 3.48.2-1 |
| GTK | `gir1.2-gtk-4.0` | 4.14 | 4.14.5+ds-0ubuntu0.10 |
| libadwaita | `gir1.2-adw-1` | 1.5 | 1.5.0-1ubuntu2 |
| GLib tools | `libglib2.0-bin` | 2.80 | 2.80.0-6ubuntu3.8 |
| Desktop file tools | `desktop-file-utils` | 0.27 | 0.27-2build1 |

Optional runtime, only for the Files integration when the user selects it:

| Component | Package | Pinned minimum | Observed |
|---|---|---|---|
| Nautilus Python extension host | `python3-nautilus` | 4.0 | 4.0-1build4 (pulls `gir1.2-nautilus-4.0` 46.4) |

Not bundled, only invoked if installed: `pwsh` (PowerShell snap 7.6.5 observed).

## 2. Development tools (Ubuntu 24.04 archive)

| Tool | Package | Version | Purpose |
|---|---|---|---|
| pytest | `python3-pytest` | 7.4.4-1 | unit tests (host and VM), integration tests (VM only) |
| mypy | `python3-mypy` | 1.9.0-4ubuntu1 | `--strict` type checking of `trier_bridge` |
| black | `black` | 24.2.0-1ubuntu1 | formatting, line length 100 |
| flake8 | `python3-flake8` | 7.0.0-1 | lint (pyflakes 3.2.0, pycodestyle 2.11.1, mccabe 0.7.0) |
| flake8-cognitive-complexity | `python3-flake8-cognitive-complexity` | 0.1.0-3 | cognitive-complexity outliers (`CCR001`, threshold 15), reported by `tools/dev.py complexity` (added 2026-09-21, CQ-02) |
| bandit | `python3-bandit` | 1.6.2-3 | security analyzer over `trier_bridge` (`tools/dev.py security`, any finding fails; added 2026-09-21, CQ-04) |
| debhelper | `debhelper` | 13.14.1ubuntu5 | `.deb` build |
| Python build dependency | `python3-all` | 3.12.3-0ubuntu2.1 | required by `Build-Depends` |
| dh-python | `dh-python` | 6.20240401 | Python packaging helper |
| pybuild pyproject plugin | `pybuild-plugin-pyproject` | 6.20240401 | build from `pyproject.toml` |
| setuptools | `python3-setuptools` | 68.1.2-2ubuntu1.2 | build backend |
| build | `python3-build` | 1.0.3-2 | PEP 517 builds |
| devscripts | `devscripts` | 2.23.7ubuntu0.2 | `debuild`, `dch` |
| lintian | `lintian` | 2.117.0ubuntu1.5 | package policy checks |
| gettext | `gettext` | 0.21-14ubuntu2 | localization pipeline (later) |

Host mirror (Windows, `.venv`, gitignored): `black==24.2.0`, `mypy==1.9.0`, `pytest==7.4.4`, `flake8==7.0.0`, `flake8-cognitive-complexity==0.1.0`, `bandit==1.6.2`. The host runs only pure-logic unit tests and static checks; GTK and D-Bus code runs in the VM.

## 3. Configuration files

- `pyproject.toml`: project metadata, black, mypy (strict), pytest.
- `.flake8`: lint settings (flake8 does not read `pyproject.toml`).
- `tools/dev.py`: the single entry point (`format`, `lint`, `typecheck`, `security`, `complexity`, `test`, `headers`, `inventory`, `size`, `all`; `results` runs pytest and normalizes the outcome to `reports/local/test-results-<suite>.json`, the same shape on the host and in the VM; `evidence` collects complexity, bandit, suppression, size, and test counts to `reports/local/quality-evidence.json` for the quality report; `map` and `limitations` regenerate the derived `docs/FEATURE-INVARIANT-MAP.md` and `docs/KNOWN-LIMITATIONS.md` from `docs/VALIDATION.md`).
- `tools/tb.py headers`: Apache header compliance for every source file.

## 4. Reproducibility contract (IMP-01.06)

A build is reproducible when, from a clean `git archive` of a tagged revision on the VM with the packages above:

1. `python3 tools/dev.py all` exits 0;
   (`dpkg-buildpackage -us -uc -b` produces `trier-bridge_<version>_all.deb`; `lintian` is clean apart from justified overrides;)
2. the `.deb` builds with `SOURCE_DATE_EPOCH` set to the commit time;
3. building twice yields identical package hashes;
4. the package content matches the ownership table in `PACKAGING.md`.

Evidence for each is recorded in `VALIDATION.md` per candidate revision.

## 5. Change control

Bumping any pin is a ledger task with evidence on the VM. A newer Ubuntu release becomes a second row here, never a silent replacement of the 24.04 baseline (DEC-016).
