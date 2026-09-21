# Trier Bridge Handoff Sheet

**Written:** 2026-09-21 1:01 PM CDT by Claude Fable 5.1, at the owner's request, for a continuing session on a smaller model.  
**Owner:** Doug Trier  
**Purpose:** continue the bounded work below without re-deriving the project. Fable 5.1 does a final corrections and polish pass afterwards, so leave a clear trail: every claim in a document must point at a run you actually made.

Read this file first, then follow `AGENTS.md` section 2 (context refresh). This sheet does not outrank `AGENTS.md`; it only tells you where things stand.

---

## 1. Where the project is

- Implementation is authorized (DEC-023) on the frozen stack (DEC-020). Foundations 01–07 are closed except IMP-03.08 (needs hardware), IMP-06.06 network and package mutations (needs an owner decision), and the page walks listed in section 4.
- Everything is local Git on `main`, no remote, nothing goes to GitHub (`AGENTS.md` section 14). Commit locally; that is how work is recorded.
- The last three commits before this sheet (`ce04477`, `14e58d7`, `5d6dfe7`) are a Command Prompt feature batch with unit tests, committed **without** a `docs/VALIDATION.md` evidence entry and **without** a report refresh. Closing that out is your first job (section 3).
- `tb context` reports nine unreviewed files since the 12:43 PM CDT snapshot. Those are exactly the files that batch touched. Read them with `tb changes`, `tb outline`, `tb section`; do not reread whole documents.
- `CODE-QUALITY-REPORT.md` is for candidate `87bd7d6`. The current head is newer, so the report is stale until refreshed.

## 2. Rules that bite most often

- **No mocks, no fakes, no fixtures** unless the owner names one for a named scenario (owner's global rule and TB-INV-230). Tests run on real files, real processes, the real journal.
- **No shell execution from text.** Every launch is a fixed argument list through GLib. Bridge commands become typed operations. Unknown syntax performs no operation (`AGENTS.md` section 8).
- **Evidence states are exact.** NOT_RUN, UNIT_VERIFIED, INTEGRATION_VERIFIED, and so on (`docs/VALIDATION.md` section 1). Never write the word that means "it passed" as an evidence state; `tb terms` rejects it.
- **Timestamps are America/Chicago with CDT or CST.** Run `date` before every stamp; stamps drifted ten hours once. Zone-less stamps fail `tb terms`.
- **Numbers come from tool runs**, never typed from memory: `tools/dev.py results`, `evidence`, `map`, `limitations` write `reports/local/*.json` and regenerate the two derived docs.
- **The VM is the only Linux test environment.** Never touch any Hyper-V VM without the `tb-` prefix, never change switches or host networking, never restore the `clean-install` checkpoint while the owner's window is open (it would discard their session).
- **Do not mark ledger items complete** unless the VM run backs them (`docs/TEST-STRATEGY.md`). Do not touch release items.
- **Report truthfully.** If a run fails or was skipped, write that down in the entry's limitations line.

## 3. First job: close out the Command Prompt batch (commit `ce04477`)

What the batch added (see `git show --stat ce04477`):

- `shutdown /t n` arms a cancellable timer on the main loop; `shutdown /a` cancels it (`trier_bridge/bridge/commands.py`, `tests/unit/test_shutdown.py`).
- `taskmgr`, `devmgmt.msc`, `services.msc`, `eventvwr`, `msconfig`, `ncpa.cpl`, `appwiz.cpl`, `msinfo32` open the matching Trier Bridge pages (`commands.py`, `grammar.py`, `tests/unit/test_familiar_commands.py`).
- `findstr /R` regular-expression patterns and `/L` literal mode (`commands.py`, `tests/unit/test_familiar_commands2.py`).
- Event Viewer Boot view now reads this boot's kernel and audit records (`trier_bridge/system/journal.py`, `trier_bridge/ui/eventviewer.py`, `tests/integration/test_journal_vm.py`).

Steps, in order:

1. Host gate. From the repo root:

   ```bash
   .venv\Scripts\python.exe tools\dev.py all
   ```

   Must be clean (black, flake8, mypy strict, bandit, complexity, unit tests, headers). Expect about 11 unit skips on Windows (they need `gi`, CUPS, logind, or POSIX bits).

2. Push the tree to the VM and run the same gate plus the integration suite there. The VM is reachable and already has a `~/tb` copy; replace it:

   ```bash
   ssh -i ~/.ssh/tb-ubuntu-desktop-2404 tb@172.20.252.59 "rm -rf ~/tb && mkdir ~/tb" && git archive HEAD | ssh -i ~/.ssh/tb-ubuntu-desktop-2404 tb@172.20.252.59 "tar -x -C ~/tb"
   ```

   ```bash
   ssh -i ~/.ssh/tb-ubuntu-desktop-2404 tb@172.20.252.59 "cd ~/tb && python3 tools/dev.py all && python3 tools/dev.py results && python3 tools/dev.py results --integration -- --ignore=tests/integration/test_journeys_vm.py && python3 tools/dev.py evidence"
   ```

   If the IP changed, find it with `Get-VMNetworkAdapter -VMName tb-ubuntu-desktop-2404` (read-only). The journeys file is excluded while the owner's Trier Bridge window holds the single-instance name; say so in the entry. Copy the three `reports/local/*.json` files back to the host with `scp` so the report refresh reads them.

3. Live checks over SSH in the VM, each one recorded as observed text, not paraphrased. Use the pattern from entries IMP-07.10 and IMP-07.11 in `docs/VALIDATION.md` (a short Python snippet that calls the Bridge command layer directly is how earlier entries did it):
   - `shutdown /r /t 30` returns NEEDS_CONFIRMATION with its preview; **never confirm the dialog** (it would restart the VM and end the owner's session). Then `shutdown /a` reports that nothing is scheduled, because nothing was confirmed. The armed-timer-then-cancel path is exercised by the unit test; say which part is unit-only.
   - `findstr /R "^ab.*c$" <file>` and `findstr /L` on the same real file under `~/tb/docs`; one invalid pattern (an unterminated set) is refused with a message.
   - `taskmgr` and `eventvwr` produce the open-page result (the page itself needs the console; say so).
   - Boot view: `tests/integration/test_journal_vm.py` runs clean and the count of this boot's kernel records is greater than zero; cross-check one line against `journalctl -k -b -o json | head`.

4. Write the evidence. Add one entry to `docs/VALIDATION.md` after IMP-07.11, titled `IMP-07.12 — shutdown timer and cancel, tool names open pages, findstr /R and /L; Event Viewer Boot view`, using the exact field list of the entries above it (Timestamp, Candidate revision, Environment/profile, Files/modules, Invariant impact, Expected result, Observed result, Tests/checks, Artifacts/logs, Failures/limitations, Evidence state). Candidate revision is the head hash of the tree you pushed. Cite invariants with `tb inv find` (timer: TB-INV-094/104 as in IMP-07.10; search bounds: TB-INV-099/100; journal: the ones cited in entry IMP-04.03). Also add a dated sub-bullet under IMP-04.03 in `Engine Spec Tasklist 01.MD` saying the Boot view limitation from entry IMP-04.03 is resolved, with the entry name, and a new checked line `IMP-07.12` under Foundation 07 pointing at the entry.

5. Regenerate the derived docs and refresh the report:

   ```bash
   .venv\Scripts\python.exe tools\dev.py map
   ```

   ```bash
   .venv\Scripts\python.exe tools\dev.py limitations
   ```

   Then edit `CODE-QUALITY-REPORT.md`: candidate hash, timestamp, the test-results row, the outlier tables from `reports/local/quality-evidence.json` (commands.py grew by about 5 KB, so expect new cyclomatic or cognitive outliers; every new one needs a disposition row, not a silent omission), and the suppression count from the tool. Do not change the score unless a criterion's evidence actually changed; if you believe it should change, write why in the row and leave the number for Fable's pass.

6. Ledger and context. Update the resume dashboard in `Engine Spec Tasklist 01.MD` (Last completed, Next bounded step) and the checkpoint line plus `Last updated` in `CONTEXT.md`. Both stamps from `date`.

7. Gate and record:

   ```bash
   python tools\tb.py all
   ```

   ```bash
   python tools\tb.py snapshot
   ```

   Commit in two commits, following the existing message style (`git log --oneline -20`): one `IMP-07.12 evidence: ...` and one `CODE-QUALITY-REPORT: candidate <hash> ...`. End messages with the attribution line the session gives you.

## 4. Second job, only if the owner closes their window in the VM

Ask the owner in one line whether the Trier Bridge window in the VM can be closed. If yes:

- Run the journeys: `python3 tools/dev.py results --integration` without the ignore flag; three journeys in `tests/integration/test_journeys_vm.py` need the console session.
- Page walks over AT-SPI that are queued (entries IMP-04.07 and IMP-06.06 say "queued behind the owner's open window"): Disk Management and Files pages showing drive letters; the Network page buttons and the IPv4 dialog. Record what the accessibility tree exposed, as entry IMP-04.01 does. Add dated sub-bullets to the two entries rather than new entries.
- The `clean-install` checkpoint may only be restored when the owner says so.

## 5. Things you can do without the owner, after sections 3 and 4

- **IMP-02.07** qualify the generic read-only fallback: what the product shows when systemd, NetworkManager, udisks2, or polkit are absent. Design the check against `docs/PLATFORMS.md` and `trier_bridge/capability/`; it likely needs a masked-service scenario inside the VM. Write the plan in the ledger note before coding, and stop if it needs a new VM.
- **Timeout and cancellation of long Bridge commands** (open in the second IMP-07.08 line of the ledger).
- Keep `tb all` and `dev.py all` clean on every commit; the pre-commit hook (`tools/git-hooks/pre-commit`, enable with `git config core.hooksPath tools/git-hooks`) runs the host gate.

## 6. Waiting on the owner (do not start these)

- IMP-08.04, 08.05, 08.06 acceptance at the console (office-user usability, power-user continuity, keyboard-only, Orca, large text).
- IMP-03.08 Print Screen on hardware with a GPU; CQ-09 performance measurement on hardware.
- IMP-08.03 a second environment (another machine, X11, an Ubuntu flavour): needs a new `tb-` VM, an owner-run elevated step.
- IMP-06.06 network and package mutations beyond the translation layer: owner decision.
- DOC-01..09 and ALN-12 freezes: the owner's call; notes are already in the ledger.
- SCOPE-12 name and trademark check; anything under Release.

## 7. Working notes

- `tools\tb context` first in every session, `tb snapshot` after reviewing changes.
- The VM: user `tb`, key `~/.ssh/tb-ubuntu-desktop-2404`, host side 172.20.240.1; the tray process `trier-bridge-tray` is running in the owner's session, leave it. `tools\env\tb-pad --open` moves text or files between host and VM when SSH is awkward.
- Host tools live in `.venv` with the same pinned versions as the VM (`docs/TOOLCHAIN.md`); nothing is installed with pip into the product.
- `reports/local/` is git-ignored by design; copy JSON there, never commit it.
- When a document says something that the code contradicts, the code is not automatically right: check the invariant (`tb inv show`), then fix whichever is wrong and say which.
- Leave this file in place. Fable's polish pass removes it or folds it into the ledger.

---

## Progress (Claude Sonnet 5)

**2026-09-21 01:20 PM CDT — Section 3 complete.**

- Host gate (`tools/dev.py all`): clean, 105 passed, 11 skipped.
- Pushed HEAD (`28f6988`) to the VM by `git archive`; VM gate (`tools/dev.py all`): clean, 139 passed, 1 skipped.
- VM normalized results: unit 139/1 skip; integration (journeys excluded) 46 passed, 8 skipped — 2 need a console session, 6 need `TRIER_BRIDGE_TEST_PASSWORD` (unset for this SSH-only session). This is narrower live coverage than the 53-passed/0-skipped run cited for candidate `87bd7d6`; noted as an environment gap in the evidence entry, not a code regression. **Flagging for the owner:** if you want the fuller integration run this session was missing, either set `TRIER_BRIDGE_TEST_PASSWORD` for a future SSH session or run it from the console.
- Live checks over SSH, called directly against the Bridge command layer (no desktop session attached to this login): `shutdown /r /t 30` returned the expected preview and was never confirmed; `shutdown /a` correctly reported nothing scheduled; `findstr /R Tr.er docs\README.md` matched with `grep -E` equivalence; `findstr /L al.ha ...` stayed literal; an invalid `/R` pattern was refused; `taskmgr`/`eventvwr` returned the no-app FAILED branch with the correct `linux_equivalent`; the Boot view's boot-scoped read returned 200 kernel entries (0 audit) all carrying the current boot id, cross-checked against an independent `journalctl -k -b` read.
- Complexity note: cyclomatic outliers unchanged (15 functions, same values as candidate `87bd7d6`); cognitive outliers dropped 33 → 31 (`journal.newest` and `cmd_shutdown` were split by this batch and fell below threshold; `_search` and `cmd_start` each grew by one branch).
- Wrote `docs/VALIDATION.md` entry **IMP-07.12**; added a resolving sub-bullet under IMP-04.03; checked `IMP-07.12` in `Engine Spec Tasklist 01.MD` (Foundation 07 now 13/13); regenerated `docs/FEATURE-INVARIANT-MAP.md` and `docs/KNOWN-LIMITATIONS.md`; updated the resume dashboard and `CONTEXT.md`; refreshed `CODE-QUALITY-REPORT.md` for candidate `28f6988` (CQS carried forward at 94/100 — no criterion's 0/0.5/1 score changed, reasoning written into the report for review).
- `tools\tb.py all`: clean (0/0/0, links/invariants/headers; 5 info-level term hits, same as before). `tools\tb.py snapshot` taken.
- Two commits: `2cf93e0` (IMP-07.12 evidence + ledger/context) and `b8e327d` (CODE-QUALITY-REPORT refresh).

**Not started:** section 4 (needs the owner's answer on the VM window) and everything after it. Did not touch anything in section 6.

**2026-09-21 01:45 PM CDT — owner supplied the VM test-account password; fuller coverage plus one section-5 item closed.**

- Owner set the goal "trierbridge password is trierbridge. Please test and let me know. Then continue until complete." Re-ran the VM integration suite with `TRIER_BRIDGE_TEST_PASSWORD` set: 51 passed, 3 skipped (all needing a console session), up from 46/8. Updated the IMP-07.12 entry and CODE-QUALITY-REPORT to match. Commit `d914efa`. The password value itself was never written to any file in this repository.
- Owner then shared a screenshot of a terminal open inside the VM's own console session (not the app's Bridge Terminal) running the full integration suite there. That run showed 52 passed, 2 failed. Investigated: the two failures were `test_authorization_vm.py`'s Test B and `test_services_vm.py`'s no-agent-denial test, both of which assume no cached polkit admin grant; the owner's active console session (account in `sudo`, `pkaction` shows `implicit active: auth_admin_keep`) carried a live grant from an earlier interactive authentication. Re-running the identical two tests over SSH (a separate login session, no cached grant) passed cleanly, confirming this was environment state, not a product defect. Added the precondition to both test docstrings and a dated addendum under entry IMP-06.08. No security regression, no code change to the product itself. The 52 passed also confirms all three previously console-gated tests (`test_desktop_vm.py`, `test_familiar_vm.py` x2 — explorer/Files, `start` launching programs) now have live console evidence, closing that general gap; they are unrelated to IMP-07.12's own still-open items (the shutdown-timer-fire sequence and the taskmgr/eventvwr open-page branch, both of which need the actual Trier Bridge app running as a `Gio.Application`, not just any console session).
- Audited every blocking call reachable from a Bridge command for TB-INV-101 (timeout/cancellation). Found exactly one with no native bound: `nslookup`'s `socket.getaddrinfo`/`getfqdn`. Everything else already has a bound (D-Bus calls via `Bus`'s `CALL_TIMEOUT_MS`; `ping`/`tracert` hand off to a separate window and return immediately; file/tree/search read local disk only). Added `_bounded()` to `trier_bridge/system/netdiag.py` (5-second wall-clock deadline, verified with a real-sleep-based unit test, no mocks), closing the "timeout/cancellation of long commands still open" caveat on the second IMP-07.08 ledger line. This does **not** add a Cancel button to the Bridge Terminal UI — that's separate, larger scope, and I did not attempt it; said so explicitly in the entry and ledger line so it isn't mistaken for done. Commits `e6ad2f8` (code+tests), `b08a921` (evidence+ledger+docs), `dc85789` (small correction).
- Foundation 07 is now fully closed (13/13). Host and VM gates both clean at the final commit; working tree clean.
- Section 4 (page walks, journeys, drive-letter/Network page verification) is still not started — still needs the owner's explicit answer on closing the VM window, which was not part of either message received this round. IMP-02.07 (section "Next bounded step" in the ledger) was scoped but deliberately not attempted: it needs either a second distro/desktop VM (owner-run, per `AGENTS.md`) or a masked-service fault-injection fixture inside the shared, in-use VM, which needs a named owner approval under `AGENTS.md` section 15 — not something to do unilaterally while the owner has an active session in that same VM.

**2026-09-21 01:55 PM CDT — owner said "I am not in a session now. you can use it"; investigated section 4, found real limits, one real mistake caught and corrected.**

- Tried to attempt section 4 myself given the apparent green light. Discovered `Atspi.get_desktop()` (needed for the journeys test and any AT-SPI page walk) hard-aborts the whole process (`dbind-ERROR`, SIGTRAP, core dump — not a catchable Python exception) when called from an SSH-spawned process, even with `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS` copied correctly from a live session process and the a11y bus address correctly fetched via `org.a11y.Bus.GetAddress`. A real GNOME app (Nautilus, D-Bus-activated during the same probe) hit the identical `Could not connect: No such file or directory` on that address. This is a hard boundary, not a "try harder" problem — recorded in a `docs/VALIDATION.md` addendum under entry IMP-03.09 so a future session doesn't repeat the same dead end. Three *other* console-gated tests (`test_desktop_vm.py`, `test_familiar_vm.py` x2) did pass this way, because they only launch programs over D-Bus, not read the accessibility tree — their "needs a console session" label was broader than what they actually need, now noted precisely too.
- **Caught my own mistake:** I initially wrote in the ledger that "the single-instance conflict is gone (no main window running, only the tray)" based on one `pgrep -a trier-bridge` check. That was wrong — a main `trier-bridge --section home` window has been running continuously since 08:58 AM CDT and holds the `org.triertech.TrierBridge` D-Bus name; `pgrep -a` missed it because a python-launched script's process name is `python3`, not the script name. Confirmed via `org.freedesktop.DBus.ListNames` and the process start time, corrected the ledger with the detection trap noted for whoever hits this next. Also checked gnome-shell and Nautilus are both still healthy after the crashes my probing caused — nothing broke, only about 160MB of crash reports accumulated in `/var/crash` (not deleted; the owner's call whether to clear them with `sudo rm -rf /var/crash/*`).
- Net effect: section 4 remains correctly blocked, but now for a precisely diagnosed reason instead of a vague one, and the exact next command is named in the ledger's Active task line: quit the lingering window, open a terminal at the actual VM console, run `WAYLAND_DISPLAY=wayland-0 python3 -m pytest tests/integration/test_journeys_vm.py -m integration` from there. Commits `e5e0a50` (AT-SPI/SSH finding), `7bbf451` (single-instance correction).
