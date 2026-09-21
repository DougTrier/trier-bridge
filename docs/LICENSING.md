# LICENSING.md
# Trier Bridge Licensing, Copyright, and Provenance Policy

**Project:** Trier Bridge  
**License:** Apache License, Version 2.0  
**SPDX identifier:** `Apache-2.0`  
**Copyright:** © 2026 Doug Trier  
**Status:** Project licensing baseline  
**Date:** September 20, 2026

---

## 1. Licensing Decision

Trier Bridge is intended to be released under the **Apache License, Version 2.0**.

The repository root should contain:

- `LICENSE` — the complete Apache License 2.0 text
- `NOTICE` — Trier Bridge attribution/provenance notices
- `LICENSING.md` — this project-specific policy
- applicable license/copyright headers in qualifying first-party source files

This mirrors the licensing model selected for Goldenage Retro.

---

## 2. Copyright Ownership

Unless a file or component states otherwise:

> **Copyright 2026 Doug Trier**

Doug Trier retains copyright in original Trier Bridge work.

Licensing the project under Apache-2.0 grants users the permissions provided
by that license. It does **not** transfer ownership of the original copyright.

Contributors retain copyright in their own original contributions unless a
separate written agreement states otherwise.

---

## 3. What Apache-2.0 Allows

Subject to the Apache License 2.0 terms, recipients may generally:

- use Trier Bridge
- reproduce it
- modify it
- create derivative works
- redistribute source or binary forms
- use it privately
- use it commercially
- include it in other products

Apache-2.0 is a permissive open-source license.

### No royalty or revenue-share right

Apache-2.0 does **not** require someone who builds a commercial or private
product from Trier Bridge to pay Doug Trier a percentage of revenue merely
because Trier Bridge code was used.

The project's protection comes instead from:

- copyright ownership
- required license preservation
- attribution/NOTICE obligations where applicable
- preservation of copyright, patent, trademark, and attribution notices
- requirements concerning modified files and redistributed works
- the Apache-2.0 patent-license framework

The purpose of this licensing choice is broad legitimate reuse while retaining
clear provenance and authorship.

---

## 4. Provenance Goal

Trier Bridge should remain identifiable as originating from Doug Trier even
when legally reused, modified, or redistributed.

The project therefore uses three complementary mechanisms:

1. **Repository-level license**
2. **NOTICE attribution**
3. **Source-file copyright/SPDX headers**

These controls should be applied consistently without altering third-party
works or falsely claiming ownership of material Doug Trier did not create.

---

## 5. Canonical Source Header

Qualifying first-party source files should use the following header, expressed
in the comment syntax appropriate for the language or file type:

```text
Copyright 2026 Doug Trier

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### Compact form

For formats where the full header is impractical or would materially harm the
file format, the approved compact form is:

```text
Copyright 2026 Doug Trier
SPDX-License-Identifier: Apache-2.0
```

Use the full header for ordinary substantive source files unless a documented
format-specific reason supports the compact form.

---

## 6. Files That Normally Receive Headers

Subject to format suitability, first-party files such as these should normally
receive a copyright/license header:

- Rust
- C / C++
- Java / Kotlin
- JavaScript / TypeScript
- Python
- shell scripts
- PowerShell
- source-like build or automation scripts
- substantial first-party configuration logic
- substantial first-party documentation when appropriate

The header policy should be enforced mechanically where practical.

---

## 7. Files That Should Not Be Blindly Rewritten

Do **not** mechanically insert Trier Bridge headers into:

- `LICENSE`
- `NOTICE`
- third-party source
- vendored dependencies
- generated files
- lockfiles
- binary files
- images
- fonts
- archives
- signed artifacts
- upstream patches retained verbatim
- files whose format does not safely permit comments
- third-party license or attribution files

Header tooling must classify these files rather than rewriting everything.

---

## 8. Third-Party Code

Third-party software keeps its original license.

Trier Bridge's Apache-2.0 license does not relicense third-party components.

For every distributed third-party dependency or copied component, determine:

- component name
- version
- source/provenance
- license
- copyright owner
- whether source is modified
- whether attribution is required
- whether a NOTICE must be retained
- whether source availability or other obligations apply
- whether the license is compatible with the intended Trier Bridge distribution

Where required, include the appropriate third-party license and notice text in
the distribution.

---

## 9. Third-Party Assets

Code licensing and asset licensing are separate.

Apache-2.0 must not be assumed to cover third-party:

- logos
- trademarks
- product names
- screenshots
- photographs
- illustrations
- icons
- fonts
- sounds
- videos
- themes
- documentation excerpts

Every non-original distributed asset requires its own provenance and usage
basis.

If that basis is not established, replace or exclude the asset.

---

## 10. Windows and Linux Branding

Trier Bridge may describe compatibility concepts using factual product and
technology names when legally appropriate, but the project must not imply
ownership of or endorsement by third parties.

Do not copy Windows proprietary visual assets merely to make Trier Bridge look
familiar.

Familiarity should be achieved through workflow, terminology, structure, and
original Trier Bridge design assets.

Third-party trademarks remain the property of their respective owners.

---

## 11. Modified Files

When redistributing modified Apache-licensed source, Apache-2.0 requires
appropriate notice that files were changed.

Trier Bridge contributors and downstream distributors should preserve existing
copyright, patent, trademark, attribution, and NOTICE information required by
the license.

Project tooling should avoid removing provenance from modified files.

---

## 12. NOTICE Policy

The repository `NOTICE` file is part of the project provenance model.

It should contain factual attribution information only.

`NOTICE` must not:

- attempt to change Apache-2.0
- add new license restrictions
- claim ownership of third-party work
- make unsupported trademark claims
- contain marketing copy disguised as a license condition

If a distributed dependency requires NOTICE attribution, include the applicable
notice according to its license and distribution requirements.

---

## 13. Contribution Policy

Unless a contribution explicitly states otherwise and is accepted under a
different documented arrangement, contributions intentionally submitted for
inclusion in Trier Bridge are expected to be provided under the project's
Apache-2.0 licensing model.

Contributors must have the right to submit what they contribute.

Contributors must not submit:

- copied proprietary source
- leaked/private source
- code they are not permitted to relicense
- unapproved copyrighted assets
- credentials or secrets
- material whose provenance cannot be established

Contribution provenance should be preserved through Git history.

A Contributor License Agreement should not be introduced merely by habit.
If future project scale or legal requirements justify one, that should be a
separate deliberate owner decision.

---

## 14. Patent Considerations

Apache-2.0 contains an express patent-license framework.

This is one reason it is preferred over some simpler permissive licenses for a
systems project that may attract substantial external contributions.

The project should not make independent statements such as "patent free" or
"no patent risk."

Patent questions beyond the license text require appropriate legal review.

---

## 15. No Additional Restrictions Through Project Policy

Project documentation, source headers, `NOTICE`, coding standards, contribution
rules, or UI text must not accidentally contradict or narrow the rights granted
by Apache-2.0.

Engineering policy can govern what Trier Bridge accepts into its own repository.

It cannot secretly convert Apache-2.0 into a more restrictive license for
downstream users.

---

## 16. Binary and Installer Distribution

Every official binary/package distribution should include or provide the
required licensing material in an appropriate accessible location.

Depending on package format, this may include:

- `LICENSE`
- `NOTICE`
- third-party notices
- third-party license inventory
- source/project URL when one exists
- version/build identity

Package-specific Linux conventions should also be followed where required.

---

## 17. Forks and Derivative Works

Apache-2.0 permits forks and derivative works subject to its terms.

Trier Bridge should not attempt to prevent lawful forks through technical or
documentation tricks.

The project should instead protect provenance by:

- retaining copyright notices
- using NOTICE appropriately
- keeping source headers
- maintaining clear project authorship
- publishing verifiable releases and hashes
- keeping accurate Git history

---

## 18. Repository and Release Checks

Before a public release, verify:

- [ ] root `LICENSE` contains the complete Apache License 2.0
- [ ] root `NOTICE` is present and factually correct
- [ ] qualifying first-party source has approved headers
- [ ] no third-party source was falsely marked Copyright Doug Trier
- [ ] generated/vendor/binary exclusions are correct
- [ ] dependency licenses have been inventoried
- [ ] required third-party notices are included
- [ ] asset provenance has been reviewed
- [ ] Windows/Linux/vendor marks and visual assets have been reviewed
- [ ] release archive/package contains required licensing files
- [ ] installer/package presents or installs required notices appropriately
- [ ] no secrets/private material are included
- [ ] reachable Git history intended for publication has been reviewed
- [ ] release source and binaries correspond to the reviewed licensing inventory

A successful compile is not licensing evidence.

---

## 19. Licensing Evidence States

For release work, classify licensing/provenance items explicitly:

- `FIRST_PARTY_CONFIRMED`
- `THIRD_PARTY_CONFIRMED`
- `LICENSE_CONFIRMED`
- `NOTICE_REQUIRED`
- `NOTICE_COMPLETE`
- `ASSET_ELIGIBLE`
- `REPLACE`
- `EXCLUDE`
- `UNRESOLVED`
- `NOT_DISTRIBUTED`

`UNRESOLVED` material does not ship.

---

## 20. Relationship to SECURITY.md and INVARIANTS.md

Licensing is part of release integrity.

`SECURITY.md` governs the security architecture.

`INVARIANTS.md` governs product, safety, recovery, and compatibility promises.

`LICENSING.md` governs copyright, license, attribution, and distribution
provenance.

None of these documents may silently weaken another.

Where a licensing issue blocks lawful distribution, the affected release or
asset remains blocked until resolved.

---

## 21. Current Status

The licensing model is selected:

> **Apache License, Version 2.0**

The root `LICENSE` and initial `NOTICE` are prepared.

Third-party dependency and asset inventories will require review once the
implementation stack and distributed assets are selected.

No future dependency or asset should be treated as distributable merely because
the Trier Bridge project itself uses Apache-2.0.

---

## Final Principle

> **Open source does not mean ownerless.**

Trier Bridge is intended to be broadly usable, modifiable, and redistributable
under Apache-2.0 while preserving accurate authorship, copyright, attribution,
and third-party provenance.

**Copyright © 2026 Doug Trier.**
