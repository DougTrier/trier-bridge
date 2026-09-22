# GitHub checks

**Task:** CI-01
**Authorization:** 2026-09-22: configure checks while the repository remains private; allow GitHub's disposable Ubuntu runners for package builds, static checks, and non-destructive unit tests. Desktop, privileged, and fault-injection tests remain on the project VM (`AGENTS.md` section 15).

## What runs

`.github/workflows/checks.yml` runs on pushes to `main`, pull requests targeting `main`, and manual dispatch. Each job uses a fresh GitHub-hosted `ubuntu-24.04` runner. No self-hosted runner or access to the Windows host/project VM is configured.

| Check | What a successful result establishes |
|---|---|
| Code and non-destructive unit checks | Documentation links, invariant references, source headers, Black, flake8, mypy, Bandit, and the explicit unit subset pass for the checked revision. Complexity outliers are reported under the existing policy, not silently treated as new failures or suppressed. |
| Debian build, policy, and reproducibility | Two clean archives of the exact commit build byte-identical `.deb` files; lintian reports no unsuppressed errors or warnings. Package metadata and contents appear in the log. |
| Secret scan of commit history | The pinned Gitleaks rules find no secrets in commits reachable from the checked revision. This is a scanner result, not a guarantee that no credential exists. Output is redacted. |

Unit results, including skipped cases, are saved as a JUnit artifact for 14 days. Build logs record installed archive tool versions and the package hash. Packages are neither installed nor uploaded, and the workflow cannot create a release. `DEB_BUILD_OPTIONS=nocheck` and `PYBUILD_DISABLE=test` disable packaging's automatic test discovery: the separate reviewed subset controls cloud execution.

## Unit coverage boundary

`tools/ci-unit.py` positively selects existing parsing, state-model, identity, catalog, resource, theme-math, terminal-helper, and temporary-file tests. New modules are not automatically admitted. Some existing modules are selected by individual test name. It uses real temporary files and the existing test inputs; no new synthetic product fixture is introduced.

Desktop widgets, default-application changes, live system services, printer/backend integration, shutdown timers, file-operation mutations, synthetic proc-tree samplers, and permission/fault-injection cases are excluded from this cloud subset. In particular, the directory permission-denial test is explicitly deselected. The full unit suite and integration suite retain their VM instructions in `TEST-STRATEGY.md`.

A green GitHub run does not establish desktop acceptance, accessibility, privilege handling, recovery under failure, or another supported distribution. Those claims still require the exact VM/hardware evidence in `VALIDATION.md`.

To run the same bounded subset locally with the documented development interpreter:

```text
python tools/ci-unit.py
```

## Security and dependency monitoring

- Dependabot alerts are enabled for GitHub-supported dependency manifests. They do not audit Ubuntu's entire package set. Automatic dependency merging is not enabled.
- The private personal repository does not have GitHub Code Security or Secret Protection enabled. The Bandit and Gitleaks jobs provide failing Actions checks independently of those paid/private-repository features; they do not populate GitHub's native code/secret-scanning dashboards.
- Each workflow has only `contents: read`. Checkout does not retain Git credentials. Pull requests use the ordinary `pull_request` event, never `pull_request_target`, and receive no repository secrets.
- Actions are pinned to full commit IDs; the Gitleaks binary is pinned by release and SHA-256. No failure is converted into success. Updating a pin requires review and a successful run.
- This workflow never changes visibility, releases, tags, signing keys, or production state.

## Tool sources

The product/runtime dependency model is unchanged. Python development and Debian packaging tools come from the Ubuntu 24.04 archive as specified in `TOOLCHAIN.md`.

| CI-only tool | Pin | Purpose |
|---|---|---|
| actions/checkout | `11d5960a326750d5838078e36cf38b85af677262` (v4) | Obtain the revision being checked. |
| actions/upload-artifact | `ea165f8d65b6e75b540449e92b4886f43607fa02` (v4) | Retain the unit-test XML, including skipped tests. |
| Gitleaks CLI | 8.24.3, official Linux x64 archive SHA-256 `9991e0b2903da4c8f6122b5c3186448b927a5da4deef1fe45271c3793f4ee29c` | Scan source history without requiring GitHub's private-repository secret-scanning product. Development only; not shipped with Trier Bridge. |

Gitleaks comes from [its official release](https://github.com/gitleaks/gitleaks/releases/tag/v8.24.3). Its CLI is MIT-licensed. GitHub documents [Actions workflows](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows) and [private-repository CodeQL availability](https://docs.github.com/en/code-security/reference/code-scanning/troubleshoot-analysis-errors/private-repository-enablement).

## Evidence

Workflow presence is not a passing run. Record the observed run URL, checked commit, environment, test counts/skips, package comparison, and scanner results in `VALIDATION.md` after the initial run. Any failed or unrun job remains explicit.
