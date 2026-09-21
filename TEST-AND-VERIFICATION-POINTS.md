# Test and Verification Points

**Written:** 2026-09-21 3:27 PM CDT  
**For:** Doug Trier, to test and mark Pass/Fail himself before any release decision  
**Where to run this:** the VM console, `tb-ubuntu-desktop-2404` — sitting at the actual screen, not SSH  

---

## How to use this

Every row below is something an agent already verified by evidence — reading real files, driving the actual running app over the accessibility interface, checking real system state. Nothing here is a guess. The point of this document is for you to verify it again yourself, with your own eyes and hands, before you trust it.

Work through each section top to bottom. For each row: do the step, compare to "Expected," and write **Pass**, **Fail**, or a note in the last column. If something fails, write what actually happened — that's worth more than the checkbox.

A few sections are marked **⚠ Caution** — those either end a session, change real settings, or need a specific accessibility tool. Read the caution note before starting that section.

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
| 1.1 | If you've never run it before (or after `apt purge`), the setup screen should appear automatically on first launch. | Setup screen shows integration groups (Essentials, Files, Shortcuts) with "Whole group" checkboxes, five individual items, and **Not now** / **Apply** buttons. | | If you've already set it up, skip to 1.3 — you won't see this screen again. |
| 1.2 | Click **Apply** with the recommended selection. | The window opens normally. A tray icon "T" appears. | | |
| 1.3 | Right-click (or left-click) the tray icon. | A menu appears: Open Trier Bridge, Task Manager, Command Prompt, Change integrations, Turn off. | | |
| 1.4 | Click **Open Trier Bridge** from the tray menu while the window is closed. | The window opens (or comes to front if already open). | | |
| 1.5 | Go to the **Integrations** page from the sidebar. Turn one switch off, then back on. | The switch state changes immediately and sticks after you leave and return to the page. | | |

---

## 2. Everyday navigation — the Home search

*Evidence: `[IMP-03.09]`, three journeys driven live*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 2.1 | On the Home page, type **Add or Remove Programs** into the search box. | A result appears with a **Show** button. | | |
| 2.2 | Click **Show**. | The window switches to the **Installed Apps** page, with a search field to find an installed program. | | |
| 2.3 | Go back to Home. Type **regedit**. | The result says **No equivalent** — honestly, not with a fake Open button. | | This is deliberate: Trier Bridge never pretends a Windows-only tool has a Linux twin. |
| 2.4 | Type **Task Manager**, **Control Panel**, **Downloads** and a few other things you'd type on a real Windows machine. | Each either shows a real place to go, or honestly says there's no equivalent — never silently does nothing. | | |

---

## 3. Files and drive letters

*Evidence: `[IMP-04.07]`, `[IMP-03.03]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 3.1 | Go to the **Files** page. | You see "Familiar places" (This Computer, Desktop, Documents, Downloads, Pictures, Music, Videos, Recycle Bin, Removable drives, Network) and a **Drives** group. | | |
| 3.2 | Look at the Drives group. | `C:` is labeled "System drive" and opens to `/`. Any other mounted volume gets the next letter (`D:`, etc.) with its real path shown underneath. | | The letter is a label only — the real folder path is always shown too. |
| 3.3 | Click **Open** next to **Documents**. | The GNOME Files app opens to your real `~/Documents` folder. | | |
| 3.4 | In Command Prompt (see section 5), type `cd C:\Users\<your username>` and press Enter. | It lands in your real home folder and shows the path both ways. | | |
| 3.5 | In Command Prompt, `cd` to `C:\Users\<you>\tb-verify-scratch` (from the setup script), then `copy test.txt test-copy.txt`. | A confirmation dialog appears naming the real source and destination paths. Confirming copies the file for real. | | Uses the file the setup script created — no need to make your own. |
| 3.6 | Delete that copy: `del test-copy.txt`, confirm. | The file moves to the Trash (Recycle Bin), not permanently deleted. | | Check the Recycle Bin in Files — it should be there and restorable. The cleanup script reminds you it's there; it won't empty the Trash for you. |

---

## 4. System tools

*Evidence: `[IMP-04.01]`, `[IMP-04.03]`, `[IMP-06.04]`, `[IMP-06.05]`, `[IMP-06.06]`, `[IMP-05]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 4.1 | Open **Task Manager**. | A live, sorted list of real processes, sampled every couple of seconds. CPU/memory columns fill in after the first sample. | | |
| 4.2 | Open a terminal and run `sleep 60`. In Task Manager, search for `sleep`. | Exactly one row, with an **End task** button (it's your own process). | | |
| 4.3 | Click **End task**, read the confirmation dialog, then click **Cancel**. | Dialog closes, nothing happens — the `sleep` command in your terminal keeps running. | | |
| 4.4 | Click **End task** again, this time confirm it. | The process actually ends; your terminal shows it stopped; Task Manager shows a toast confirming it. | | |
| 4.5 | Open **Event Viewer**. Switch between the view options (All events, System, Application, Security). | Each view filters differently; counts update. | | |
| 4.6 | Switch to the **Boot** view. | Shows kernel and audit messages from *this specific boot*, not just whatever's newest overall. | | |
| 4.7 | Open **Device Manager**, **Disk Management**, **Startup Apps**, **Network**. | Each shows real data read from this machine — no placeholders, no "coming soon." | | |
| 4.8 | On the **Network** page, note the adapter's facts (IP, gateway, DNS, MAC). Click **IPv4…**. | A dialog opens: "Obtain an IP address automatically" switch, address/gateway/DNS fields, Cancel/Apply. | | Click **Cancel** — don't Apply unless you actually want to change your network settings. |
| 4.9 | Close Trier Bridge entirely while something is genuinely mid-operation if you can arrange it (or ask whoever handles the next session to seed one) — otherwise skip this row; it's already been verified once and is low-value to keep re-testing. | On the next start, a banner says an earlier action was interrupted and needs review, with a way to mark it reviewed. | | Optional — this one's expensive to reproduce safely without deliberately killing the app mid-write. |

---

## 5. Command Prompt (Bridge Terminal)

*Evidence: `[IMP-07]` and the whole IMP-07.x series*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 5.1 | Open **Command Prompt**. Type `hostname` and press Enter. | Prints this machine's real hostname, plus a small note showing the Linux equivalent command. | | |
| 5.2 | Type `ipconfig /all`. | Shows real adapter facts matching what Network page showed. | | |
| 5.3 | Type `dir C:\Users`. | Lists real home folders. | | |
| 5.4 | In the same `tb-verify-scratch` folder, type `findstr /I hello sample.txt`. | Lists two matching lines ("Hello there..." and "HELLO IN CAPS...") — case-insensitive, so both match. | | Uses the file the setup script created. |
| 5.5 | Type `findstr /R "^H.llo" sample.txt` (a regular expression). | Matches lines starting with "Hello" — case matters this time, so "HELLO IN CAPS" should *not* match. | | |
| 5.6 | Type `tree`. | Shows a folder tree, hidden folders excluded by default. | | |
| 5.7 | Type `taskmgr`. | Switches the window to the Task Manager page. | | |
| 5.8 | Type `sc query ssh` (or another known service). | Shows the service's real state. | | |
| 5.9 | Type `shutdown /r /t 60`. **Read the confirmation dialog. Click Cancel.** | Dialog previews "Restart this computer after 60 seconds?" and warns about unsaved work. Cancel means nothing happens. | | ⚠ Do not confirm this unless you actually want the VM to restart. |
| 5.10 | Type something nonsensical, like `frobnicate --wat`. | Refused plainly — never silently passed to a real shell. | | |
| 5.11 | Type `net stop cups` (or another real service). | Same confirmation-dialog pattern as everything else — nothing happens until you confirm. | | |

---

## 6. PowerShell

*Evidence: `[IMP-07.06/07]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 6.1 | In Command Prompt, click the **PowerShell** button (or type `powershell`). | A real PowerShell (`pwsh`) window opens in a separate terminal. | | |
| 6.2 | In that pwsh window, run `Get-Process`. | Real process list (pwsh's own, not routed through Trier Bridge — this is genuine PowerShell). | | |
| 6.3 | Back in Command Prompt, type `Get-Service ssh` (a cmdlet name, not `powershell`). | Answered directly by Trier Bridge with a "PowerShell X → Y" translation line, then the real result. | | |
| 6.4 | Type `Get-EventLog System`. | Refused with an explanation pointing you to Event Viewer — not silently ignored. | | |

---

## 7. Services

*Evidence: `[IMP-06.05]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 7.1 | Open **Services**. | A real list of systemd services/units with their state. | | |
| 7.2 | Pick a user-scope service you don't mind restarting. Restart it. | Confirmation dialog, then Linux asks for permission if needed, then a verified result. | | |
| 7.3 | Try to change a system-scope service. | Either asks Linux for permission (a real polkit prompt) or is denied plainly — never silently succeeds without you noticing. | | |

---

## 8. Printers

*Evidence: `[IMP-03.06/HELP]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 8.1 | Open **Printers**. | Shows the real print service state and any configured printers (likely "0 printers" in this VM — that's correct, not a bug). | | |
| 8.2 | Click the Settings button on that page. | Opens the real GNOME printer settings panel. | | |

---

## 9. Default apps

*Evidence: `[IMP-03.05]`*

| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| 9.1 | Open **Apps**. Find a file type with more than one program available. | A drop-down shows the current default; a **Set** button next to it. | | |
| 9.2 | Change the default to the other option, confirm. | The change is real — verify with `xdg-mime query default <type>` in a terminal afterward. | | |
| 9.3 | Change it back. | Reverts cleanly; no leftover state. | | |

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
