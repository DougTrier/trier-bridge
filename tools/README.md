# Trier Bridge Tools

**Class:** read-only engineering automation (`docs/ENGINEERING.md` section 10).  
**Not a stack decision:** these are project tooling scripts, chosen for what the maintainer's machines already have. They do not select the product implementation language (`AGENTS.md` section 4, `docs/DECISIONS.md` open list).

## Contract

- Read-only. The only writes are reports under `reports/local/`, which `.gitignore` excludes.
- No shell execution, no network. Git is queried with a fixed argument list.
- Exit codes: `0` clean, `1` findings or unreviewed changes present, `2` tool error or misuse.
- Output is brief by default. `--full` shows every finding including info-level; `--json` also writes `reports/local/<tool>.json`.
- Timestamps are America/Chicago.

## Running

Windows:

```bash
tools\tb context
```

PowerShell (5.1 or 7, Windows or Linux):

```bash
.\tools\tb.ps1 context
```

Direct:

```bash
python tools/tb.py context
```

Requires Python 3.12 or newer on PATH. No packages beyond the standard library.

## Commands

| Command | Purpose | When to run |
|---|---|---|
| `tb context` | Status digest, changes since last snapshot, ledger summary. | Start of every session. Replaces rereading the project. |
| `tb status` | One-screen digest: file count, git state, snapshot age, ledger dashboard, recent files. | Any time. |
| `tb snapshot` | Record a hash manifest of the current tree as "reviewed". | After a reviewer has read everything that changed. |
| `tb changes` | Files added, removed, or modified since the snapshot. | Before deciding what to reread. |
| `tb ledger [ID]` | Per-section done/total and next task; with an ID, that task and its notes. | Resume protocol step 4. |
| `tb outline <file> [--depth N]` | Headings with line numbers and section sizes. | Before reading a large doc. |
| `tb section <file> <regex> [-n] [--all]` | Print one section by heading match. | Read only the part that matters. |
| `tb inv` | Invariant index checks: contiguity, total, family coverage, undefined references. | After editing invariants or anything that cites them. |
| `tb inv show 050 SEC-003 IA-12` | Print specific invariant rows. | Instead of opening the file. |
| `tb inv find <regex>` | Search must/failure text. | Finding which invariant governs a topic. |
| `tb links` | Markdown links and backticked path mentions resolve. | After moving or renaming files. |
| `tb terms` | Policy-phrase and code-smell rules from `tb-config.json`. | Before review; on every code change once code exists. |
| `tb headers` | Source-header compliance per `docs/LICENSING.md`. | Once code exists. |
| `tb all` | `links`, `inv`, `terms`, `headers` in one run. | Pre-review gate. |
| `tb-env.ps1 [-Json]` | Host environment profile for evidence records. | When recording an environment in `docs/VALIDATION.md`. |
| `env\tb-pad --open` | Shared notepad and file drop reachable from the host and the test VM. | Whenever text or files need to cross into or out of the VM. |

`<file>` arguments accept a path or a bare name; `SECURITY.md` resolves to `docs/SECURITY.md`.

## Token-efficient review protocol

1. `tb context` at session start.
2. Reread only the files `tb changes` lists; use `tb outline` and `tb section` for large ones.
3. `tb all` before declaring a review complete.
4. `tb snapshot` once the changes have been reviewed, so the next `tb changes` starts from here.

## Term rules

Rules live in `tb-config.json` under `terms.rules`. Each has an ID (`TB-TERM-###`), a regex, a severity, a message that cites the governing invariant or document, and optional `include`, `exclude`, `code_only`, and `flags`. Adding a rule is a config edit, not a code change. Rules marked `code_only` only apply to files matching `terms.code_globs`, so documentation may discuss a forbidden pattern without tripping the scan.

Current rules cover: UTC or zone-less timestamps, numeric CQS claims, PASS as an evidence state, asserting an implementation stack, generic root primitives, shell execution from constructed text, `sudo`, secret literals, TODO markers, "works on Linux" claims, and legacy root links to governing docs.

## Adding a tool

Add a module under `tbtools/` exposing `check_<name>(cfg) -> Report` and `cmd_<name>(args, cfg) -> int`, register it in `tb.py`, keep the full Apache header, and never write outside `reports/local/`. Tools that will need the product stack (lint, static analysis, test normalization, dependency inventory, CQS evidence collection) are deferred until Foundation 01 freezes the toolchain.

## Layout

```text
tools/
  tb.cmd          Windows entry
  tb.ps1          PowerShell entry
  tb.py           dispatcher
  tb-env.ps1      host profile (PowerShell-native)
  tb-config.json  ignore lists, file classes, term rules, header policy
  tbtools/        common, snapshot, ledger, links, invariants, terms, headers, outline
  env/            test environment: Hyper-V VM create/remove scripts, autoinstall seed, tb-pad notepad/file drop, README
```
