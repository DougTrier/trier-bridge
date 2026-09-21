# Trier Bridge Accessibility Criteria

**Status:** criteria frozen for the first release (SCOPE-09), 2026-09-21. Evidence states follow `VALIDATION.md` section 1.

Accessibility was a stack-selection gate (ARC-02): the framework had to expose every control to AT-SPI on Wayland with a name and a description, without a screen reader running. GTK 4 + libadwaita passed that gate (RESEARCH F17) and every page since has been checked the same way.

## 1. Criteria

| ID | Criterion | How it is checked | State |
|---|---|---|---|
| TB-A11Y-01 | Every interactive control has an accessible name; every control that changes something has an accessible description saying what it does and that it asks first. | AT-SPI walk of each page (`a11y_walk.py`, test aid) after every foundation; TB-INV-209 | verified for every shipped page (entries IMP-01..IMP-08) |
| TB-A11Y-02 | Every action a pointer can take can be taken through AT-SPI actions (click, toggle) and therefore through assistive technology. | `a11y_do.py` drives buttons, switches, and dialogs; the setup screen, Integrations page, Task Manager, terminal dialogs, and file operations were driven that way | verified for the flows in entries SCOPE-14, IMP-03.03, IMP-06.04 |
| TB-A11Y-03 | Text entry works through the editable-text interface (no reliance on synthesized key events). | `a11y_type.py` set the Bridge command entry text (entry IMP-03.03) | verified |
| TB-A11Y-04 | Results are announced: every outcome is a toast or a text line, never colour or icon alone. | `MainWindow.notify` toasts; terminal output lines; dialogs carry the preview as body text | verified by reading (TB-INV-078) |
| TB-A11Y-05 | Data-driven titles never carry markup; names from the system are shown verbatim. | `Adw.ActionRow(use_markup=False)` everywhere; unit tests on hostile names | verified |
| TB-A11Y-06 | Keyboard-only operation: every page reachable and every action completable with Tab, arrows, Enter, Space, Escape. | needs a person at the console with no pointer | NOT RUN |
| TB-A11Y-07 | Screen reader session: Orca reads the sidebar, each page, each dialog, and each result in a sensible order. | needs a person with Orca in the console session | NOT RUN |
| TB-A11Y-08 | Large text and high contrast: the window stays usable at 200% text scaling and with the high-contrast theme; nothing is clipped or colour-only. | needs a person; GNOME Settings text scaling and high contrast | NOT RUN |
| TB-A11Y-09 | Localization readiness: every user-visible string is plain and complete (no concatenated fragments that break when translated). | by reading; translation itself is out of scope for the first release (English only, DEC pending) | partly (strings are plain; no gettext yet) |

## 2. What "verified" means here

AT-SPI is the same interface Orca uses. A control that a walk cannot name is a control a screen reader cannot name; a control a walk cannot act on is a control a switch user cannot act on. The walks are evidence for TB-A11Y-01..05. They are not evidence for TB-A11Y-06..08, which need a person and stay NOT RUN until then (TB-IA acceptance cases in `VALIDATION.md` section 6).

## 3. Known gaps

- Drop-downs (default apps) are named after the selected program; the purpose is in the description. Acceptable, but a label would be better if GTK allows it without replacing the widget.
- The Task Manager list exposes up to 200 rows; a screen reader user will want the search field first. The field precedes the list in the tree.
- No translations exist; the product is English only until a localization decision is recorded.
