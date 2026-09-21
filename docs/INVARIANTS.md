# INVARIANTS.md
# Trier Bridge — Product, Safety, Recovery, and Compatibility Invariants

**Project:** Trier Bridge  
**Status:** Design baseline — no runtime PASS implied  
**Revision:** 0.1  
**Date:** September 20, 2026  
**Owner:** Doug Trier  

> **North Star:** Do not make Linux look like Windows. Make existing Windows knowledge useful on Linux — without weakening Linux, damaging the system, or lying about what happened.

> **Failure doctrine:** Prevent failure where possible. When failure still occurs: protect user/system state → stop scope expansion → preserve evidence → return control → explain what changed → provide the safest recovery path.

---

## 1. Research baseline

Research performed September 20, 2026 found many adjacent projects, but no exact mature match for the full Trier Bridge concept. This is a research result, **not proof that no such project exists anywhere**.

### Existing categories and what they prove

- **Windows-familiar Linux distributions:** Zorin OS, AnduinOS, Linux Mint, and Lindows reduce visual/workflow migration friction. They prove demand for familiarity, but their core proposition is the desktop/distribution experience rather than a portable Windows-knowledge translation layer.
- **Windows-like system monitors:** Mission Center, SysMonTask, and System Monitoring Center provide familiar process/performance/service views. They prove familiar administration UI is useful, but they do not unify the broader Windows mental model.
- **Graphical Linux administration:** Cockpit is the strongest adjacent architecture. It uses native system mechanisms, exposes only available capabilities, works with actual user permissions, and covers services/logs/network/storage/packages. It is primarily a server administration console, not a Windows-to-Linux knowledge bridge.
- **Journal/Event Viewer analogs:** GNOME Logs provides categorized systemd-journal viewing, but it does not translate the rest of Windows administration.
- **Command compatibility:** the `ChenPi11/cmd` project reimplements `cmd.exe` semantics on Unix. Small command-translator repositories also exist. These validate interest in command familiarity, but Trier Bridge must use typed system intents rather than making arbitrary shell translation its security boundary.
- **Migration helpers:** Linux Migration Companion helps users assess migration readiness; iGloo automates aspects of moving from Windows to Linux; `win2linux-migration` documents workflow parity. These help before/during migration rather than providing the proposed post-install runtime administration bridge.
- **Static knowledge mapping:** Win-Linux.com teaches Linux concepts from a Windows perspective. Trier Bridge would make that mapping interactive and operational.

### Research-derived design lessons

1. **Familiar appearance is not enough.** Windows migrants still report friction when familiar workflows behave differently.
2. **Capability-driven UI is safer than fake universality.** Cockpit and PackageKit expose operations according to available backends/capabilities.
3. **Do not run the whole application as root.** Some older system-monitor tools recommend this for additional data; Trier Bridge explicitly rejects that architecture.
4. **Missing metrics are normal on Linux.** GPU, process, sensor, desktop, and driver visibility vary. Unknown must remain unknown.
5. **Linux administration is plural.** Distros, init systems, package managers, desktops, display servers, network stacks, and packaging formats vary.
6. **Authorization is native and contextual.** polkit treats privileged mechanisms as serving untrusted subjects; user interaction should occur only when tied to a user action.
7. **Native APIs should remain authoritative.** NetworkManager, systemd, udisks/storaged, PackageKit, D-Bus, and other platform APIs already encode policy and capability boundaries.
8. **Rollback support should be used when the platform provides it.** Network configuration is a prime example.
9. **Static documentation alone does not solve migration friction.** The translation needs to happen at the point of action.
10. **The product must teach differences, not erase them.** A bridge that lies about Linux semantics creates future failure.

### Research references

- Zorin OS — https://zorin.com/os/
- AnduinOS — https://www.anduinos.com/
- Linux Mint — https://linuxmint.com/
- Lindows — https://lindows.org/
- Cockpit — https://cockpit-project.org/
- Cockpit feature internals — https://docs.cockpit-project.org/cockpit-guide/latest/guide/features.html
- Mission Center — https://missioncenter.io/
- SysMonTask — https://github.com/KrispyCamel4u/SysMonTask
- System Monitoring Center — https://github.com/hakandundar34coding/system-monitoring-center
- GNOME Logs — https://apps.gnome.org/Logs/
- Unix cmd.exe reimplementation — https://github.com/ChenPi11/cmd
- Linux Migration Companion — https://github.com/dennishilk/linux-migration-companion
- iGloo — https://github.com/gillesduif/iGloo
- Windows-to-Linux workflow notes — https://github.com/Michael-Matta1/win2linux-migration
- Windows-to-Linux concept guides — https://win-linux.com/
- polkit reference — https://polkit.pages.freedesktop.org/polkit/
- NetworkManager reference — https://networkmanager.pages.freedesktop.org/NetworkManager/
- PackageKit backend model — https://www.freedesktop.org/software/PackageKit/gtk-doc/introduction-backends.html
- D-Bus specification — https://dbus.freedesktop.org/doc/dbus-specification.html

---

## 2. Authority and invariant rules

1. This file is the canonical invariant ledger for Trier Bridge.
2. `SECURITY.md` supplies detailed security architecture. If the two documents appear to conflict, the **stricter safety/security rule controls until explicitly reconciled**.
3. An invariant may be clarified without weakening it. Narrowing scope, reducing failure coverage, converting Unknown to Supported, or weakening recovery requires an explicit owner-approved design amendment.
4. A design statement, code path, compile, mockup, or successful happy-path test is **not** proof that an invariant passes.
5. Each invariant has a default one-to-one test identity: `TB-INV-###` → `TB-T###`. Additional integration, distro, UX, or destructive-failure tests may also apply.
6. If a later change invalidates evidence, the invariant returns to unverified for the affected build/environment.
7. Invariants apply only where technically relevant, but non-applicability must be documented rather than assumed.

---

## 3. Canonical invariants

### 3.1 Product truth, scope, and user trust

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-001** | Trier Bridge is a compatibility and learning layer, not a Linux distribution, Windows emulator, Wine replacement, or hidden shell wrapper. | If the environment cannot support a requested bridge feature, keep Linux usable and explain the limitation without pretending compatibility. |
| **TB-INV-002** | Linux remains the authoritative operating system; Trier Bridge may translate concepts but may not replace native security, ownership, service, package, or filesystem semantics. | If native Linux policy disagrees with Trier Bridge intent, Linux wins and the user receives a plain-language explanation. |
| **TB-INV-003** | Windows terminology is a presentation aid, never a claim that Linux and Windows are internally identical. | When no faithful mapping exists, say “no direct equivalent” and perform no silent substitute. |
| **TB-INV-004** | Every user-visible claim must distinguish supported, unsupported, unknown, requires authorization, degraded, and failed states. | Never display success or availability when evidence is incomplete. |
| **TB-INV-005** | A feature may be hidden or disabled when its required backend is absent; it may not be simulated with an unsafe fallback. | Preserve unrelated features and provide the closest safe educational path. |
| **TB-INV-006** | A successful dispatch is not a successful operation; success requires an observable postcondition where verification is technically possible. | If verification cannot be completed, report “requested / unverified” rather than “completed.” |
| **TB-INV-007** | Documentation must distinguish design intent, implemented behavior, automated evidence, distro-specific evidence, physical evidence, and release evidence. | Missing evidence remains visible and cannot be converted to PASS by prose. |
| **TB-INV-008** | No visual resemblance to Windows may require weakening Linux behavior, security, recoverability, accessibility, or update mechanisms. | Prefer a slightly less familiar UI over unsafe imitation. |
| **TB-INV-009** | Core local administration and learning features must not require an account, subscription, cloud service, or Internet connection. | If optional network features fail, local functions remain available. |
| **TB-INV-010** | Trier Bridge must preserve the user’s ability to use native Linux tools alongside it. | Changes made outside Trier Bridge must be rediscovered rather than overwritten. |
| **TB-INV-011** | The product must never take ownership of files, services, packages, repositories, users, or devices merely because it can see them. | Ownership must be explicit and scoped. |
| **TB-INV-012** | Read-only discovery must be separable from mutation. | If mutation capability fails or is unavailable, inspection should continue whenever native permissions allow it. |
| **TB-INV-013** | The beginner experience must not conceal consequences that an experienced Linux administrator would consider material. | Show impact, privilege, reversibility, and interruption risk before consequential actions. |
| **TB-INV-014** | The advanced experience must not expose unsafe bypasses merely because the user requests more control. | Advanced mode increases detail, not trust. |
| **TB-INV-015** | No invariant may be weakened for visual polish, performance, convenience, token savings, platform coverage, or code reuse without an explicit documented design decision. | If a requirement conflicts with an invariant, stop the affected feature and surface the conflict. |

### 3.2 Installation, distribution, desktop, and environment boundaries

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-016** | Distribution identity must be detected from authoritative runtime facts, not guessed from branding, theme, hostname, or filesystem shape. | Unknown distributions enter a generic capability-detection path. |
| **TB-INV-017** | Distribution version and derivative relationships must be recorded separately. | If lineage is ambiguous, avoid distro-specific mutation. |
| **TB-INV-018** | The init/service manager must be detected; systemd may not be assumed merely because it is common. | On non-systemd systems, service mutation stays unavailable until an adapter is qualified. |
| **TB-INV-019** | The network management backend must be detected; NetworkManager may not be assumed. | If no qualified backend exists, show read-only interface facts where safe and disable network mutation. |
| **TB-INV-020** | The package-management backend must be detected independently from distribution name. | If multiple package managers coexist, preserve package provenance and do not merge identities. |
| **TB-INV-021** | The desktop environment must be detected where desktop integration depends on it. | Unknown desktops receive generic behavior without forced theme/config edits. |
| **TB-INV-022** | Wayland and X11 behavior must be treated as separate capability surfaces. | If a window-management or global-input feature is unavailable under the active display protocol, degrade without switching protocols. |
| **TB-INV-023** | Headless, remote, nested, containerized, kiosk, and local interactive sessions must not be conflated. | Disable assumptions requiring a physical desktop session when one is not present. |
| **TB-INV-024** | Flatpak, Snap, AppImage, native packages, containers, and manually installed applications must retain distinct provenance. | Do not claim one packaging system can safely manage another without an explicit adapter. |
| **TB-INV-025** | Installation must not overwrite existing shell startup files, desktop settings, aliases, PowerShell profiles, or user customizations without explicit consent. | If integration cannot be added non-destructively, leave it unmodified and provide manual instructions. |
| **TB-INV-026** | Uninstall must remove Trier Bridge-owned components without deleting unrelated user or system configuration. | Unknown ownership means preserve. |
| **TB-INV-027** | Installation failure must leave the pre-install system bootable and normally usable. | Partial installation must be detectable and recoverable or cleanly removable. |
| **TB-INV-028** | Upgrade must preserve user choices, audit history required for recovery, and compatibility settings unless a migration explicitly says otherwise. | On migration failure, retain or restore the last usable state. |
| **TB-INV-029** | Downgrade compatibility must be explicit; an older build may not silently interpret newer state. | Open read-only or refuse safely rather than corrupting state. |
| **TB-INV-030** | CPU architecture must be detected and package/artifact compatibility verified before installation. | Wrong-architecture artifacts must be rejected before mutation. |
| **TB-INV-031** | Filesystem case sensitivity, path rules, mount semantics, and permission behavior must be discovered rather than Windows-assumed. | Ambiguous path mappings remain unexecuted. |
| **TB-INV-032** | Locale, encoding, keyboard layout, and input method must not be inferred from UI language alone. | Preserve text as valid Unicode and surface unsupported input behavior. |
| **TB-INV-033** | A missing optional runtime dependency must disable only the dependent capability. | Do not fail application startup for an unrelated optional component. |

### 3.3 Capability discovery and adapter contracts

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-034** | Every system-facing feature must declare the capability it requires and the adapter that supplies it. | No adapter means no mutation. |
| **TB-INV-035** | Adapters must report Supported, Unsupported, Unknown, Degraded, and Error distinctly. | Unknown may never be converted to Supported by a default. |
| **TB-INV-036** | Capability detection must be side-effect free unless the user explicitly starts a test that documents its effects. | If safe detection is impossible, mark unknown. |
| **TB-INV-037** | Capability results must include the evidence source and freshness needed to decide whether revalidation is required. | Stale capability data cannot authorize mutation. |
| **TB-INV-038** | An adapter must expose its supported operations individually rather than claiming blanket subsystem support. | Hide or disable unsupported operations without disabling supported siblings. |
| **TB-INV-039** | Adapters must define required privilege separately for read, preview, and mutate paths. | Do not elevate the entire adapter because one operation needs privilege. |
| **TB-INV-040** | Adapters must return structured errors, not only exit codes or human text. | Unparseable errors become Unknown/Error, not success. |
| **TB-INV-041** | Adapter timeouts must be bounded and cancellable. | Timeout returns control to the user and does not trigger a weaker fallback. |
| **TB-INV-042** | Adapter output must be size-bounded and streamed where appropriate. | Oversized output is truncated or paged with an explicit notice. |
| **TB-INV-043** | Adapter behavior must be version-aware when upstream APIs change semantics. | Unsupported versions remain unavailable rather than heuristically driven. |
| **TB-INV-044** | Distribution-specific adapters may not leak distro assumptions into core domain logic. | A missing specialization falls back to safe generic read-only behavior where available. |
| **TB-INV-045** | Native APIs or stable D-Bus interfaces are preferred over parsing localized CLI text when both are available. | If only CLI output exists, parser version/locale assumptions must be explicit and tested. |
| **TB-INV-046** | Capability probes must not leave services enabled, packages installed, files created, or configuration changed. | Any temporary probe artifact must be removed or explicitly reported. |
| **TB-INV-047** | Multiple available backends must be selected deterministically with documented precedence. | Do not race two mutation backends against the same resource. |
| **TB-INV-048** | Backend disappearance or restart must invalidate affected capability state. | Pending actions revalidate before continuing. |

### 3.4 Stable identity, state, concurrency, and lifecycle

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-049** | UI row position, list order, display label, device path, PID, interface index, and package display name are not sufficient stable identities by themselves. | Capture stronger identity before mutation or refuse the action. |
| **TB-INV-050** | Process actions must defend against PID reuse by revalidating identity immediately before signaling. | If identity changed, cancel rather than affect the replacement process. |
| **TB-INV-051** | Removable storage actions must defend against device-node reuse and hotplug replacement. | If the device identity changed, cancel and rediscover. |
| **TB-INV-052** | Network actions must bind to stable connection/device identity, not only an interface name that may be reused. | Stale targets require reconfirmation. |
| **TB-INV-053** | Service actions must bind to the exact manager/unit identity active at execution time. | If the unit was replaced, reloaded incompatibly, or vanished, stop. |
| **TB-INV-054** | Package actions must bind to package identity, source, architecture, and planned version. | If repository metadata changes the plan, require a refreshed preview. |
| **TB-INV-055** | Every consequential operation must capture a correlation/operation ID. | Retries must be idempotent or explicitly rejected. |
| **TB-INV-056** | A second request must not silently overwrite a still-pending first request. | Queue, merge, cancel, or reject according to operation semantics. |
| **TB-INV-057** | Cancellation must have a defined boundary: before commit, during commit, or after commit. | Never label an uncancellable committed phase as cancelled. |
| **TB-INV-058** | UI closure must not imply operation cancellation. | Background work must expose truthful state on return. |
| **TB-INV-059** | Application crash must not convert Pending into Success. | On restart, reconcile from external reality and durable journal state. |
| **TB-INV-060** | System reboot must not replay destructive or privileged operations automatically unless the operation contract explicitly requires safe resume. | Uncertain work becomes Needs review. |
| **TB-INV-061** | Suspend/resume must invalidate time-sensitive, device-sensitive, and network-sensitive observations. | Revalidate before mutation. |
| **TB-INV-062** | Clock, timezone, or daylight-saving changes must not corrupt ordering or timeout logic. | Use monotonic clocks for durations and stable timestamps for audit. |
| **TB-INV-063** | Cross-window or multi-instance actions must coordinate through one authority for mutable state. | Conflicts are serialized or rejected, never last-writer-wins by accident. |

### 3.5 Familiar UX, mental-model translation, and learning

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-064** | Familiar Mode, Bridge Mode, and Native Mode alter terminology and teaching depth, not authorization or backend behavior. | A mode switch cannot unlock a capability. |
| **TB-INV-065** | Every Windows-labeled concept must have an explicit mapping note describing what is equivalent, approximate, or different on Linux. | If the mapping is approximate, the UI must say so. |
| **TB-INV-066** | Task Manager presentation must not imply that every Linux process maps to a Windows application. | Distinguish apps, processes, threads, services, and kernel/system workloads. |
| **TB-INV-067** | Services UI must keep Start/Stop/Restart separate from Enable/Disable at boot. | Never copy Windows wording in a way that merges runtime and boot-state semantics. |
| **TB-INV-068** | Event Viewer presentation must not imply Windows event IDs or channels exist when showing journald/syslog data. | Use familiar categories as views while preserving source fields. |
| **TB-INV-069** | Device Manager presentation must not imply driver update/removal semantics that Linux does not support through a qualified route. | Unsupported driver actions remain explanatory only. |
| **TB-INV-070** | Disk Management must never hide Linux mount points, filesystems, encryption, or multi-device storage behind misleading drive-letter fiction. | Familiar aliases may be shown only as optional learning aids. |
| **TB-INV-071** | Network Connections must distinguish interface state, connection profile state, link state, IP configuration, and Internet reachability. | Do not collapse them into one Connected/Disconnected flag. |
| **TB-INV-072** | Installed Apps must preserve package format, source, scope, and update authority. | A unified list cannot erase provenance. |
| **TB-INV-073** | Windows-style paths shown for familiarity must never become authoritative Linux paths. | The underlying canonical Linux path remains visible in Bridge/Native detail. |
| **TB-INV-074** | Right-click actions must be capability-driven and context-specific. | Unsupported actions disappear or explain themselves instead of failing after click. |
| **TB-INV-075** | Drag-and-drop must never execute, install, mount, or elevate automatically. | Drop is preview/import intent until explicitly confirmed when consequential. |
| **TB-INV-076** | Familiar keyboard shortcuts may be offered only when they do not override critical desktop/window-manager behavior without consent. | Conflicts are detected or left to the native desktop. |
| **TB-INV-077** | The product must not globally rebind keys, mouse behavior, or file associations just to resemble Windows. | Integration remains opt-in and reversible. |
| **TB-INV-078** | Every destructive action must use plain-language impact text understandable without Linux knowledge. | Technical detail remains available but cannot replace the plain explanation. |
| **TB-INV-079** | Every recoverable failure must offer the safest next action before advanced troubleshooting. | Do not send beginners directly to an unrestricted root shell. |
| **TB-INV-080** | “Show me the Linux way” must reflect the actual operation semantics. | If Trier Bridge used a D-Bus/API path, label a shell command as an equivalent, not as the action secretly run. |
| **TB-INV-081** | Teaching content must be versioned with the feature contract. | If the backend changes, stale teaching is flagged or updated before release. |

### 3.6 Bridge Terminal and Windows-command translation

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-082** | Bridge Mode must be visually unmistakable from Bash, Zsh, Fish, PowerShell, and other native shells. | A mode mismatch must never silently execute under another interpreter. |
| **TB-INV-083** | Bridge Mode must use a grammar/parser, not string replacement. | Parse failure performs no operation. |
| **TB-INV-084** | Recognized commands must map to typed operations before execution. | No typed mapping means unsupported. |
| **TB-INV-085** | Unknown commands must not fall through to a native shell automatically. | Offer explanation or explicit mode switch. |
| **TB-INV-086** | Unknown switches/flags must be rejected unless the command contract explicitly allows passthrough. | Do not ignore syntax that could alter intent. |
| **TB-INV-087** | Trailing tokens must be fully consumed by the parser. | Unparsed residue causes rejection. |
| **TB-INV-088** | Shell metacharacters, substitutions, redirection, pipes, and chaining must be treated as syntax features with explicit support, never incidental shell behavior. | Unsupported compound syntax is rejected as a whole. |
| **TB-INV-089** | Command translation must preserve quoting and Unicode without enabling injection. | Invalid encoding or ambiguous quoting fails without execution. |
| **TB-INV-090** | Environment-variable expansion rules must be explicit per Bridge command. | Do not mix Windows `%VAR%`, PowerShell `$env:VAR`, and shell `$VAR` semantics implicitly. |
| **TB-INV-091** | Path translation must be explicit and context-aware. | Ambiguous drive-letter, UNC, WSL, Wine, or Linux paths require clarification. |
| **TB-INV-092** | Windows current-directory semantics must not invent fake drive state that changes Linux paths unpredictably. | Display familiarity may differ from internal canonical location. |
| **TB-INV-093** | Read-only commands should not trigger elevation merely to make output more complete. | Show restricted fields as unavailable. |
| **TB-INV-094** | Mutation commands must preview the normalized typed operation before privilege is requested when feasible. | If normalization changes the apparent target, require confirmation. |
| **TB-INV-095** | Command aliases must share one canonical implementation. | Aliases cannot diverge in security or side effects. |
| **TB-INV-096** | Compatibility output may resemble Windows but must preserve Linux-specific warnings and unknown values. | Never fabricate fields merely to fill a familiar template. |
| **TB-INV-097** | Exit status must distinguish parse error, unsupported, denied, execution failure, verification failure, partial success, cancelled, and success. | Do not reduce all failures to nonzero without an explanation. |
| **TB-INV-098** | Bridge Terminal history must exclude secrets and allow scoped clearing. | Sensitive commands may be marked non-persistent. |
| **TB-INV-099** | Command output must be bounded, cancellable, and safe to render. | Log floods or infinite streams cannot freeze the UI. |
| **TB-INV-100** | ANSI/control-sequence handling must prevent terminal escape abuse. | Unsafe sequences are stripped or safely interpreted. |
| **TB-INV-101** | Commands that may hang must have documented timeout/cancellation behavior. | Timeout never implies kill unless the command contract permits it. |
| **TB-INV-102** | Native shell execution must require an explicit mode chosen by the user. | Bridge Mode cannot become a convenience gateway to arbitrary shell execution. |
| **TB-INV-103** | PowerShell integration must use real `pwsh` where appropriate rather than pretending full Windows PowerShell compatibility. | Unavailable Windows-only modules/cmdlets are explained honestly. |
| **TB-INV-104** | Trier-provided PowerShell cmdlets must invoke the same typed-operation layer as the GUI and Bridge Terminal. | PowerShell cannot bypass policy. |
| **TB-INV-105** | A Windows command with no faithful Linux equivalent must remain educational-only. | No destructive approximation is allowed. |

### 3.7 Privilege, security, IPC, and trust

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-106** | The normal Trier Bridge application runs unprivileged. | If privileged features are unavailable, the application still launches and provides safe capabilities. |
| **TB-INV-107** | No generic root command, root shell, arbitrary privileged file-write, chmod-anything, or chown-anything API may exist. | A requested feature requiring such a primitive remains unimplemented until narrowed. |
| **TB-INV-108** | Privileged operations must be finite, named, versioned, schema-validated, and independently testable. | Unknown operation IDs are rejected. |
| **TB-INV-109** | Interactive authorization may be requested only from a current user-initiated action. | Background tasks cannot unexpectedly prompt for administrator credentials. |
| **TB-INV-110** | Authorization must be scoped to the exact action/target as far as the native platform allows. | Broad temporary authorization cannot silently widen the requested operation. |
| **TB-INV-111** | Privilege must not be retained merely for convenience after the bounded action. | Reauthorization occurs when the native policy requires it. |
| **TB-INV-112** | The product must not ship broad polkit rules that silently grant privileges. | Respect administrator-defined policy. |
| **TB-INV-113** | Authorization backend assumptions must be adapter-specific; not every privileged Linux API is mediated by polkit. | If the native mechanism differs, use and document that mechanism. |
| **TB-INV-114** | Frontend/UI/renderer input is untrusted even when generated by Trier Bridge. | Trusted backend validates every request. |
| **TB-INV-115** | Every IPC message must have bounded size, schema, enum/range validation, and version handling. | Malformed or oversized messages are rejected without process compromise. |
| **TB-INV-116** | Frontend-supplied executable strings are prohibited at privileged boundaries. | Only typed data crosses to privileged execution. |
| **TB-INV-117** | D-Bus names, object paths, interfaces, members, and payloads must be validated against the exact adapter contract. | Unexpected messages cannot become generic dispatch. |
| **TB-INV-118** | Deep links and URI handlers may navigate or request intent but cannot directly execute privileged actions. | Consequential requests still require normal validation/confirmation. |
| **TB-INV-119** | Drag-and-drop, clipboard, file-open, and imported configuration are untrusted inputs. | Parsing occurs with bounded resources and no automatic execution. |
| **TB-INV-120** | Path traversal and symlink escape are prohibited for Trier Bridge-owned writes and destructive operations. | Out-of-scope targets are rejected. |
| **TB-INV-121** | TOCTOU-sensitive targets are revalidated as close to mutation as practical. | Changed targets cause cancellation. |
| **TB-INV-122** | Secrets must not be stored in frontend state when avoidable. | If the secure backend is unavailable, secret-dependent features stay unavailable. |
| **TB-INV-123** | Secrets must not appear in logs, audit records, crash reports, URLs, clipboard automation, terminal history, or support bundles. | Redaction failure blocks export of the affected bundle. |
| **TB-INV-124** | Trier Bridge must not store Linux account passwords. | Authentication remains with native facilities. |
| **TB-INV-125** | TLS/certificate verification may not be disabled in production to make a network feature work. | Network feature fails closed. |
| **TB-INV-126** | No security feature may downgrade silently when a preferred mechanism fails. | Expose the failure and recovery options. |
| **TB-INV-127** | SELinux/AppArmor or other MAC denial is a policy result, not an obstacle to bypass. | Do not recommend globally disabling protection as the default fix. |
| **TB-INV-128** | Security controls must behave the same in Familiar, Bridge, and Native modes. | Presentation cannot weaken enforcement. |
| **TB-INV-129** | Audit events for privileged/destructive actions must identify operation, target, result, and verification state without sensitive payloads. | If audit is required for a critical action and cannot be recorded, follow the operation’s fail-closed policy. |
| **TB-INV-130** | Security claims require exact evidence on the supported environment. | A design rule, unit test, or one distro cannot certify all Linux environments. |

### 3.8 Processes, applications, services, and logs

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-131** | Zero resource usage means measured zero; unavailable metrics must display Unknown/Unavailable. | Missing GPU/process/network data is never converted to zero. |
| **TB-INV-132** | Process lists must respect native visibility permissions. | Do not elevate automatically to reveal other users’ data. |
| **TB-INV-133** | Process command lines and environment-derived data must be treated as potentially sensitive. | Default views minimize disclosure. |
| **TB-INV-134** | Terminate and Force terminate are separate actions with separate consequences. | Escalation from graceful to forceful termination requires explicit policy/user intent. |
| **TB-INV-135** | Managed-service processes should be identified as such when reliably known. | Offer service-level recovery instead of blindly killing a child process. |
| **TB-INV-136** | System-critical/kernel processes must receive stronger protection and may be non-actionable. | If safety classification is uncertain, require advanced confirmation or disable. |
| **TB-INV-137** | Process tree relationships are observational and can change during display. | Actions revalidate the chosen process, not its old tree position. |
| **TB-INV-138** | Service Running and Enabled are separate states. | Never infer one from the other. |
| **TB-INV-139** | Service Start, Stop, Restart, Reload, Enable, Disable, Mask, and Unmask are distinct operations. | Unsupported operations stay unavailable. |
| **TB-INV-140** | Service failure must preserve native diagnostic detail while presenting a plain-language explanation. | No automatic reset or config deletion. |
| **TB-INV-141** | A service that changes state outside Trier Bridge must be reflected without fighting the administrator. | External changes are authoritative. |
| **TB-INV-142** | Unit/service aliases must resolve to canonical identity before mutation. | Ambiguous aliases require clarification. |
| **TB-INV-143** | A restart that stops successfully but fails to start must be reported as partial failure. | Do not claim Restart succeeded. |
| **TB-INV-144** | Log content is untrusted text and never executable markup or command input. | Escape/sanitize control content. |
| **TB-INV-145** | Log access restrictions must be shown as restricted, not as “no events.” | Offer authorization only when the user explicitly requests privileged visibility. |
| **TB-INV-146** | Log queries must be bounded by time/range/count and cancellable. | Large journals cannot exhaust memory. |
| **TB-INV-147** | Log timestamps, severity, source, boot/session, and structured fields must preserve native meaning. | Windows-like categories are views, not rewritten provenance. |
| **TB-INV-148** | Links or paths found inside logs are not auto-opened or executed. | Require deliberate user action and normal validation. |

### 3.9 Networking, storage, packages, devices, and system configuration

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-149** | Network state must distinguish link, profile, IP configuration, DNS, route, connectivity check, and Internet reachability. | Unknown layers remain unknown. |
| **TB-INV-150** | Network mutations use the detected native backend and its permission model. | No qualified backend means read-only. |
| **TB-INV-151** | When the backend offers a checkpoint/rollback mechanism, risky network changes should use it where appropriate. | If rollback is unavailable, present stronger recovery guidance before committing. |
| **TB-INV-152** | A remote-session user must be warned before an action that could disconnect the management path. | If safe rollback cannot be assured, require explicit confirmation. |
| **TB-INV-153** | Network profile edits must distinguish current runtime state from persistent configuration. | Do not promise persistence without verifying it. |
| **TB-INV-154** | Existing unmanaged interfaces/configurations must not be silently adopted or rewritten. | Preserve external ownership. |
| **TB-INV-155** | DNS, proxy, route, firewall, and hostname changes are separate capabilities. | One network action cannot silently modify another. |
| **TB-INV-156** | Wi-Fi scanning, hotspot creation, and radio enable/disable must respect native permissions and privacy implications. | Denied scans remain denied. |
| **TB-INV-157** | Storage inventory must distinguish physical device, partition, filesystem, encrypted container, logical volume, RAID, mount, and network filesystem when detectable. | Do not flatten them into misleading drive letters. |
| **TB-INV-158** | Destructive storage actions may never choose a target by display order or `/dev/sdX` name alone. | Require stable identity plus fresh confirmation. |
| **TB-INV-159** | Mount and unmount are distinct from format, repair, resize, encrypt, decrypt, or partition operations. | Capabilities remain separately gated. |
| **TB-INV-160** | A busy/in-use filesystem must not be force-unmounted by default. | Explain blockers and safe next steps. |
| **TB-INV-161** | Filesystem repair must not be run automatically merely because a filesystem is dirty. | Require explicit supported workflow. |
| **TB-INV-162** | Disk health data must identify source/support and may be unavailable under USB bridges, VMs, permissions, or vendor limitations. | Unavailable is not healthy. |
| **TB-INV-163** | User data is never Trier Bridge cache. | Cleanup routines may remove only owned, unreferenced, policy-eligible data. |
| **TB-INV-164** | Recursive delete/chmod/chown must be treated as high-risk and must not cross mount or symlink boundaries unintentionally. | Partial completion is explicitly reported. |
| **TB-INV-165** | Package identity includes packaging system, repository/source, architecture, name, and version as applicable. | Same display name across systems is not the same package. |
| **TB-INV-166** | A package manager frontend may expose only operations the active backend supports. | Unsupported backend commands never appear as functional buttons. |
| **TB-INV-167** | Install/remove/update must preview dependency additions, removals, replacements, download/disk impact, and trust status where available. | If the plan changes before commit, reconfirm. |
| **TB-INV-168** | Package signatures and repository trust remain native and mandatory. | No unsigned/invalid-signature fallback. |
| **TB-INV-169** | Adding/removing a software repository is a separate security-sensitive operation from installing a package. | No silent repository addition. |
| **TB-INV-170** | A package-manager lock/contention condition is recoverable state, not a reason to kill another package manager automatically. | Wait, retry, or instruct safely. |
| **TB-INV-171** | Interrupted package operations must reconcile with the native package database before retry. | Never blindly replay. |
| **TB-INV-172** | Flatpak, Snap, AppImage, native, source-built, and containerized applications retain their own update/uninstall models. | Unified UI must not imply identical sandbox or ownership. |
| **TB-INV-173** | Device enumeration must tolerate hotplug, missing permissions, unsupported classes, virtualization, and vendor-specific gaps. | Missing fields remain Unknown. |
| **TB-INV-174** | Driver/kernel-module mutation is high-risk and cannot be treated like Windows Device Manager’s generic Update Driver button. | Early versions prefer inspection and native guidance. |
| **TB-INV-175** | USB/removable-device metadata and labels are untrusted input. | Rendering and matching must be injection-safe and identity-aware. |
| **TB-INV-176** | Power, battery, thermal, fan, GPU, SMART, and sensor metrics must carry capability/quality state. | Unsupported sensors do not fail the whole dashboard. |
| **TB-INV-177** | System configuration files not owned by Trier Bridge must not be rewritten wholesale when a structured native API exists. | If file editing is unavoidable, preserve ownership, comments where required, atomicity, backup/recovery, and exact scope. |
| **TB-INV-178** | Multiple configuration authorities for the same subsystem must not be mutated concurrently by Trier Bridge. | Choose one qualified authority or remain read-only. |

### 3.10 Persistence, recovery, interruption, and graceful failure

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-179** | Every mutable Trier Bridge setting must have a defined owner, durability class, default, migration rule, and recovery behavior. | Unknown fields are preserved or safely ignored according to schema policy. |
| **TB-INV-180** | Acknowledged user preferences must survive normal restart and upgrade. | Write failure is shown before acknowledgment. |
| **TB-INV-181** | State writes must be atomic where practical. | Partial files do not replace known-good state. |
| **TB-INV-182** | Critical writes must account for full disk, read-only filesystem, inode exhaustion, permission loss, and abrupt process death. | Retain the last known-good state or explicit recovery state. |
| **TB-INV-183** | Operation journals must distinguish planned, authorized, executing, committed, verified, failed, cancelled, partial, and unknown states as applicable. | Restart reconciliation uses these states rather than guessing. |
| **TB-INV-184** | Retry must preserve operation identity and must not duplicate a committed side effect. | Non-idempotent retries require reconciliation first. |
| **TB-INV-185** | A failure in one subsystem must not corrupt unrelated Trier Bridge state. | Contain failures behind subsystem boundaries. |
| **TB-INV-186** | A backend crash or D-Bus disconnect must invalidate pending assumptions. | Reconnect and rediscover before further mutation. |
| **TB-INV-187** | Native service restarts during Trier Bridge use must be tolerated. | Pending actions re-evaluate or fail gracefully. |
| **TB-INV-188** | If the Trier Bridge UI crashes while a privileged helper is active, the helper must remain bounded to the already-authorized operation and exit when complete. | It cannot become an orphaned general privileged service. |
| **TB-INV-189** | Power loss during an operation must not cause automatic destructive replay on boot. | Recover by inspecting actual system state. |
| **TB-INV-190** | If rollback fails, the product must stop attempting further automatic repair and present the exact degraded state. | Do not enter an endless repair loop. |
| **TB-INV-191** | Recovery instructions must be available offline for core features. | Network outage cannot remove the user’s path to understand a failure. |
| **TB-INV-192** | An error message must say whether anything changed. | Never leave the user guessing about mutation. |
| **TB-INV-193** | Partial success must enumerate what succeeded, what failed, and what remains pending. | Do not collapse partial into Success/Failure only. |
| **TB-INV-194** | Unknown final state must be a first-class result. | Require reconciliation before another conflicting action. |
| **TB-INV-195** | User cancellation must never be reported before the operation has actually reached a cancellable safe point. | Show “stopping” or “finishing current step” truthfully. |
| **TB-INV-196** | Recovery data retention must be bounded but may not expire while still required to restore from an unresolved operation. | Active recovery references are protected. |

### 3.11 Offline behavior, performance, resource efficiency, and scale

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-197** | Core local administration must remain usable with DNS failure, gateway failure, or complete Internet disconnection. | Network-only enhancements degrade independently. |
| **TB-INV-198** | Startup must not block indefinitely on network, package metadata, update checks, remote icons, or telemetry. | Use bounded background work or skip. |
| **TB-INV-199** | System monitoring must impose bounded CPU, memory, disk, and GPU overhead. | If high-frequency data becomes expensive, reduce sampling before harming the host. |
| **TB-INV-200** | Sampling rate must adapt or pause when views are hidden, system is under pressure, or the user requests reduced activity. | Do not spend significant resources monitoring a system monitor. |
| **TB-INV-201** | Process, log, package, and device lists must support large systems without unbounded in-memory expansion. | Page/virtualize/stream. |
| **TB-INV-202** | A machine with hundreds of CPU cores, thousands of processes, large journals, many mounts, or many packages must remain usable. | Scale overflow becomes a bounded/degraded presentation, not a crash. |
| **TB-INV-203** | Background indexing/caching must have explicit size and retention budgets. | When limits are reached, evict only replaceable data. |
| **TB-INV-204** | Low-memory handling must preserve user control and avoid retry storms. | Pause optional work and surface degraded state. |
| **TB-INV-205** | Low-storage handling must stop optional cache growth before critical state writes fail. | Never delete user content to recover space. |
| **TB-INV-206** | Performance optimizations may not remove verification, authorization, recovery, or truthful state distinctions. | A faster unsafe path is rejected. |

### 3.12 Accessibility, localization, privacy, and multi-user behavior

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-207** | All core operations must be reachable without a mouse and without requiring terminal use. | If an accessibility path breaks, the feature is not release-ready. |
| **TB-INV-208** | Focus, activation, and selection are distinct UI states. | Keyboard/controller navigation cannot trigger destructive actions merely by moving focus. |
| **TB-INV-209** | Screen-reader labels must communicate action, target, privilege, and consequence for consequential controls. | An icon alone is insufficient. |
| **TB-INV-210** | Large text, high contrast, reduced motion, and common accessibility settings must not hide required confirmation or recovery information. | Layouts adapt instead of clipping critical content. |
| **TB-INV-211** | Localization must not alter parsing, identifiers, command semantics, or backend matching. | Machine-facing values stay canonical. |
| **TB-INV-212** | Localized CLI output must not be parsed when a stable API/structured output exists. | If localized parsing is unavoidable, support must be explicitly qualified. |
| **TB-INV-213** | Right-to-left and non-Latin text must not corrupt paths, service names, package names, or audit identity. | Display transformations are separate from stored canonical values. |
| **TB-INV-214** | Multiple logged-in users must not see each other’s private process/environment/history data beyond native permissions. | Trier Bridge must not become an information side channel. |
| **TB-INV-215** | Per-user preferences and system-wide configuration must remain separate. | A user-scoped change cannot silently become global. |
| **TB-INV-216** | No telemetry, analytics, or crash upload is required for core use. | If introduced later, it is opt-in, data-minimized, documented, and independently disableable. |
| **TB-INV-217** | Support bundles must preview included categories and redact secrets/unrelated personal data. | If redaction confidence is insufficient, omit the sensitive category. |
| **TB-INV-218** | Clipboard use must be deliberate for sensitive/system data. | Trier Bridge never auto-copies secrets. |

### 3.13 Updates, supply chain, extensions, testing, and release

| ID | Must remain true | Graceful failure requirement |
|---|---|---|
| **TB-INV-219** | Trier Bridge updates must be origin-verified and cryptographically verified before installation. | Verification failure blocks the update without disabling the installed version. |
| **TB-INV-220** | Automatic download and automatic installation are separate choices. | Offline users remain fully functional on the installed version. |
| **TB-INV-221** | Update staging must be recoverable and must not overwrite the last working build before verification. | Failed update returns to the prior usable state. |
| **TB-INV-222** | Rollback/downgrade must respect state-schema compatibility. | If unsafe, explain and refuse rather than corrupt data. |
| **TB-INV-223** | Release artifacts must have reproducible identity: version, commit/source revision, architecture, package type, and hash. | Unknown artifact provenance is not release-ready. |
| **TB-INV-224** | Dependencies must be locked/reviewed according to the build system and an SBOM generated for release candidates where practical. | Unresolved high-risk reachable vulnerabilities remain blockers or explicit owner-reviewed exceptions. |
| **TB-INV-225** | Third-party licenses/notices must be preserved; copied UI assets or Windows marks/icons require explicit rights review. | Familiarity does not authorize cloning protected assets. |
| **TB-INV-226** | A plugin/extension system must not exist until capability, sandbox, provenance, update, and privilege boundaries are designed. | Customizability cannot inherit privileged authority. |
| **TB-INV-227** | If extensions are later supported, they receive no secrets or privileged operations by default. | Capabilities are explicit and revocable. |
| **TB-INV-228** | Every invariant has a corresponding verification obligation; by default `TB-T###` maps to `TB-INV-###`. | An invariant is not PASS until its applicable test/evidence exists. |
| **TB-INV-229** | Tests must include success, denial, malformed input, stale state, cancellation, interruption, and recovery where applicable. | Happy-path-only evidence is incomplete. |
| **TB-INV-230** | Destructive/fault-injection tests run only on disposable VMs, containers, loopback images, synthetic devices, or explicitly authorized test hardware. | Never test failure handling by risking the user’s real machine. |
| **TB-INV-231** | Distribution support claims require an explicit tested matrix of distro version, desktop/session, backend versions, architecture, and package form as applicable. | One Ubuntu success is not “Linux supported.” |
| **TB-INV-232** | Known unsupported or unverified combinations must be documented in-product or in release documentation. | Do not let marketing widen the compatibility matrix. |
| **TB-INV-233** | Release is blocked by unresolved data-loss, privilege-escape, arbitrary-command, update-trust, or unrecoverable-system-mutation defects. | Severity cannot be averaged away by other passing metrics. |

---

## 4. Invariant family index

| Family | IDs |
|---|---|
| Product truth, scope, and user trust | TB-INV-001–TB-INV-015 |
| Installation, distribution, desktop, and environment boundaries | TB-INV-016–TB-INV-033 |
| Capability discovery and adapter contracts | TB-INV-034–TB-INV-048 |
| Stable identity, state, concurrency, and lifecycle | TB-INV-049–TB-INV-063 |
| Familiar UX, mental-model translation, and learning | TB-INV-064–TB-INV-081 |
| Bridge Terminal and Windows-command translation | TB-INV-082–TB-INV-105 |
| Privilege, security, IPC, and trust | TB-INV-106–TB-INV-130 |
| Processes, applications, services, and logs | TB-INV-131–TB-INV-148 |
| Networking, storage, packages, devices, and system configuration | TB-INV-149–TB-INV-178 |
| Persistence, recovery, interruption, and graceful failure | TB-INV-179–TB-INV-196 |
| Offline behavior, performance, resource efficiency, and scale | TB-INV-197–TB-INV-206 |
| Accessibility, localization, privacy, and multi-user behavior | TB-INV-207–TB-INV-218 |
| Updates, supply chain, extensions, testing, and release | TB-INV-219–TB-INV-233 |

**Total baseline invariants: 233.**

---

## 5. Required fault-injection and hostile-environment catalog

The following scenarios are not automatically separate invariants; they are mandatory **things to look at** when freezing test plans. Apply them to every affected invariant instead of testing only successful use.

### Process and lifecycle
- kill Trier Bridge during read, preview, authorization, mutation, verification, and recovery
- kill/restart the privileged helper during an authorized operation
- restart systemd/NetworkManager/PackageKit/udisks-equivalent backend during use
- log out, switch user, lock session, suspend, hibernate, resume, and reboot
- run two Trier Bridge instances and issue conflicting actions
- change the target outside Trier Bridge between preview and commit
- PID reuse after process exit

### Privilege and policy
- no polkit agent available
- authorization denied, cancelled, timed out, or expired
- administrator policy changes while Trier Bridge is open
- SELinux/AppArmor denial
- user removed from an administrative group mid-session
- privileged helper version mismatch

### Filesystem and storage
- disk full
- inode exhaustion
- read-only remount
- permission revoked
- symlink loop
- symlink escape
- mount disappears
- USB drive unplugged/reinserted with reused device path
- NFS/FUSE/network mount stalls
- filenames with newlines, control characters, emoji, RTL text, huge length, and Unicode confusables
- filesystem becomes busy between preview and operation
- interrupted atomic write

### Networking
- cable unplugged / Wi-Fi loss
- DNS failure with local network still working
- gateway loss
- NetworkManager restart
- interface rename/hotplug
- DHCP lease change
- route changes outside Trier Bridge
- remote administration path would be disconnected by the proposed change
- checkpoint creation succeeds but rollback fails
- connection profile replaced between preview and commit

### Packages and software
- package-manager lock held by another process
- repository unreachable
- repository metadata changes between preview and install
- signature invalid/expired/untrusted
- dependency plan expands unexpectedly
- dependency conflict
- insufficient disk during install
- native package transaction interrupted
- same app name present as native + Flatpak + Snap + AppImage
- package database reports partial/broken state

### Logs and monitoring
- journal unavailable or permission denied
- enormous journal
- log flood
- malicious ANSI/control sequences
- HTML/script-like log text
- malformed timestamp
- GPU/sensor metric unsupported
- metric source disappears while displayed
- hundreds of CPU cores
- thousands of processes
- very long uptime/counters

### Command translation
- unsupported command
- unsupported flag
- partial command
- nested quotes
- shell metacharacters
- pipes/redirection/chaining
- environment variable syntax from CMD, PowerShell, and POSIX shells
- paths containing spaces, quotes, Unicode, `..`, symlinks, UNC-like text, drive-letter-like text
- extremely long input
- command whose Windows meaning has no faithful Linux equivalent
- command whose target changes after preview
- output never terminates

### Desktop and packaging environment
- GNOME, KDE Plasma, Cinnamon, XFCE and unknown desktop
- Wayland and X11
- local graphical session, remote desktop, SSH-forwarded GUI, headless, nested compositor
- native package, Flatpak, Snap, AppImage
- sandbox denies host access
- theme/high contrast/large text changes while running
- default terminal/file manager/browser changes

### Resource pressure
- low RAM / OOM pressure
- CPU saturation
- slow storage
- huge package database
- many network adapters
- many disks/mounts
- GPU driver missing or unsupported
- battery critical / suspend during mutation

### Localization and accessibility
- non-English system locale
- locale changes while running
- non-Latin service/package/file names
- RTL display
- IME composition
- screen reader
- keyboard-only
- large text
- reduced motion
- high contrast

---

## 6. Graceful-failure hierarchy

When an invariant cannot be satisfied at runtime, Trier Bridge should apply this order unless a more specific invariant overrides it:

1. **Do not damage user data or system state.**
2. **Do not widen privilege or scope.**
3. **Stop before an uncertain destructive boundary.**
4. **Preserve the last known-good state and recovery evidence.**
5. **Return control to the user.**
6. **State whether anything changed.**
7. **Classify the result accurately:** unsupported / unknown / denied / cancelled / failed / partial / unverified.
8. **Offer the safest recovery action.**
9. **Expose technical detail progressively.**
10. **Never hide the failure behind a familiar Windows-looking success message.**

---

## 7. Release interpretation

A release may claim a capability only for the exact environments with evidence. Trier Bridge should prefer statements such as:

> Service inspection and bounded service control verified on Ubuntu 26.04 / GNOME / systemd under native package build.

over:

> Works on Linux.

The eventual supported matrix should track, as applicable:

- distribution + version
- architecture
- desktop environment
- Wayland/X11/headless session
- init/service manager
- network backend
- package backends
- storage backend
- authorization mechanism
- Trier Bridge package format
- feature/operation
- evidence level

---

## 8. Current evidence state

**All invariants in this revision are DESIGN requirements only.**

No invariant is implemented, tested, qualified, or release-proven merely because it appears in this file.

---

## Final rule

> **If Trier Bridge cannot prove that it knows what it is about to do, to exactly what target, with the right authority, and with a defined recovery path, it does not do it.**

> **Failing gracefully is not hiding an error. It is containing the failure, preserving the machine, telling the truth, and giving the user a safe way forward.**