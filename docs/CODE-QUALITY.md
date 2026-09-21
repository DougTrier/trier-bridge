# CODE-QUALITY.md
# Trier Bridge Code Quality Standard and Scoring

**Project:** Trier Bridge  
**Status:** Design baseline — no quality score is currently measured  
**Revision:** 0.1  
**Date:** September 20, 2026  
**Owner:** Doug Trier  

This standard applies to every existing and future production change regardless of author, editor, generator, tool, or development method.

Correctness, durability, security, compatibility, recoverability, accessibility, and the full Trier Bridge invariant set cannot be traded for aesthetics, brevity, performance, code size, or a quality score.

No bulk refactoring, formatter migration, architecture rewrite, suppression baseline, or automated "cleanup" is authorized by a metric or analyzer finding alone.

> **The score measures evidence. It does not replace engineering judgment.**

---

# 1. CQS — Code Quality Score

CQS is a **0–100 engineering quality score** only when all eight categories have current, scope-matched evidence.

Each category contains five equally weighted criteria.

Each criterion is scored:

- `0` — absent, contradicted, or known unacceptable
- `0.5` — documented partial coverage, incomplete evidence, or bounded open findings
- `1` — complete current evidence for the assessed scope

Category score:

```text
category weight × (sum of five criterion values / 5)
```

Every awarded criterion must link exact candidate evidence and reviewer rationale.

Unmeasured criteria are:

> **NOT MEASURED**

They are not zero.

They are not assumed to pass.

A partially assessed category remains **NOT MEASURED** as a whole, with the observed criteria reported separately.

Do not normalize a partial subtotal into a 100-point score.

Report:

- assessed weight
- unassessed weight
- observed findings
- blockers
- exact evidence

Independent review remains required wherever Trier Bridge security, privilege, release, or distribution contracts require it.

---

## 1.1 CQS rubric

| Category | Weight | Five criteria requiring evidence |
| --- | ---: | --- |
| **Architecture / boundaries** | **20** | module purposes and allowed dependency direction; acyclic dependency graph; single authoritative ownership for mutable state; explicit domain/interfaces/adapters; cohesive responsibilities without unreviewed god objects or generic privileged managers |
| **Readability / naming** | **15** | Trier Bridge domain vocabulary; accurate/descriptive names; understandable control flow; consistent capability/state/result terms; coherent function/module scope |
| **Complexity** | **15** | cyclomatic distribution/outlier disposition; cognitive distribution/outlier disposition; nesting review; function/class/module/parameter scope; duplicated decision/protocol review |
| **Documentation / rationale** | **15** | API ownership/errors/side effects; privilege/security assumptions; persistence/recovery; concurrency/lifecycle; non-obvious compatibility decisions with accurate invariant references |
| **Testing / regression** | **15** | mapped invariant/boundary behavior; meaningful unit tests; integration/negative tests; failure/lifecycle/recovery cases; candidate-specific affected regression evidence |
| **Static-analysis health** | **10** | compiler/build diagnostics; language-specific lint/static analysis; security/safety findings; justified suppression inventory; resource/nullability/unsafe/boundary warning disposition |
| **Dependency hygiene** | **5** | necessity/alternatives; pins/locks/checksums; license/provenance; maintenance/security/platform compatibility; transitive/package/distribution cost |
| **Dead code / duplication** | **5** | unused production path review; unreachable/obsolete branch review; exact duplicate review; semantic duplicate/state-authority review; legitimate standalone foundations distinguished from abandoned code |

---

## 1.2 Score interpretation

| Score | Interpretation |
| --- | --- |
| **90–100** | May qualify as release-quality if all hard gates are also clear |
| **80–89** | Active development; bounded remediation remains |
| **Below 80** | Requires remediation before release qualification |
| **NOT MEASURED** | Insufficient complete evidence to issue a score |

These classifications never waive hard gates.

No initial score may be fabricated from:

- successful compilation
- low warning counts
- passing unit tests
- a clean UI
- a successful demo
- a single supported distribution
- a successful installer
- a small codebase

---

# 2. Hard gates and review blockers

The following block release regardless of CQS average:

- invariant violations
- privilege-boundary violations
- arbitrary root execution
- shell injection paths
- path traversal or symlink escape
- security-critical findings
- unresolved data-loss paths
- unrecoverable system mutation
- silently ignored failures
- unknown state reported as success
- unsupported capability reported as supported
- circular dependencies
- duplicated mutable-state authority
- stale-target mutation risks
- dangerous undocumented concurrency
- cancellation loss across destructive boundaries
- hidden weakened fallbacks
- unvalidated configuration changes
- package/update trust bypass
- unexplained suppressions
- unjustified broad exception catches
- behavior-affecting dead code
- unreviewed high-risk dependencies
- unsafe distro/backend assumptions
- incomplete rollback for an operation that claims rollback
- release claims broader than actual compatibility evidence

No score or exception may waive:

- `SECURITY.md`
- `INVARIANTS.md`
- Apache-2.0 licensing obligations
- owner scope decisions
- required release/security review

Other bounded exceptions require:

- named reviewer
- exact finding
- exact scope
- rationale
- risk
- supporting tests
- expiry or review trigger

No accepted exception is created merely by:

- adding a suppression
- adding a baseline file
- disabling a warning
- excluding a path
- lowering a threshold

---

# 3. Quality principles

## 3.1 Domain-specific ownership

Prefer domain-specific modules over generic buckets such as:

- `Utils`
- `Helpers`
- `Managers`
- `Common`
- `Misc`
- `SystemStuff`

A module record should state:

- what it owns
- what it may depend on
- what may depend on it
- what it exposes
- what it must not expose
- its security/privilege boundary
- its failure behavior
- its tests

---

## 3.2 Document why

Comments and API documentation should explain:

- **WHY**
- **RECOVERY**
- **SECURITY**
- **OWNERSHIP**
- **CONCURRENCY**
- **COMPATIBILITY**
- **INVARIANT constraints**

Use **PERFORMANCE** only for measured or explicitly hypothesized tradeoffs.

Do not mechanically fill files with comments.

Do not add speculative invariant references.

---

## 3.3 Preserve distinct states

Do not collapse distinct system states into booleans.

Examples that must remain distinct where applicable:

- Supported
- Unsupported
- Unknown
- Degraded
- PermissionRequired
- Denied
- Pending
- Executing
- Committed
- Verified
- Failed
- Partial
- Cancelled
- OutcomeUnknown
- RecoveryRequired
- Stale
- Offline
- Unavailable

Avoid:

```text
success = true/false
```

when reality contains more states.

---

## 3.4 No catch-all success

Prohibited patterns include:

- catch exception → return success
- missing backend → return empty
- unavailable metric → return zero
- unknown capability → return false
- timeout → retry forever
- cancelled request → continue silently
- verification failure → assume mutation succeeded
- failed secure route → execute through weaker route

---

## 3.5 Metrics trigger review, not automatic redesign

Complexity and size metrics identify review work.

They do not prove a cohesive protocol should be split.

A privileged transaction, rollback protocol, package plan, recovery state machine, or parser may legitimately require more logic than a simple UI function.

The correct response to an outlier is:

1. understand responsibility
2. identify ownership boundaries
3. verify failure semantics
4. inspect tests
5. decide whether decomposition preserves behavior
6. change only when the result is safer and clearer

---

# 4. Tool selection and review

Trier Bridge has not yet frozen its implementation stack.

Therefore this document does **not** pretend that a specific compiler, linter, language version, framework, package manager, or static analyzer is already authoritative.

Tool selection occurs only after the implementation stack is chosen.

The selected toolchain must satisfy these rules.

---

## 4.1 General tool rules

Quality tooling should be:

- reproducible
- version-pinned
- locally runnable
- non-destructive by default
- usable without uploading private source
- deterministic where practical
- documented
- capable of preserving findings rather than rewriting them away

Do not introduce overlapping tools merely to increase the number of checks.

Do not enable auto-correction across the repository until its behavior and diff scope have been reviewed.

---

## 4.2 Required analysis coverage

The final toolchain must provide appropriate evidence for the languages and package types actually used.

Potential coverage includes:

### Rust, if selected

- compiler warnings
- `cargo clippy`
- formatting verification
- unsafe-code review
- dependency audit
- license/SBOM inventory
- panic/error-boundary review

### TypeScript / JavaScript, if selected

- TypeScript compiler
- ESLint or equivalent
- dependency audit
- unsafe DOM/rendering review
- IPC boundary review
- bundle/dependency-size evidence

### Python, if selected

- static/lint checks
- type checking where useful
- dependency locking
- subprocess/shell-boundary review
- filesystem/error handling

### Shell, if selected

- shellcheck or equivalent
- explicit shell selection
- quoting/injection review
- error propagation
- platform assumptions

### PowerShell, if selected

- PSScriptAnalyzer or equivalent
- strict error handling
- command/argument boundary review
- platform-specific cmdlet review

### Native packaging

- package metadata validation
- dependency declaration review
- install/uninstall script review
- privilege behavior
- file ownership
- rollback behavior
- license/NOTICE installation

No tool listed above is mandatory merely because it appears here.

Only tools matching the actual stack should be introduced.

---

## 4.3 Security tooling does not replace architecture review

Static analyzers may find:

- injection risks
- unchecked results
- unsafe functions
- broad catches
- dead code
- dependency vulnerabilities

They do not prove:

- privilege correctness
- rollback correctness
- stable-target identity
- distro compatibility
- authorization scope
- package-plan correctness
- recovery semantics
- graceful failure
- UX truthfulness

Those require design and behavioral evidence.

---

# 5. Thresholds and measurement limits

Exact numeric thresholds should be frozen only after the selected analyzers and languages are known.

Until then, use the following as review signals rather than design laws.

Potential review triggers:

- high cyclomatic complexity
- high cognitive complexity
- deep nesting
- very long functions
- very large classes/modules
- large parameter lists
- repeated branching on the same domain decision
- broad exception/error catches
- repeated stringly typed operation names
- repeated capability checks
- repeated privilege checks
- repeated distro/backend detection
- repeated error-to-user-message translation
- repeated shell/process spawning logic

A threshold finding requires:

> **review**

not:

> **automatic split**

---

## 5.1 Physical size

Record physical file/module size separately from semantic complexity.

Large files are navigation and ownership signals.

They are not automatically defects.

A 500-line coherent adapter may be better than six files with duplicated state assumptions.

---

## 5.2 Duplication

Text duplication is not always semantic duplication.

Semantic duplication is more dangerous.

Examples:

- two modules independently deciding whether a service can restart
- two package paths calculating dependency safety differently
- two places translating `taskkill`
- multiple distro detectors
- multiple privilege policies
- multiple meanings of Supported
- multiple recovery authorities

Prefer one canonical domain decision.

---

# 6. Candidate quality report process

A future `CODE-QUALITY-REPORT.md` should record:

- candidate commit/revision
- dirty-source fingerprint if applicable
- timestamp
- selected tool versions
- tool/config hashes
- assessed source scope
- CQS criteria
- assessed/unassessed weight
- compiler/build results
- lint/static-analysis results
- security-analysis results
- complexity outliers
- file/module/function outliers
- documentation gaps
- suppressions
- broad catches
- dependency/license/NOTICE coverage
- source-header coverage
- invariant tests
- failure tests
- integration tests
- distro/backend matrix evidence
- exceptions
- blockers
- risk-ranked remediation tasks

Generated machine reports may remain ignored artifacts.

The reviewed summary and deterministic commands should be tracked.

---

## 6.1 Freeze before measurement

Freeze the source candidate before collecting release-quality evidence.

Later source changes require an evidence-impact assessment.

Header-only, comment-only, or formatting-only changes may preserve behavioral evidence when verified as non-semantic.

Implementation or behavioral changes require affected checks to rerun.

Release qualification is always candidate-specific.

---

# 7. Remediation priority

Prioritize findings in this order:

1. data loss / destructive mutation
2. privilege escalation / security
3. target identity / stale-state risk
4. recovery / interruption
5. ownership / duplicated authority
6. concurrency / lifecycle
7. silent failure / false success
8. compatibility / distro/backend assumptions
9. architecture / dependency direction
10. complexity
11. documentation
12. local readability/style

Every remediation task should record:

- stable task ID
- affected files/modules
- exact `TB-INV-###` IDs
- invariant delta
- Must remain true
- baseline evidence
- bounded change
- tests
- post-change evidence

No metric-triggered speculative architectural cleanup.

---

# 8. Existing and future code — controlled convergence

This standard applies to all first-party source, including:

- production code
- tests
- packaging
- build logic
- migration logic
- installer/uninstaller logic
- privileged helpers
- command translation
- adapters
- scripts
- verification tools
- documentation generators

Audit areas include:

- headers/provenance
- naming
- modules
- ownership
- documentation
- invariant rationale
- recovery rationale
- security rationale
- complexity
- duplication
- dead code
- suppressions
- state ownership
- error handling
- dependency boundaries
- shell/process execution
- platform assumptions

Analyzer coverage will always be narrower than this full audit.

Unreviewed languages or areas remain open.

Age alone is not evidence of a defect.

---

## 8.1 Touch-it rule

Substantially modifying an area for feature work requires bringing the **modified area** into the current standard.

If doing so would materially expand risk or scope:

- record the exact deferred area
- explain why
- name an owner
- create or reference a follow-up task

Do not refactor unrelated areas opportunistically.

Existing violations are not automatically grandfathered.

---

# 9. Trier Bridge architectural vocabulary

The following vocabulary should remain stable unless explicitly revised.

| Boundary / pattern | Preferred form and reason |
| --- | --- |
| **Domain modules** | Name modules after responsibilities such as process, service, journal, network, storage, package, device, command bridge, capability, privilege, recovery; avoid generic Managers |
| **Presentation boundary** | UI collects intent and displays structured state; it is never the authority for system security or mutation |
| **Typed operation boundary** | Windows-style actions and commands normalize into typed Trier Bridge operations before execution |
| **Platform adapters** | Native Linux APIs, D-Bus services, package managers, desktops, and distro-specific behavior stay behind bounded capability adapters |
| **Privilege boundary** | Normal application remains unprivileged; privileged helper APIs are finite, typed, and operation-scoped |
| **State authority** | One owner per mutable domain state; UI mirrors state rather than independently deciding system truth |
| **Capability state** | Supported / Unsupported / Unknown / Degraded / Error remain distinct |
| **Operation state** | Planned / Authorized / Executing / Committed / Verified / Partial / Failed / Cancelled / OutcomeUnknown / RecoveryRequired remain distinct where applicable |
| **Identity** | Mutation uses stable target identity plus revalidation, not presentation labels, list positions, PIDs/device names alone |
| **Errors** | PermissionDenied / Unsupported / Unknown / Busy / Stale / Partial / VerificationFailed / RecoveryRequired remain semantically distinct |
| **Recovery** | Inspect actual Linux state before retry; no automatic destructive replay after uncertain outcomes |
| **Concurrency** | Accepted operations have explicit ownership, cancellation boundaries, idempotency, and stale-state fences |
| **Documentation** | API documentation describes ownership, side effects, privilege, errors, recovery, compatibility, and invariant constraints |
| **Logging** | Bounded, local, redacted diagnostics; no secrets and no false success claims |
| **Tests** | Behavior and invariant boundary tests, negative/fault tests, synthetic fixtures, exact environment evidence |
| **Naming** | Use Linux/Trier Bridge domain terms accurately; Windows terms belong primarily to presentation/translation surfaces |
| **Compatibility** | Claims bind to exact distro/backend/session/package evidence rather than generic “Linux” |
| **Failure** | Graceful failure means containment + truthful state + safe recovery, not swallowing an exception |

---

# 10. Preferred dependency direction

The exact module names depend on the selected implementation stack, but the conceptual direction should resemble:

```text
Presentation
    ↓
Intent / Command Parsing
    ↓
Domain Operations
    ↓
Capability / Policy
    ↓
Platform Adapter Interfaces
    ↓
Linux-specific Implementations
```

Privileged execution is a side boundary reached through explicitly authorized typed operations.

Avoid:

```text
UI
 ↓
shell command strings
 ↓
sudo/root
```

Avoid domain modules importing desktop-, distro-, package-manager-, or shell-specific implementation details without an explicit adapter boundary.

---

# 11. Error-handling standard

Errors must retain meaning.

Do not write catch-all behavior such as:

```text
try operation
catch everything
return false
```

or:

```text
catch everything
log
return success
```

Boundary catches are acceptable only when they:

- prevent an error from crossing a defined process/API boundary
- convert to a fixed structured result
- preserve OutcomeUnknown where commit may have occurred
- do not leak secrets
- have explicit rationale
- have negative tests

---

## 11.1 Broad catches

A broad catch is a mandatory review signal.

The reviewer must answer:

- What failures can arrive here?
- Can a commit have happened already?
- Is cancellation handled separately?
- Can identity have changed?
- Can this leak sensitive information?
- Is retry safe?
- What does the user see?
- What evidence distinguishes Failed from OutcomeUnknown?

Do not suppress the finding before answering those questions.

---

# 12. Command execution quality

Command/process spawning is a protected area.

Preferred order:

1. native API / library
2. stable D-Bus/system service API
3. structured command invocation with fixed executable + argument array
4. shell execution only when the subsystem genuinely requires shell semantics and its risk is explicitly reviewed

Never construct shell text from untrusted user input.

Do not use shell execution merely because it is shorter code.

---

# 13. Capability and adapter quality

Every adapter should document:

- subsystem
- supported environments
- discovery method
- read capabilities
- mutation capabilities
- required privilege
- structured errors
- timeout/cancellation
- stale-state behavior
- recovery
- tests

Adapter implementations must not silently claim support for unknown versions.

A new distro/backend is not "supported" because the adapter compiled.

---

# 14. Privileged helper quality

A privileged helper must have:

- finite operation vocabulary
- versioned request schema
- bounded request size
- explicit target identity
- caller/auth context
- no arbitrary shell
- no arbitrary privileged path write
- structured results
- postcondition verification where possible
- auditability
- termination/lifecycle rules
- replay/stale-request protection as applicable
- fault-injection tests

Privileged-helper code is always high-risk review.

---

# 15. Persistence and recovery quality

Trier Bridge-owned persistent data must define:

- schema/version
- writer authority
- atomicity
- migration
- backup/recovery
- retention
- failure handling
- cross-version behavior

No acknowledged setting change may disappear silently.

No uncertain system mutation may be converted into a clean local state merely to simplify the database.

---

# 16. Testing quality

Test count alone is not quality.

Tests should cover behavior boundaries.

For affected protected areas, include as applicable:

- happy path
- invalid input
- unsupported environment
- authorization denial
- missing backend
- stale identity
- concurrent action
- cancellation
- process kill
- backend restart
- disk full
- network loss
- malformed output
- hostile text
- rollback
- rollback failure
- partial success
- unknown final state
- restart reconciliation

Use disposable environments for destructive fault injection.

Never use a contributor's real machine as the test fixture for data-loss or system-corruption scenarios.

---

# 17. Test evidence vocabulary

Use explicit evidence states:

- `PASS`
- `FAIL`
- `NOT_RUN`
- `BLOCKED`
- `NOT_APPLICABLE`
- `UNSUPPORTED`
- `UNKNOWN`
- `PARTIAL`

Do not use:

> "Looks good"

as test evidence.

---

# 18. Compatibility evidence

Compatibility claims require environment identity.

Record, as applicable:

- distro
- distro version
- architecture
- desktop environment
- display/session type
- init/service manager
- network backend
- package backend
- storage backend
- authorization mechanism
- Trier Bridge package type
- feature
- adapter version
- test result

One successful Ubuntu run does not prove:

> Linux support

---

# 19. Documentation quality

Public APIs and protected internal boundaries should document:

- owner
- purpose
- inputs
- output/result states
- side effects
- required privilege
- cancellation
- concurrency
- stale-state behavior
- recovery
- compatibility assumptions
- relevant invariants

Local comments should explain non-obvious decisions.

Avoid narrating trivial syntax.

---

# 20. Logging quality

Logs must be:

- bounded
- redacted
- actionable
- structured where useful
- clear about uncertainty

Never log:

- passwords
- tokens
- private keys
- secret environment values
- sensitive authorization material
- full private home-directory content
- unrestricted process environments

"Operation dispatched" must not be logged as "operation succeeded."

---

# 21. Dependency quality

Every production dependency needs a reason.

Record:

- purpose
- alternatives considered where material
- version/pin
- update policy
- license
- provenance
- security/maintenance status
- transitive cost
- package/distribution impact
- platform assumptions

Prefer using stable native Linux interfaces over adding dependencies that merely wrap one trivial operation.

Do not add a framework to avoid writing a small explicit adapter.

---

# 22. Dead code quality

Do not confuse these categories:

### Dead code

No supported or planned path reaches it.

### Standalone foundation

Implemented intentionally before its consumer.

### Feature-gated code

Reachable only under a documented capability/build path.

### Recovery code

Rare by design but required for failure handling.

### Obsolete code

Superseded by a new authority or architecture.

Removal requires understanding which category applies.

Do not delete recovery or compatibility behavior merely because normal-path coverage is low.

---

# 23. Duplication quality

Review both:

### Exact duplication

Nearly identical code.

### Semantic duplication

Different code answering the same authority question.

Semantic duplication is often more dangerous.

High-risk duplicated decisions include:

- whether privilege is required
- whether a capability is supported
- how service state maps
- how a Windows command translates
- how paths normalize
- how distro/backend detection works
- whether a package action is safe
- how partial success maps to user state
- how rollback/retry works

Prefer one authority.

---

# 24. Formatting and style

Use formatter/linter conventions appropriate to each selected language.

Formatting exists to:

- reduce noise
- improve consistency
- simplify review

Formatting does not justify repository-wide churn during unrelated feature work.

Large mechanical formatting migrations should be isolated.

---

# 25. Source-header and provenance quality

Qualifying first-party source must follow [LICENSING.md](LICENSING.md).

The source-quality inventory must not blindly rewrite:

- third-party code
- generated files
- vendored code
- binary files
- lockfiles
- licenses/notices
- unsupported formats

Header compliance is a release-quality criterion.

Header compliance is not behavioral quality.

---

# 26. Local-only/private material boundary

If the repository later defines a private/local-only root, it must be treated as outside normal:

- quality scanning
- header insertion
- formatting
- refactoring
- publication
- recursive analysis

Only exact evidence files required by an authorized task should be inspected.

Private paths accidentally tracked by Git are an error.

Path metadata should be checked before reading private content where practical.

---

# 27. Quality automation

Quality automation may:

- enumerate changed files
- verify headers
- verify provenance metadata
- run selected analyzers
- collect metrics
- map affected invariants
- suggest affected tests
- detect protected areas
- generate reports

Quality automation may not:

- approve architecture
- approve release
- waive invariants
- add suppressions automatically
- rewrite complex code because a metric is high
- run destructive tests on the host
- broaden scope
- infer support for an untested environment

---

# 28. Code review questions

Every meaningful review should ask:

### Ownership
- Who owns this state?
- Is there another writer?
- Is this decision duplicated?

### Security
- Does this cross a privilege or trust boundary?
- Can input reach a shell?
- Can the target change?
- Can scope expand?

### Failure
- What happens if the dependency disappears?
- What happens after partial commit?
- Can outcome be unknown?
- Can the retry duplicate the action?

### Compatibility
- What Linux assumptions exist?
- Which distro/backend/session has evidence?
- What happens when the assumption is false?

### Recovery
- Is previous state recoverable?
- What evidence survives a crash?
- Can the user tell what changed?

### Quality
- Is the code understandable?
- Is complexity cohesive or accidental?
- Are tests proving the right boundary?
- Is documentation explaining the non-obvious decisions?

---

# 29. CQS release requirements

Before a release may receive a numeric CQS:

- all eight categories are measured
- evidence matches the exact candidate
- all suppressions are inventoried
- complexity outliers are dispositioned
- privileged boundaries are reviewed
- compatibility scope is explicit
- dependency/license evidence is current
- affected invariant tests are current
- release hard gates are clear or explicitly blocking

A CQS above 90 does not make a blocked candidate releasable.

A CQS below 90 does not automatically mean the architecture is wrong.

The purpose is controlled convergence and transparent evidence.

---

# 30. Current Trier Bridge quality status

Trier Bridge is currently in the design/documentation stage.

Therefore:

- no implementation stack is frozen
- no production source baseline exists
- no static-analysis baseline exists
- no complexity baseline exists
- no dependency baseline exists
- no release candidate exists
- no numeric CQS is valid

Current result:

> **CQS: NOT MEASURED**

This is the only truthful score until implementation produces scope-matched evidence.

---

# 31. Future implementation freeze requirements

Before the first substantial implementation phase, freeze:

- selected languages
- runtime/framework
- module boundaries
- package/build systems
- compiler versions
- formatter/linter/static-analysis tools
- dependency lock strategy
- source-header verification
- test runners
- quality-report commands
- approved ignored/private paths
- CI/local verification boundaries

Only then should exact numeric analyzer thresholds and tool versions be added to this document.

---

# 32. Final standard

Trier Bridge code quality is not defined by whether code is clever, short, fashionable, generated, manually written, or highly abstract.

It is defined by whether the system is:

- understandable
- bounded
- correct
- secure
- recoverable
- testable
- maintainable
- honest about uncertainty
- compatible only where evidence exists

> **No half-working abstraction is better than an explicit unsupported state.**

> **No shorter implementation is better than a recoverable one.**

> **No quality score is more important than preserving the machine and telling the truth.**
