# AGENTS.md
# Trier Bridge Agent / Contributor Operating Rules

**Updated:** 2026-09-20 9:17 PM CDT

This file governs automated coding agents, AI assistants, scripted engineering workers, and similar contributors operating in the Trier Bridge repository.

Human contributors should also follow `CONTRIBUTING.md`.

---

## 1. Authority order

Use this order when documents conflict:

1. latest explicit Doug Trier instruction
2. this file
3. `CONTEXT.md`
4. `Engine Spec Tasklist 01.MD`
5. `docs/PRODUCT-NORTH-STAR.md`
6. `docs/SECURITY.md` and `docs/INVARIANTS.md`
7. `docs/DECISIONS.md`
8. `docs/ENGINEERING.md`
9. affected subsystem contracts
10. roadmap/task indexes
11. historical reports

Do not silently choose a weaker interpretation.

---

## 2. Context refresh

At every new context window or resumed session:

1. read latest owner direction
2. read `AGENTS.md`
3. run `tools\tb context` (status, unreviewed changes since the last snapshot, ledger digest; see `tools/README.md`)
4. read `CONTEXT.md`
5. reread only the files `tb changes` lists; use `tb outline`, `tb section`, and `tb inv show` instead of whole-file reads
6. inspect Git state if a repository exists
7. read only affected decision/invariant/subsystem sections
8. run `tools\tb snapshot` once the changed files have been reviewed, so the next session starts from here

Before consequential work, state internally:

- task ID/objective
- authority
- allowed files/scope
- invariant impact
- invariant delta
- Must remain true
- verification plan
- recovery/rollback boundary

Refresh after:

- owner scope correction
- architecture surprise
- failed invariant
- branch/worktree change
- task boundary
- significant dependency change
- before release/publication work

---

## 3. Timestamp policy

All human-facing project timestamps use:

> **America/Chicago**

Record CDT/CST as applicable.

Do not use UTC timestamps as the primary project chronology unless explicitly labeled UTC.

---

## 4. Current implementation boundary

Trier Bridge is currently in design foundation.

Until Doug explicitly authorizes implementation and the Foundation 01 stack is frozen:

- do not create speculative production modules
- do not choose a framework silently
- do not choose a language silently
- do not create a generic privileged helper
- do not add dependencies because they "might be useful"
- do not treat the `tools/` scripts (Python/PowerShell/batch) as a product-stack choice; they are read-only engineering automation
- do not mark implementation/test tasks complete
- do not publish a repository or release

Documentation/research may continue within owner direction.

---

## 5. Product North Star

Primary user:

> typical Windows office/home user through advanced Windows users

The product should let users preserve learned behavior.

Priority:

1. everyday continuity
2. familiar troubleshooting
3. advanced Windows continuity
4. optional Linux learning

Do not let Linux-expert preferences redefine the primary UX.

---

## 6. Invariant rule

`docs/INVARIANTS.md` is binding.

No optimization, abstraction, simplification, style cleanup, compatibility shortcut, or token-saving strategy may weaken an invariant.

Unknown remains Unknown.

Unsupported remains Unsupported.

No false PASS.

If a requirement appears to need an invariant change:

1. stop affected implementation
2. document the conflict
3. propose the exact amendment
4. wait for owner approval

---

## 7. Security rule

`docs/SECURITY.md` is binding.

Never introduce:

- generic root shell
- arbitrary root command execution
- arbitrary privileged file-write
- shell interpolation of untrusted input
- silent TLS/certificate bypass
- global SELinux/AppArmor disable advice as normal recovery
- hidden privilege caching
- weaker fallback after secure-path failure

UI is not a security authority.

---

## 8. Command translation rule

Bridge commands become typed Trier Bridge operations.

Never implement:

```text
Windows command text
→ string replacement
→ shell command
→ execute
```

Unknown syntax performs no operation.

---

## 9. Platform rule

Do not assume:

- systemd
- NetworkManager
- apt
- dnf
- GNOME
- KDE
- Wayland
- X11
- Flatpak
- Snap
- polkit
- PackageKit

Detect and qualify capabilities.

No one-machine result becomes a generic Linux claim.

---

## 10. Code-quality rule

`docs/CODE-QUALITY.md` is binding.

Authoring method does not affect quality expectations.

AI-generated and hand-written code receive the same review.

No metric-triggered blind refactor.

No automatic suppression baseline.

CQS remains NOT MEASURED until all required dimensions have current evidence.

---

## 11. Evidence rule

Do not mark PASS because:

- code exists
- build succeeds
- test file exists
- mockup looks correct
- one environment works
- an operation was dispatched

Evidence belongs to the exact candidate, environment, fixture, and claim.

Record limitations and NOT_RUN items.

---

## 12. Failure doctrine

When failure occurs:

1. protect user/system state
2. do not widen privilege/scope
3. stop before uncertain destructive boundary
4. preserve recovery evidence
5. return control
6. say whether anything changed
7. classify result truthfully
8. offer safest recovery
9. expose technical detail progressively

Do not hide failure to keep a Windows-familiar appearance.

---

## 13. File/source boundaries

Do not recursively process private/local-only roots if introduced.

Do not modify:

- third-party source
- generated artifacts
- vendored dependencies
- license/NOTICE files

with first-party header/format tooling unless explicitly designed for that format.

---

## 14. Publication

GitHub creation, push, release, package upload, signing-key use, public distribution, and external publication remain owner-gated actions.

**Owner direction 2026-09-20: the repository is local Git only.** No remote is configured and none may be added. No `git push`, `git fetch`, `gh`, or any GitHub/hosting interaction until Doug explicitly instructs otherwise. Local commits on `main` are the normal way to record work.

Readiness is not authorization.

---

## 15. Test environments

Per `docs/DECISIONS.md` DEC-017 (rejected) and DEC-016:

- All Linux testing uses the project-owned Hyper-V Ubuntu Desktop VM `tb-ubuntu-desktop-2404` created by `tools/env/New-TbDesktopVm.ps1`. WSL is not used for project testing. The owner may keep the VM for other uses; its removal is owner discretion.
- Qualification runs start from the `clean-install` checkpoint of that VM (restore before each run) so evidence is tied to a known state. Checkpoints are allowed only on `tb-` VMs.
- Never start, stop, export, import, checkpoint, modify, or read the owner's work-production Hyper-V VM, or the pre-existing `Ubuntu-24.04-Recovered` WSL distro.
- Never change Hyper-V virtual switches, host networking, or Windows optional features. Creating or removing the project VM is an owner-run elevated step; agents prepare the exact command and wait.
- Destructive or fault-injection tests run only inside the disposable VM (TB-INV-230). No synthetic fixtures unless the owner explicitly approves a named fixture for a named scenario.
- Evidence records the exact environment profile (Ubuntu 24.04 Desktop / Hyper-V Gen2 / desktop / backends observed).

---

## Final rule

> **If Trier Bridge cannot prove that it knows what it is about to do, to exactly what target, with the right authority, and with a defined recovery path, it does not do it.**
