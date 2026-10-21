# Implementation Plan: AMA-Local Extension List CLI

**Branch**: `001-extension-list` | **Date**: 2026-09-21 | **Spec**: `specs/001-extension-list/spec.md`  
**Input**: Clarified specification and authoritative design artifacts under `specs/001-extension-list/`

## Summary

Implement an independently packageable Spec Kit-compatible extension inventory
CLI inside this AMA repository at `tools/specify-cli`. It exposes only
`ama-specify` and `python -m specify_cli`; it never imports, edits, replaces, or
shadows an upstream `specify` installation or another checkout.

The default view lists installed extensions from registry and physical manifest
observations. `--available` lists validated project catalogs, and `--all`
reconciles installed and catalog records by exact stable identifier. The design
retains malformed local records, derives activation separately from metadata
health, coalesces multiple observations of one physical installation, reports
true identity conflicts, preserves deterministic source evidence, and falls
back atomically to installed inventory when any catalog source fails.

Implementation is test-first and preserves the existing dirty worktree. Three
standard-library bootstrap executions prove the protected-state module and the
dispatcher/root-regression implementation: protected-state green, dispatcher
expected red, then the byte-identical dispatcher self-check green. After those
explicit exceptions, every executable local operation
runs through a peer-authenticated `local-synthetic` daemon with immediate
pre/post protection and an owner-only ephemeral hash-chained journal. It needs
no Azure VM or Azure resource and accepts synthetic data only. Raw Git diffs and
process output are ephemeral; repository files retain only source, schemas,
tests, and docs, never runtime evidence or red-test output.

The existing CI workflow receives one sovereign `specify-cli-quality` job on a
pre-registered AU Azure Linux runner. Actual cross-platform and human-study
evidence remains external and pending: it is collected only into authorized
AU-resident stores with managed identity, private networking, pseudonymous
closed-coded review, and
Privacy Act controls.

## Technical Context

**Language/Version**: Python 3.12 or later; uv `>=0.11,<1`  
**Primary Dependencies**: Typer `>=0.12,<1`, Rich `>=13,<15`, PyYAML `>=6,<7`, Requests `>=2.32,<3`, jsonschema `>=4.23,<5`, rfc8785 `>=0.1.4,<1`, cryptography `>=44,<47`, azure-identity `>=1.19,<2`, azure-storage-blob `>=12.24,<13`, azure-mgmt-resource `>=23.1,<24`, azure-mgmt-authorization `>=4,<5`, azure-keyvault-keys `>=4.10,<5`, Hatchling `>=1.27,<2`; Azure/HTTP/schema modules are lazy daemon-side imports and never enter the cold installed-only client  
**Storage**: No runtime evidence in this repository; local-synthetic development uses owner-only local temporary storage and an ephemeral journal; sovereign validation uses encrypted AU VM storage and an immutable private AU Azure Blob ledger; external platform and study evidence exists only in authorized Australian Azure stores
**Testing**: pytest, at least 90% branch-aware line coverage, strict mypy, Ruff, strict JSON Schema Draft 2020-12 compilation, contract fixtures, subprocess and clean-wheel tests, fake clocks/processes/transports, AST import-boundary tests; shared root/package tests use only pytest APIs compatible across `>=8,<10`, while package metadata pins `>=8,<9`  
**Target Platform**: Local Windows and Linux; external validation on standalone Azure Windows x64 and Ubuntu x64 VMs in `australiaeast` or `australiasoutheast`  
**Project Type**: Standalone src-layout CLI package inside the AMA monorepo  
**Performance Goals**: Installed-only JSON over 100 pre-materialized records through one pre-started verified daemon, with feature/public transport denied but pinned private AU audit allowed; 3 warmups and 30 cold client processes including handshake and both ledger appends, nearest-rank P95 at rank 29 no greater than 2.000 seconds  
**Constraints**: Read-only command; local development is synthetic-only through a local daemon and may use the configured HTTPS package proxy; normal non-synthetic, qualifying evidence, CI release, and external validation are sovereign-daemon-only with offline AU-cache packaging and private AU Blob catalogs; exact dirty-state preservation; no runtime evidence in repo; no external checkout; no command collision; no commits/pushes; lazy installed-only imports; at most 8 catalog sources, 1,000 records per source, 5 seconds per source, 5 HTTPS redirects, and 1 MiB decoded content  
**Scale/Scope**: Three views, two output modes, two entry points, four activation states, two health states, nine current schemas, two planned ephemeral-evidence schemas, one immutable AU audit ledger, one CI quality job, one fake-tested external operator script

## Constitution Check

| Requirement | Status | Plan response |
| --- | --- | --- |
| Human authorization | Pass | Listing is read-only. Installation, activation, repair, enablement, disablement, and removal remain out of scope. |
| Australian data sovereignty | Pass | Local-synthetic fixtures and the owner-only ephemeral journal contain only synthetic, non-regulated development data and are logically deleted; they are not operator audit or evidence. Repository and CI retain no runtime evidence payload. All real operator actions, runtime audit, platform evidence, and participant evidence remain in authorized AU Azure stores. |
| Privacy by design | Pass | Raw output/diffs are ephemeral; synthetic fixtures contain fake data; participant evidence uses pseudonyms, consent, separation, least privilege, AU storage, audit, retention, deletion, withdrawal, and incident controls. |
| Graceful degradation | Pass | Any catalog source failure discards all catalog rows but preserves complete installed rows and one warning. |
| Accessibility | Pass | Exact text labels and states survive 80x24, 40x12, color-disabled, and redirected modes with no pager or input. |
| Automated PR gates | Pass, execution required | CI gains `specify-cli-quality`; package lint/type/test/coverage/build/install/smokes run on a sovereign AU runner. Actual PR gates must be green before merge. |
| Auditability | Pass | Local-synthetic development writes the same closed two-phase records to an ephemeral owner-only journal; sovereign actions write them to the immutable AU ledger. Local journals are not evidence. |
| Interoperability (non-negotiable #4) | Not applicable | This read-only developer CLI exposes no agent or emergency-management API and does not alter CAP, EDXL, GeoJSON, OpenAPI, or integration surfaces. |
| Lessons management quality gate | Not applicable | The feature performs no incident or exercise workflow and does not change the platform's lessons capture, analysis, or integration capabilities. |
| Azure infrastructure governance | Pass, external dependency | This feature provisions no Azure resource; sovereign runner, network, identity, role, and Blob prerequisites remain externally governed and fail-closed. |

No constitutional exception is requested. Local completion is not merge
readiness and cannot imply external platform or human-study completion.
The local-synthetic daemon is development/test tooling and is not deployed
infrastructure. Every deployed production component and every non-synthetic
runtime dependency remains Azure-hosted under the sovereign controls above.

**Execution Readiness**: Local development is ready after the three bootstrap
self-check executions and `--start-session --execution-mode local-synthetic`.
Before T001, environment provisioning requires uv `>=0.11,<1` and one root
`uv sync --locked --extra dev --no-install-project` using only the configured
HTTPS proxy or existing cache, so root pytest is available without building the
declared root project, which has no buildable package target. Root guarded children then use `uv run --no-sync`.
It also requires Python 3.12+, Git, owner-only local IPC/temp storage, and synthetic fixtures, but no
Azure VM or Azure resource. Sovereign validation/release remains
conditional on the signed control-plane preflight covering the immutable ledger,
external coordinator, standalone AU VM/encrypted volume, offline AU cache,
private stores, managed identities, private endpoints/DNS, role enumeration,
Key Vault, and reviewer/study stores.

## Architecture

```text
ama-specify / python -m specify_cli
     | thin client / routing UUID
     v
 peer-authenticated IPC boundary
     |
     v
 mode-bound peer-authenticated daemon
 local-synthetic: owner-only temp + ephemeral journal
 sovereign: AU encrypted volume + immutable AU audit append
     |
     v
   Typer stream/option boundary
     |
     v
    ancestor-only project discovery
    /                    \
   v                      v
registry + manifests        lazy catalog collector
   |                  local / verified private AU Blob
   +---------+----------+
       v
  normalize, coalesce, hash evidence
       |
       v
   deterministic reconciliation
       |
       v
     immutable projection
      /             \
     v               v
  buffered text    sole JSON serializer
```

### Installed Inventory

Project discovery walks ancestors only for `.specify/extensions`; no match is a
valid empty context. Registry and physical observations resolving to the same
normalized physical source and valid stable ID coalesce before grouping.
Registry state and manifest metadata combine while both observations remain
evidence. Contradictory valid IDs at one physical source create one invalid
identity-conflict row. Only distinct physical sources sharing one valid ID form
a duplicate-installed conflict. Identifier-less rows use normalized source
fallback identity, remain invalid, and never catalog-match.

### Catalog Collection

Catalog code is imported only for available/all views with a discovered root.
Configuration is schema-validated before semantic duplicate-name rejection.
Each source has one absolute five-second monotonic deadline. Local reads enforce
project containment, pre-stat size, and a 1,048,577-byte growth-race read.
Production remote catalogs are private AU Azure Blob URLs accompanied by storage
ARM resource ID and container scope. Managed identity verifies AU location,
disabled public access, deny-by-default rules, approved private endpoint,
host/resource match, private-only DNS, and exact container-scoped Blob Data
Reader with no broader data-plane role before retrieval. Tests may inject fake
HTTPS transports. Remote reads use a module-level picklable worker under spawn, HTTPS-only redirect
revalidation, remaining-budget timeouts, decoded-body bounds, and deterministic
process/queue cleanup. Any source violation discards all catalog rows.

Catalog records exist only after complete source validation. Non-null versions
are non-empty; null/omitted versions normalize to `unknown`. Duplicate candidates
sort by priority, case-folded then raw catalog name, normalized record SHA-256, and
source ordinal only for byte-identical ties. Output source evidence retains only
kind, source-identity SHA-256, ordinal, and record SHA-256; raw source identities, normalized records,
alternate descriptions, and author values are not emitted.

### Output Contract

Human rows/empty states use stdout. Human warnings/runtime errors use stderr.
Human usage errors emit Typer usage to stderr and exit 2. JSON usage errors
suppress Typer prose, leave stdout empty, emit one compact JSON error plus
newline to stderr, and exit 2. Explicit help takes precedence over JSON, emits
human help to stdout, leaves stderr empty, and exits 0. Runtime output is
buffered; only documented catalog fallback can emit successful rows after a
catalog failure.

At 80x24 and 40x12, color-disabled and redirected, each record appears once;
labels `Installed`, `Activation`, `Health`, `Commands`, and `Hooks` remain;
disabled/invalid/conflict remain literal; normalized output has no ANSI escapes;
wrapping preserves label/value order; and no pager or input occurs.

## Repository Safety And CI

Only the protected-state self-check and the dispatcher/root-regression
self-check red/green pair execute before the dispatcher is proven.
`--start-session --execution-mode local-synthetic` then verifies owner-only
local temporary storage, synthetic-data policy, network denial, and local IPC
before launching a long-lived custodian daemon. Sovereign session startup
additionally verifies standalone Azure VM IMDS, AU location, OS/architecture,
encrypted ephemeral storage, immutable ledger, and owner-only permissions.
Afterward,
complete canonical commands run through:

```text
python scripts/spec001/run_local_gates.py -- <command> <arguments...>
```

Dispatcher-owned modes are allowed only when they connect to the same daemon and
internally perform the same immediate pre/post protection. Windows uses a named
pipe restricted to current SID and SYSTEM. Linux uses an owner-only Unix socket
with mode 0600 and `SO_PEERCRED` UID verification. The UUID is routing metadata,
not a credential; daemon loss blocks continuation.

Post-start edits and decisions use explicit `--begin-action` and
`--complete-action` dispatcher operations. Begin appends the intent and opens
the sole active action before mutation; complete verifies the same task, action,
target identifier, and pre-state, computes post-state, and appends the linked
result before another action. A multi-file task performs one complete serialized
transaction per file with the same task ID and each file's distinct target;
transactions never span files. Child commands and runtime list requests use the
same transaction internally. The closed target descriptor and its RFC 8785
digest are defined by `agent-action-audit.schema.json`; attempts to bypass an
active intent, overlap actions, or change target identity freeze the session.

The CI quality job and every real external collect/finalize operation use this
post-implementation lifecycle: run protected-state green and one dispatcher/
root-regression self-check green; complete sovereign preflight; start an
IMDS-verified AU daemon;
route every payload-producing child through its peer-authenticated IPC; and
finalize. Direct package-gate or external-mode invocation fails before payload
creation. Custody loss after the first feature source/workflow edit is terminal;
recapture is allowed only before any such edit in a new verified AU session.

That terminal rule applies only to sovereign custody. Local-synthetic custody
loss ends one non-evidentiary segment; development may start a new local segment
from the current worktree, record the discontinuity, and capture a new local
baseline that can never be promoted to release or sovereign evidence.

A latent local bootstrap defect discovered after T008 uses an explicit
incomplete-segment boundary: append the incomplete final intent/result pair,
delete the local journal and temporary payloads, repair the bootstrap file only
as pre-journal repository/tooling work, rerun both bootstrap self-checks green
without an expected red, then start a new explicitly discontinuous non-
evidentiary segment from the repaired worktree. The new
segment discloses lost pre-repair attribution and reruns the full final root
selection. Segments cannot be resumed or combined; sovereign post-edit defects
remain terminal.

Normal non-synthetic CLI entry points are thin daemon clients connected to a
verified sovereign session. Local-synthetic entry points process only synthetic
fixtures and reject production catalogs, qualifying evidence producers, and real
external modes. Local dependency bootstrap may use the configured HTTPS package
proxy; sovereign sync/build/install uses `UV_OFFLINE=1` against an authorized
pre-seeded AU cache.

Every guarded `uv run` child receives dispatcher-injected `UV_FROZEN=1` and is
rejected before launch if the value is absent or different, preventing implicit
root or package lockfile rewrites. T022 package-lock generation is the deliberate
exception because it uses `uv sync`, not `uv run`; T023 proves the generated
lock with `--locked`. Every package-project `uv run` selects `--extra dev` for
Ruff, mypy, and pytest. Guarded mypy commands set `MYPY_CACHE_DIR` beneath the
owner-only external temporary root, and repository `.mypy_cache` is mutation-
checked recursively as absent or byte-identical. Every guarded pytest child
receives `PYTEST_ADDOPTS=-pno:cacheprovider`; repository root/package
`.pytest_cache` trees remain absent or recursively byte-identical.

The wheel packages `daemon.py`, `daemon_client.py`, and `daemon_protocol.py`.
Client discovery is limited to the current-SID named pipe on Windows or
`$XDG_RUNTIME_DIR/ama-specify/daemon.sock` on Linux when that directory is
owner-owned, non-symlink, and mode 0700. If unset, Linux uses the owner-created,
non-symlink mode-0700 `${TMPDIR:-/tmp}/ama-specify-<uid>/daemon.sock` and rejects
ownership/mode mismatch.
An owner-only startup lock serializes launch of `python -m specify_cli.daemon`.
The versioned handshake binds protocol version, peer identity, session UUID,
execution mode, repository digest, temporary-root policy, and audit head.
Sovereign handshakes additionally bind AU IMDS/encryption/immutable-ledger state.
A mode or state mismatch fails closed; `cli.py` owns parsing/rendering only and
has no in-process inventory/catalog fallback.
Windows pipe/DACL and Linux socket/peer/lock implementation uses only the Python
standard library plus `ctypes` bindings to `kernel32`/`advapi32`; no extra IPC
or OS-security dependency is introduced.

The protected manifest is:

```text
pyproject.toml
uv.lock
package.json
pnpm-workspace.yaml
azure.yaml
ruff.toml
.pre-commit-config.yaml
.github/workflows/ci.yml
apps/api/Dockerfile
apps/api/app/main.py
apps/agents/Dockerfile
apps/agents/dispatcher/__main__.py
apps/agents/communication/__main__.py
apps/agents/evacuation/__main__.py
apps/agents/maf_runtime/workflow/builder.py
apps/ingestion/Dockerfile
apps/ingestion/worker.py
apps/web/package.json
```

Each path records SHA-256 or `absent`. Raw staged/unstaged binary Git diff bytes
exist only in memory for exact pre/post comparison. Only digests and equality
results may be reported; raw bytes, Base64, absolute paths, secrets, query
values, raw exceptions, and environment values never enter artifacts or logs.
The one deliberate edit to `.github/workflows/ci.yml` adds the red-tested
`quality`-job changed-path output and the `specify-cli-quality` job. The output
is true only for `tools/specify-cli/**`, `scripts/spec001/**`, or
`specs/001-extension-list/**`; the sovereign job depends on it and is skipped
without requesting a runner for unrelated changes. The existing `quality`
checkout is updated to `fetch-depth: 0` so the event base/head diff is available;
shallow history is not accepted. Before editing, the daemon issues one session-bound,
path-specific transition permit with the exact pre-edit digest
and a 10-minute expiry. A separate accept operation proves every other protected
path and staged/unstaged diff streams over the frozen path set excluding the
permitted workflow path unchanged, checks the exact post-edit
digest, atomically updates only the workflow baseline, and invalidates the
permit before the identical green child command. Reuse, expiry, unrelated drift,
or digest mismatch blocks.

Every expected-red command uses one canonical complete guarded command string.
The identical green task repeats that exact string. A single sanitizer converts
ephemeral output into exit status, normalized test identities, category/code,
byte/line counts, SHA-256, and a bounded secret/path-scrubbed summary. Raw output
is deleted after validation from owner-only local temporary storage in local-
synthetic mode or the verified encrypted AU ephemeral volume in sovereign mode; no
claim of physical secure erasure is made. No red `.txt` artifact is retained.

Root regression keeps exact pytest arguments but redirects `COVERAGE_FILE`,
`COVERAGE_RCFILE`, XML output, and process output to an external temporary
directory. The generated owner-only external rcfile reproduces root
`[tool.coverage.run]` (`source`, `branch`, and `omit`) and
`[tool.coverage.report]` settings and adds
`[xml] output = <external-temp>/root-coverage.xml`, which is the only mechanism
that redirects the frozen `--cov-report=xml` argument. Repository `.coverage*`
and `coverage.xml` are preflighted and mutation-checked as absent or byte-
identical. The baseline is an ephemeral in-memory/external-temp object
held for the implementation session; if safe continuity is unavailable, the
gate blocks. It stores only normalized identities and metadata and is deleted
after final comparison.

T008 captures the actual normalized failure and collection-error sets from the
provisioned root environment. Every captured identity is known-pre-existing only
for that segment's local attribution. Post-implementation sets may remove a
captured identity, but any identity absent from the T008 baseline blocks. No
literal count or path is assumed, and the baseline is never merge readiness.

At pre-T001 provisioning, owner-only session state binds the exact Python
executable, Python/uv versions, OS, and architecture. Every gate in the segment
uses that same binding. Results are workstation-, architecture-, interpreter-,
and segment-specific and cannot become cross-platform or sovereign evidence.

Package `microsoft-package-feed-proxy` metadata is package-owned and self-
contained. Any root index metadata is advisory only and may be uncommitted user
content; implementation does not depend on, stage, or commit it.

The `specify-cli-quality` job runs on labels `self-hosted`,
`ama-au-sovereign`, `azure-au`, `linux`, `x64`, verifies IMDS location before
package work, has `timeout-minutes: 30`, clears inherited `PIP_INDEX_URL` and
`UV_DEFAULT_INDEX`, sets `PIP_NO_INDEX=1` and `UV_OFFLINE=1`, rejects installer
egress, uses synthetic fixtures only, and runs locked sync, Ruff,
format-check, strict mypy, package pytest/coverage, wheel build, clean install,
and both entry-point smokes. It uploads no runtime evidence or inventory payload.
It collects branch data and separately parses machine-readable coverage output
from owner-only external-temp `package-coverage.xml` to require line coverage at
least 90.00%; `COVERAGE_FILE`, `COVERAGE_RCFILE`, and XML output all remain in
that directory, and repository coverage paths are mutation-checked. The pytest
fail-under value alone is not treated as independent line-coverage proof.

Within `scripts/spec001/local_gate_sequence.py`, named boundaries enforce
FR-040: `assemble_package_commands` constructs commands without execution,
`parse_package_coverage` evaluates external XML without running gates, and
`run_local_gate_sequence` owns final dependency ordering/execution without
defining root guard semantics. `scripts/spec001/root_regression.py` remains the
sole owner of baseline capture and comparison; T074 and T128 verify this split.

## Evidence And Privacy

Nine current strict schemas exist before implementation:

The existing `usability-evidence.schema.json` HTTPS `$id` is intentionally
retained as its established contract identity while the other contracts use
`urn:ama:specify:contracts:*`; strict validation requires all IDs to remain
unique and non-empty, so cosmetic normalization is not an implementation edit.

1. `agent-action-audit.schema.json`
2. `catalog-config.schema.json`
3. `catalog-source.schema.json`
4. `extension-list.schema.json`
5. `external-validation-status.schema.json`
6. `implementation-prerequisite-attestation.schema.json`
7. `platform-evidence.schema.json`
8. `root-regression-baseline.schema.json`
9. `usability-evidence.schema.json`

Implementation adds only strict `read-only-evidence.schema.json` and
`performance-evidence.schema.json`; these validate ephemeral objects and do not
authorize repository persistence. Computed/cross-record invariants are checked
by post-schema semantic validators.

The closed read-only object uses the exact `ReadOnlyEvidence` fields in
`data-model.md`: invocation identity/mode/outcome, three before/after SHA-256
pairs for source/protected/coverage state, verified peer/AU/encrypted-storage
flags, completed audit transaction, logical raw-output deletion, and false
repository persistence. Semantics require each digest pair equal and require
success exactly when exit code is zero. Read-only and performance evidence also
bind to `execution_mode=sovereign`, `audit_sink=immutable-au`, the sovereign
session UUID, signed preflight digest, live VM resource ID, and immutable audit
intent event ID/digest; semantic validation cross-checks all bindings.

### Action Audit Profiles

Every action is a two-record transaction: an `intent`/`started`
record appends before execution, and a linked `result` record appends before the
action is reported complete or another action starts. If result append fails
after execution, the session freezes and retries only that result append.
Records use pseudonymous principal IDs, task/action/rationale codes, outcomes,
closed target descriptors, target digests, and hash-chain digests only.
Identifier and kind-specific state objects follow the exact version-1 algorithm
in the specification. Every state digest hashes RFC 8785 canonical JSON bytes;
every target digest hashes the exact schema-valid target object. Intent has a
non-null pre-state and null post-state; result retains the intent identifier and
pre-state and has a non-null post-state, repeating pre-state when unchanged.
`event_digest` is SHA-256 over RFC
8785 canonical JSON with itself omitted; `previous_event_digest` forms the
chain. The closed
schema-versioned rationale enum is the rationale registry. Sink failure blocks
or freezes the lifecycle. Local-synthetic records use
`execution_mode=local-synthetic`, `audit_sink=ephemeral-local`, and an owner-only
temporary journal deleted at finalization; the closed bootstrap set is its only
pre-journal exception and becomes genesis hashes. Sovereign records use
`execution_mode=sovereign`, `audit_sink=immutable-au`, and the external
coordinator before daemon startup. The daemon assumes ownership after session
start in either profile.

Every record in a segment repeats `session_manifest_digest`, the SHA-256 of the
RFC 8785 canonical protected/bootstrap manifest captured at segment start. The
value is constant across the segment and chain validation rejects a change.
The partition is `spec001-extension-list/<session_id>` and holds at most 49,000
records. Ordinary actions stop after sequence 48,998 so the final intent/result
pair remains reserved for session finalization. Sessions never split pairs or
roll over; a new session receives a new partition without continuity claims.

The local journal is owner-only NDJSON. Under `msvcrt.locking` on Windows or
`fcntl.flock` on Linux, the daemon validates the complete chain/head, uses the
pre-append byte length as `append_position_bytes`, writes one RFC 8785 canonical
JSON line plus LF, flushes, and `fsync`s before acknowledgement. Local data-
bearing commands require `SPEC001_TEST_MODE=synthetic` and either no project root
or an owner-only session-temp fixture with a closed marker binding fixture ID and
the canonical sorted `{path,sha256}` seed-manifest digest; repository/live roots,
symlinks, and marker mismatch fail before inventory access. Session lifecycle
and non-data-bearing guarded commands do not require a fixture marker and perform
no project discovery.

### Sovereign Prerequisite Attestation

Before sovereign validation/release, `--preflight-prerequisites
--execution-mode sovereign` validates the closed
`implementation-prerequisite-attestation.schema.json` artifact
`{claims, compact_jws, attestation_digest, replay_protection}` and its compact
ES256 JWS using an owner-only external AU trust bundle. The dispatcher first
computes the repository digest from a sorted RFC 8785 manifest covering the
protected paths, bootstrap set, constitution, and all regular non-symlink
feature files, then generates a challenge UUID and 256-bit nonce and sends the
closed request to the pinned private AU control plane. It accepts only one
compact JWS response and requires the decoded payload to equal the schema-valid
`claims` object field-for-field.
It verifies pinned key, issuer/audience, request challenge/nonce/time, unique
JTI, repository digest/branch, 10-minute
maximum lifetime, 2-minute skew, audit ledger, AU VM/encrypted IPC, offline AU
cache, and every private dependency/control-plane/Key Vault claim. Acceptance
atomically creates the immutable AU `preflight-jti/<jti>` marker first; an
existing marker rejects replay. File-set races, symlinks, unreadable paths,
claim/JWS divergence, failure, or ambiguity block; the feature provisions
nothing. Local-synthetic startup neither requests nor fabricates this artifact.

### Local Validation

Qualifying read-only and performance objects live only in memory or on the
verified encrypted ephemeral volume of the attested AU Azure VM, are
schema/semantic validated, and are deleted. Local-synthetic development may run
shape, semantic, and producer tests with fake objects but emits no qualifying
payload or success claim. Performance semantics sort exactly 30
durations, select one-based rank 29, verify reported P95 and threshold 2.000,
and derive pass/fail.

The frozen dispatcher remains a generic audited command/session boundary after
T009. The read-only producer is implemented in package-owned `evidence.py`, and
final dependency assembly is implemented in non-bootstrap
`local_gate_sequence.py`; both are invoked through the dispatcher without
modifying any frozen bootstrap file.

### Human Study

Synthetic fixtures use fake IDs/data. Actual participant evidence exists only
in an authorized AU store. The study provides Privacy Act notice and records
explicit consent before collection, limits purpose to SC-001/SC-006, uses random
pseudonyms independent of names/contact records, prohibits direct identifiers
and free-text PII, separates the re-identification key/recruitment records from
evidence, grants least-privilege named study-team access, retains immutable
access audit, encrypts in transit/at rest, honors withdrawal before
de-identification/aggregation, applies incident handling, and deletes evidence
within 90 days after review unless an approved legal hold exists. Accommodation
details use generic category codes only, never medical details.

Eligibility, deterministic allocation, mandatory accommodation/replacement,
SC-001, and SC-006 semantics remain as defined in the specification. Valid
evidence may record a failed study; lifecycle completion does not imply outcome
success.

### Sovereign External Platform Validation

The checked-in operator script supports `collect` and `finalize`, tested only
with fakes locally. Before any real read/write, managed identity queries ARM and
verifies the standalone VM and target storage account, AU location,
`publicNetworkAccess=Disabled`, default network action Deny, approved private
endpoint, Blob-host/resource match, private-only DNS resolution, and exact
Storage Blob Data Contributor assignment at container scope. It also validates
an AU-resident security/compliance pre-write attestation covering resource,
private endpoint, container scope, a pseudonymous reviewer identifier,
timestamp, role breadth, and digest.
The attestation is a compact ES256 JWS signed by an exact versioned Azure Key
Vault key and retrieved over private HTTPS with managed identity from an
allowlisted AU control plane. The reviewed package trust bundle pins exact
`kid` to public JWK, the control-plane `Microsoft.Web/sites` ARM resource ID,
and the signing Key Vault ARM resource ID. Before requesting an attestation,
managed identity verifies both resources are in an allowed AU region, public
network access is disabled, approved private endpoints and private DNS match the
pinned hosts, and the signing key is enabled and unexpired. Claims bind
issuer `ama-security-control-plane`, audience
`spec001-extension-list-prewrite`, validation session, a fresh 256-bit nonce,
unique JTI, storage/private-endpoint/container identifiers, VM principal, and
role breadth. Signature/key allowlist, 10-minute maximum lifetime, 2-minute
clock skew and nonce/session/resource equality are mandatory. The compact JWS is
retained in AU-only evidence and its SHA-256 is recorded. Every attested write,
including both fragment writes and final canonical publication, uses a distinct
fresh attestation/JTI/nonce and atomically creates its replay marker first. The
Blob container has a locked time-based immutability policy of at least one day.
Evidence retains marker URI, successful conditional creation, retention expiry,
and locked policy mode, so a Data Contributor cannot remove replay state during
the window. An existing marker rejects cross-process replay.

The trust bundle also pins one exact private HTTPS attestation endpoint and
managed-identity scope `api://ama-security-control-plane/.default`. The script
performs one no-redirect/no-retry JSON POST under a five-second total deadline.
The closed request binds feature, operation, session, fresh nonce, timestamp,
target blob, and repeated resource/scope/principal/role fields. The endpoint
cannot be overridden and must resolve privately. Only a 200 `application/jose`
response no larger than 16 KiB containing exactly `compact_jws` is accepted.
Any missing check fails before evidence access.

Authorization verification resolves the VM service principal and transitive
group memberships, enumerates active role assignments and PIM eligibility at
container, account, resource-group, subscription, and inherited management-
group scopes, resolves built-in/custom role definitions, and evaluates effective
DataActions minus NotDataActions. Catalog reads require exactly container-scoped
Blob Data Reader. Evidence writes require exactly container-scoped Blob Data
Contributor. Any other effective or eligible broader Blob write/delete grant,
custom-role ambiguity, unresolved ancestry/group/role, or enumeration failure
blocks.

Collect conditionally creates one fragment at:

```text
spec001-extension-list/<session>/fragments/<os>-<vm-id>.json
```

Finalize, in the AU environment, validates exactly one Windows and one Ubuntu
fragment for matching session/package/lock/script, records approved/rejected
review using only a pseudonymous reviewer identifier and closed reason code,
and conditionally creates:

```text
spec001-extension-list/<session>/final/platform-evidence.json
```

Both modes use managed identity, TLS/private endpoint, create-if-absent writes,
value-free terminal summaries, and no credential/SAS/local/repository payload.
This feature provisions none of the prerequisites and never executes real modes
during implementation.

External status remains prose/checklist state `pending-external`; the optional
status schema describes an in-memory minimized handoff object only and is never
instantiated in this repository.

## Project Structure

```text
tools/specify-cli/
├── README.md
├── pyproject.toml
├── uv.lock
├── src/specify_cli/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── daemon.py
│   ├── daemon_client.py
│   ├── daemon_protocol.py
│   ├── evidence.py
│   ├── azure_authorization.py
│   ├── trusted_attestation_keys.json
│   └── extensions/
│       ├── __init__.py
│       ├── models.py
│       ├── inventory.py
│       ├── catalogs.py
│       └── rendering.py
└── tests/
   ├── conftest.py
   ├── contract/test_evidence_schemas.py
   ├── fixtures/
   │   ├── installed_cases.py
   │   ├── problem_cases.py
   │   ├── catalog_local_cases.py
   │   ├── catalog_remote_cases.py
   │   ├── extensions/installed/performance-100/
   │   └── evidence/
   │       ├── platform-valid.json
   │       ├── usability-passing.json
   │       ├── usability-failed.json
   │       └── usability-template.json
   ├── test_ci_workflow.py
   ├── test_inventory.py
   ├── test_inventory_problems.py
   ├── test_catalogs.py
    ├── test_azure_authorization.py
   ├── test_catalog_network_limits.py
   ├── test_reconciliation.py
   ├── test_cli.py
   ├── test_cli_problems.py
   ├── test_cli_catalogs.py
   ├── test_contracts.py
   ├── test_import_boundaries.py
   ├── test_packaging.py
   ├── test_installed_performance.py
   ├── test_usability_evidence.py
   ├── test_external_platform_script.py
   ├── test_read_only_privacy.py
   ├── test_root_regression.py
   ├── test_root_coexistence.py
   ├── test_local_gate_sequence.py
   └── test_local_implementation_gate.py

scripts/spec001/
├── protected_state_selfcheck.py
├── dispatcher_selfcheck_cases.py
├── protected_state.py
├── root_regression.py
├── local_gate_sequence.py
├── benchmark_installed.py
├── run_external_platform_validation.py
└── run_local_gates.py

docs/specify/
├── extension-list.md
├── extension-list-usability-protocol.md
└── extension-list-validation-handoff.md

specs/001-extension-list/contracts/
├── read-only-evidence.schema.json
└── performance-evidence.schema.json

.github/workflows/ci.yml
```

No feature runtime evidence or red-output file is created under `artifacts/`.
`tools/specify-cli/tests/conftest.py` prepends only the package `src` directory
for product imports. Fixture builder modules remain non-package test assets and
are loaded by explicit file path with `importlib.util.spec_from_file_location`.

The closed pre-baseline bootstrap set is limited to
`scripts/spec001/protected_state_selfcheck.py`,
`scripts/spec001/dispatcher_selfcheck_cases.py`,
`scripts/spec001/protected_state.py`, `scripts/spec001/root_regression.py`, and
`scripts/spec001/run_local_gates.py`. Local-synthetic development treats these
as the sole pre-journal exception and records their hashes in the local session
genesis. Sovereign execution uses the external AU coordinator before daemon
startup. Session start hashes and freezes the files with the protected manifest;
no bootstrap file may change within that session. All package source, docs, new
schemas, tests, fixtures, and workflow edits occur only after baseline capture.

Sovereign prerequisites are not provisioned here: private immutable AU audit
ledger, external coordinator, standalone AU VM/encrypted ephemeral volume,
pre-seeded AU package cache, private AU catalog containers, managed identities,
private endpoints/DNS, control-plane/Key Vault resources, and reviewer/study
stores must already exist and pass fail-closed verification.

**Structure Decision**: Package-owned source/tests live under
`tools/specify-cli`; root safety/orchestration and the fake-tested external
operator script live under `scripts/spec001`; documentation lives under
`docs/specify`; contracts stay with the feature; the only root workflow edit is
the tested `specify-cli-quality` job.

## Implementation Phases

1. **Protected bootstrap and CI contract**: as the documented local pre-journal
  exception, author only the closed bootstrap set; run protected-state green, dispatcher/root-regression
  expected red, and the byte-identical dispatcher self-check green; then start
  a local-synthetic session, record bootstrap genesis, and freeze the local
  product baseline; observe canonical sanitized
  CI-contract red; deliberately add the quality job; establish post-edit
  protection; rerun exact command green.
2. **Root comparison and package contract under existing custody**: extend
  package-level contract coverage for the already red/green-proven frozen root
  implementation and compare against the baseline captured in Phase 1; do not
  recapture after CI/product edits; observe
  packaging red, add metadata/lock, and rerun the exact command green.
3. **Foundation and user stories**: implement projections, no-root behavior,
  installed listing, problem diagnosis, and bounded catalog views with exact
  paired red/green commands.
4. **Packaging/privacy/performance contracts**: define clean-wheel, import,
  read-only, command-sequence, and SC-002 checks without producers.
5. **Schema and semantic validators**: strict-test nine current schemas;
  observe missing two planned schemas red; add them; implement performance,
  usability, and external lifecycle semantics with exact paired commands.
6. **External script and producer contracts**: fake-test collect/finalize,
  qualifying evidence producers, and pre-write Azure verification; document
  human-study and sovereign handoffs. Local mode creates no qualifying evidence
  and executes no real external action.
7. **Final local gate**: execute package/root gates under protection, compare
  local baseline, validate fake objects, report sovereign gates pending, and
  perform no study, Blob write, review, PR, commit, or push.

After T134, a human performs a separate handoff outside the implementation
session: review the intended source/docs/schemas/tests/workflow changes including
`tools/specify-cli/uv.lock`, stage and commit them, push the branch, open the PR,
and run all required PR and sovereign gates. The local implementation agent does
none of those source-control actions.

T006 remains one red/green checkpoint because the dispatcher self-check proves
the interaction between its only two frozen implementation files. It executes
as two separately audited file substeps with no intervening executable action.
T033-T036 are serial and touch no more than two files each. T128 creates one
aggregate test file, while T134 is a terminal review/finalize command and
performs no repository mutation; their breadth does not create an unaudited
multi-file edit.
T071 creates one `records.json` seed containing 100 records in one audited file;
tests materialize the physical fixture tree on encrypted external temporary
storage before timing, so repository audit volume is exactly one transaction
and setup cost does not enter SC-002.

## Complexity Tracking

| Complexity | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Independent package | Avoids root dependency/entry-point collisions | Root integration would change application ownership and could shadow upstream tooling. |
| Spawned catalog worker | Bounds DNS and blocking transport stages | Requests timeouts cannot reliably interrupt platform DNS. |
| Protected dispatcher | Preserves a dirty worktree exactly | Git status or restoration cannot prove byte equality and risks user data. |
| Schema plus semantic validators | Enforces computed/cross-record rules | JSON Schema cannot recompute P95, digests, allocation, or aggregates. |
| AU external collect/finalize | Satisfies evidence sovereignty and review | Repository/GitHub persistence violates residency; placeholders fabricate completion. |
