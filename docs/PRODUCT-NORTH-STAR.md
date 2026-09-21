# Trier Bridge Product North Star

**Status:** Governing product direction  
**Owner:** Doug Trier  
**Date:** September 20, 2026

## North Star

> **Everything a Windows user already knows how to do should have a familiar place to go on Linux.**

Trier Bridge targets the normal Windows user first: office users, home users, small-business users, and people who already know Windows well enough to be productive without thinking about the operating system.

Power users, technicians, and Windows administrators are also first-class users, but they are deeper layers of the same experience rather than the sole audience.

## Product promise

A user should be able to move from Windows to a supported Linux environment and continue normal work with minimal cognitive reset.

Everyday tasks should feel familiar:

- files and folders
- copy/cut/paste
- right-click actions
- drag and drop
- search
- application launching and switching
- documents and downloads
- printers and scanners
- USB/removable drives
- Wi-Fi and network shares
- common settings
- default applications
- installed applications
- updates
- screenshots and clipboard
- basic troubleshooting

Advanced users should additionally find familiar mental models for:

- Task Manager
- Startup Apps
- Device Manager
- Disk Management
- Network Connections
- Event Viewer
- Services
- Command Prompt
- PowerShell

## UX priority order

1. **Everyday continuity**
2. **Familiar troubleshooting**
3. **Advanced Windows continuity**
4. **Optional Linux learning**

Learning Linux is optional. Productivity is not.

## Decision test

For every product decision ask:

1. Does this reduce unnecessary Windows-to-Linux cognitive friction?
2. Can the user complete the task without needing Linux knowledge that Windows never required?
3. Does the solution preserve Linux security and native authority?
4. Does failure leave the machine safe and the user informed?
5. Does the interface tell the truth when an exact Windows equivalent does not exist?

If a design makes Linux internals more visible without adding user value, prefer the simpler familiar path with progressive disclosure.

---

## Owner product directive

**Owner:** Doug Trier  
**Date:** September 20, 2026

This directive governs product prioritization and is the owner's own statement of intent.

The intended audience is the typical Windows office/home user through advanced Windows users.

Trier Bridge should make the transition to Linux feel seamless enough that:

> **Everything I know how to do on Windows, I can now do on Linux through a familiar experience whenever Linux provides a safe equivalent.**

Everyday tasks should be easy and require little thought.

The experience should feel familiar in:

- file handling
- right-click
- drag/drop
- search
- applications
- printers
- USB
- network shares
- settings
- common shortcuts
- troubleshooting

Advanced tools such as Task Manager, Event Viewer, Device Manager, Services, Command Prompt, and PowerShell are important but are deeper layers, not the entire product.

The project should hide unnecessary Linux complexity behind safe defaults and progressive disclosure without weakening Linux security or lying about capability.

Additional standing owner direction:

1. Linux remains Linux underneath.
2. Core functionality is local-first.
3. Do not weaken security to create familiarity.
4. Design to prevent failure; when failure occurs, fail gracefully.
5. Use America/Chicago (Central Time) for project timestamps.
6. **Non-invasive (2026-09-20):** Trier Bridge must not be invasive and must never be mistaken for a virus. The owner defines the outcome; the engineering approach is delegated, subject to `SECURITY.md`, `INVARIANTS.md`, and DEC-018.
