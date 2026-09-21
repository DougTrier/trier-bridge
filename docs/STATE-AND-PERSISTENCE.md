# Trier Bridge State Model and Persistence

**Status:** Logical design only. Storage engine not selected.

## 1. Principle

Do not collapse Linux reality into booleans.

Trier Bridge persists only what it owns. Linux system state remains authoritative.

## 2. Capability state

```text
Unknown
Supported
Unsupported
Degraded
Error
```

`Unknown` is not `Unsupported`. `Degraded` is not `Supported`. `Error` is not absence.

## 3. Authorization state

```text
NotRequired
Required
Requested
Granted
Denied
Cancelled
Expired
Unavailable
```

## 4. Operation lifecycle

```text
Draft
→ Previewed
→ Authorized
→ Executing
→ Committed
→ Verifying
→ Verified
```

Alternate terminal states:

```text
Unsupported
Denied
Cancelled
Failed
Partial
OutcomeUnknown
RecoveryRequired
```

A UI may use simpler words but must preserve these semantics internally.

## 5. Observation freshness

Observed system state carries:

- stable target identity
- source/backend
- timestamp
- generation/revision where available
- freshness
- capability quality

Mutation revalidates stale or identity-sensitive observations.

## 6. Desired versus actual

For settings Trier Bridge owns:

```text
Desired
Pending
Durable
Effective
Failed
```

Acknowledged changes may not disappear silently.

For Linux system state Trier Bridge does not own, Linux actual state is authoritative. Trier Bridge may remember user intent but must not fight external changes automatically.

## 7. Recovery state

```text
NoRecoveryNeeded
RecoveryAvailable
RecoveryInProgress
RecoveryFailed
NeedsReview
```

Uncertain post-crash state requires inspection before retry.

## 8. UI rule

The interface may simplify wording, but it must never collapse:

- Unknown into Off
- Denied into Unsupported
- Partial into Success
- Committed into Verified
- Missing permission into Empty

## 9. What Trier Bridge may persist

Trier Bridge-owned durable data may include:

- user experience mode
- UI preferences
- pinned/favorite routes
- familiar-name preferences
- search/help history subject to privacy policy
- optional Bridge Terminal history
- adapter capability cache with freshness metadata
- recovery journals for Trier Bridge operations
- audit records
- per-user settings
- optional system-wide Trier Bridge policy where explicitly administered

Do **not** duplicate as authoritative local truth:

- service running state
- package installed state
- network configuration
- mount state
- process existence
- device presence

These are re-observed from Linux.

## 10. Logical stores

| Store | Contents |
|---|---|
| Preferences | Per-user experience and UI choices. |
| Capability cache | Replaceable observations with backend, version, environment identity, freshness, qualification state. |
| Operation journal | Consequential operations: operation ID, target identity, preview, authorization state, execution state, verification, recovery. |
| Audit | Security-relevant action summary without secrets. |
| Help/search index | Replaceable local index for familiar Windows terms, Linux terms, and Manual routes. |

Logical entities (schema and indexes wait for stack freeze):

- `UserPreference`
- `EnvironmentProfile`
- `CapabilityObservation`
- `AdapterQualification`
- `OperationJournal`
- `OperationTarget`
- `VerificationResult`
- `RecoveryRecord`
- `AuditEvent`
- `SearchSynonym`
- `HelpRoute`

## 11. Storage requirements

- atomic updates
- versioned schema
- bounded growth
- no secrets unless a separate reviewed secret store is selected
- crash recovery
- upgrade migration; every migration reversible or recoverable
- corruption detection; corruption cannot cause destructive system reconciliation
- per-user versus system-wide separation
- replaceable caches marked replaceable
- recovery references protected until resolved
- no assumption that one database engine is already selected

## 12. Failure handling

Handle:

- disk full
- read-only filesystem
- permission loss
- crash
- power loss
- stale revision
- two Trier Bridge instances
- migration failure

Keep the last known-good state and preserve recovery evidence.

## 13. Persistence qualification (NOT RUN)

Future persistence qualification covers: atomic writes, restart, crash during write, disk full, read-only filesystem, permission loss, migration success/failure, stale revision, concurrent instances, operation-journal reconciliation, unresolved recovery retention, cache eviction without user-data loss.

Results are recorded per `VALIDATION.md`. No result is implied by this document.
