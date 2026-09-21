# Trier Bridge Experience Design

**Status:** Design inventory and rules, not final UI.

This document covers interaction rules, the screen/flow inventory, search, connectivity and display surfaces, the Manual, localization, and theming/visual-asset policy. The product-level description of each surface is in `PRODUCT-CONCEPT.md`.

## 1. Core rule

The user should spend attention on their work, not on translating operating-system concepts.

## 2. Everyday behavior

- single click selects where the active desktop convention expects it
- double click/open follows the safe conventions of the selected desktop
- right-click exposes useful familiar actions
- drag-and-drop visibly communicates copy/move/import intent
- destructive actions require deliberate activation
- Back returns predictably
- search is always easy to reach
- Settings and Help are always discoverable
- keyboard-only use is supported
- screen-reader labels describe action and consequence

## 3. Familiar terminology

Use Windows-familiar terminology where it improves comprehension, but do not misstate Linux semantics.

- "Installed Apps" may aggregate several Linux package sources.
- "Task Manager" may display processes/apps/services from Linux sources.
- "Event Viewer" is a familiar view over native logs, not a claim that Windows Event Log exists.

## 4. Progressive disclosure

Default surface: user task, plain language, familiar concept.

Optional detail: Linux native term, backend, command equivalent, source/provenance, technical diagnostics.

## 5. Failure

Every failed action must answer:

1. Did anything change?
2. What stopped it?
3. What is the safest next step?

## 6. Screen and flow inventory

### Everyday experience

1. Home / launcher / search
2. Applications
3. Recent / pinned
4. Files entry
5. Documents
6. Downloads
7. Desktop
8. Pictures
9. Removable drives
10. Network locations
11. Printers
12. Bluetooth/devices
13. Displays
14. Sound
15. Network/Wi-Fi
16. Default Apps
17. Installed Apps
18. Updates
19. Storage overview
20. Accounts/session
21. Accessibility
22. Privacy
23. Settings search
24. Help / Manual

### Familiar troubleshooting

25. Task Manager — Apps
26. Task Manager — Processes
27. Task Manager — Performance
28. Task Manager — Startup
29. Network Connections
30. Device Manager
31. Disk Management
32. Event Viewer
33. Services

### Advanced continuity

34. Bridge Terminal
35. PowerShell entry
36. System information
37. Advanced diagnostics
38. Capability/environment details

### Supporting states required for every applicable screen

loading, empty, unavailable, unsupported, unknown, permission required, denied, offline, stale, error, partial success, cancellation, retry, recovery required, help, large text, keyboard-only, screen reader.

A pictured happy path does not complete a flow.

## 7. Search and identification

A Windows user should be able to search using the words they already know: Task Manager, Device Manager, Event Viewer, Add or Remove Programs, Default Apps, Network Connections, Startup Apps, Printers, Disk Management, Services, CMD, PowerShell.

Search routes familiar terms to Trier Bridge capabilities and native Linux destinations.

Search domains: applications, files, settings, system tools, help/manual, Windows synonyms, Linux native names, common task phrases.

Identity rules:

- A search result label is not mutation identity.
- For system objects, preserve stable canonical identifiers separately from human labels.

Privacy: local search remains local by default. No file names, queries, or system inventory are uploaded merely to provide search.

No-results behavior offers synonym suggestions, the closest familiar concept, an unavailable-capability explanation, and a Manual/help result. Never fabricate a setting or tool that the current environment cannot provide.

## 8. Connectivity surfaces

Core Trier Bridge functionality remains useful without Internet access.

Everyday surfaces: Wi-Fi, Ethernet, VPN, IP information, DNS/gateway, network shares, printer discovery where local protocols allow, Bluetooth entry point, connectivity troubleshooting.

Network shares: provide familiar workflows for SMB/CIFS and other qualified sources without requiring users to know mount commands. Preserve credential scope, connection identity, reconnect behavior, offline/unavailable state, read/write capability, and safe disconnect.

No account, cloud service, or remote API is required for the file experience, Task Manager, Event Viewer, device inventory, storage inventory, service management, Bridge Terminal translation, or local help. Optional online functionality degrades independently.

## 9. Displays

Windows users should be able to manage monitors without learning Linux display-stack details.

Familiar capabilities: identify displays, arrange visually, primary display where the desktop supports it, resolution, scaling, orientation, refresh rate where available, mirror/extend, detect/reconnect, laptop lid/dock behavior where supported.

Rules:

- Wayland/X11/backend capability is detected.
- Physical display identity and UI order are separate.
- Preview risky changes before commit where possible.
- Offer automatic rollback for settings that could make the display unusable.
- External desktop changes are rediscovered.
- Unsupported controls remain unavailable rather than simulated.
- Large text/scaling must not make recovery confirmation unreachable.

## 10. Manual and context help

The Manual is optional help, not required training. A normal user should be productive without reading it.

Layers:

- **Everyday tasks:** files and folders, printers, USB, Wi-Fi, network shares, apps, defaults, displays, sound, screenshots
- **Troubleshooting:** Task Manager, Event Viewer, Device Manager, Network Connections, storage
- **Advanced:** Services, Bridge Terminal, PowerShell, native Linux equivalents

Every system tool supports: What is this? What changed? Why is this unavailable? What should I do next? Show me the Linux way.

Core Manual content is bundled and usable without Internet. Documentation must match the shipped version.

## 11. Localization

Language must not become another migration barrier.

- UI language does not change backend identifiers.
- Familiar Windows concepts need reviewed translations, not literal word substitution.
- Linux native names may be preserved in technical detail.
- Search synonyms are locale-aware.
- RTL and non-Latin input must not corrupt canonical identifiers.
- IME composition must work.
- Number/date/size formatting is locale-aware.
- Localized shell text is not parsed when structured APIs exist.

Advertised languages require UI coverage, help/manual coverage, Windows/Linux terminology review, large-text checks, search/synonym checks, and native-speaker review where practical. Draft translation is not qualified localization.

## 12. Theming, visual assets, and reuse

Goal: feel familiar without cloning protected Windows visual assets. Final assets do not yet exist.

Principles:

- original Trier Bridge icons/assets for branding, launcher/search, system-tool categories, help/learning, status and recovery
- familiar hierarchy and interaction, not trademark imitation
- accessibility over decorative fidelity
- desktop integration rather than fighting the host
- theme follows light/dark/high-contrast environment where practical
- user can retain native Linux appearance while using Trier Bridge workflows

Not allowed:

- copying Microsoft proprietary icons, logos, wallpapers, or screenshots
- pixel-for-pixel Windows reproduction as a product requirement
- hard-coded visuals that break high contrast or large text
- theme changes that alter security/behavior

Reuse preference order:

1. original Trier Bridge design
2. platform-native open components with compatible licensing
3. clearly licensed third-party assets/components
4. functional familiarity through interaction patterns

For every reused component record source, version, license, attribution, security maintenance, accessibility, distro/desktop assumptions, package cost, and whether modification is required. Unknown provenance means do not ship. See `LICENSING.md`.
