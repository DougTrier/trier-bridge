# Test and Verification Points

**Written:** 2026-09-21 3:27 PM CDT  
**For:** Doug Trier, to test and mark Pass/Fail himself before any release decision  
**Where to run this:** the VM console, `tb-ubuntu-desktop-2404` — sitting at the actual screen, not SSH  

---

## How to use this

Every row below is something an agent already verified by evidence — reading real files, driving the actual running app over the accessibility interface, checking real system state. Nothing here is a guess. The point of this document is for you to verify it again yourself, with your own eyes and hands, before you trust it.

Work through each section top to bottom. For each row: do the step, compare to "Expected," and write **Pass**, **Fail**, or a note in the last column. If something fails, write what actually happened — that's worth more than the checkbox.

A few sections are marked **⚠ Caution** — those either end a session, change real settings, or need a specific accessibility tool. Read the caution note before starting that section.

**One thing to know before you type any Command Prompt row:** if a step shows `<something>` as a stand-in for a real value (your username, a file type), that's a writing convention, not literal text to type. Bridge Terminal correctly refuses a real `<` character as a shell-redirect symbol — that's a security feature working as designed, not a bug — but it means copying a placeholder verbatim will get refused with a parse error. I already fixed every row I could find that had this problem after hitting it myself during testing; if you spot another one, that's the same issue, not a new bug.

If you want the full technical evidence behind any row — exact commands, exact output, timestamps — the entry ID in brackets (e.g. `[IMP-03.09]`) is a heading in `docs/VALIDATION.md`; search for `### <that ID>`.

---

## 0. Before you start

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 0.1 | Open a terminal in the VM console. Run `pgrep -a trier-bridge` (yes, this specific check has a quirk — see below). | If nothing is running, nothing prints. If something is running, close it before starting so you begin from a clean, single instance. | | `pgrep -a trier-bridge` alone can miss a running window because a Python-launched window's process name is `python3`, not `trier-bridge`. If you're not sure, run `pgrep -a -f trier_bridge` instead — that one catches everything. |
| 0.2 | From the repo root, run `sh test-verification-setup.sh`. | Prints where it put two throwaway test files and reminds you to `cd` there for the Command Prompt steps. | | This creates the files section 3 and section 5 use, so you're not hand-typing them mid-checklist. It only writes under `~/tb-verify-scratch`; nothing else on the system is touched. |
| 0.3 | Open Trier Bridge from the applications menu (or run `trier-bridge` in a terminal). | The window opens on the Home page within a couple of seconds. | | |

---

## 1. First run and setup

*Evidence: `[SCOPE-14]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 1.1 | If you've never run it before (or after `apt purge`), the setup screen should appear automatically on first launch. | Setup screen shows integration groups (Essentials, Files, Shortcuts) with "Whole group" checkboxes, five individual items, and **Not now** / **Apply** buttons. | | If you've already set it up, skip to 1.3 — you won't see this screen again. |pass
| 1.2 | Click **Apply** with the recommended selection. | The window opens normally. A tray icon "T" appears. | | |
| 1.3 | Right-click (or left-click) the tray icon. | A menu appears: Open Trier Bridge, Task Manager, Command Prompt, Change integrations, Turn off. | | |pass
| 1.4 | Click **Open Trier Bridge** from the tray menu while the window is closed. | The window opens (or comes to front if already open). | | |pass
| 1.5 | Go to the **Integrations** page from the sidebar. Turn one switch off, then back on. | The switch state changes immediately and sticks after you leave and return to the page. | | |pass

---

## 2. Everyday navigation — the Home search

*Evidence: `[IMP-03.09]`, three journeys driven live*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 2.1 | On the Home page, type **Add or Remove Programs** into the search box. | A result appears with a **Show** button. | | |pass
| 2.2 | Click **Show**. | The window switches to the **Installed Apps** page, with a search field to find an installed program. | | |pass
| 2.3 | Go back to Home. Type **regedit**. | The result says **No equivalent** — honestly, not with a fake Open button. | | This is deliberate: Trier Bridge never pretends a Windows-only tool has a Linux twin. |pass
| 2.4 | Type **Task Manager**, **Control Panel**, **Downloads** and a few other things you'd type on a real Windows machine. | Each either shows a real place to go, or honestly says there's no equivalent — never silently does nothing. | | |pass

---

## 3. Files and drive letters

*Evidence: `[IMP-04.07]`, `[IMP-03.03]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 3.1 | Click **Files** in the Trier Bridge sidebar (left side, under "Everyday" — this stays *inside* the Trier Bridge window; it's not the same as the separate Files/Nautilus app rows 3.3 onward will open). | You see "Familiar places" (This Computer, Desktop, Documents, Downloads, Pictures, Music, Videos, Recycle Bin, Removable drives, Network) and, below it, a **Drives** group. If you don't see Drives, scroll down — it's a second group after Familiar places, not merged into it. | | |Pass
| 3.2 | Look at the Drives group. | `C:` is labeled "System drive" and opens to `/`. Any other real mounted volume gets the next letter (`D:`, etc.) with its real path shown underneath — but only for volumes actually mounted *right now*. If a USB stick or similar isn't mounted, it correctly won't have a letter yet; that's not a bug. | | The letter is a label only — the real folder path is always shown too. |pass
| 3.3 | Click **Open** next to **Documents**. | A *different*, separate window opens: the real GNOME Files app, to your real `~/Documents` folder. This is not Trier Bridge anymore — Trier Bridge routes you here rather than reimplementing a file manager. | | |Pass
| 3.4 | In Command Prompt (see section 5), type `cd C:\Users\tb` (or whatever your account name is — check with `whoami` in a terminal first if unsure) and press Enter. **Do not type the literal words `<your username>`** — Bridge Terminal correctly refuses the `<` character as a shell-redirect symbol, exactly as designed; that's it working right, not a bug, but it will stop this exact row cold if copied verbatim. | It lands in your real home folder and shows the path both ways. | | |Pass
| 3.4a | Type `cd tb-verify-scratch`, then `cd..` (no space) to go back up. | Both work — lands in the scratch folder, then back in home. | | New fix: `cd..` with no space failed as "unknown command" until just now; real `cmd.exe` accepts `cd`/`chdir` glued straight to `.` or `\` with no space (`cd..`, `cd\`, `cd\Users\tb`), so it's fixed to do the same. `cd ..` with a space always worked and still does. |
| 3.5 | In Command Prompt, `cd` to `C:\Users\tb\tb-verify-scratch` (substitute your real account name; from the setup script), then `copy test.txt test-copy.txt`. **Before confirming, actually read the dialog's two paths** — if either one does not end in `\tb-verify-scratch\...`, the `cd` above didn't land where you think, and confirming will copy the wrong `test.txt` (your real home folder may have its own, unrelated one). Cancel and re-`cd` if so. | A confirmation dialog appears naming the real source and destination paths, both inside `tb-verify-scratch`. Confirming copies the file for real. | | Uses the file the setup script created — no need to make your own. |Fail - said it was success but neither file exit or does not show up.
| 3.6 | Delete that copy: `del test-copy.txt`, confirm. | The file moves to the Trash (Recycle Bin), not permanently deleted. | | Check the Recycle Bin in Files — it should be there and restorable. The cleanup script reminds you it's there; it won't empty the Trash for you. |Pass - This worked and I verified it was in recyclebin unless this is something you tried via ssh and it was left in there.

---

## 4. System tools

*Evidence: `[IMP-04.01]`, `[IMP-04.03]`, `[IMP-06.04]`, `[IMP-06.05]`, `[IMP-06.06]`, `[IMP-05]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 4.1 | Open **Task Manager**. | A live, sorted list of real processes, sampled every couple of seconds. CPU/memory columns fill in after the first sample. | | |Pass
| 4.2 | Open a terminal and run `sleep 60`. In Task Manager, search for `sleep`. | Exactly one row, with an **End task** button (it's your own process). | | |Pass
| 4.3 | Click **End task**, read the confirmation dialog, then click **Cancel**. | Dialog closes, nothing happens — the `sleep` command in your terminal keeps running. | | |pass
| 4.4 | Click **End task** again, this time confirm it. | The process actually ends; your terminal shows it stopped; Task Manager shows a toast confirming it. | | |Pass
| 4.5 | Open **Event Viewer**. Switch between the view options (All events, System, Application, Security). | Each view filters differently; counts update. | | |Pass
| 4.6 | Switch to the **Boot** view. | Shows kernel and audit messages from *this specific boot*, not just whatever's newest overall. | | |Pass
| 4.7 | Open **Device Manager**, **Disk Management**, **Startup Apps**, **Network**. | Each shows real data read from this machine — no placeholders, no "coming soon." | | |Pass - but should have ability to stop startup apps like you can in Windows.
| 4.8 | On the **Network** page, note the adapter's facts (IP, gateway, DNS, MAC). Click **IPv4…**. | A dialog opens: "Obtain an IP address automatically" switch, address/gateway/DNS fields, Cancel/Apply. | |Pass Click **Cancel** — don't Apply unless you actually want to change your network settings. |Pass
| 4.9 | Close Trier Bridge entirely while something is genuinely mid-operation if you can arrange it (or ask whoever handles the next session to seed one) — otherwise skip this row; it's already been verified once and is low-value to keep re-testing. | On the next start, a banner says an earlier action was interrupted and needs review, with a way to mark it reviewed. | | Optional — this one's expensive to reproduce safely without deliberately killing the app mid-write. |skipped intentionally

---

## 5. Command Prompt (Bridge Terminal)

*Evidence: `[IMP-07]` and the whole IMP-07.x series*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 5.1 | Open **Command Prompt**. Type `hostname` and press Enter. | Prints this machine's real hostname, plus a small note showing the Linux equivalent command. | | |pass
| 5.2 | Type `ipconfig /all`. | Shows real adapter facts matching what Network page showed. | | |pass
| 5.3 | Type `dir C:\Users`. | Lists real home folders. | | |Pass
| 5.4a | Type `cd tb-verify-scratch` and press Enter. (Not `C:\Users\tb\tb-verify-scratch` this time — Command Prompt starts in your home folder, so the short relative form works. Substitute your real account name only if `cd tb-verify-scratch` says the path isn't found.) | Lands in the scratch folder and shows the path both ways. | | This row was missing — that's the actual bug behind 5.4 below. Section 5 never tells you to `cd` into `tb-verify-scratch` on its own; row 5.4 wrongly assumed you were still there from 3.4/3.5, which doesn't hold if you did section 5 on its own or reopened the app since. |Pass
| 5.4 | In the same `tb-verify-scratch` folder, type `findstr /I hello sample.txt`. | Lists two matching lines ("Hello there..." and "HELLO IN CAPS...") — case-insensitive, so both match. | | Uses the file the setup script created. Now that 5.4a exists, retry this one. | Need clarification otherwise failed.. was I suppose to do this from CMD — yes, from CMD; the missing step was 5.4a above, now added.
| 5.5 | Type `findstr /R "\AH.llo" sample.txt` (a regular expression; note `\A`, not `^` — see the note). | Matches lines starting with "Hello" — case matters this time, so "HELLO IN CAPS" should *not* match. | | This row originally used `^H.llo`, the normal regex way to say "starts with." That's wrong for Bridge Terminal specifically: `^` (and `$`, `(`, `)`) are refused outright as shell-redirect/chaining characters before the command is even parsed, quotes or not — same family as the `<` refusal, but this one was baked into the example itself, not something you could avoid by typing differently. `\A` means the same thing ("start of the text") without using a refused character, and was verified against the real parser and the real sample.txt content directly, not guessed. Bottom line: `/R` regex patterns here can't use `^`, `$`, `(`, or `)` at all right now — a real, narrower-than-advertised limitation, not just this one example. |
| 5.6 | Type `tree`. | Shows a folder tree, hidden folders excluded by default. | | |pass
| 5.7 | Type `taskmgr`. | Switches the window to the Task Manager page. | | |pass
| 5.8 | Type `sc query ssh` (or another known service). | Shows the service's real state. | | |pass
| 5.9 | Type `shutdown /r /t 60`. **Read the confirmation dialog. Click Cancel.** | Dialog previews "Restart this computer after 60 seconds?" and warns about unsaved work. Cancel means nothing happens. | |pass ⚠ Do not confirm this unless you actually want the VM to restart. |
| 5.10 | Type something nonsensical, like `frobnicate --wat`. | Refused plainly — never silently passed to a real shell. | | |pass
| 5.11 | Type `net stop cups` (or another real service). | Same confirmation-dialog pattern as everything else — nothing happens until you confirm. | | |pass

---

## 6. PowerShell

*Evidence: `[IMP-07.06/07]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 6.1 | In Command Prompt, click the **PowerShell** button (or type `powershell`). | A real PowerShell (`pwsh`) window opens in a separate terminal. | | |pass
| 6.2 | In that pwsh window, run `Get-Process`. | Real process list (pwsh's own, not routed through Trier Bridge — this is genuine PowerShell). | | |pass
| 6.3 | Back in Command Prompt, type `Get-Service ssh` (a cmdlet name, not `powershell`). | Answered directly by Trier Bridge with a "PowerShell X → Y" translation line, then the real result. | | |pass
| 6.4 | Type `Get-EventLog System`. | Refused with an explanation pointing you to Event Viewer — not silently ignored. | | |Pass

---

## 7. Services

*Evidence: `[IMP-06.05]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 7.1 | Open **Services**. | A real list of systemd services/units with their state. | | |pass
| 7.2 | Pick a user-scope service you don't mind restarting. Restart it. | Confirmation dialog, then Linux asks for permission if needed, then a verified result. | | |
| 7.3 | Try to change a system-scope service. | Either asks Linux for permission (a real polkit prompt) or is denied plainly — never silently succeeds without you noticing. | | |pass

---

## 8. Printers

*Evidence: `[IMP-03.06/HELP]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 8.1 | Open **Printers**. | Shows the real print service state and any configured printers (likely "0 printers" in this VM — that's correct, not a bug). | | |pass
| 8.2 | Click the Settings button on that page. | Opens the real GNOME printer settings panel. | | |Pass

---

## 9. Default apps

*Evidence: `[IMP-03.05]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 9.1 | Open **Apps**. Find a file type with more than one program available. | A drop-down shows the current default; a **Set** button next to it. | | |
| 9.2 | Change the default to the other option, confirm. Leave the Apps page (go to Home, say) and come back. | The new default is still shown selected — the change actually stuck, not just a UI flicker. | | (Skip this if you want — it doesn't need proving beyond what's on screen. If you're curious whether it's real at the Linux level too: `xdg-mime query default x-scheme-handler/mailto` for Email links, `inode/directory` for Folders, `x-scheme-handler/http` for Web links, should print the program you just set. Not required.) |
| 9.3 | Change it back the same way. | Reverts cleanly — the original default shows again after leaving and returning. | | |

---

## 10. Recovery from a real mistake

*Evidence: `[IMP-05]`, `[IMP-06.04]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 10.1 | Try to end a system-critical process (search Task Manager for `systemd`, PID 1 if visible, or `gnome-shell`). | No End task button is offered at all — protected processes aren't actionable. | | |
| 10.2 | Try `taskkill` in Command Prompt against a process you don't own. | Refused, naming why. | | |

---

## 11. Accessibility ⚠ Caution — needs specific tools

*Evidence: `docs/ACCESSIBILITY.md`; TB-A11Y-06/07/08 are explicitly untested until a person does this*

These three are the ones that genuinely could not be verified without a real person, because they depend on how a human perceives or navigates the screen, not just whether the software responds correctly.

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 11.1 | Unplug or ignore your mouse/trackpad. Using only Tab, Shift+Tab, arrow keys, Enter, Space, and Escape, try to reach every page and take at least one action (e.g., open Task Manager, search for a process). | Everything reachable, nothing requires a pointer. | | |
| 11.2 | Turn on Orca (GNOME's screen reader: Settings → Accessibility → Screen Reader, or `Super` then search "Orca"). Navigate the sidebar and a couple of pages with your eyes closed if you're comfortable, or just listening. | Orca reads sensible names for everything — no "unlabeled button," no silence where something should be announced. | | |
| 11.3 | In GNOME Settings, turn text scaling up to 200% (Accessibility → Text Size, or Displays → Scale). Reopen Trier Bridge. | Nothing is clipped, cut off, or overlapping. Still fully usable. | | |
| 11.4 | Turn on High Contrast (Settings → Accessibility → High Contrast). | The app stays legible; nothing relies on color alone to convey meaning. | | |

---

## 12. Package behavior ⚠ Caution — changes what's installed

*Evidence: `[IMP-08.02]`. Optional — only if you want to verify the installer itself, not just the app.*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 12.1 | `sudo apt purge trier-bridge` | Cleanly removes everything under `/usr`. Your own settings, ledger, and integration records under your home folder survive. | | |
| 12.2 | Reinstall the `.deb`. | The setup screen appears again (fresh state at the system level), but your per-user history is still there if the install script is meant to preserve it — check what you actually expect here before marking pass/fail, since "what should survive" is partly your call, not just a technical fact. | | |

---

## What's deliberately not on this list

- **A second Linux distro or desktop** (Mint, Zorin, etc.) — that's your own test on a new VM once there's a real installer, not something to try here.
- **Real hardware behavior** (Print Screen with a GPU, USB, Bluetooth, an actual printer) — this VM can't produce that; needs a physical machine.
- **The one pending fault-injection test** (temporarily stopping the print service to check the "not available" fallback) — sitting in the ledger under `IMP-02.07` waiting on your go-ahead. Not part of this checklist because it hasn't been approved to run yet.

---

## When you're done

Run `sh test-verification-cleanup.sh` from the repo root to remove the scratch test files. It will remind you that anything you moved to the Trash during testing (section 3.6) is still sitting there — empty it yourself in Files if you want it gone.

Whatever fails, write it down with what you actually saw — that's a real defect report, more useful than a passing grade. Whatever passes, you've now verified yourself, firsthand, which is worth more than any evidence document written about it. Bring this back with your Pass/Fail marks and notes, and that becomes the real basis for what ships.
