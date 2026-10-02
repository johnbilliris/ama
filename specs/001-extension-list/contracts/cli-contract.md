# CLI Contract: `ama-specify extension list`

**Status**: Planned contract for feature `001-extension-list`

## Invocation

```text
ama-specify extension list [--available | --all] [--json]
```

| Option | Scope |
| --- | --- |
| no scope option | Installed extensions only |
| `--available` | All configured catalog entries, including installed entries |
| `--all` | Reconciled union of installed and catalog entries |
| `--json` | Machine-readable output for the selected scope |

`--available` and `--all` are mutually exclusive. Supplying both is a usage
error with exit code 2. The command is read-only and must not install, repair,
enable, disable, activate, or rewrite any extension or catalog state.

## Scope Behavior

| Condition | Installed | Available | All |
| --- | ---: | ---: | ---: |
| Healthy installed record | include | include only when catalog ID matches | include |
| Invalid installed record | include | include only when catalog ID matches; identifier-less records cannot match | include |
| Catalog-only record | exclude | include | include |
| Installed-only record | include | exclude | include |
| Catalog retrieval failure | include normally | show installed fallback plus warning | show installed fallback plus warning |

When catalog retrieval fails, no successfully fetched subset may be represented
as a complete catalog result. Exit status remains 0 when local inventory can be
shown; the warning communicates degraded catalog coverage.

## Text Output

Each installed row includes:

- human-readable name;
- stable ID, or `Source: <relative-path>` for identifier-less records;
- installed version or `unknown`;
- description when available;
- literal activation state;
- literal metadata health state;
- command and hook counts; and
- metadata diagnostic reasons when invalid; and
- the independent activation diagnostic when activation failed.

Catalog rows include name, stable ID, all reported available versions,
description when available, literal installation state, health, and normalized
command/template/script/hook counts. A schema-valid catalog-only row defaults
to `healthy`, has no activation state, and uses zero for every omitted
capability count. Combined rows show installed and available versions separately
when they differ, use source kind `combined`, and retain both installed and
catalog evidence.

Conflict rows use the literal word `conflict`, list every source and distinct
version, and name each differing field without repeating alternate free-text
values. Before stable-ID
grouping, registry and physical observations of the same normalized source and
same valid ID coalesce into one installed source record combining registry state
with manifest metadata and retaining both observations as evidence. Only
distinct normalized physical sources sharing a valid ID form a
duplicate-installed conflict. Contradictory valid IDs on one normalized source
form one invalid local identity-conflict record, never separate healthy rows.
Identifier-less observations of the same normalized local source form one
invalid conflict row; distinct normalized sources remain separate even when
names collide. Color and symbols may supplement but never replace literal state
and diagnostic words.

Empty messages are scope-specific:

```text
No extensions installed.
No catalog extensions available.
No installed or catalog extensions found.
```

Project-root discovery walks ancestors and succeeds only when an ancestor
contains `.specify/extensions`. When no project root is discovered, both
installed entry points MUST exit 0. Installed text emits
`No extensions installed.`, available text emits
`No catalog extensions available.`, all text emits
`No installed or catalog extensions found.`, and JSON for every scope emits
`[]`. Catalog configuration can only be loaded from a discovered project root;
there is no user-home, process-global, or current-directory fallback catalog.

Long output relies on normal terminal scrolling and Rich wrapping. Contract
tests run at 80x24 and 40x12 with colour disabled and under redirected plain
text. Every record appears exactly once and retains literal labels `Installed`,
`Activation`, `Health`, `Commands`, and `Hooks`; disabled, invalid, and conflict
remain exact words; normalized output contains no ANSI escapes; wrapping
preserves label/value token order; and no pager or input path is invoked. These
are objective output assertions, not a general human-comprehension claim.

Contract tests MUST generate output exceeding one screen, force a narrow
terminal width to exercise wrapping, verify all rows and text-complete states
remain present, and instrument pager entry points so any interactive pager
invocation fails the test. The command must complete without waiting for input.

Rows and empty-state messages are buffered and written to stdout only after the
selected result is complete. Human-mode warnings and runtime errors go to
stderr. A runtime error exits 1 and writes no partial table. The sole degraded
success exception is catalog-unavailable fallback: complete installed rows go
to stdout, one warning goes to stderr, and the command exits 0. Human-mode Typer
usage errors write usage/help to stderr, leave stdout empty, and exit 2.
Explicit `--help` takes precedence over `--json`, follows normal human Typer
behavior by writing help to stdout, leaves stderr empty, and exits 0.

## JSON Output

Successful stdout is one UTF-8 JSON array followed by a newline and conforms to
`extension-list.schema.json`. Installed, available, and combined invocations use
the same item projection, with null or empty fields where a source does not
apply. Availability flags broaden JSON output exactly as they broaden text
output.

Every JSON row includes ordered `evidence` items containing source kind,
source-identity SHA-256, source ordinal, and normalized record SHA-256. Raw
source identity, canonical records, author values, and alternate descriptions are
never emitted as evidence. `source.kind` is `local`,
`catalog`, or `combined` and must agree with `installed`, `source_locations`,
`catalog_sources`, evidence kinds, activation fields, and `install_allowed`.
Local-only rows use null `install_allowed`; catalog and combined rows use a
boolean. A duplicate disagreement projects `install_allowed=false`.
Every row also includes `activation_diagnostic`. It is a non-empty string exactly
when `activation_state` is `activation-failed`, and null when activation is
disabled, inactive, active, or null. It does not depend on or substitute for
`health.diagnostics`.

Catalog-unavailable degradation writes the selected-scope installed array to
stdout, emits one JSON warning object to stderr, and exits 0:

```json
{
  "warning": {
    "code": "catalog-unavailable",
    "message": "Extension catalog unavailable; showing installed extensions only."
  }
}
```

Runtime failure writes no stdout, writes exactly one compact
`{"error":"..."}` object plus one newline to stderr, and exits 1. JSON-mode
usage errors suppress Typer usage prose, leave stdout empty, write exactly one
compact JSON error object plus one newline to stderr, and exit 2. Exact-output
tests assert stdout bytes, stderr bytes, the single trailing newline, and exit
status. `--help --json` follows the human help contract above.

## Ownership And Stability

- The command is newly implemented by the AMA-local package at
  `tools/specify-cli` as a Spec Kit-compatible standalone subset. It neither
  replaces nor augments an existing upstream `specify` executable.
- Keep the accepted command and option names stable:
  `ama-specify extension list`, `--available`, `--all`, and `--json`.
- Keep `python -m specify_cli extension list` behavior equivalent. The package
  MUST NOT register a `specify` console script.
- Keep the top-level JSON array and item fields defined by
  `extension-list.schema.json` stable once implemented.
- `--available --json` and `--all --json` honor the same scopes as text output.
- Catalog support is list-only. Search, install, update, trust administration,
  and catalog mutation are outside this package and feature.
- The command reads AMA's `.specify/extensions` data without modifying it and
  has no import dependency on AMA disaster-response application modules.
- Non-synthetic entry points are thin clients to a verified peer-authenticated
  AU daemon session. Inventory/catalog data and command output are processed only
  on that daemon's encrypted AU ephemeral volume; direct in-process production
  processing fails before project data is read.
- `--start-session --execution-mode local-synthetic` is the development path on
  ordinary Windows or Linux workstations. It requires owner-only local IPC/temp
  storage and an ephemeral hash-chained journal, accepts only synthetic fixtures
  and fake external transports, rejects production remote catalogs and
  qualifying evidence/external modes, and makes no AU, release, or external-
  validation claim. `--execution-mode sovereign` requires the signed preflight,
  AU IMDS/encryption, managed identity, private networking, and immutable ledger.
  Session mode is handshake-bound and cannot be changed by a client.
- On Linux, use `$XDG_RUNTIME_DIR/ama-specify/daemon.sock` only when the runtime
  directory is current-UID-owned, non-symlink, and mode 0700. Otherwise use
  `${TMPDIR:-/tmp}/ama-specify-<uid>/daemon.sock`, atomically creating and
  validating the non-symlink mode-0700 per-UID directory. The socket is mode
  0600 and peers pass `SO_PEERCRED`. Windows uses standard-library `ctypes`
  bindings to `kernel32`/`advapi32` to create the named pipe and current-SID+
  SYSTEM DACL. No additional IPC/security dependency is allowed.
- A local-synthetic data-bearing request requires
  `SPEC001_TEST_MODE=synthetic` and either no discovered project or a project
  under the owner-only session temporary root with a closed marker
  `.spec001-synthetic-fixture.json` binding schema/feature, non-empty fixture ID,
  and the lowercase SHA-256 of the RFC 8785 canonical sorted `{path,sha256}`
  manifest of all checked-in seed/builder files. Repository-resident
  extension roots, symlinks, path escape, and missing/mismatched markers fail
  before data access.
- Session startup and other non-data-bearing lifecycle operations perform no
  project discovery and do not require `SPEC001_TEST_MODE` or a fixture marker.
- Every runtime list action appends one privacy-minimized, hash-chained
  `intent`/`started` record before processing and one linked `result` record
  conforming to `agent-action-audit.schema.json` before success/failure is
  returned or another action starts. Audit append failure blocks or freezes the
  lifecycle as specified.
- Local development may bootstrap dependencies from the repository-configured
  HTTPS package proxy before guarded tests. Sovereign CI/build/install uses
  `UV_OFFLINE=1` and a cache pre-seeded by an authorized AU package mirror.

## Catalog Configuration

Catalog views read the optional AMA-local
`.specify/extensions/catalogs.json`, which conforms to
`catalog-config.schema.json`. No file means zero configured catalogs. Each
configured catalog has a unique name, positive priority, and exactly one
project-relative JSON `path` or private Azure Blob HTTPS `url`. A remote entry
also requires storage-account ARM resource ID and container scope. Configuration contains at most 8
catalogs, and each `catalog-source.schema.json` document contains at most 1,000
records. Numeric priority 1 is highest. A configured source failure invokes the
catalog-unavailable behavior above; successful subsets are discarded. No
additional global deadline is required.

`catalog-config.schema.json` validates the array and entry shape, but JSON
Schema cannot enforce uniqueness by the `name` property of each object. The
configuration loader MUST therefore run a semantic duplicate-name validator
after schema validation and before any path resolution, stat, file read, DNS,
connection, or other source access. A duplicate name rejects the configuration
as a whole.

For each local or remote source, processing starts one absolute monotonic
deadline 5 seconds later. Local files larger than 1 MiB are rejected before
parse using stat and a bounded 1,048,577-byte read to detect growth races; stat,
read, UTF-8 decoding, JSON parsing, and schema validation consume the same
budget.

Before production remote processing, managed identity verifies through ARM that
the storage account is in `australiaeast` or `australiasoutheast`, public access
is disabled, default network action is Deny, an approved private endpoint
exists, Blob host matches the ARM account and resolves only privately, and the
daemon principal has exactly Storage Blob Data Reader at container scope with no
broader data-plane role. Any failure rejects the source before content access.

Remote processing propagates remaining budget through DNS/connection, each
redirect, decoded streamed reads, UTF-8 decode, JSON parse, and schema
validation; follows no more than 5 redirects; and revalidates every target as
HTTPS. Production configuration rejects HTTP URLs. Isolated tests may inject
loopback HTTP fixtures on `localhost`, `127.0.0.1`, or `::1`, but this exception
does not alter production configuration.

The transport/deadline interface is injectable. A standard synchronous
Requests adapter alone is not accepted as proof of the total deadline because
it cannot guarantee interruption of blocked platform DNS. The production
adapter supervises the complete remote source pipeline through
`multiprocessing.get_context("spawn")` on every platform with a module-level
picklable worker target, terminates and boundedly joins that worker at the
parent deadline, closes process and queue resources on every path, and still
forwards remaining timeout values inside the worker. Fake-clock and process
tests exhaust the budget at DNS, connect, redirect, streamed read, decode,
parse, and validation stages and assert spawn selection plus cleanup.

## Installed-Only Import Boundary

Installed-only execution is lazy. A cold client subprocess for each entry point
inspects its own `sys.modules` after command completion and fails when Requests,
jsonschema, `specify_cli.extensions.catalogs`, or any feature catalog transport
module is present. The pre-started daemon may already contain transitive HTTP
modules required by the private audit stack; its installed handler snapshots
`sys.modules` before work and rejects newly imported
`specify_cli.extensions.catalogs`, feature catalog transports, Requests, or
jsonschema. This process-specific boundary is measured under SC-002.

The adapter MUST stream responses, stop when the decoded body would exceed
1 MiB (1,048,576 bytes), parse UTF-8 JSON, and validate the complete source
document against `catalog-source.schema.json` before accepting any source
record. Timeout, redirect, scheme, size, decoding, JSON, schema, or local-path
containment violations are source failures and trigger all-or-nothing fallback.

## Reconciliation And Tie-breaking

Catalog candidates for one stable ID are ordered by ascending priority,
case-folded catalog name, raw catalog name, normalized record SHA-256, and
zero-based source ordinal only as a final tie-break for byte-identical records.
The first candidate supplies preferred catalog fields independently of source
record order. Source ordinal remains retained evidence.
Every differing field is named in conflict reasons and every distinct version
remains in `available_versions`; alternate names, descriptions, authors, and
other raw values are not duplicated in evidence. Permission conflicts fail
closed to `install_allowed=false`.

## Contract Fixtures

Positive fixtures cover healthy local, activation-failed with an independent
non-empty activation diagnostic, invalid identifier-less local with at least one
metadata-health diagnostic,
catalog-only defaults, combined provenance, duplicate installed, duplicate
catalog, same-normalized-source identifier-less conflict, and empty output.

Negative fixtures MUST be rejected for each of these contradictions:

- `conflict=true` with empty reasons, healthy health, empty diagnostics, or one
  evidence item;
- `conflict=false` with non-empty reasons;
- healthy health with diagnostics or invalid health without diagnostics;
- local source kind with catalog sources/evidence, non-null
  `install_allowed`, or available versions;
- catalog source kind with installed/local evidence, activation, null
  `install_allowed`, or invalid non-conflict health;
- activation-failed with a missing, null, or empty `activation_diagnostic`;
- disabled, inactive, active, or null activation with a non-null
  `activation_diagnostic`;
- combined source kind missing local or catalog evidence/source arrays;
- fallback identity combined with catalog evidence or a non-null stable ID;
- an identifier-less row with healthy metadata health;
- an identifier-less invalid row without a metadata-health diagnostic;
- source/evidence kinds that disagree; and
- duplicate diagnostic objects in any diagnostics array; and
- omitted required provenance, evidence, capability, or permission fields.

Configuration contract tests validate structural limits with JSON Schema and
exercise duplicate catalog names through the loader's semantic validator,
asserting rejection occurs before any source-access adapter is invoked.

Usability evidence fixtures first validate against
`usability-evidence.schema.json` and then invoke the AMA-local semantic validator
in `tools/specify-cli/src/specify_cli/evidence.py`. Semantic negative fixtures
cover ineligible or previously exposed participants, duplicate participant IDs
across strata, aggregates that disagree with raw participant records, invalid
exclusions or replacements, allocation records that do not match deterministic
recomputation, and mismatched requested and provided accommodations. Every
included participant is an adult monthly CLI user and records
`prior_feature_exposure=false`, a six-month Spec Kit workflow count, prior
extension-management use, and required boolean
`consulted_installation_directories` and `attempted_extension_command` fields.
Novices require 0-2 workflows and no extension-management use; experienced
participants require at least 5 workflows and prior use. Allocation uses
`sha256-seeded-stratified-order-v1`, a 64-character lowercase hexadecimal seed,
at least two unique non-empty task variants, SHA-256 ordering of
`<seed>:<stratum>:<participant_id>` with participant ID as final tie-break, and
round-robin assignment in declared variant order. Requested accommodations are
provided without changing the measured task and are represented only by closed
generic category codes. If required support is unavailable, the person is
excluded before exposure as `required-accommodation-unavailable`, only the
unavailable category codes are recorded, and same-stratum replacement is
required. No accommodation field contains medical detail or free text. The
schema rejects a qualifying
`sc_006_clear=true` record when either field is true; separate negative fixtures
cover each violation. The semantic validator independently derives qualification
as rating 4 or 5 with both fields false and excludes any participant with either
field true from the SC-006 aggregate. It also recomputes the SC-001 truth table
from installed-answer correctness, enabled-answer correctness, and elapsed time
at or below 30 seconds. Both participant booleans and both top-level aggregates
must equal semantic recomputation; schema validity alone is insufficient. The
schema permits both aggregate counts from 0 through 20. The validator separately
reports SC-001 pass at 19 or more and SC-006 pass at 18 or more, so a completed
and reviewed study may be valid evidence of a failed criterion.

The top-level privacy object proves Privacy Act-compliant notice and explicit
consent before collection, purpose limitation to SC-001/SC-006, independently
generated random pseudonymous IDs, authorized AU-store resource ID, delete-by
time no later than 90 days after review unless legal hold applies, controller
role, no-direct-identifier assertion, separation of re-identification and
recruitment records, named least-privilege study-team access, immutable audit,
encryption, withdrawal handling before de-identification or aggregation, and a
breach-response process. Evidence contains no name, email, employer, precise
location, medical detail, or free-text PII. Actual study payloads never exist in
GitHub, the repository, or local implementation artifacts.

Performance evidence first validates against the planned closed
`performance-evidence.schema.json`, then invokes `specify_cli.evidence`.
Semantic tests require exactly 30 durations, ascending sort, one-based
nearest-rank position 29, exact equality with `p95_seconds`, constant
`threshold_seconds=2.000`, and exact passed equality against the expression
`p95_seconds <= threshold_seconds`. The producer and final gate both invoke
this post-schema validator. The payload exists only in external temporary
storage during validation and is deleted afterward. A machine not verified as
authorized and AU-resident emits only pass/fail status.

## Package And Validation Boundary

The package is tested with explicit package-local configuration:

```text
uv run --project tools/specify-cli --extra dev pytest -c tools/specify-cli/pyproject.toml tools/specify-cli/tests -q
```

`tools/specify-cli/tests/conftest.py` prepends only `tools/specify-cli/src`.
Production package source cannot import root `apps` or `packages`; a package-local
AST/import-boundary test enforces that contract. Root CI invokes exactly
`ruff check apps tests packages` and `ruff format --check apps tests packages`,
so those workflow command-line selections exclude `tools`. Root `ruff.toml`
still includes `tools/**/*.py`, and the repository's unscoped pre-commit
`ruff` and `ruff-format` hooks cover package files. Package-local Ruff settings
must match line length 120, Python 3.12, and E/F/I/UP, and package code must pass
both package-local and repository pre-commit Ruff semantics without editing
root configuration. Root mypy, coverage, and import-linter scopes exclude
`tools`; package strict mypy, branch coverage with at least 90% line coverage,
build/clean-install smokes, and the AST boundary replace those root gates.

One reviewed edit to `.github/workflows/ci.yml` adds `specify-cli-quality`.
That job targets a pre-registered runner with labels `self-hosted`,
`ama-au-sovereign`, `azure-au`, `linux`, and `x64`; verifies through IMDS before
package work that the location is `australiaeast` or `australiasoutheast`; and
runs locked sync, package Ruff check/format, strict mypy, package pytest/coverage,
wheel build, clean external install, and both smokes. It uses synthetic fixtures,
uploads no artifact or evidence, prints no inventory/source/evidence payload,
and emits only normal status or minimized failure summaries. It is a PR quality
gate, not platform evidence. The post-edit workflow state remains in the FR-033
protected manifest and every later executable operation preserves it exactly.

Package metadata MUST declare package-scoped `[tool.pytest.ini_options]` with
`testpaths = ["tests"]`, importlib mode, strict markers, branch coverage, and
the 90% line threshold. It MUST also declare the package-owned self-contained
`[[tool.uv.index]]` named `microsoft-package-feed-proxy` at
`https://packagefeedproxy.microsoft.io/pypi/simple` as metadata only.
Sovereign dependency sync, build, and clean installation MUST set
`UV_OFFLINE=1`, use only a cache pre-seeded by an authorized AU mirror, and fail
on DNS, socket, HTTP, proxy, index, or public-endpoint access. Local-synthetic
dependency bootstrap MAY use only the configured HTTPS package proxy or an
existing cache; subsequent guarded tests retain production-catalog and
unapproved-network denial.

The first packaging test is intentionally runnable before package metadata or
package `conftest.py` exists. From the repository root it runs exactly:

```text
uv run --no-sync pytest -c pyproject.toml tools/specify-cli/tests/test_packaging.py -q
```

It uses root development pytest plus standard-library parsing only and must be
observed failing before package metadata is implemented.

Pre-T001 provisioning uses
`uv sync --locked --extra dev --no-install-project`. Every guarded root pytest
invocation uses `uv run --no-sync`; every guarded package pytest invocation
places `--extra dev` after `--project tools/specify-cli`. The dispatcher rejects
a root pytest command that attempts another sync or a package pytest command
that omits the selected development extra.

Package coverage commands set `COVERAGE_FILE` and `COVERAGE_RCFILE` to an
owner-only external temporary directory. The temporary rc configures pytest-cov
XML output at `<external-temp>/package-coverage.xml`; the independent parser
reads that XML and requires line coverage at least 90.00%. Repository
`.coverage*`, `coverage.xml`, and `package-coverage.xml` are pre/post mutation
checks and never valid outputs.

## Dispatcher Output Contract

Only `python scripts/spec001/protected_state_selfcheck.py` and
`python scripts/spec001/run_local_gates.py --self-check` may execute before the
dispatcher is proven. The protected-state command runs green once; the
dispatcher/root-regression command is then observed red and replayed
byte-for-byte green after its implementation, for exactly three bootstrap
executions in the initial implementation segment. A recovery segment runs the
protected-state and dispatcher self-checks green without an expected red.
Dispatcher-owned modes may execute after proof only when they apply
the same pre/post protected-state checks as ordinary child dispatch.

After session start, each edit or decision uses one serialized
`--begin-action`/`--complete-action` envelope; guarded commands and runtime list
requests are wrapped internally. For both audit phases, `target_digest` is
SHA-256 over RFC 8785 canonical JSON bytes of the exact schema-valid `target`.
The identifier and kind-specific state objects follow the version-1 algorithm
in the specification. Intent requires pre-state and null post-state; result
retains identifier/pre-state and requires post-state, repeating pre-state when
unchanged. The daemon permits only one active action, so repository mutations
are never parallelized.

The prerequisite exchange accepts no attestation input file. It computes the
repository digest, creates a challenge UUID/nonce/request time, sends the closed
request to the pinned private AU control plane, and accepts one compact JWS.
The decoded payload must equal the schema-valid `claims` object exactly. The
accepted artifact is `{claims, compact_jws, attestation_digest,
replay_protection}`, and the immutable AU JTI marker is created before
acceptance. It is invoked only with `--execution-mode sovereign`; local-
synthetic startup rejects both `--trust-bundle` and any attestation payload.

Dispatcher environment names are closed for this feature. `SPEC001_SESSION_ID`
is routing metadata only and never authorizes a peer. `SPEC001_TEST_MODE` may be
exactly `synthetic` only for checked-in fake-data tests. `SPEC001_EXTERNAL_TRANSPORT`
may be exactly `fake` only for local external-boundary tests and cannot enable a
real collect/finalize path. `SPECIFY_CLI_NETWORK_DISABLED=1` denies feature
catalog, package-index, proxy, public-endpoint, and every other unapproved
transport while allowing only peer-authenticated local IPC and pinned private
AU audit/control-plane endpoints; tests fail on any destination outside that
allowlist. Sovereign mode injects and verifies `UV_OFFLINE=1` for every `uv` child; local dependency
bootstrap does not, while later local test commands may set it explicitly once
dependencies exist. Production rejects test-only environment controls, and unknown
`SPEC001_*` or `SPECIFY_CLI_*` controls fail closed.
Sovereign mode specifically rejects `SPEC001_TEST_MODE` and
`SPEC001_EXTERNAL_TRANSPORT` when present; local tests exercise this policy only
through injected pure validators and never open a sovereign session with those
controls.

Every guarded child whose executable is `uv run` receives exact
`UV_FROZEN=1`; missing or different values fail before child launch. T022's
intentional package-lock generation uses `uv sync` and is excluded, while T023
uses explicit `--locked`. Every package-project `uv run` selects `--extra dev`
for Ruff, mypy, and pytest. Guarded mypy children receive `MYPY_CACHE_DIR` beneath
the owner-only external temporary root, and repository `.mypy_cache` is an
absent-or-recursively-byte-identical mutation check.
Every guarded pytest child receives exact
`PYTEST_ADDOPTS=-pno:cacheprovider`; missing or changed values fail before
launch, and root/package `.pytest_cache` trees remain absent or recursively
byte-identical.

Every audit record includes the session execution mode and sink. Local-synthetic
uses `ephemeral-local` in one owner-only temporary segment; sovereign uses
`immutable-au`. Local segment loss permits a new baseline segment with explicit
discontinuity but never a sovereign claim. Sovereign custody loss after product
edits remains terminal.
If a latent bootstrap defect is discovered after T008 locally, finalization
records an incomplete intent/result pair and deletes local custody before any
repair. Repair is pre-journal repository/tooling work; the repaired worktree
reruns the protected-state and dispatcher self-checks green without an expected
red, then starts a new explicitly discontinuous non-evidentiary segment with lost-
attribution disclosure and a full final root rerun. The segments cannot be
resumed, combined, or promoted; sovereign defects remain terminal.
Every record also repeats the segment's constant `session_manifest_digest`; a
change is a chain-validation failure.

The local journal is NDJSON. Writers hold `msvcrt.locking` on Windows or
`fcntl.flock` on Linux, validate the chain under the lock, set
`append_position_bytes` to the current file length, append one RFC 8785 canonical
JSON UTF-8 record plus LF, flush and `fsync` before acknowledgement, and delete
the journal at finalization.

Each local journal or sovereign append blob is one bounded per-session partition
`spec001-extension-list/<session_id>`. It allows at most 49,000 records and
stops ordinary actions after sequence 48,998, reserving the final intent/result
pair for session finalization. It never splits a pair or rolls over in place.

SC-002 starts and verifies the daemon session before timing. Each of its three
warmup and 30 measured runs starts a fresh client process and measures through
complete stdout, including peer handshake, installed work, and both private AU
ledger appends. Daemon launch, IMDS/session preflight, and fixture materialization
are excluded from the interval.

Every expected-red task defines a complete canonical command beginning with
`python scripts/spec001/run_local_gates.py --`, including required environment,
test file paths, `-q`, selectors, and markers. Its green task repeats that exact
string. A combined red command has one exact combined green replay. The
dispatcher captures stdout/stderr only in an external temporary directory and
applies one sanitizer contract to every red and gate output. The retained
in-memory/terminal status is limited to exit code, normalized test IDs,
category/code, byte and line counts, SHA-256, and a bounded secret- and
path-scrubbed summary. Raw output is deleted after validation from the verified
owner-only local temporary storage in local-synthetic mode or the verified
encrypted AU ephemeral volume in sovereign mode; no claim of physical secure
erasure is made. No raw exception,
absolute path, environment value, inventory record, Git diff, human data,
evidence payload, `.txt`, or runtime JSON is retained in the repository.

## Root Regression Contract

Before package source implementation, execute this exact selection from the
repository root:

```text
uv run --no-sync pytest tests/unit tests/contract tests/integration tests/simulation -m "not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging and not e2e and not load and not locust" --cov=apps --cov=packages --cov-report=xml --cov-report=term
```

The guard creates a temporary directory outside the repository before dispatch,
sets `COVERAGE_FILE` and `COVERAGE_RCFILE` to files there, and generates a
temporary coverage rc that reproduces root `[tool.coverage.run]`
`source`/`branch`/`omit` and all `[tool.coverage.report]` settings, then adds
`[xml] output = <external-temp>/root-coverage.xml`. If the exact command cannot honor those
locations without changing its arguments, preflight blocks. Repository
`.coverage*` and `coverage.xml` paths/globs are explicit pre/post mutation
checks; creation or change fails the gate, and the guard never restores or
deletes user files.

Capture its exact exit code, normalized failure set, normalized collection-error
set, and output byte/line/SHA-256 metadata in an external temporary object
validated by `root-regression-baseline.schema.json`. The long-lived custodian daemon
holds the object only for the implementation session. A nonzero baseline is valid and records
pre-existing failures. After implementation, rerun the exact same selection and
block only when the post-run adds a normalized failure or collection error, the
command drifts, or comparison cannot be completed. Existing failures remain
documented and non-blocking only for local attribution. This comparison is not
merge readiness: actual pull-request lint, unit, and integration jobs must all
be green before merge. This contract never weakens protected-path hashes or
immediate in-memory staged/unstaged Git-diff byte equality. Digests and equality
results remain only in external temporary guard state; raw diff bytes, digests,
equality payloads, and Base64 encodings are prohibited in repository artifacts
and logs.

T008 captures the actual normalized failure and collection-error sets from the
provisioned root environment. Those identities are known-pre-existing only for
that segment's local attribution. Later disappearance is allowed; any identity
absent from the captured baseline blocks. No literal count/path is assumed.

`root_regression.py` solely owns baseline capture/comparison.
`assemble_package_commands` and `parse_package_coverage` are pure boundaries in
`local_gate_sequence.py`; `run_local_gate_sequence` is added only for final
dependency ordering/execution. Tests reject command execution in the pure
boundaries and root-guard semantics outside `root_regression.py`.

Sovereign external platform validation uses one checked-in script at
`scripts/spec001/run_external_platform_validation.py` with locally tested
`collect` and `finalize` modes; neither mode is externally executed during
implementation. Later, collect runs once on each standalone Windows x64 and
Ubuntu x64 Azure VM, proves standalone identity and AU location through IMDS,
and conditionally creates one validated fragment at
`spec001-extension-list/<validation_session_id>/fragments/<os>-<imds_vm_id>.json`.
The shared session ID is a UUID and same-key overwrite is prohibited.

The operator supplies storage-account ARM resource ID, container name, and Blob
URI, never credentials or SAS. Before first read or write, collect and finalize
authenticate with managed identity and query ARM to require an AU location,
`publicNetworkAccess=Disabled`, default network action `Deny`, and an approved
private-endpoint connection. They require the Blob account host to match the ARM
account and resolve only to private IP addresses; derive the managed-identity
principal from the standalone VM ARM identity; and verify exactly Storage Blob
Data Contributor at the target container scope. Over private HTTPS with managed
identity they retrieve a compact ES256 JWS attestation from the authorized AU
control plane. They require an exact versioned Azure Key Vault key ID and public
JWK, exact private HTTPS endpoint, and token scope
`api://ama-security-control-plane/.default` from the reviewed package trust
bundle `tools/specify-cli/src/specify_cli/trusted_attestation_keys.json`; verify
signature, issuer
`ama-security-control-plane`, audience `spec001-extension-list-prewrite`, the
current session and script-generated 256-bit nonce, unique JTI, and repeated
resource/private-endpoint/container/principal/role claims; enforce a maximum
10-minute lifetime and at most 2 minutes clock skew; retain the compact JWS in
AU-only evidence; require `attestation_digest` to equal SHA-256 of its UTF-8
bytes; and atomically create an AU Blob
`spec001-extension-list/attestation-jti/<jti>` marker with create-if-absent and
at least 24-hour retention before every fragment or final canonical write. The
container must have a locked time-based immutability policy of at least one day;
evidence records marker name, conditional creation, retain-until time, policy,
and operation. Each write uses a distinct attestation/JTI/nonce. An existing
marker rejects cross-process replay.

The attestation request is one HTTPS POST to the exact trust-bundle endpoint,
using managed identity for the pinned scope, private-only DNS, no redirects or
retries, and a five-second total monotonic deadline. The closed JSON request is
the schema's `attestationRequest`; it includes operation, session, fresh nonce,
timestamp, target blob, and resource/scope/principal/role bindings. The only
accepted response is HTTP 200 `application/jose`, at most 16 KiB, with the
closed `attestationResponse` containing only `compact_jws`. Operator input cannot
override host, path, scope, or key. Any missing, ambiguous, stale, replayed,
redirected, oversized, public-DNS, or inconsistent result fails closed before
evidence access.

Finalize runs in the AU environment after both fragments exist. It reads exactly
one fragment per OS for the same session/package/lock/script version, validates
shape and digest, assembles the canonical document, records a pseudonymous
security/compliance reviewer identifier plus closed approved/rejected decision
and reason code, validates canonical and hosted lifecycle semantics, and conditionally creates
`spec001-extension-list/<validation_session_id>/final/platform-evidence.json`.
The script suppresses evidence values and command output and emits only a
value-free success/failure summary. Access is TLS/private endpoint plus managed
identity and container-scoped Blob Data Contributor; credentials and SAS tokens
never occur in code, configuration, evidence, or logs.

The canonical platform document contains the UUID session and exactly one Windows record with non-empty
product name/version and one Ubuntu record with `distribution_id=ubuntu` and
non-empty distribution version. Each record retains only VM resource ID, VM ID,
location, OS/architecture, script/Python/package/lock metadata, exact command
outcomes, execution time, and RFC 8785 SHA-256 digest. An authorized
security/compliance reviewer is represented only by a pseudonymous reviewer ID
and records a closed approved/rejected decision and reason code in the AU store;
automated validation proves only internal consistency. Pending-external remains
prose in the specification, handoff, and checklist; no repository status JSON,
completed status, or platform payload is created. No GitHub artifact, log publication, run provenance,
external execution, or infrastructure provisioning represents platform
completion. The separate quality workflow is permitted by FR-034 but publishes
no platform evidence.
The usability protocol, schema verification, semantic validator, anonymized
fixtures, and handoff are local implementation outputs; the actual 20-person
study and SC-001/SC-006 proof remain `pending-external`. Neither pending status
is a local implementation failure or evidence of success.
