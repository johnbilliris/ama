# Data Model: Extension List

**Feature**: `001-extension-list`  
**Date**: 2026-09-21

## Overview

The feature uses immutable, read-only projections. Raw registry, manifest, file
system, runtime-registration, and catalog records are normalized independently
before they are reconciled into display entries. The list action never repairs
or writes any source.

All model implementations are new files under
`tools/specify-cli/src/specify_cli/extensions`. Installed data
comes from the existing AMA-local `.specify/extensions/.registry` and
`*/extension.yml` files. Optional catalog configuration comes from the new
`.specify/extensions/catalogs.json`. No model or adapter imports code or data
from another repository.

## Enumerations

### ExtensionListView

| Value | Meaning |
| --- | --- |
| `installed` | Locally installed records only; default |
| `available` | Every catalog group, marked with local installation state |
| `all` | Union of installed and catalog groups |

### ActivationState

| Value | Meaning |
| --- | --- |
| `disabled` | Registry metadata explicitly sets `enabled` to false |
| `inactive` | Enabled, but no successful or failed activation attempt is known |
| `active` | Activation completed or compatible legacy runtime evidence proves activation |
| `activation-failed` | The most recent recorded activation attempt failed |

### HealthState

| Value | Meaning |
| --- | --- |
| `healthy` | Required identity and metadata are valid and no conflict exists |
| `invalid` | At least one validation diagnostic or conflict exists |

### SourceKind

| Value | Meaning |
| --- | --- |
| `local` | Only installed source records contributed |
| `catalog` | Only catalog source records contributed |
| `combined` | At least one installed and at least one catalog record contributed |

### ProjectContext

The invocation context discovered by walking ancestors from the current working
directory.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `project_root` | project-relative or absolute internal path, or null | yes | Non-null only when an ancestor contains `.specify/extensions`; never serialized to user output |
| `extensions_root` | internal path or null | yes | Exactly `<project_root>/.specify/extensions` when a root exists |
| `catalog_config` | internal path or null | yes | Non-null only when a discovered root contains `.specify/extensions/catalogs.json` |

When `project_root` is null, installed collection returns no rows and catalog
collection returns no rows without attempting a user-home, process-global, or
current-directory fallback. All scopes succeed with their normal empty-state
projection. Catalog configuration can only be attached to a non-null discovered
project root.

## Entities

### InstalledSourceRecord

One coalesced local installation candidate before stable-ID grouping. It may
contain a registry observation, a physical manifest observation, or both.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `source_location` | project-relative POSIX path | yes | Never expose an absolute machine path |
| `observation_kinds` | unique array of `registry` and/or `physical` | yes | Retains which local observations contributed after coalescence |
| `registry_key` | string or null | no | Registry lookup key; not automatically a stable ID |
| `stable_id` | string or null | no | Accepted only from a valid manifest ID matching `^[a-z0-9-]+$` |
| `name` | string | yes | Manifest name or deterministic fallback label |
| `installed_version` | string or null | no | Prefer registry version, then valid manifest version |
| `description` | string or null | no | Missing optional text does not invalidate the record |
| `priority` | positive integer | yes | Existing normalized priority, default 10 |
| `enabled` | boolean | yes | Existing registry value, default true for legacy records |
| `command_count` | non-negative integer | yes | Count valid manifest command declarations |
| `hook_count` | non-negative integer | yes | Count hook event keys, preserving existing semantics |
| `registered_commands` | mapping of integration to string array | yes | Invalid members are ignored and diagnosed |
| `registered_skills` | string array | yes | Invalid members are ignored and diagnosed |
| `activation_evidence` | ActivationEvidence or null | no | Optional registry metadata plus compatible legacy evidence |
| `diagnostics` | Diagnostic array | yes | Stable order by code, then source location |

**Identity rule**: Normalize physical source identity before stable-ID grouping.
Registry and physical observations of the same normalized source and same valid
stable ID coalesce into one record that combines registry state with manifest
metadata and retains both observations as evidence. Same-source observations
with contradictory valid stable IDs coalesce into one invalid
`local-identity-conflict` record with no authoritative stable ID. Only distinct
normalized physical sources sharing one valid stable ID become a
duplicate-installed conflict.

A valid `stable_id` comes from validated manifest identity. A registry key or
directory name does not substitute for a missing manifest ID. A record without
a stable ID can never join a catalog group. Its display identity is a canonical
project-relative POSIX path. Its grouping key is the resolved, project-contained
path normalized with platform path semantics, so observations consolidate
despite dot segments, separator aliases, resolvable symlinks, or case aliases on
case-insensitive platforms. Distinct normalized paths remain separate even when
names collide.

### ActivationEvidence

Optional registry metadata read when present, never written by the list action.
Existing registered command or skill evidence can also support legacy `active`
derivation without changing the registry.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `state` | `active`, `inactive`, or `activation-failed` | yes | `disabled` remains derived from `enabled` |
| `integration` | string or null | no | Integration for which activation was attempted |
| `attempted_at` | RFC 3339 timestamp or null | no | Informational; not used for ordering entries |
| `diagnostic` | string or null | no | Required when state is `activation-failed` |

Unknown state values produce an `invalid-activation-state` diagnostic and are
projected as `inactive` so no fifth user-facing state is introduced.

### CatalogSourceRecord

One schema-valid entry from one configured active catalog after complete source
validation and before grouping. A malformed entry fails its entire source and
does not become a projected invalid row.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `stable_id` | string | yes | Must match the extension ID grammar |
| `name` | string | yes | Already proven valid by source schema validation |
| `available_version` | non-empty string or null | no | Empty string is invalid; null or omission normalizes to `unknown` for display |
| `description` | string or null | no | Optional |
| `catalog_name` | string | yes | Added by the catalog adapter |
| `catalog_priority` | positive integer | yes | Used only for deterministic preferred-field selection |
| `source_ordinal` | non-negative integer | yes | Zero-based position in the validated source array |
| `record_sha256` | lowercase 64-hex string | yes | SHA-256 of the normalized internal record; raw/free-text values are not emitted as evidence |
| `install_allowed` | boolean | yes | Display metadata; does not affect inclusion |
| `provides` | capability summary | yes | Missing commands/templates/scripts/hooks normalize to zero |

### CatalogConfiguration

One optional AMA-local `.specify/extensions/catalogs.json` document.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `schema_version` | string | yes | Initial value `1.0` |
| `catalogs` | CatalogConfigurationEntry array | yes | 0..8 entries; empty means no configured catalogs |

Each `CatalogConfigurationEntry` contains a unique `name`, positive integer
`priority`, and exactly one `path` or private Azure Blob `url`. A remote entry
also requires `storage_account_resource_id` and `container_scope`. Numeric priority 1 is highest.
The array schema validates entry shape but JSON Schema cannot enforce uniqueness
by one object property. After schema validation, the configuration loader MUST
run a semantic validator that rejects duplicate `name` values before opening,
statting, resolving, or retrieving any configured source. `path` is resolved
within the AMA project root and cannot escape it. A production `url` must be an
Azure Blob HTTPS URL. Before retrieval, managed identity verifies the account is
in an allowed AU region, public access is disabled, default network action is
Deny, an approved private endpoint exists, the Blob host matches the ARM account
and resolves privately, and the daemon principal has exactly container-scoped
Storage Blob Data Reader with no broader data-plane role. A source
document has `schema_version: "1.0"` and an `extensions` array containing at
most 1,000 records and contributes no records until complete schema validation
succeeds.

Every local or remote source starts one `SourceDeadline` with a monotonic
absolute deadline 5 seconds later. Local processing checks the stat size before
parsing, rejects values over 1,048,576 bytes, and performs a bounded read of at
most 1,048,577 bytes to detect growth races. Stat, read, UTF-8 decode, JSON
parse, and schema validation all consume the same budget. Remote processing
follows at most 5 redirects, revalidates every target as HTTPS, and limits the
decoded body to 1,048,576 bytes. HTTP loopback URLs are injected test-fixture
inputs only and are invalid production configuration. Any deadline, safety,
retrieval, decoding, JSON, or schema failure makes catalog data incomplete for
that invocation.

### SourceDeadline

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `started_at` | monotonic timestamp | yes | Captured immediately before source work |
| `deadline` | monotonic timestamp | yes | Exactly `started_at + 5.0` seconds |
| `clock` | injected monotonic callable | yes | Fakeable for deterministic tests |

`remaining()` computes `deadline - clock()` immediately before and after every
stage and raises `catalog-source-deadline-exceeded` when the value is not
positive. The remaining value is propagated to DNS/connect, redirect handling,
each streamed read, decode, parse, and validation. A `DeadlineTransport`
interface accepts the absolute deadline and clock. The production transport
supervises the complete remote pipeline with
`multiprocessing.get_context("spawn")` on every platform. Its worker target is
module-level and picklable. The parent terminates and boundedly joins it at the
deadline, then closes every process and queue resource, because a standard
synchronous Requests timeout cannot by itself guarantee interruption of blocked
DNS. Tests inject stage and process fakes that consume the clock budget at every
boundary and deterministically assert spawn selection, termination, join, and
resource cleanup on success, failure, and timeout.

### Diagnostic

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `code` | kebab-case string | yes | Stable machine-readable reason |
| `message` | string | yes | Text-complete user-facing explanation |
| `source` | project-relative path, catalog name, or null | no | Must not contain secrets or absolute local paths |

Initial diagnostic codes include `missing-stable-id`, `invalid-stable-id`,
`manifest-unreadable`, `manifest-invalid`, `registry-metadata-invalid`,
`local-identity-conflict`,
`invalid-activation-state`, `activation-failed`, `duplicate-installed-id`, and
`duplicate-catalog-id`, `duplicate-fallback-source`,
`catalog-source-too-large`, `catalog-source-record-limit`, and
`catalog-source-deadline-exceeded`.

### SourceEvidence

One immutable contribution retained on every projection row.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `kind` | `local` or `catalog` | yes | Origin of the contribution |
| `source_sha256` | lowercase 64-hex string | yes | SHA-256 of the privacy-minimized source identity; raw source label is not serialized |
| `source_ordinal` | non-negative integer | yes | Discovery order within the source before deterministic sorting |
| `record_sha256` | lowercase 64-hex string | yes | Fingerprint only; raw canonical data is never serialized |

Evidence is sorted by source kind, source identity, source ordinal, and
record SHA-256. Conflicts retain at least two evidence items. Differing field
names are summarized by non-empty conflict reasons and distinct versions remain
in `available_versions`; alternate names, descriptions, authors, and other raw
free-text values are not duplicated in evidence.

### ExtensionListEntry

One reconciled row returned to renderers and JSON serialization.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `id` | string or null | yes | Null only for fallback-identity installed rows, which are always invalid with metadata-health diagnostics |
| `fallback_identity` | string or null | yes | Present only when `id` is null |
| `source_locations` | unique string array | yes | Local source locations in lexical order |
| `name` | string | yes | Preferred installed name, else highest-priority catalog name, else fallback label |
| `description` | string or null | yes | Preferred installed value, then catalog value |
| `installed` | boolean | yes | True when one or more local records contribute |
| `installed_version` | string or null | yes | Null when catalog-only or unavailable |
| `available_versions` | unique string array | yes | Sorted deterministic set from all catalog records |
| `version` | string | yes | Legacy field: installed version, else preferred available version, else `unknown` |
| `priority` | integer or null | yes | Installed priority; null for catalog-only rows |
| `enabled` | boolean or null | yes | Installed enablement; null for catalog-only rows |
| `source` | SourceKind object | yes | `local`, `catalog`, or explicit `combined` |
| `evidence` | SourceEvidence array | yes | Every contributing record; never empty |
| `provides` | capability counts | yes | Commands, templates, scripts, and hooks |
| `install_allowed` | boolean or null | yes | Null for local-only; conservative catalog value otherwise |
| `activation_state` | ActivationState or null | yes | Null for catalog-only rows |
| `activation_diagnostic` | string or null | yes | Non-empty only for `activation-failed`; independent of metadata health diagnostics |
| `health` | HealthAssessment | yes | Installed and catalog conflicts are explicit |
| `conflict` | boolean | yes | True for duplicate installed or catalog stable IDs |
| `conflict_reasons` | string array | yes | Empty when `conflict` is false |
| `catalog_sources` | string array | yes | Unique catalog names in priority/name order |

### HealthAssessment

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `state` | HealthState | yes | `invalid` iff diagnostics is non-empty |
| `diagnostics` | Diagnostic array | yes | Must be non-empty for `invalid`; empty for `healthy` |

### ExtensionListResult

Internal command result, not the stdout JSON envelope.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `view` | ExtensionListView | yes | Resolved from CLI flags |
| `entries` | ExtensionListEntry array | yes | Deterministically sorted |
| `warnings` | Diagnostic array | yes | Includes `catalog-unavailable` on graceful degradation |
| `catalog_complete` | boolean | yes | False when any active catalog failed |

### UsabilityEvidence

One evidence document for the shared SC-001 and SC-006 protocol.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `schema_version` | string | yes | Constant `1.0` |
| `feature` | string | yes | Constant `001-extension-list` |
| `privacy` | PrivacyProtocol object | yes | Proves notice, consent, purpose limitation, AU storage, retention, separation, access, audit, encryption, withdrawal, incident, and no-direct-identifier controls |
| `allocation_algorithm` | string | yes | Constant `sha256-seeded-stratified-order-v1` |
| `allocation_seed` | string | yes | Exactly 64 lowercase hexadecimal characters |
| `task_variants` | unique string array | yes | At least two non-empty values; declared order controls round-robin assignment |
| `allocation_records` | AllocationRecord array | yes | Exactly one recomputable record per included participant |
| `participants` | object with `novice` and `experienced` arrays | yes | Each required array contains exactly 10 unique IncludedParticipant records |
| `excluded_participants` | ExcludedParticipant array | yes | Unique records; may be empty |
| `aggregates` | UsabilityAggregates | yes | Required nested aggregate object |
| `review` | UsabilityReview | yes | Pseudonymous reviewer ID, closed role/decision/reason, and review timestamp; no name or free text |

`UsabilityAggregates` has exactly three required fields and no others:
`included_participant_count` is constant 20, `sc_001_success_count` is an
integer from 0 through 20, and `sc_006_clear_count` is an integer from 0
through 20. These are observed counts, not schema-level pass assertions.

`UsabilityReview` contains `reviewer_identifier` matching
`reviewer-<16 lowercase hex>`, role `privacy` or `research-governance`, RFC 3339
`reviewed_at`, decision `approved` or `rejected`, and closed reason code
`study-verified` or `study-rejected`. Names and free-text notes are prohibited.

Each `IncludedParticipant` contains exactly these required fields:
`participant_id`, `is_adult`, `uses_cli_monthly`,
`prior_feature_exposure`, `spec_kit_workflows_last_6_months`,
`used_extension_management`, `task_variant`, `requested_accommodations`,
`provided_accommodations`, `installed_answer_correct`,
`enabled_answer_correct`, `elapsed_seconds`, `sc_001_success`,
`sc_006_clarity_rating`, `consulted_installation_directories`,
`attempted_extension_command`, and `sc_006_clear`. Every included record has
`is_adult=true`, `uses_cli_monthly=true`, and
`prior_feature_exposure=false`. Accommodation arrays contain only unique closed
generic category codes and the requested and provided sets must match exactly
without changing the measured task. They contain no free text or medical
details. `sc_001_success=true` requires both answers true and elapsed
time at most 30 seconds; false requires at least one incorrect answer or elapsed
time greater than 30 seconds. `sc_006_clear=true` requires a rating of 4 or 5
and both prohibited-action fields false; false requires a rating at most 3 or
at least one prohibited-action field true.

The novice stratum requires 0-2 completed Spec Kit workflows in the prior 6
months and `used_extension_management=false`. The experienced stratum requires
at least 5 completed workflows in that period and
`used_extension_management=true`. Semantic validation rejects the unclassified
gap of 3-4 workflows rather than weakening either stratum.

Each `AllocationRecord` contains required `participant_id`,
`experience_stratum`, `task_variant`, and positive `allocation_position`.
Within each stratum, sort eligible anonymized IDs, then order by SHA-256 of
`<allocation_seed>:<stratum>:<participant_id>` with participant ID as the final
tie-break. Assign task variants round-robin in declared `task_variants` order.
Every allocation record must match this recomputation exactly.

Each `ExcludedParticipant` contains required `participant_id`,
`experience_stratum`, constant `excluded_before_task_exposure=true`,
`exclusion_reason`, `unavailable_accommodations`, and
`replacement_participant_id`. The reason is either
`documented-technical-interruption`, which requires an empty unavailable array,
or `required-accommodation-unavailable`, which requires at least one recorded
unavailable category code. Participant IDs match the schema's pseudonymous ID
grammar.
The containing array supplies the participant's experience stratum. Every
post-exposure outcome remains in `participants`. Each excluded record satisfies
one allowed pre-exposure reason and identifies a replacement participant in the
same stratum. A semantic evidence validator MUST
confirm exactly 20 participant identifiers are unique across both strata; each
participant belongs to exactly one stratum and each stratum contains exactly 10
included records; aggregate counts equal values derived from participant records;
excluded identifiers are not included, exclusions satisfy the allowed
pre-exposure rules, and every replacement is a distinct included
participant in the same stratum; exactly one allocation record exists for every
included participant and matches deterministic recomputation; and every
included participant's requested accommodations equal the provided
accommodations. It MUST also derive each SC-006 qualification from the rating
and both prohibited-action booleans, reject a qualifying record when either
boolean is true, and derive the aggregate only from participants that satisfy
all three conditions. These cross-record comparisons are not expressible in
JSON Schema Draft 2020-12. The AMA-local implementation is
`tools/specify-cli/src/specify_cli/evidence.py`, tested by
`tools/specify-cli/tests/test_usability_evidence.py`. Evidence publication and
gating MUST invoke it after JSON Schema validation. The validator separately
reports SC-001 passed only when the derived success count is at least 19 and
SC-006 passed only when the derived clear count is at least 18. A schema-valid,
semantically consistent document may therefore record a failed study;
lifecycle completion means validation and review completed, not that either
criterion passed.

`PrivacyProtocol` is a closed object containing notice version and provision
time, `consent_recorded_for_all_included_and_excluded=true`, purpose limited
exactly to SC-001 and SC-006, an authorized AU Storage account resource ID,
review timestamp, delete-by timestamp no later than 90 days after review unless
`legal_hold_approved=true`, `verified_deletion_required=true`, controller role,
`no_direct_identifiers=true`, separate re-identification key and recruitment
records, named least-privilege study-team access, immutable access audit,
encryption in transit and at rest, and confirmed withdrawal and breach-response
processes. Random pseudonymous IDs are generated independently from identity or
contact data. Evidence excludes names, email, employer, precise location,
medical detail, and free-text PII. Actual study evidence never exists in GitHub,
the repository, or local implementation artifacts.

### SovereignExternalPlatformEvidence

One authoritative Draft 2020-12 document validated by
`contracts/platform-evidence.schema.json` and stored only in a pre-provisioned
private AU Azure Blob container. The top-level closed object has constants
`schema_version=1.0`, `feature=001-extension-list`,
`category=sovereign-external-platform`, UUID `validation_session_id`, and script path
`scripts/spec001/run_external_platform_validation.py`; exactly two platform
records; and one review object. It contains no repository, commit, ref,
workflow, GitHub run, runner-label, credential, SAS, command-output, inventory,
source-content, absolute-path, or regulated-data fields.

Each record contains OS, x64 architecture, standalone Azure VM resource ID,
IMDS VM ID, allowed AU location, script version, Python/package/lock metadata,
exact command outcomes, execution timestamp, and `evidence_digest`. The Windows
record requires non-empty `windows_product_name` and `windows_version`. The
Ubuntu record requires `distribution_id=ubuntu` and non-empty
`distribution_version`. The Azure resource ID grammar admits only
`Microsoft.Compute/virtualMachines`, not VM scale sets.

`evidence_digest` is lowercase 64-character hexadecimal SHA-256 over RFC 8785
canonical JSON UTF-8 bytes of the record with `evidence_digest` omitted. Schema
and semantic validation establish internal consistency only. The closed review
object contains only pseudonymous `reviewer_identifier` matching
`reviewer-<16 lowercase hex>`, role `security` or `compliance`, RFC 3339 review
time, decision `approved` or `rejected`, and closed `decision_reason_code`
`evidence-verified` or `evidence-rejected`. Names and free-text notes are
prohibited. The authorized pseudonymous reviewer supplies the independent
external trust decision in the AU-resident evidence document.

The same schema exposes a closed `platformFragment` definition for collect-mode
shape validation. A fragment carries schema version, feature, fragment category,
the shared UUID `validation_session_id`, script path, one verified
`StorageBoundary`, and one platform record.
Collect mode conditionally creates exactly one fragment at
`spec001-extension-list/<validation_session_id>/fragments/<os>-<imds_vm_id>.json`;
same-key overwrite is invalid. Finalize mode reads exactly one Windows and one
Ubuntu fragment for the same session and requires equal package metadata, lock
metadata, and script version before assembly. The hosted semantic validator
recomputes each digest, enforces exact OS cardinality and fragment-key identity,
requires the pseudonymous closed-coded review, validates the canonical document, and conditionally
creates `spec001-extension-list/<validation_session_id>/final/platform-evidence.json`.
Rejected review remains valid retained external evidence and never changes the
prose pending-external handoff.

`StorageBoundary` is a closed pre-write verification result containing the
storage-account ARM resource ID, container name, matching Blob account host,
allowed AU location, disabled public network access, deny-by-default network
rule, approved private-endpoint connection, private-only DNS result, exact
container scope, standalone VM managed-identity principal, exact Storage Blob
Data Contributor role definition and assignment scope, no-broader-write-role
assertion, and an AU-resident security/compliance attestation with a
pseudonymous reviewer identifier, timestamp, and digest. The attestation is a compact ES256 JWS whose exact versioned Azure
Key Vault key ID and public JWK belong to the reviewed package trust bundle. It
includes constant issuer
and audience, UUID JTI/session, 256-bit nonce, issued/not-before/expiry times,
and repeated storage, endpoint, scope, principal, and role claims. Semantic
validation verifies signature and allowlist membership, exact repeated claims,
maximum 10-minute lifetime, 2-minute clock skew, nonce/session binding, and JTI
replay rejection. The compact JWS is retained in AU-only evidence and its UTF-8
SHA-256 equals `attestation_digest`. Before every fragment or final canonical
write, the mode atomically creates `spec001-extension-list/attestation-jti/<jti>`
with create-if-absent. The container has a locked time-based immutability policy
of at least one day; evidence records marker name, successful creation,
retain-until time, policy mode, and operation. Each write uses a distinct fresh
attestation/JTI/nonce; an existing marker rejects cross-process replay.

The trust-bundle entry pins the exact private HTTPS endpoint, managed-identity
scope `api://ama-security-control-plane/.default`, versioned key ID, and public
JWK. `AttestationRequest` and `AttestationResponse` use the closed schema
definitions. Transport is one no-redirect/no-retry POST under a five-second
deadline, private DNS only, with at most 16 KiB `application/jose` response.
Operator input cannot override endpoint, scope, or key.
Collect and finalize fail before evidence access when ARM, DNS, RBAC, or
attestation verification is missing or inconsistent. Inputs never include
credentials or SAS.

### ExternalValidationStatus

Optional shape for a non-persisted in-memory or terminal-minimized handoff
object. It is never instantiated in the repository; authoritative pending state
is prose in the specification, handoff, and checklist.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `validation` | `sovereign-external-platform` or `human-study` | yes | Exactly one record per external validation class |
| `status` | constant `pending-external` | yes | Non-persisted handoff can never represent completion |
| `reason` | string | yes | Names the external VM/store/reviewer or participant prerequisite |
| `evidence_path` | null | yes | Azure Blob URI exists only in external handoff/store context |
| `validated_at` | null | yes | Completed validation time is not committed |

The non-persisted handoff status is intentionally pending-only. Platform completion
and its `https://<account>.blob.core.windows.net/<container>/<blob>` location
exist only in the AU-resident store after both standalone VM collect runs,
AU-side finalize, and the pseudonymous closed-coded review. A rejected review is still completed
external validation but does not satisfy approval. Human-study completion
likewise exists outside this local status and does not imply SC-001 or SC-006
passed.
No local semantic resolver follows a repository platform-evidence path, and
`local-current-platform` can never substitute for external platform evidence.

### AgentActionAuditRecord

One closed, privacy-minimized record conforming to
`contracts/agent-action-audit.schema.json`. Local-synthetic records append to an
owner-only temporary journal; sovereign records append to the private immutable
AU ledger. Each action has an intent record before execution and one
linked result record before completion/next action. It contains schema/feature/
ledger constants, UUID event/session and pseudonymous actor principal, monotonic
sequence and append byte position, phase/link, timestamp, closed action,
task/rationale code, outcome, session-manifest digest, closed `target`, target digest, previous-event digest, and event
digest. It contains no command output, source values, paths, human data, secrets,
or free text. The single feature append-blob chain uses one genesis record,
previous digest, Azure Blob lease, and append-position condition. Pre-action
conflicts reload/retry intent; post-action conflicts freeze and retry only the
result. The external coordinator owns sovereign bootstrap records; local
bootstrap hashes become the first local journal genesis; the daemon owns later
records in either profile. `identifier_digest`, kind-specific pre/post state digests, and
`target_digest` use the exact version-1 canonicalization algorithm in the
specification. Intent requires pre-state and null post-state; result retains the
same identifier/pre-state and requires post-state, repeating pre-state when no
state changed. Each repository-file mutation has its own complete serialized
transaction; a multi-file task reuses its task ID across distinct file targets
but no action spans files. Append or chain validation failure blocks/freezes.

`execution_mode` is `local-synthetic` or `sovereign`; `audit_sink` is
respectively `ephemeral-local` or `immutable-au`. Local journals are never
evidence and are logically deleted at finalization. A local session may restart
from the current worktree after custody loss, but segment discontinuity is
recorded and segments cannot be promoted to sovereign evidence.
`session_manifest_digest` is constant within a segment and hashes the RFC 8785
canonical protected/bootstrap manifest captured at session start.
`ledger_partition` is `spec001-extension-list/<session_id>`. Each session has
one genesis and at most 49,000 records; ordinary actions stop after sequence
48,998 so the final intent/result pair is reserved. No pair spans partitions and
a new session/partition makes no continuity claim.

### SovereignPrerequisiteAttestation

One closed artifact `{claims, compact_jws, attestation_digest,
replay_protection}` conforming to
`contracts/implementation-prerequisite-attestation.schema.json`. The decoded
JWS payload equals the closed `claims` object exactly and binds the
repository digest and branch to a fresh nonce/JTI, short validity window, audit
ledger controls, standalone AU VM/encrypted IPC, offline AU cache, and all
private dependency/control-plane/Key Vault/reviewer-store readiness claims.
Before sovereign validation/release the dispatcher computes the exact repository
manifest digest, generates the challenge/nonce/time request, accepts one compact
JWS from the pinned private control plane, validates schema then exact payload
equality, signature/key, issuer/audience, digest, nonce/JTI replay, 10-minute
lifetime, 2-minute skew, and every closed claim using an owner-only external AU
trust bundle, and creates the immutable AU replay marker before acceptance. It
is never committed. Local-synthetic startup neither requests nor fabricates it.

### ReadOnlyEvidence

One closed qualifying sovereign object proving that a single list invocation did not
mutate source, protected, or coverage state. It exists only on the verified
encrypted AU temporary volume through schema and semantic validation and is
then logically deleted.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `schema_version` | string | yes | Constant `1.0` |
| `feature` | string | yes | Constant `001-extension-list` |
| `category` | string | yes | Constant `read-only-validation` |
| `lifecycle` | string | yes | Constant `encrypted-au-ephemeral` |
| `validation_id` | UUID | yes | Unique synthetic/local validation identifier |
| `validated_at` | RFC 3339 timestamp | yes | Validation completion time |
| `view` | `installed`, `available`, or `all` | yes | Invoked list scope |
| `output_mode` | `text` or `json` | yes | Invoked output mode |
| `outcome` | `succeeded`, `failed`, or `blocked` | yes | Minimized execution result |
| `exit_code` | integer 0..255 | yes | Exact process exit code |
| `source_state_before_sha256` | lowercase SHA-256 | yes | Digest of the closed source-state snapshot |
| `source_state_after_sha256` | lowercase SHA-256 | yes | Must equal the before digest |
| `protected_state_before_sha256` | lowercase SHA-256 | yes | Digest of protected-state metadata |
| `protected_state_after_sha256` | lowercase SHA-256 | yes | Must equal the before digest |
| `coverage_state_before_sha256` | lowercase SHA-256 | yes | Digest of repository coverage-path state |
| `coverage_state_after_sha256` | lowercase SHA-256 | yes | Must equal the before digest |
| `execution_mode` | string | yes | Constant `sovereign` |
| `audit_sink` | string | yes | Constant `immutable-au` |
| `sovereign_session_id` | UUID | yes | Must equal the active daemon session |
| `preflight_attestation_digest` | lowercase SHA-256 | yes | Must match the verified compact-JWS digest |
| `execution_vm_resource_id` | Azure VM ARM resource ID | yes | Must match signed preflight claims and live IMDS |
| `audit_intent_event_id` | UUID | yes | Intent record for this producer action |
| `audit_intent_event_digest` | lowercase SHA-256 | yes | Must match the immutable ledger record |
| `peer_authenticated` | boolean | yes | Constant true |
| `au_vm_verified` | boolean | yes | Constant true |
| `encrypted_temporary_storage` | boolean | yes | Constant true |
| `audit_transaction_complete` | boolean | yes | Constant true after linked result append |
| `raw_output_deleted` | boolean | yes | Constant true after logical deletion |
| `repository_payload_persisted` | boolean | yes | Constant false |

The semantic validator requires equality for all three before/after digest
pairs. `outcome=succeeded` is equivalent to `exit_code=0`; `failed` or `blocked`
requires a nonzero exit code. No path, raw output, diff, Base64 value, inventory
record, environment value, secret, human datum, or sovereign external claim is
permitted. Binding semantics cross-check session ID, attestation digest, VM
resource ID, and audit intent ID/digest against signed claims, live IMDS, and the
immutable ledger before accepting the object. Local-synthetic tests may validate fake objects of this shape but do
not emit or retain a qualifying object.

### PerformanceEvidence

The implementation-owned planned `performance-evidence.schema.json` is a
closed shape contract for an ephemeral SC-002 object on the verified encrypted
AU volume. It requires: OS; architecture; CPU
model; positive logical CPU count; positive total memory bytes; Python version;
package version; lowercase 64-character lock SHA-256; optional non-empty
baseline runner identifier; constant `network_disabled=true`; non-empty fixture
ID; constant fixture count 100; exactly three warmup outcome records; exactly
30 non-negative duration values; constant nearest-rank `rank=29`; computed P95;
constant `threshold_seconds=2.000`; passed boolean consistent with P95 at or
below threshold; and RFC 3339 execution timestamp. It cannot contain human or
sovereign-external claims.

It also requires `execution_mode=sovereign`, `audit_sink=immutable-au`, UUID
`sovereign_session_id`, lowercase SHA-256 `preflight_attestation_digest`, the
standalone Azure VM ARM `execution_vm_resource_id`, UUID
`audit_intent_event_id`, and lowercase SHA-256 `audit_intent_event_digest`.
Semantics cross-check those values against the signed preflight, live IMDS, and
immutable ledger before the timing object is accepted.

For this evidence, `network_disabled=true` means feature catalog, package-index,
proxy, public-endpoint, and other unapproved transport is denied; only local
peer-authenticated IPC and pinned private AU audit/control-plane endpoints are
allowed. One verified daemon session is started before timing. Each warmup and
measured duration covers a fresh client process through complete stdout,
including peer handshake, installed processing, and both audit-ledger appends,
while excluding daemon startup, IMDS/session preflight, and fixture materialization.

JSON Schema validates only this shape. The post-schema semantic validator in
`specify_cli.evidence` requires exactly 30 durations, sorts them ascending,
selects one-based nearest-rank position 29, requires that value to equal
`p95_seconds`, requires `threshold_seconds=2.000`, and requires `passed` to equal
`p95_seconds <= threshold_seconds`. Both the producer and final gate invoke it
after schema validation, with matching red/green semantic tests.
The runtime object is deleted after validation and is never retained in the
repository. An unattested, non-AU, or unauthorized machine may run only fake
shape/semantic/producer tests and cannot emit qualifying performance evidence.

### RootRegressionBaseline

One ephemeral external-temp machine-readable observation captured before
package source implementation, held by the long-lived custodian daemon for the
implementation session, and validated by
`contracts/root-regression-baseline.schema.json`. It does not require the root
suite to pass.

A sovereign session may capture this baseline only before any feature source or
workflow edit; custody loss after the first edit blocks recapture. A local-
synthetic session may capture the current worktree when a new local journal
segment starts; that baseline supports local attribution only and cannot be
combined across segments or used as release evidence.

| Field | Type | Required | Rules |
| --- | --- | ---: | --- |
| `schema_version` | string | yes | Constant `1.0` |
| `feature` | string | yes | Constant `001-extension-list` |
| `lifecycle` | string | yes | Constant `external-temp-ephemeral` |
| `raw_output_deleted` | boolean | yes | Constant true after normalization and hashing |
| `command` | string | yes | Frozen root CI pytest argument selection from `.github/workflows/ci.yml`, executed through `uv run --no-sync` after non-package root provisioning |
| `runtime` | RootRegressionRuntime | yes | Exact Python version, uv version, OS, and architecture bound to the segment; contains no executable path |
| `working_directory` | string | yes | Constant `.` using repository-relative POSIX notation |
| `captured_before_package_source` | boolean | yes | Constant true |
| `captured_at` | RFC 3339 timestamp | yes | UTC capture time |
| `exit_code` | integer | yes | Exact process exit code, including nonzero baseline |
| `normalized_failures` | unique string array | yes | Sorted pytest node IDs after volatile path/duration normalization |
| `normalized_collection_errors` | unique string array | yes | Sorted collection module/error identities |
| `output` | RootRegressionOutputMetadata | yes | Metadata for the captured combined output |

`RootRegressionOutputMetadata` contains non-negative `byte_count`, positive or
zero `line_count`, and lowercase 64-character `sha256`. Raw output exists only
in memory or an external temporary file while normalized identities and metadata
are derived, then is deleted. No capture path, baseline object, metadata payload,
or raw output is stored in the repository. If orchestrator continuity cannot be
retained safely, baseline recapture before source edits is mandatory; otherwise
the implementation blocks.

`RootRegressionRuntime` is a closed object with non-empty `python_version`
(Python 3.12 or later), `uv_version`, `os`, and `architecture`. The absolute
interpreter path remains only in owner-only session state and is never placed in
the baseline object or repository.

The post-implementation comparison reuses the same normalizer and exact command.
Existing baseline failures are non-blocking. Any normalized failure or
collection-error identity present after implementation but absent from the
baseline is blocking. Command drift, a missing baseline, or unparseable output
is also blocking. This behavioral comparison does not substitute for protected-
path SHA-256 and immediate in-memory raw Git-diff equality.

This local comparison attributes newly introduced failures only. It is not a
merge-readiness signal and does not waive the constitution: the actual
pull-request lint, unit, and integration jobs must all be green before merge.

## Package Import Boundary

`tools/specify-cli` is a standalone src-layout distribution. Its tests load the
project through `tools/specify-cli/tests/conftest.py`, which prepends only the
package-local `src` directory. Production source MUST NOT import root `apps` or
`packages`; a package-local AST/import-boundary test enforces this rule.

Root mypy, coverage, and import-linter scopes remain unchanged and exclude
`tools`. Root CI Ruff command arguments also select only `apps tests packages`,
but root `ruff.toml` includes `tools/**/*.py` and unscoped pre-commit Ruff and
Ruff-format hooks cover package files. Package-local Ruff settings therefore
match line length 120, Python 3.12, and E/F/I/UP, and package code passes both
package-local and repository pre-commit Ruff semantics. Package-local strict
mypy, branch coverage with at least 90% line coverage, and AST boundary gates
provide equivalent coverage for the root gates that truly exclude `tools`.

## Relationships

```text
InstalledSourceRecord --0..*-->
                                ExtensionListEntry
CatalogSourceRecord   --0..*-->

ExtensionListEntry --1--> HealthAssessment --0..*--> Diagnostic
InstalledSourceRecord --0..1--> ActivationEvidence
ExtensionListResult --0..*--> ExtensionListEntry
ExtensionListResult --0..*--> Diagnostic (warnings)
```

## Reconciliation Rules

1. Normalize registry and physical observations by physical source identity.
   Coalesce same-source observations with the same valid stable ID into one
   installed source record while retaining both observations as evidence.
2. Convert contradictory valid same-source IDs into one invalid
   `local-identity-conflict` record with no authoritative stable ID.
3. Group coalesced valid installed records by exact `stable_id`; only distinct
   normalized physical sources in one group form an installed conflict.
4. Emit one normalized identifier-less candidate for each source occurrence,
   retaining that occurrence's canonical source evidence without grouping it.
5. Group valid catalog records by exact `stable_id` without discarding records
   from lower-priority catalogs.
6. Join installed and catalog groups only by exact stable ID.
7. Consolidate staged identifier-less candidates sharing the same normalized
   source identity into one invalid `duplicate-fallback-source` conflict entry
   retaining every contributing occurrence as evidence. A normalized source
   identity represented by one occurrence remains one invalid non-conflict entry
   because its stable ID is missing. Distinct normalized source identities remain
   separate even when display names collide.
8. Mark catalog groups with more than one source record as conflicts and list
   every differing field and every distinct reported version.
9. Order catalog candidates by ascending numeric priority, case-folded catalog
   name, raw catalog name, normalized record SHA-256, then source ordinal only for
   byte-identical records. Use the first candidate for preferred catalog fields
   without deleting any evidence.
10. If duplicate catalog `install_allowed` values disagree, project false.
11. Prefer installed descriptive fields for a combined row; set its source kind
    to `combined` and retain both local source locations and catalog sources.
12. Catalog-only non-conflict rows are healthy after schema validation, have
    null activation and enablement, and normalize missing capability counts to
    zero. Catalog conflicts are invalid with diagnostics.
13. Sort rows by case-folded display name, then stable ID or fallback identity,
    then raw display name and identity.

## Activation Derivation

For a single healthy installed record:

```text
enabled=false                                        -> disabled
enabled=true + recorded activation failure          -> activation-failed
enabled=true + recorded success                      -> active
enabled=true + valid legacy active-runtime evidence -> active
enabled=true + no conclusive evidence                -> inactive
```

For a duplicate installed group:

```text
all records disabled -> disabled
any recorded failure -> activation-failed
otherwise            -> inactive (conflict prevents claiming active)
```

Metadata health and activation are independent. A record can, for example, be
`activation-failed` and `invalid`, or `disabled` and `healthy`. The projected
`activation_diagnostic` is the non-empty reason for `activation-failed` and is
null for `disabled`, `inactive`, `active`, and null activation states; it is not
stored in or inferred from `health.diagnostics`.

## State Transitions

The list projection is stateless and read-only. It does not own activation
transitions. Each invocation derives a display state from the current registry
and manifest evidence using the precedence above; no state file is changed.

## Validation Invariants

- A healthy installed entry has a non-null stable ID and no diagnostics.
- Registry and physical observations of one normalized source and one valid ID
   produce one installed source record retaining both observations as evidence.
- Contradictory valid IDs on one normalized source produce one invalid local
   identity-conflict record and never multiple healthy rows.
- Duplicate installed-ID conflicts require at least two distinct normalized
   physical sources after coalescence.
- An invalid entry has at least one diagnostic reason.
- An entry with a null stable ID is invalid and has at least one metadata-health
   diagnostic; its activation diagnostic remains independently derived.
- A fallback identity and stable ID are mutually exclusive.
- A fallback-identity record never contains catalog sources or available
  versions through reconciliation.
- Catalog-only entries have null activation and enablement fields.
- Local-only entries have source kind `local`, at least one local evidence item,
   no catalog evidence, and null `install_allowed`.
- Catalog-only entries have source kind `catalog`, at least one catalog evidence
   item, no local evidence, and boolean `install_allowed`.
- Reconciled entries have source kind `combined`, at least one evidence item of
   each kind, and both non-empty source-location arrays.
- Every installed entry has exactly one activation state.
- `activation-failed` has a non-empty `activation_diagnostic`; every other or
   null activation state has a null `activation_diagnostic`.
- `conflict=true` implies non-empty conflict reasons, invalid health, non-empty
   diagnostics, and at least two retained evidence items.
- `conflict=false` implies an empty conflict-reason array; invalid non-conflict
   records remain permitted when validation diagnostics exist.
- A healthy health assessment has no diagnostics; an invalid assessment has at
   least one diagnostic.
- `available_versions`, `source_locations`, `catalog_sources`, diagnostics, and
  conflict reasons contain no duplicates and have deterministic ordering.
- Usability evidence contains exactly 20 included unique eligible adult
   participants: exactly 10 novice and exactly 10 experienced, all monthly CLI
   users with no prior feature or fixture exposure.
   Schema-valid, semantically consistent evidence may record any derived SC-001
   and SC-006 count from 0 through 20. The validator reports SC-001 passed only
   when the derived success count is at least 19 and SC-006 passed only when the
   derived clear count is at least 18; these are outcome thresholds, not
   evidence-validity conditions.
   Exclusions occur only before exposure for
   `documented-technical-interruption` or
   `required-accommodation-unavailable` and identify a distinct same-stratum
   replacement; unavailable accommodations are recorded for the latter, and
   post-exposure outcomes are included. Aggregate counts are derived from
   participant records, every included participant has exactly one allocation
   record matching deterministic recomputation, and every requested
   accommodation is provided without changing the measured task. Every
   participant records both SC-006 prohibited-action booleans, and only a rating
   of 4 or 5 with both values false contributes to `sc_006_clear_count`.
- Catalog configuration contains at most 8 sources; after schema validation, a
   semantic validator rejects duplicate catalog names before any source access;
   and each source contains at most 1,000 records.
- Local and decoded remote source content never exceeds 1,048,576 bytes before
   parsing, and every source stage completes within one monotonic 5-second budget.
- A catalog source contributes zero records before complete schema validation.
- Any configured catalog source failure yields zero catalog-contributed rows
   from every source for that invocation.
- A null project root yields zero installed and catalog rows without attempting
   catalog configuration discovery; every scope remains a successful empty
   result.
- A root regression baseline may have a nonzero exit code, but its normalized
   failure and collection-error sets are sorted, unique, and compared against
   the exact same post-implementation selection.
