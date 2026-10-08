# Data Model: a finite batch evidence record

**Feature directory**: `C:\code\ama\specs\001-proxy-dependency-upgrades`  
**Scope**: documentation data only. No runtime classes, database, API, schema library or new tooling is proposed.

The initial populated record is split between `research.md` (decisions) and `evidence.md` (observations). Later validation can extend the same record and reference existing run outputs. A table/CSV or JSON export may be used for review, but is not a new product or a prerequisite framework.

## Entities and relationships

### 1. Chore PR snapshot — exactly 33 records

Fields: repository, PR number/URL, ecosystem, package/action identity, original target, original scope description, observed head SHA, observed base SHA, changed file paths, observation time, inclusion, work-item ID, planning direction and eventual outcome.

Key: `(repository, PR number, observed head SHA)`. Every original PR is included. A changed head becomes a new observation, not an overwritten historical target. Additions/removals require a scope decision.

Relationship: many PRs may refer to one work item, but retain separate targets and outcomes. #149/#132/#133 share NW-next; root/agents Python duplicates do not share a scope.

### 2. Dependency scope and environment

Fields: scope ID, absolute repository root, manifest/importer path, independent lock path and SHA-256 (or explicit `unlocked consumer`), install recipe, extras/markers, runtime and exact version, OS, architecture, libc/base-image digest where applicable, package-manager version, effective source policy and protected input hashes.

Key: `(scope ID, install recipe, runtime/OS/architecture/extras tuple)`. A shared npm lock does not erase importer identities. Separate uv locks, pip recipes and container recipes do not become the same environment because they contain the same package.

Relationship: one scope has one or more supported environments; each affected environment owns its two-install evidence. Unaffected scopes are recorded as protected with a reason, not falsely marked as successfully tested.

### 3. Upgrade work item — initially 31

Fields: work-item ID, package/action, scope ID, source PR IDs and original targets, verified resolved baseline, reconciled target, candidate/retained version or full SHA, selection kind, required related changes, rejected alternatives, evidence IDs, blocker IDs and readiness state.

An Action work item also carries an embedded record for every active `(workflow path, job, step)` reference: original ref, resolved baseline SHA/provenance, desired SHA, runner environment and validation links. The five Action decision groups do not collapse their 55 active occurrences or mixed baselines into one generic environment. The count of 31 work items is not a count of required validation environments.

For libraries, the initial goal is the highest proposed release in that same scope, compared using npm SemVer or Python PEP 440. A fallback must satisfy:

```text
stable(candidate)
major(candidate) == major(reconciled_target)
verified_baseline < candidate < reconciled_target
candidate is the highest member of the eligible, retrievable, secure set
```

An empty or ambiguous set produces `blocked`, not an arbitrary selection. A newer baseline may be retained only with its own retrieval/compatibility/security/validation evidence. Never treat a range minimum as the resolved baseline.

Actions have no numeric SHA comparison and no alternative-release fallback. Eligibility is the exact proposed target, or a verified newer existing baseline proven by official release ordering or repository ancestry/provenance. Timestamps alone are insufficient.

### 4. Availability and selection observation

Fields: evidence ID, work-item/scope references, observation time in UTC, approved source policy, metadata request and result, catalogue identity/digest if used, exact artifact URL/filename, redirect provenance, final host, HTTP/error classification, byte count, expected checksum and algorithm, actual checksum, identity/version check, wheel/platform tags or npm engine/peers, environment coverage, rejection/selection rationale.

Allowed availability classifications:

- `retrieved-integrity-verified` for the **recorded artifact**, not the whole environment;
- `version-absent`, backed by a trustworthy source query;
- `required-file-missing` or `platform-incompatible`;
- `integrity-failed`;
- `access-unavailable` for authentication, permission, rate-limit, timeout, connection or service failure;
- `unverified` where evidence is insufficient.

A catalogue hit, tag, public announcement, HTTP success without identity/hash checking, or cached file is not an installability result. Preserve an initial failed observation even if a later retry succeeds. Do not retain credentials, access tokens or signed redirect query strings in the feature record.

For Actions, add official repository, full commit/tree SHA, tag-to-commit mapping where relevant, source blob verification, release asset identities and checksums/signature evidence. Separate proposed-target source success from missing baseline provenance.

### 5. Validation record

Fields: run ID, candidate input-set ID, scope/environment ID, baseline-or-candidate designation, command and absolute working directory, tool/runtime versions, non-secret environment settings, start/end time, status, exit code, installed version map/Action SHA map, before/after protected input hashes, evidence location, failure fingerprint and applicability rationale.

Status is one of `passed`, `failed`, `blocked`, `not-run`, or `not-applicable`. The last requires a scope-specific reason and is not a passed execution.

For every affected independently resolved supported environment, link two distinct clean-install run IDs. Both must use the same approved candidate inputs, start without installed packages/shared caches, demonstrate fresh approved-source retrieval, produce the same resolved version/Action SHA maps and preserve declarations/locks/workflows. A single run reused under two IDs is invalid.

Quality-gate records attach to those exact candidate inputs. A later lock change invalidates prior candidate validation. Baseline failure evidence establishes provenance but cannot waive a mandatory gate.

### 6. Blocker

Fields: blocker ID, category (scope/source/compatibility/security/consistency/validation/authority), affected PR/work-item/environment IDs, cause or uncertainty, evidence references, responsible role, next action, required human decision if any, status and resolution evidence.

Every incomplete PR must link to at least one actionable blocker. `Waiting for later authorised validation` is explicit, not an implied pass. Reopened source/validation failures reopen dependent readiness.

## State transitions

```text
accounted
  -> candidate direction recorded
  -> artifact coverage established
  -> compatibility and security established
  -> two clean installs and applicable quality gates passed
  -> verified outcome

any incomplete state -> blocked
blocked -> prior state only after new evidence or explicitly approved policy resolution
verified outcome -> blocked if final source/input revalidation fails
```

`Planning direction` and `verified outcome` are separate fields. The current P/F/R/H matrix is not the last state in this diagram.

Verified outcomes are exactly: `exact-target upgrade`, `approved fallback upgrade`, `verified already-satisfied/superseded`, or `blocked/incomplete`. Current inclusion policy does not permit exclusion. Final accounting must satisfy:

```text
count(original PRs) = 33
every PR -> work item -> independent scope -> evidence/outcome
fully upgrade-complete => no incomplete PR and no unmet mandatory gate
```

No state grants permission to commit, push, merge, comment, publish or deploy. Human lifecycle/remote-operation authority is a separate recorded approval.
