# Phase 0 Research: Extension List

**Feature**: `001-extension-list`  
**Date**: 2026-09-21  
**Status**: Complete; no unresolved clarifications

## Decision 1: Own and package the CLI inside AMA

**Decision**: Create `tools/specify-cli` as an independent Python 3.12+
package. Its package-local metadata exposes
`ama-specify = "specify_cli.cli:app"` and uses bounded ranges: Typer `>=0.12,<1`,
Rich `>=13,<15`, PyYAML `>=6,<7`, Requests `>=2.32,<3`, jsonschema
`>=4.23,<5`, rfc8785 `>=0.1.4,<1`, cryptography `>=44,<47`,
azure-identity `>=1.19,<2`, azure-storage-blob `>=12.24,<13`,
azure-mgmt-resource `>=23.1,<24`, azure-mgmt-authorization `>=4,<5`,
azure-keyvault-keys `>=4.10,<5`, Hatchling `>=1.27,<2`, pytest `>=8,<9`, Ruff `>=0.8,<1`, mypy
`>=1.14,<2`, pytest-cov `>=6,<8`, types-PyYAML `>=6.0.12,<7`, and
types-requests `>=2.32,<3`. Runtime requirements remain in
`[project.dependencies]`; test, lint, typing, coverage, and stub requirements
are declared in `[project.optional-dependencies].dev`.
Azure, cryptography, Requests, and jsonschema imports are confined to lazy
daemon-side sovereign/catalog/evidence paths; the cold installed-only client
does not import them.
Windows named-pipe creation and current-SID+SYSTEM DACL construction use Python
standard-library `ctypes` bindings to `kernel32`/`advapi32`; Linux uses standard-
library Unix sockets, `SO_PEERCRED`, and `fcntl.flock`. No extra IPC/security
dependency is permitted.
Because package metadata declares a README, `tools/specify-cli/README.md` is
part of the package and describes the supported standalone subset.
Generate `tools/specify-cli/uv.lock` with package-local `uv sync` and retain it
for the eventual reviewed change set; no implementation step commits it;
CI uses exactly
`uv sync --project tools/specify-cli --extra dev --locked`.
Package metadata also declares its package-owned self-contained
`[[tool.uv.index]]` named `microsoft-package-feed-proxy` with URL
`https://packagefeedproxy.microsoft.io/pypi/simple`, plus package-scoped
`[tool.pytest.ini_options]` for `tests`, importlib mode, strict markers, branch
coverage, and the 90% line threshold. Local-synthetic dependency bootstrap may
use the configured HTTPS package proxy or an existing cache because no real or
regulated data is processed. Sovereign sync, build, and clean wheel installation
set and verify `UV_OFFLINE=1` and use only a pre-seeded cache produced by an
authorized AU mirror. Runtime tests deny production catalogs and unapproved
network access in both profiles.

Independent proof consists of `uv build`, installing the resulting wheel into
a new temporary environment outside the repository root, invoking the installed
`ama-specify` console script,
and invoking `python -m specify_cli`. Both smoke paths execute
`extension list --json` against a deterministic fixture.

The package is a Spec Kit-compatible standalone subset. It neither replaces nor
augments an upstream `specify` executable and deliberately uses a distinct
console-script name to prevent command shadowing.

**Rationale**: This provides an installable artifact and executable command
without changing the root AMA application or depending on another checkout.
Bounded ranges express compatibility intent while the lock makes CI resolution
reproducible.

**Alternatives considered**:

- Modify or import another Spec Kit checkout: rejected; AMA is authoritative.
- Add the command to the root disaster-response package: rejected; repository
  tooling must remain independently installable.
- Use only lower dependency bounds: rejected; unconstrained major upgrades can
  invalidate CLI and rendering contracts despite a passing historical lock.
- Permit sovereign dependency installation to contact a configured index:
  rejected; only local-synthetic bootstrap may use the configured proxy.

## Decision 2: Keep local and catalog collection separate and read-only

**Decision**: One adapter inventories `.specify/extensions/.registry` and
physical extension directories. A separate catalog adapter reads the optional
`.specify/extensions/catalogs.json`. Neither writes source state. Catalog
configuration contains at most 8 sources, and a validated source contains at
most 1,000 records.

**Rationale**: Separate adapters preserve useful local inventory when catalog
work fails and expose malformed, unregistered, or duplicate installations.
The explicit bounds cap total catalog reconciliation at 8,000 records.

**Alternatives considered**:

- Registry-only discovery: rejected because broken and legacy directories
  would disappear.
- Priority-wins collection: rejected because it destroys conflict evidence.
- Add a global catalog deadline: rejected; bounded source count plus the
  existing per-source deadline already bounds invocation work.

## Decision 3: Normalize source identity without broadening reconciliation

**Decision**: Normalize registry and physical observations before stable-ID
grouping. Observations resolving to the same normalized physical source and the
same valid stable ID coalesce into one installed source record that combines
registry state with manifest metadata and retains both observations as evidence.
Distinct normalized physical sources sharing a valid stable ID form a
duplicate-installed conflict. Same-source observations with contradictory valid
stable IDs form one invalid `local-identity-conflict` record and never two
healthy rows.

After coalescence, exact valid manifest IDs are the only
installed-to-catalog join key. Identifier-less installed observations use
canonical project-relative POSIX paths for display and a platform-aware
resolved-path comparison key for grouping. Dot segments, separator aliases,
resolvable symbolic links, and case aliases on case-insensitive platforms that
identify the same source consolidate into one invalid conflict row. Distinct
normalized sources remain separate even when names collide.

**Rationale**: This prevents both duplicate rows for one physical source and
false catalog matches based on names or directory labels. Absolute machine
paths never enter output.

**Alternatives considered**:

- Match by display or directory name: rejected because neither is stable or
  unique.
- Group by valid ID before physical-source coalescence: rejected because
  registry and manifest observations of one installation would become a false
  duplicate conflict.
- Keep every identifier-less observation separate: rejected because registry
  and physical discovery can observe the same source twice.
- Emit contradictory same-source IDs as separate rows: rejected because that
  would present an identity conflict as healthy installations.
- Merge equal names across different sources: rejected because that hides
  independent malformed installations.

## Decision 4: Separate health, activation, and catalog defaults

**Decision**: Installed activation remains exactly `disabled`, `inactive`,
`active`, or `activation-failed`; metadata health remains `healthy` or
`invalid`. Catalog-only records have no activation or enablement. After complete
source schema validation, a non-conflicted catalog-only row is `healthy`, and
missing command, template, script, and hook counts normalize to zero. Any
duplicate conflict is `invalid` with non-empty diagnostics.
An independent nullable `activation_diagnostic` projection is non-empty exactly
for `activation-failed` and null for every other or null activation state.

**Rationale**: Catalogs describe availability, not local activation. Schema
validation establishes catalog metadata health, while deterministic zero
normalization avoids nullable capability semantics.

**Alternatives considered**:

- Derive catalog activation: rejected because no installation exists.
- Leave missing counts null: rejected because consumers need stable numeric
  capability fields.
- Mark schema-valid catalog rows unknown: rejected because the health enum has
  no unknown state and validation is the health boundary.

## Decision 5: Enforce one monotonic five-second budget per source

**Decision**: Start an absolute monotonic deadline before each configured local
or remote source. A `remaining()` operation fails before returning zero and is
called before and after every potentially blocking or CPU stage. Local sources
are stat-checked before parsing and reject sizes over 1,048,576 bytes; a bounded
read of 1,048,577 bytes detects growth between stat and read. Local decode,
parse, and schema validation also consume the same deadline.

Remote processing propagates remaining budget to DNS/connection, every
redirect, streamed decoded-body reads, UTF-8 decoding, JSON parsing, and schema
validation. The transport is injected behind a `DeadlineTransport` contract.
A plain synchronous Requests adapter does not meet the contract because its
timeout cannot reliably interrupt a blocked platform DNS lookup. The production
adapter therefore runs the complete remote-source pipeline with
`multiprocessing.get_context("spawn")` on every platform. The spawned process
uses a module-level picklable worker target and is supervised by the parent's
monotonic deadline; the parent terminates and boundedly joins the worker on
expiry. Every success, source failure, and deadline path closes queues and
process resources. Inside the worker, remaining timeout is still passed to
Requests connection/read operations. Tests use fake clocks and stage fakes to
exhaust the budget deterministically at DNS, connect, redirect, stream-read,
decode, parse, and schema-validation boundaries, and deterministic process
fakes assert spawn selection, termination, join, and cleanup.

**Rationale**: Remaining-budget propagation prevents per-stage timeout reset,
and worker supervision provides an enforceable outer bound where synchronous
DNS cannot. The design does not claim a guarantee from Requests that Requests
cannot provide.

**Alternatives considered**:

- Use `requests.get(timeout=5)`: rejected because it resets or partitions stage
  timeouts and cannot guarantee DNS cancellation.
- Use elapsed wall-clock time: rejected because wall time can jump.
- Check size only after parsing: rejected because oversized input would already
  consume memory and parser work.

## Decision 6: Fail catalog collection atomically

**Decision**: Follow at most five redirects, revalidate every target as HTTPS,
stream decoded bodies to the 1 MiB limit, decode UTF-8, parse JSON, and validate
the complete source before accepting records. Any source failure discards every
catalog row collected in that invocation and returns installed fallback with a
catalog-unavailable warning. Loopback HTTP exists only behind injected test
configuration and is invalid in production schemas.

**Rationale**: A successful subset cannot truthfully represent the configured
available set. Installed inventory remains independently useful.

**Alternatives considered**:

- Show partial catalogs with a warning: rejected as misleading.
- Fail without local output: rejected because graceful degradation is required.
- Reuse silent stale cache: rejected because freshness would be unknowable.

## Decision 7: Retain canonical evidence and deterministic conflicts

**Decision**: Every output row includes ordered source evidence with source
kind, privacy-minimized source identity, normalized record SHA-256, and
zero-based source ordinal. Raw canonical records and alternate free-text values
are never emitted.
Combined installed/catalog rows use source kind `combined` and contain both
local and catalog evidence. Duplicate catalog candidates are ordered by
ascending priority, case-folded then raw catalog name, normalized record SHA-256,
and source ordinal only as a final tie-break for byte-identical records. The
first candidate supplies preferred optional fields, but every differing field
is named in conflict reasons and every distinct version remains in
`available_versions`. Source ordinal remains
retained evidence but cannot make preferred fields depend on input record
order. Conflicting `install_allowed` values resolve to false.

**Rationale**: A total ordering is reproducible even for duplicate records from
one catalog, and conservative install permission avoids choosing an unsafe true
value. Evidence makes preferred-value selection auditable.

**Alternatives considered**:

- Stop after priority and catalog name: rejected because ties remain dependent
  on input iteration order.
- Emit raw alternate values: rejected because names, descriptions, and authors
  can contain personal or sensitive data; field names and record fingerprints
  provide deterministic diagnosis without duplicating content.
- Resolve permission by preferred record: rejected because disagreement must
  fail closed.

## Decision 8: Use one schema-backed output projection

**Decision**: JSON stdout is one top-level array. Its schema links conflict,
non-empty reasons, invalid health, diagnostics, source kind, local/catalog
arrays, activation, an independent activation diagnostic, and retained evidence.
Contract fixtures include positive
healthy local, invalid fallback, catalog-only, combined, and conflict rows plus
negative contradictions for each conditional.

**Rationale**: One immutable projection keeps human and JSON output aligned and
lets contract tests reject impossible states before compatibility hardens.

**Alternatives considered**:

- Separate serializers per scope: rejected because invariants would drift.
- An envelope object: rejected because accepted warnings use stderr and the
  planned compatibility contract is a top-level array.
- Prose-only invariants: rejected because machine consumers require rejection
  of contradictory payloads.

## Decision 9: Define output channels and failure atomicity

**Decision**: Human rows and empty states go to stdout. Warnings and runtime
errors go to stderr. Runtime failure emits no partial table unless catalog
failure invokes the explicit installed fallback contract. Human-mode Typer
usage errors emit usage/help to stderr, leave stdout empty, and exit 2.
JSON-mode usage errors suppress Typer usage prose, leave stdout empty, emit
exactly one compact JSON error object plus one newline to stderr, and exit 2.
Explicit `--help` takes precedence over `--json`, emits normal human help to
stdout, leaves stderr empty, and exits 0. Exact-output tests assert bytes,
channels, newline, and exit status.

**Rationale**: Stream separation supports scripting and prevents a failed table
from being mistaken for complete output.

**Alternatives considered**:

- Put warnings in stdout: rejected because it corrupts row and JSON streams.
- Render incrementally: rejected because later runtime errors would leave an
  apparently valid partial result.
- Override explicit help as an error: rejected because that conflicts with
  normal CLI behavior.

## Decision 10: Use exact performance and usability protocols

**Decision**: SC-002 starts and verifies one daemon session before timing, then
runs installed-only JSON against a pre-materialized deterministic fixture with
non-empty ID and count 100. Feature catalog, package-index, proxy, public, and
other unapproved transport is disabled; peer-authenticated local IPC and the
pinned private AU audit/control-plane endpoints remain allowed. Each measured
cold client includes peer handshake, installed processing, and both required
audit-ledger appends through complete stdout, but excludes daemon startup,
IMDS/session preflight, and fixture materialization.
After exactly three warmups, record exactly 30 runs and compute nearest-rank P95
at rank 29; it must be at most 2.000 seconds. Evidence records OS,
architecture, CPU model/logical count, total memory bytes, Python/package
versions, lock SHA-256, optional baseline runner identifier,
`network_disabled=true`, fixture ID/count, all warmup outcomes, all durations,
rank, P95, threshold, passed boolean, and timestamp.

JSON Schema validates only the performance document shape. After schema
validation, `specify_cli.evidence` sorts the exactly 30 durations, selects
one-based nearest-rank position 29, requires equality with `p95_seconds`,
requires `threshold_seconds=2.000`, and requires `passed` to equal
`p95_seconds <= threshold_seconds`. Both the producer and final gate invoke this
semantic validator, with an observed red before implementation and an identical
green rerun afterward. The runtime document exists only in an external
temporary directory while validation runs and is deleted afterward; the
repository contains the schema and tests, never a performance payload.

SC-001 and SC-006 share exactly 20 included unique adult participants: exactly
10 novice and exactly 10 experienced Spec Kit users. Every included participant
uses command-line developer tools at least monthly and has no prior exposure to
this feature or test fixture. A novice has completed 0-2 Spec Kit workflows in
the prior 6 months and has no prior extension-management use. An experienced
participant has completed at least 5 such workflows and has prior
extension-management use.

Allocation uses the constant `sha256-seeded-stratified-order-v1`, one
64-character lowercase hexadecimal seed, and at least two unique non-empty task
variants. Within each stratum, sort eligible anonymized participant IDs, order
them by SHA-256 of `<seed>:<stratum>:<participant_id>` with participant ID as
the final tie-break, and assign task variants round-robin in declared order.
Recorded allocations must match recomputation exactly.

Every requested accessibility accommodation is provided without changing the
measured task. If an accommodation cannot be provided, exclude the person
before task exposure with reason `required-accommodation-unavailable`, record
only a closed generic unavailable-category code, and replace within the same
stratum. Requested and provided accommodations likewise use closed generic
category codes and contain no medical details. A
pre-exposure `documented-technical-interruption` remains permitted. Every
post-exposure outcome remains included. SC-001 requires at least 19 of 20
included participants to succeed, and SC-006 requires at least 18 of 20
included participants to qualify.

Actual study evidence is collected only after Privacy Act-compliant notice and
explicit consent and is limited to SC-001/SC-006. Random pseudonymous IDs are
generated independently from names and contact data. Evidence excludes names,
email, employer, precise location, medical details, and free-text PII. The
re-identification key and recruitment records remain separate from evidence in
authorized AU-resident stores. Named study-team access is least privilege and
immutably audited; data is encrypted in transit and at rest; withdrawal is
honored before de-identification or aggregation; incidents follow the approved
breach process; and evidence is deleted no later than 90 days after review
unless an approved legal hold applies.

After JSON Schema validation, an AMA-local semantic validator checks the privacy
metadata and retention deadline, eligibility,
cross-record participant uniqueness and stratum membership/counts, derives
aggregate counts, validates exclusions and distinct same-stratum replacements,
recomputes every allocation, and requires every included participant's requested
accommodations to equal the provided accommodations. The schema permits both
aggregate counts from 0 through 20 so valid evidence can retain a failed study.
The validator separately reports SC-001 pass at 19 or more successes and SC-006
pass at 18 or more qualifying participants. Completed validation and review do
not imply either threshold passed.

**Rationale**: Exact timing boundaries and cohort rules make the success
criteria reproducible and prevent selective exclusion or experience imbalance.

**Alternatives considered**:

- One timing run: rejected because startup variance makes it unrepresentative.
- Warm in-process timing: rejected because users pay process startup cost.
- Unspecified representative users: rejected because ineligible or previously
  exposed participants and experience imbalance can mask usability problems.
- Opaque randomization: rejected because allocation cannot be independently
  reproduced or audited.
- Post-enrollment accommodation refusal: rejected because unavailable
  required support must be resolved before exposure through same-stratum
  replacement without changing the measured task.

## Decision 11: Keep installed-only startup dependency-light

**Decision**: Command registration and installed collection use lazy imports.
A cold client subprocess invokes the installed-only path, inspects its own
`sys.modules`, and fails if Requests, jsonschema, or any catalog module is
loaded. The pre-started daemon may already contain HTTP dependencies required by
the private audit stack, so daemon verification snapshots `sys.modules` before
the installed handler and rejects newly imported `specify_cli.extensions.catalogs`,
feature catalog transports, Requests, or jsonschema. The same cold client path
is used for the 30-run SC-002 measurement.

**Rationale**: Optional catalog machinery is unnecessary for the default path
and can consume a meaningful share of the 2-second cold-start budget.

**Alternatives considered**:

- Import catalog support at CLI module load: rejected because it couples the
  default local inventory path to network and schema dependencies.
- Verify imports only by source inspection: rejected because transitive imports
  are observable only at runtime.

## Decision 12: Prove package isolation without assuming a clean root

**Decision**: Protect exactly `pyproject.toml`, optional `uv.lock`,
`ruff.toml`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`,
`package.json`, `pnpm-workspace.yaml`, `azure.yaml`, `apps/api/Dockerfile`,
`apps/api/app/main.py`, `apps/agents/Dockerfile`,
`apps/agents/dispatcher/__main__.py`,
`apps/agents/communication/__main__.py`,
`apps/agents/evacuation/__main__.py`,
`apps/agents/maf_runtime/workflow/builder.py`,
`apps/ingestion/Dockerfile`, `apps/ingestion/worker.py`, and
`apps/web/package.json`. Before package sync, build, clean installation, or
smoke execution, record a SHA-256 digest or `absent` for every manifest path.
For the paths that exist at that point, separately run
`git diff --binary --no-ext-diff -- <paths>` and
`git diff --cached --binary --no-ext-diff -- <paths>`, capture each command's
raw stdout bytes without text decoding, compare the pre/post byte streams in
memory, and hold each SHA-256 digest and equality result only in external
temporary guard state. After each
package operation, repeat the same captures using the original existing-path
set and require exact in-memory byte equality plus digest equality. Raw bytes
digests, equality payloads, and Base64 encodings are never written to repository
artifacts or logs.
Never revert, stash, commit, remove, or alter existing user changes.
Package-local metadata declares its README and development extra explicitly.

One reviewed source edit to `.github/workflows/ci.yml` is permitted before
package command execution solely to add `specify-cli-quality`. Its post-edit
bytes and Git diff representations become the protected baseline; every later
executable operation preserves that state exactly. Root `pyproject.toml`,
`ruff.toml`, and `.pre-commit-config.yaml` remain unchanged.

**Rationale**: Per-path hashes detect tracked and untracked content changes,
while immediate equality of the unstaged and staged binary diff byte streams proves
that package operations preserve a dirty baseline rather than incorrectly
requiring the repository to begin clean. An absent optional root lock remains a
valid recorded state.

**Alternatives considered**:

- Require an empty scoped Git diff: rejected because protected paths may already
  contain legitimate staged or unstaged user changes.
- Check only Git status: rejected because unrelated repository changes make it
  ambiguous and untracked generated effects can be missed.
- Hash only root metadata: rejected because existing application entry points
  are part of the compatibility boundary.

## Decision 13: Distinguish root workflow Ruff selection from shared Ruff coverage

**Decision**: Place the project under `tools/specify-cli`, not under `packages`.
Keep root `pyproject.toml`, `ruff.toml`, and `.pre-commit-config.yaml` unchanged,
while adding one reviewed `specify-cli-quality` job to
`.github/workflows/ci.yml`.
Root CI invokes exactly `ruff check apps tests packages` and
`ruff format --check apps tests packages`; those command-line selections do
not include `tools`. Shared Ruff coverage is broader: root `ruff.toml` includes
`tools/**/*.py`, and the repository's unscoped pre-commit `ruff` and
`ruff-format` hooks cover package files. Package-local Ruff configuration must
therefore match line length 120, target Python 3.12, and lint families E, F, I,
and UP, and package code must satisfy both package-local and repository
pre-commit Ruff semantics.

Root mypy continues to target `apps packages`, coverage sources remain `apps`
and `packages`, and import-linter roots remain `apps` and `packages`. Root
regression uses the explicit `tests/unit tests/contract tests/integration
tests/simulation` selection and marker exclusion from
`.github/workflows/ci.yml`, never a bare root pytest invocation.

The tool owns equivalent gates: Ruff check and format, strict mypy, pytest with
branch coverage and at least 90% line coverage, wheel build, clean-install
entry-point smokes, and an AST/import-boundary test that rejects imports from
root `apps` or `packages`. `tools/specify-cli/tests/conftest.py` prepends the
package-local `src` directory, and package tests always use explicit config:
`uv run --project tools/specify-cli --extra dev pytest -c tools/specify-cli/pyproject.toml tools/specify-cli/tests -q`.
The CI job runs on a pre-registered sovereign self-hosted AU Linux x64 runner
with labels `self-hosted`, `ama-au-sovereign`, `azure-au`, `linux`, and `x64`.
Before package work it verifies through IMDS that location is `australiaeast`
or `australiasoutheast`, then runs exact locked sync, package Ruff check/format,
strict mypy, package pytest/coverage, wheel build, clean install, and both
smokes. It uses only synthetic fixtures, uploads no artifact or evidence,
prints no extension inventory/source/evidence payload, and emits only normal
status or minimized failure summaries. This is PR quality validation, not
sovereign platform evidence.
Root coexistence validation asserts each scope according to its real owner:
workflow Ruff invocation paths exclude `tools`; `ruff.toml` and pre-commit Ruff
cover `tools`; mypy, coverage, and import-linter exclude `tools`. It executes
the existing root test selection without editing root configuration. Root
`lint-imports` and the coverage ratchet exclude `tools` by construction, so the
package-local boundary and coverage gates replace them for this project.

**Rationale**: This resolves recursive collection and silent root typing or
coverage expansion while preserving independent packaging and repository-local
ownership.

**Alternatives considered**:

- Keep the project under `packages`: rejected because root mypy and coverage
  scopes would include it while root pytest collection and dependencies would
  not support its src-layout package reliably.
- Modify root `pyproject.toml`: rejected because the tool must not change root
  application metadata or broaden unrelated gates.
- Exempt the package from all gates: rejected because equivalent package-local
  quality and boundary gates are required.
- Assert that all root Ruff behavior excludes `tools`: rejected because that
  contradicts both `ruff.toml` and unscoped pre-commit hooks.

## Decision 14: Keep platform evidence sovereign and external

**Decision**: Implementation checks in one platform-validation script at
`scripts/spec001/run_external_platform_validation.py`, with locally tested
`collect` and `finalize` modes that are never externally executed during local
implementation. Later, collect runs once on a standalone Windows x64 Azure VM
and once on a standalone Ubuntu Linux x64 Azure VM. Each VM proves its
`Microsoft.Compute/virtualMachines` resource ID, IMDS VM ID, and AU location;
VM scale sets are inadmissible.

Each collect run conditionally creates one validated fragment over TLS/private
endpoint with managed identity at
`spec001-extension-list/<validation_session_id>/fragments/<os>-<imds_vm_id>.json`.
The UUID session is shared, Blob Data Contributor is container-scoped, and
same-key overwrite is prohibited.

The operator supplies only storage-account ARM resource ID, container name, and
Blob URI. Before its first read or write, each mode uses managed identity to
query ARM and fail closed unless the account is in an allowed AU region, public
network access is disabled, default network action is deny, and an approved
private endpoint exists. It verifies that the Blob host belongs to the ARM
account and resolves only to private IPs, derives the standalone VM principal,
and proves the exact Storage Blob Data Contributor assignment at target
container scope. It retrieves over private HTTPS with managed identity a compact
ES256 JWS attestation from the authorized AU control plane. The exact versioned
Azure Key Vault key ID and public JWK must appear in the reviewed package trust
bundle `tools/specify-cli/src/specify_cli/trusted_attestation_keys.json`, which
also pins one exact private HTTPS endpoint and managed-identity scope
`api://ama-security-control-plane/.default`. The script verifies signature,
issuer `ama-security-control-plane`, audience
`spec001-extension-list-prewrite`, validation session, a script-generated
256-bit nonce, unique JTI, storage/private-endpoint/container/principal/role
claims, a maximum 10-minute lifetime, and at most 2 minutes clock skew. It
retains the compact JWS in AU-only evidence, hashes its UTF-8 bytes for the
attestation digest, and atomically creates an AU Blob
`spec001-extension-list/attestation-jti/<jti>` marker with create-if-absent
before every fragment or final canonical write. A locked container immutability
policy retains markers for at least one day; evidence records marker identity,
creation, retention expiry, policy, and operation. Each write uses a distinct
fresh attestation/JTI/nonce. The attestation transport is one private-DNS HTTPS
POST, no redirects/retries, five-second total deadline, closed request, and a
maximum 16 KiB HTTP 200 `application/jose` closed response. Credentials, SAS,
and operator endpoint overrides are invalid. Any unverifiable condition blocks
before evidence access.

After both fragments exist, finalize runs in the AU environment. It reads
exactly one Windows and one Ubuntu fragment for the same session, package, lock,
and script version; validates each contract and RFC 8785 digest; assembles the
canonical document; records a pseudonymous security/compliance reviewer ID plus
a closed `approved` or `rejected` decision and reason code; validates canonical
shape and hosted lifecycle semantics;
and conditionally creates
`spec001-extension-list/<validation_session_id>/final/platform-evidence.json`.
A rejected review is retained externally and does not alter repository pending
status.

The platform schema is the canonical finalized-document schema, includes the
UUID session, and defines closed fragment shape under `$defs`. JSON Schema
validates shape only. Hosted semantic validation proves key uniqueness,
session/package/lock/script agreement, exact OS cardinality, each digest,
canonical assembly, review presence, and conditional final creation.

Both modes emit only value-free success/failure summaries. No credentials, SAS
tokens, evidence values, or command payloads occur in output, code, or
configuration. Fragments, canonical evidence, command output, and review are
never uploaded to GitHub, committed, or stored outside Australia. The
`specify-cli-quality` workflow is separate PR validation and cannot represent
external completion.

The repository retains only schemas, tests, and handoff instructions. Pending
external state is prose in the specification, handoff, and checklist; no status
JSON is instantiated. Completed status and evidence exist only in the AU store.
This feature provisions no VM, network, identity,
storage, encryption, retention, or reviewer infrastructure. External collect,
finalize, and review executions are not local implementation tasks.

Implementation also creates the 20-person protocol, verifies or minimally
extends its schema, implements the semantic validator, supplies anonymized
templates and fixtures, and documents the handoff. Conducting the study and
proving SC-001/SC-006 remain `pending-external`. Final local verification reports
both external states without treating them as implementation failures or as
completed success criteria.

**Rationale**: Compliant standalone VMs and human participants are unavailable
to an autonomous local implementation, and fabricated or solely self-declared
evidence would invalidate the feature's auditability and sovereignty boundary.

**Alternatives considered**:

- Use any GitHub Actions publication path: rejected because logs and artifacts
  are not the sovereign AU evidence store and expose unnecessary provenance.
- Use Azure VM scale sets: rejected because this contract requires standalone
  VM resource IDs and avoids ambiguous VMSS provenance.
- Claim macOS validation: rejected because no constitution-compliant Azure
  macOS runner is available under this plan.
- Store platform evidence in the repository: rejected because external payload
  and completed status must remain only in the AU-resident Blob store.
- Treat absent external evidence as local failure: rejected because it blocks
  otherwise complete implementation on unavailable external actors.
- Generate passing placeholders: rejected because evidence must report only
  observed execution or study results.

## Decision 15: Treat project-root discovery as optional

**Decision**: Discover a project only by walking ancestors for
`.specify/extensions`. When no ancestor contains that directory, both installed
entry points return scope-specific empty results with exit 0: installed text is
`No extensions installed.`, available text is
`No catalog extensions available.`, all text is
`No installed or catalog extensions found.`, and JSON for every scope is `[]`.
Catalog configuration is available only through a discovered project root;
there is no user-home, process-global, or current-directory fallback source.

**Rationale**: A clean installed-wheel smoke must work outside any checkout,
and silently loading unrelated catalog configuration would make behavior
machine-dependent and weaken privacy.

**Alternatives considered**:

- Fail when no project root exists: rejected because listing an empty installed
  state is a valid read-only operation.
- Search user configuration for catalogs: rejected because catalog sources are
  project policy and require an explicit discovered root.

## Decision 16: Compare root regression against a captured dirty baseline

**Decision**: Before package source implementation, run the exact root CI pytest
selection and capture its command, working directory, UTC time, exit code,
normalized failure IDs, normalized collection-error IDs, and output byte/line/
SHA-256 metadata as an ephemeral object in an external temporary directory,
validated by `contracts/root-regression-baseline.schema.json`. The long-lived
custodian daemon holds it for the implementation session and deletes raw output
after normalization. Local-synthetic custody loss ends that segment and permits
a new explicitly discontinuous non-evidentiary segment from the current
worktree. Sovereign custody loss after the first feature source or workflow edit
is unconditionally blocking and recapture or reconstruction is prohibited. After
implementation, rerun
the exact selection and compare normalized sets. Existing failures are
documented and non-blocking only for local attribution; new failures or
collection errors block. Missing or drifting command/baseline data also blocks.
Baseline comparison is not merge readiness: the actual pull-request lint, unit,
and integration jobs must all be green before merge.

T008 captures the actual normalized failure and collection-error sets produced
by the provisioned root environment. Those identities are known-pre-existing
only for that segment. Post-implementation disappearance is allowed, but any
identity absent from the baseline blocks. No literal error count/path is an
acceptance condition.

A discontinuous local restart cannot attribute regressions introduced before
the loss because they are already part of the new baseline. After any restart,
the final gate reruns the complete root selection and reports the attribution
gap; local success remains non-release evidence and sovereign/PR gates cannot be
waived.

A latent bootstrap defect discovered after T008 is not repaired under active
custody. The local daemon finalizes that segment as incomplete, appends the
linked final pair, deletes journal/temp custody, and stops. Repair then occurs
as pre-journal repository/tooling work; both bootstrap self-checks rerun green
without an expected red, and the repaired worktree starts a new
explicitly discontinuous non-evidentiary segment with the same attribution-gap
disclosure and full final root rerun. Segments are never resumed or combined,
and sovereign post-edit defects remain terminal.

Preserve the exact pytest arguments while isolating generated coverage state.
Before dispatch, create a temporary directory outside the repository, set
`COVERAGE_FILE` and `COVERAGE_RCFILE` to files there, and generate a temporary
coverage rc that reproduces root `[tool.coverage.run]` `source`/`branch`/`omit`
and every `[tool.coverage.report]` setting while adding
`[xml] output = <external-temp>/root-coverage.xml`. This is the sole redirection
mechanism for the frozen `--cov-report=xml` argument. Preflight blocks if coverage cannot honor those
locations without argument changes. The mutation guard snapshots repository
`.coverage*` and `coverage.xml` paths/globs and fails if any are created or
changed; it never restores or deletes user files.

The baseline guard is independent of protected-path hashes and raw staged and
unstaged Git diff equality. `root_regression.py` alone captures and compares the
baseline. `local_gate_sequence.py` first exposes pure
`assemble_package_commands` and `parse_package_coverage` boundaries; T130 later
adds only `run_local_gate_sequence` to integrate the tested components. Tests
reject execution from either pure boundary and reject root-guard ownership
outside `root_regression.py`.

**Rationale**: The repository is already dirty and may contain known failures.
Requiring an absolute green root suite would misattribute pre-existing state,
while allowing arbitrary failures would hide regressions. Set comparison gives
a truthful local boundary without modifying user work.

**Alternatives considered**:

- Require root exit code 0 before implementation: rejected because existing
  failures are valid baseline observations.
- Compare only exit codes: rejected because equal nonzero codes can hide a new
  failure and a removed old failure.
- Fold root regression into protected-path equality: rejected because content
  preservation and behavioral regression are independent gates.

## Decision 17: Keep tests and producers in explicit red-green order

**Decision**: Packaging, performance, privacy, schema, external-script, and evidence
producer work begins with a focused failing test or fixture validation. The
packaging test runs first from the repository root as
`uv run --no-sync pytest -c pyproject.toml tools/specify-cli/tests/test_packaging.py -q`,
using only root development pytest and standard-library parsing before package
metadata or package `conftest.py` exists. Each corresponding implementation or
producer is added only after its red is observed, then the same focused test
runs green. Every expected-red task defines one complete canonical
`python scripts/spec001/run_local_gates.py -- ...` command with required
environment, test files, `-q`, selectors, and markers; the green task repeats
the exact string, and each combined red has an exact combined green replay.

The dispatcher writes child stdout/stderr only to an external temporary
directory. One sanitizer derives exit code, normalized test IDs, category/code,
byte and line counts, SHA-256, and a bounded secret- and path-scrubbed summary.
Only minimized in-memory or terminal status survives; raw output is logically
deleted from owner-only local temporary storage in local-synthetic mode or the
verified encrypted AU temporary volume in sovereign mode, and no red or gate
`.txt` or JSON observation is retained in the repository. Before dispatcher proof, only the protected-state self-check and
dispatcher `--self-check` may execute. Dispatcher-owned modes are allowed only
afterward and must apply identical pre/post protection.

Package coverage uses an owner-only external temporary `COVERAGE_FILE`,
`COVERAGE_RCFILE`, and `package-coverage.xml`; the independent parser reads that
XML. Repository `.coverage*`, `coverage.xml`, and `package-coverage.xml` are
mutation-checked and never used as outputs.

Every guarded `uv run` child receives `UV_FROZEN=1`, which prevents implicit
lockfile updates and fails before launch when absent or changed. T022's explicit
package-lock-generating `uv sync` is the sole local exception; T023 proves it
with `--locked`. Every package-project `uv run` selects `--extra dev` for Ruff,
mypy, and pytest. Strict mypy uses `MYPY_CACHE_DIR` beneath owner-only external
temporary storage, and repository `.mypy_cache` remains absent or recursively byte-identical.
Every guarded pytest child receives `PYTEST_ADDOPTS=-pno:cacheprovider`; root
and package `.pytest_cache` trees remain absent or recursively byte-identical.

Baseline capture/comparison is implemented in one tested module. Package gate
sequence assembly is separate. A later orchestrator integrates package gates,
protected-path checks, and root regression, and final execution occurs only
after those components pass independently.

**Rationale**: Explicit red-green boundaries prove that packaging, performance,
privacy, and evidence tests can detect a missing producer, while split guard
responsibilities keep failure attribution narrow.

**Alternatives considered**:

- Add tests and producers in one step: rejected because an immediately green
  test does not prove it can detect absence or malformed output.
- Put capture, gate definitions, integration, and execution in one script:
  rejected because it couples policy, side effects, and final reporting into an
  oversized unit that cannot be discriminated cheaply.

## Decision 18: Define readability through observable text invariants

**Decision**: Exercise 80x24 and 40x12 terminals with colour disabled and a
redirected plain-text stream. Require every record exactly once, literal labels
`Installed`, `Activation`, `Health`, `Commands`, and `Hooks`, exact disabled,
invalid, and conflict words, no ANSI escapes after normalization, preserved
label/value token order after wrapping, and no pager or input.

**Rationale**: Automated tests can verify stable text structure and
non-interactivity, but cannot establish general human comprehension.

**Alternatives considered**:

- Assert that narrow output is “understandable”: rejected as subjective and
  not independently reproducible.
- Snapshot only a default-width coloured terminal: rejected because it misses
  constrained and redirected output modes.

## Decision 19: Require durable minimized audit in an immutable AU ledger

**Decision**: Every action is one two-record transaction: a closed hash-chained
`intent`/`started` record before execution and one linked `result` before
completion or the next action. Local-synthetic development writes those records
to an owner-only temporary journal; the bootstrap files become genesis hashes,
the journal is not evidence, and finalization deletes it. Sovereign execution
writes to the private immutable AU Blob ledger and uses the external coordinator
before daemon startup. Each file mutation has a distinct serialized transaction.
Local custody loss may start a new explicitly discontinuous non-evidentiary
segment; sovereign custody loss remains fail-closed.
Each session uses partition `spec001-extension-list/<session_id>` with at most
49,000 records. Ordinary actions stop after sequence 48,998, reserving one final
intent/result pair. Sessions never split pairs or roll over; a new session gets
a new partition without continuity claims.

**Rationale**: Ephemeral gate data protects privacy but cannot satisfy durable
auditability by itself. A minimized AU ledger preserves provenance and rationale
without copying command output, inventory data, paths, or human content.

## Decision 20: Keep every non-synthetic data path in Australia

**Decision**: Normal non-synthetic CLI use is a thin client to a verified AU
daemon. Local-synthetic development uses a mode-bound local daemon, synthetic
fixtures, fake transports, owner-only temporary storage, and no Azure resource.
It cannot access production catalogs or produce qualifying evidence. Sovereign
package sync/build runs offline from an authorized pre-seeded AU mirror cache.
Production remote catalogs are private AU Azure Blob sources carrying storage
ARM resource and container scope; managed identity verifies AU location,
disabled public access, deny-by-default networking, approved private endpoint,
host/private DNS, and exact container-scoped Blob Data Reader before access.

**Rationale**: Deletion after processing does not satisfy a strict sovereignty
rule if bytes were processed elsewhere. AU-only execution and endpoints prevent
the data from leaving Australian borders.

## Compatibility Baseline

- All source, tests, metadata, lock files, docs, and CI remain in this
  repository; no external checkout is permitted.
- The root `ama-disaster-response-hub` package and application entry points are
  unchanged.
- The CLI provides `ama-specify extension list`, `--available`, `--all`, and
  `--json`, plus `python -m specify_cli` parity. It does not install a
  `specify` console script or modify an upstream one.
- Installed-only mode performs no feature catalog, package-index, proxy,
  public-endpoint, or other unapproved network access; mandatory pinned private
  AU audit/control-plane traffic remains allowed and is included in SC-002.
- Catalog support is list-only; search, install, update, and administration are
  out of scope.
