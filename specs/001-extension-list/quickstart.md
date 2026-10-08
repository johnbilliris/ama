# Quickstart: Implement and Validate Extension List

**Feature**: `001-extension-list`

## Prerequisites

- Work from the repository root with Python 3.12 or later.
- Install uv `>=0.11,<1`, then provision the root development environment before
   T001 with `uv sync --locked --extra dev --no-install-project` using only the
   configured HTTPS package proxy or an existing cache. This supplies pytest
   without building the declared root project, which has no buildable package
   target. Bind the selected Python
   executable, exact Python/uv versions, OS, and architecture for the segment.
   This is not a feature runtime action.
- Use the new AMA-local package project at `tools/specify-cli/`.
- Local development requires no Azure VM or Azure resource. Use only synthetic
   fixtures/fake transports through `local-synthetic`; its owner-only temporary
   journal is not evidence and is deleted at finalization.
- Normal non-synthetic CLI use, qualifying evidence, sovereign CI/release, and
   real collect/finalize require the standalone AU Azure VM, managed identity,
   private networking, immutable ledger, encrypted temporary volume, signed
   preflight, and authorized AU package cache.
- Local dependency bootstrap may use the repository-configured HTTPS package
   proxy. Guarded tests still deny production catalogs and unapproved network
   traffic. Sovereign dependency operations set `UV_OFFLINE=1`.
- Before any package or root-test command, implement and prove the standard-library
   protected-state guard and its single-command dispatcher:

```powershell
python scripts/spec001/protected_state_selfcheck.py
python scripts/spec001/run_local_gates.py --self-check
python scripts/spec001/run_local_gates.py --self-check
```

```sh
python scripts/spec001/protected_state_selfcheck.py
python scripts/spec001/run_local_gates.py --self-check
python scripts/spec001/run_local_gates.py --self-check
```

The self-checks use only Python's standard library and Git. These are the only
bootstrap exceptions: protected-state green runs first, then the dispatcher/
root-regression self-check is observed red for the missing implementation and
replayed byte-for-byte green after implementation. No dispatcher-owned mode or
child command may run before that green replay. It must pass before the first `uv`, pytest, Ruff,
mypy, build, install, benchmark, smoke, or evidence-production command.
Afterward, invoke each executable operation through
`python scripts/spec001/run_local_gates.py -- <executable> <arguments...>` so
protected state is captured immediately before and compared immediately after.

Start ordinary development on Windows or Linux after the three bootstrap
executions:

```text
python scripts/spec001/run_local_gates.py --start-session --execution-mode local-synthetic
```

The local daemon verifies owner-only temporary storage and IPC, synthetic-data
policy, network denial, protected state, and its ephemeral journal. It returns a
session UUID; set `SPEC001_SESSION_ID` to it. It rejects real project inventory,
production remote catalogs, qualifying evidence, and real external modes. If a
local daemon is lost, start a new local segment from the current worktree; the
new baseline is local attribution only and cannot become release evidence.
Session startup itself is non-data-bearing: it performs no project discovery and
therefore needs no fixture marker even when invoked from the repository root.

On Linux the daemon uses `$XDG_RUNTIME_DIR/ama-specify/daemon.sock` only when
that directory is current-UID-owned, non-symlink, and mode 0700; otherwise it
atomically creates and validates `${TMPDIR:-/tmp}/ama-specify-<uid>/daemon.sock`.
On Windows, named-pipe creation and the current-SID+SYSTEM DACL use standard-
library `ctypes` bindings. No extra IPC/security package is required. Each
session journal/ledger partition is `spec001-extension-list/<session_id>` and is
limited to 49,000 records; ordinary actions stop after 48,998 so finalization
retains its intent/result pair. A session never rolls over in place.

Later, on an eligible AU VM, sovereign qualification runs:

```text
python scripts/spec001/run_local_gates.py --preflight-prerequisites --execution-mode sovereign --trust-bundle <owner-only-au-path>
python scripts/spec001/run_local_gates.py --start-session --execution-mode sovereign
```

The sovereign dispatcher computes the exact repository digest, performs the
pinned private control-plane/JWS/replay checks, verifies IMDS/encrypted storage/
immutable ledger/private dependencies, and fails closed. Local mode never
requests or fabricates this attestation.

The abbreviated quickstart commands below omit an explicit `--session-id` only
because `run_local_gates.py` MUST resolve the required value from
`SPEC001_SESSION_ID` and peer-authenticate to that daemon. If the variable is
missing, names a dead daemon, or peer authentication fails, the dispatcher MUST
reject the command before creating output or launching a child.

Examples also omit test-only environment switches for readability. During
implementation, execute the complete canonical command from `tasks.md`,
including `SPEC001_TEST_MODE=synthetic`, `SPEC001_EXTERNAL_TRANSPORT=fake`,
`SPECIFY_CLI_NETWORK_DISABLED=1`, and `UV_OFFLINE=1` exactly where specified.
Every guarded root pytest child uses `uv run --no-sync pytest` against that
pre-provisioned environment; every guarded
package pytest child uses
`uv run --project tools/specify-cli --extra dev pytest`, preventing uv's exact
sync from pruning the selected development extra.
The dispatcher also injects `UV_FROZEN=1` into every guarded `uv run` child and
rejects a missing or different value before launch, preventing implicit lockfile
updates. T022 lock generation remains the deliberate `uv sync` exception.
Every guarded pytest child receives `PYTEST_ADDOPTS=-pno:cacheprovider`, so root
and package `.pytest_cache` trees remain absent or recursively byte-identical.
Before strict mypy, create an owner-only external cache directory and pass it as
`MYPY_CACHE_DIR`; repository `.mypy_cache` must remain absent or recursively byte-identical.

The checklist in `tasks.md` is the execution authority for every edit and
decision below. After T009, do not perform an edit directly from this abbreviated
guide: for each file, run the task's exact `--begin-action` with that repository-
relative path, mutate only that file, then run its matching `--complete-action`
and obtain the linked result before opening the next file transaction. A
multi-file task reuses its task ID but never spans files with one action.
Decisions use their own transaction. Guarded commands are wrapped internally.
Because the daemon admits one active action, implementation tasks execute
serially even when they touch different files.

After the dispatcher self-check's green replay, start the protected session. Author and run the static
CI contract once to observe the planned job missing. Then request a one-use,
10-minute transition permit bound to the active daemon session, repository,
`.github/workflows/ci.yml`, transition UUID, and exact pre-edit SHA-256. Make
only the reviewed `specify-cli-quality` edit. Before any next child command,
accept the transition in a separate dispatcher-owned mode using the exact
post-edit SHA-256. Acceptance must prove every other protected path and both
staged/unstaged diff streams computed with the permitted workflow path excluded
unchanged, atomically update only the workflow baseline,
invalidate the permit, and fail on reuse, expiry, unrelated drift, or digest
mismatch. Then rerun the exact static CI command green. Do not edit root
`pyproject.toml`, `ruff.toml`, or `.pre-commit-config.yaml`.

Install development dependencies without changing the root
`ama-disaster-response-hub` package:

```text
python scripts/spec001/run_local_gates.py -- uv sync --project tools/specify-cli --extra dev
python scripts/spec001/run_local_gates.py -- uv sync --project tools/specify-cli --extra dev --locked
```

The first guarded sync creates or refreshes the package-local lock file retained for
the eventual reviewed change set at `tools/specify-cli/uv.lock`; no
implementation step commits it. The second command proves the lock is current. Runtime,
build, and development requirements in package metadata use bounded compatible
ranges. CI MUST run exactly
`UV_OFFLINE=1 uv sync --project tools/specify-cli --extra dev --locked` and fail on
metadata/lock drift. CI command substitutions are not permitted. The root lock
and root project metadata are not modified.

- `tools/specify-cli/pyproject.toml` declares its package-owned self-contained
   `[[tool.uv.index]]` named `microsoft-package-feed-proxy` at
   `https://packagefeedproxy.microsoft.io/pypi/simple`; root index metadata is
   advisory only and is neither required nor staged.
- Local dependency bootstrap may use only the configured HTTPS package proxy or
   an existing cache. Sovereign sync, build, and clean installation use only the
   pre-seeded authorized AU cache with `UV_OFFLINE=1`. Keep production catalogs
   and unapproved network access disabled during local tests; use fakes.

## Implementation Order

Every implementation path below is repository-relative and uses POSIX
separators.

1. Implement `scripts/spec001/protected_state.py`, its isolated self-check, and
   a skeletal self-check runner. Run protected-state green, observe the
   dispatcher/root-regression self-check red, implement the frozen root and
   dispatcher units, then replay the identical dispatcher self-check green
   before creating or executing package tests.
2. Start the T008 local-synthetic session and have the custodian daemon capture
   the exact root CI pytest baseline before any product edit. No Azure preflight
   is needed. Only after that
   capture, author `tools/specify-cli/tests/test_root_regression.py`; those tests
   mirror the already green bootstrap vectors and add no new frozen behavior.
   Hold the validated baseline in an external temporary directory under
   custodian-daemon custody before creating any file under
   `tools/specify-cli/src/`. Never write the baseline beneath the repository. A
   new local segment may recapture the current worktree after local custody loss,
   but the discontinuity is recorded and the baseline remains non-evidentiary.
   Sovereign custody still prohibits recapture after product edits.
   If a latent local bootstrap defect is found after T008, finalize that segment
   as incomplete, delete its journal/temp payloads, repair only after custody has
   ended, rerun the protected-state and dispatcher self-checks green without an
   expected red, then start a new explicitly discontinuous non-evidentiary
   segment. Rerun the full final root selection and disclose lost pre-repair
   attribution; never resume/combine segments or use this path for sovereign recovery.
3. Before `tools/specify-cli/tests/conftest.py` or package metadata exists, add
   only the failing packaging contract at
   `tools/specify-cli/tests/test_packaging.py`. From the repository root run
   exactly:

   ```text
   python scripts/spec001/run_local_gates.py -- uv run --no-sync pytest -c pyproject.toml tools/specify-cli/tests/test_packaging.py -q
   ```

   The test relies only on root development pytest and standard-library
   metadata/TOML parsing. Observe the expected red before implementation, but
   retain no stdout, stderr, `.txt`, JSON, or other runtime evidence in the
   repository.
4. Add `tools/specify-cli/pyproject.toml` with Python 3.12+, bounded runtime
   dependencies, `[project.optional-dependencies].dev` containing pytest, Ruff,
   mypy, pytest-cov, types-PyYAML, types-requests, and any additional strict-check
   stubs proven necessary, Hatch wheel
   configuration, and `ama-specify = "specify_cli.cli:app"` under
   `[project.scripts]`. Include `src/specify_cli/trusted_attestation_keys.json`
   explicitly in the wheel. Include package-scoped `[tool.pytest.ini_options]` with
   `testpaths = ["tests"]`, importlib mode, strict markers, branch coverage, and
   90% line coverage; package-local Ruff settings compatible with root line
   length 120, Python 3.12, and E/F/I/UP; and the default
   `microsoft-package-feed-proxy` index and URL. Add
   `tools/specify-cli/README.md` because package metadata declares it. This
   package is a Spec Kit-compatible standalone subset and does not replace,
   augment, or shadow an upstream `specify` executable.
   Generate `tools/specify-cli/uv.lock` with package-local `uv sync` and retain
   it for the eventual reviewed change set; no implementation step commits it.
   Rerun the exact focused packaging test and require green.
5. Add `tools/specify-cli/tests/conftest.py` to prepend only
   `tools/specify-cli/src`, then add package bootstraps at
   `tools/specify-cli/src/specify_cli/__init__.py`,
   `__main__.py`, `daemon.py`, `daemon_client.py`, `daemon_protocol.py`, and
   `cli.py`. Register the Typer `extension list` command in `cli.py`; keep it
   limited to options, IPC delegation, rendering, and exit codes, with no
   in-process inventory/catalog fallback.
6. Before root discovery implementation, add and run failing installed-wheel
   tests for both entry points from outside any ancestor containing
   `.specify/extensions`. Installed, available, and all JSON must return `[]`;
   text must return the corresponding scope-specific empty state; every
   invocation must exit 0; and no catalog fallback may be consulted.
7. Add frozen projection models and the only JSON serializer in
   `tools/specify-cli/src/specify_cli/extensions/models.py`, matching
   `specs/001-extension-list/contracts/extension-list.schema.json`. Do not add
   `_installed_list_json.py`.
8. Add `tools/specify-cli/src/specify_cli/extensions/inventory.py` for
   read-only enumeration of `.specify/extensions/.registry` and physical
   `*/extension.yml` manifests, validation, activation derivation,
   reconciliation, sorting, and warnings. It must not import Typer or Rich.
   Normal entry points are thin clients and perform this work only inside the
   verified AU daemon; direct non-synthetic in-process inventory access fails.
9. Add `tools/specify-cli/src/specify_cli/extensions/catalogs.py` for the
   optional `.specify/extensions/catalogs.json` configuration and all-or-nothing
   retrieval of at most 8 project-relative JSON or private AU Azure Blob HTTPS catalogs containing at
   most 1,000 records each. Enforce one 5-second monotonic deadline per source,
   at most 5 HTTPS redirects, a 1 MiB maximum local or decoded remote body, and
   complete configuration schema validation followed by semantic duplicate-name
   rejection before any source access, and complete source schema validation
   before accepting records. Remote production entries include storage ARM ID
   and container scope; before access, managed identity verifies AU location,
   disabled public access, default Deny, approved private endpoint, host/private
   DNS match, and exact container-scoped Blob Data Reader with no broader role.
   Implement an injectable deadline transport with
   supervised worker cancellation using `multiprocessing.get_context("spawn")`
   on every platform and a module-level picklable worker target rather than
   claiming a bare Requests timeout bounds DNS. Terminate, boundedly join, and
   clean up process and queue resources on success, failure, and timeout.
10. Add `tools/specify-cli/src/specify_cli/extensions/rendering.py` for
   escaped, text-complete Rich output. The list command reads optional activation
   evidence but never writes registry, manifest, or catalog state.
11. Add `tools/specify-cli/src/specify_cli/evidence.py` as the AMA-local
   post-schema semantic validator. Focused red/green tests cover usability,
   performance, and hosted fragment/finalization semantics. Performance requires
   exactly 30 durations, sorted rank 29, exact `p95_seconds`, threshold 2.000,
   and exact passed comparison. The read-only producer is implemented in this
   package-owned module after its producer red; the frozen dispatcher only
   invokes it. Producers and final gates invoke semantic validation only after
   JSON Schema validation.
12. Keep Requests, jsonschema, and catalog transport imports lazy so installed-
   only client execution does not load them. Verify each cold client's
   `sys.modules`; separately snapshot the pre-started daemon's modules and prove
   the installed handler newly loads no feature catalog module/transport and
   initiates no Requests/jsonschema import. Pre-existing audit-stack transitive
   modules are allowed. Retain the 2-second cold-client target.
13. Add package-local tests under `tools/specify-cli/tests/`, including an AST
   import-boundary test forbidding imports from root `apps` or `packages`, and
   command documentation at `docs/specify/extension-list.md`.
14. Add one external operator script at
   `scripts/spec001/run_external_platform_validation.py` with locally tested
   `collect` and `finalize` modes, but never externally execute either mode
   during implementation. Later, collect runs once on each standalone Windows
   x64 and Ubuntu x64 Azure VM and conditionally writes one fragment to
   `spec001-extension-list/<validation_session_id>/fragments/<os>-<imds_vm_id>.json`.
   Finalize runs in AU after both fragments exist, validates same session,
   package, lock, script version, digests, OS cardinality, and review, then
   conditionally writes
   `spec001-extension-list/<validation_session_id>/final/platform-evidence.json`.
   Both modes use IMDS, private-endpoint TLS, managed identity, value-free
   terminal summaries, and create-if-absent writes. Do not execute these runs as
   local tasks. Create the usability protocol, schema/semantic checks,
   anonymized template/fixture, and external handoff without conducting the
   study.

For packaging, performance, privacy, schema fixtures, usability semantics, and
every evidence producer, run the focused failing test before adding its matching
implementation or producer, then rerun the same test green. Do not combine a
producer and its first test execution into one implementation step.

Every expected-red task generated later MUST contain one complete canonical
command beginning with `python scripts/spec001/run_local_gates.py --`, including
all environment assignments, test files, `-q`, selectors, and markers. Its
green task MUST repeat that command byte-for-byte. A combined red command MUST
have one exact combined green replay; selector fragments or reconstructed
commands are invalid. The dispatcher captures child stdout/stderr only in an
external temporary directory, derives exit code, normalized test IDs,
category/code, byte and line counts, SHA-256, and a bounded secret- and
path-scrubbed summary, reports only minimized status in memory or terminal, and
deletes raw output after validation from owner-only local temporary storage in
local-synthetic mode or the verified encrypted AU ephemeral volume in sovereign
mode, without claiming physical secure erasure. One sanitizer contract applies
to every red and gate command.

## Focused Tests

```powershell
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev pytest -c tools/specify-cli/pyproject.toml tools/specify-cli/tests -q
```

```sh
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev pytest -c tools/specify-cli/pyproject.toml tools/specify-cli/tests -q
```

The focused suite must cover:

- default installed-only scope;
- available and combined scope reconciliation;
- all four activation states and both health states;
- activation-failed with a visible non-empty activation diagnostic and null
   activation diagnostics for every non-failed or null activation state;
- identifier-less records that never catalog-match;
- registry and physical observations with the same normalized source and valid
   ID coalescing into one installed source record with both observations retained;
- contradictory valid IDs on one normalized source producing one invalid local
   identity-conflict record, and duplicate installed conflicts requiring distinct
   normalized physical sources;
- duplicate installed and catalog IDs;
- duplicate catalog configuration names rejected by the semantic validator
   after schema validation and before source access;
- same-normalized-source identifier-less aliases and distinct-source name
   collisions;
- catalog defaults for health, activation, and all four capability counts;
- deterministic duplicate catalog tie-breaking through normalized record SHA-256
   before source ordinal, retained differing values, source-order-independent
   preferred fields, and fail-closed
   `install_allowed` disagreement;
- installed/available version mismatch;
- missing optional metadata;
- unknown activation values;
- catalog all-or-nothing failure fallback;
- local pre-parse stat size, local bounded-read growth, source-count, record-
   count, redirect-count, redirect-scheme, and remote decoded-body-size limits;
- deterministic deadline exhaustion at local stat/read/decode/parse/validation
   and remote DNS/connect/redirect/read/decode/parse/validation stages;
- deterministic spawn-context selection with a module-level picklable worker,
   termination, bounded join, and process/queue cleanup assertions;
- installed-only `sys.modules` verification proving Requests, jsonschema, and
   catalog transport modules were not imported;
- both entry points invoked outside any ancestor containing
   `.specify/extensions`, covering installed, available, and all text/JSON empty
   states and proving that no catalog fallback is consulted;
- exact 80x24 and 40x12 terminal output with colour disabled, plus redirected
   plain text; every record exactly once; literal labels `Installed`,
   `Activation`, `Health`, `Commands`, and `Hooks`; exact disabled, invalid,
   and conflict words; no ANSI escapes after normalization; wrapped label/value
   token order preserved; and proof that no pager or input is invoked;
- exact human usage-error stderr with empty stdout and exit 2; exact JSON
   usage-error output consisting of one compact error object plus newline on
   stderr, empty stdout, and exit 2; `--help` precedence over `--json` with
   human help on stdout, empty stderr, and exit 0; and
- deterministic ordering independent of source order.

## Contract Validation

Validate representative payloads against:

```text
specs/001-extension-list/contracts/agent-action-audit.schema.json
specs/001-extension-list/contracts/extension-list.schema.json
specs/001-extension-list/contracts/catalog-config.schema.json
specs/001-extension-list/contracts/catalog-source.schema.json
specs/001-extension-list/contracts/usability-evidence.schema.json
specs/001-extension-list/contracts/external-validation-status.schema.json
specs/001-extension-list/contracts/implementation-prerequisite-attestation.schema.json
specs/001-extension-list/contracts/root-regression-baseline.schema.json
specs/001-extension-list/contracts/platform-evidence.schema.json
```

`usability-evidence.schema.json` already exists. Verify its privacy object and
closed accommodation codes. `platform-evidence.schema.json` is the authoritative
sovereign external contract. Nine schemas currently exist; the implementation
additionally owns planned `read-only-evidence.schema.json` and
`performance-evidence.schema.json` shape contracts. Those contracts validate
ephemeral objects only and never imply a repository runtime-evidence file.
`external-validation-status.schema.json` is likewise an optional non-persisted
handoff shape and is never instantiated under the repository.

The read-only schema requires exactly the positive `ReadOnlyEvidence` fields in
`data-model.md`: identity/lifecycle, invocation view/mode/outcome/exit code,
three before/after SHA-256 pairs for source/protected/coverage state, verified
peer/AU/encrypted-storage flags, completed audit transaction, logical deletion,
and false repository persistence. Semantic validation requires all digest pairs
equal and success exactly when exit code is zero.

Compile and fixture-test all nine current schemas first in strict Draft
2020-12 mode with zero warnings. They must be green before any expected red.
The initial schema-focus red may be caused only by the two absent planned
schemas; the semantic focuses may be red only for missing usability,
performance, or hosted fragment/finalization validators. Use one explicit
platform fixture file and one schema command rather than duplicate platform
schema work. Implement hosted fragment/finalization and performance semantic
validation before rerunning the identical focus green.

Keep usability work in three ordered steps: run the existing schema focus;
conditionally edit the schema only when that run proves a missing
schema-expressible constraint; then rerun the identical schema focus green.
Only after that green result add and run the semantic red, implement the
validator, and rerun identically green. Valid fixtures include failed studies:
both aggregate counts accept 0 through 20, while semantic reporting separately
applies the 19/20 SC-001 and 18/20 SC-006 pass thresholds.

At minimum, include healthy installed, invalid fallback with a metadata-health
diagnostic, catalog-only,
combined version-mismatch, duplicate conflict, empty-array, valid local-file
catalog configuration, valid HTTPS configuration, and invalid dual-source
configuration fixtures. Catalog-source fixtures must include an empty valid
source, valid extension records, invalid IDs, missing required fields, unknown
fields, schema-version mismatch, 1,000 and 1,001 records, and capability fields
omitted for zero normalization. Catalog configuration fixtures include 8 and 9
sources.

Output-contract negative fixtures reject conflict/reason/health/diagnostic
contradictions, conflicts with fewer than two evidence items, local/catalog/
combined source-kind mismatches, fallback identities with catalog evidence,
identifier-less healthy rows, identifier-less invalid rows without metadata-health
diagnostics, catalog non-conflicts marked invalid, null/non-null `install_allowed` in the
wrong source kind, duplicate diagnostics, and omitted required evidence fields.
Configuration schema fixtures cover structural validity; duplicate catalog-name
fixtures exercise the loader semantic validator and assert that no source access
occurs.

Usability evidence fixtures pass schema validation before semantic validation.
Positive evidence has exactly 20 unique eligible adult included IDs, correct
derived aggregates, valid same-stratum replacements, and allocation records that
exactly match `sha256-seeded-stratified-order-v1` recomputation from a
64-character lowercase hexadecimal seed and at least two declared task variants.
Every included participant uses CLI tools at least monthly, has no prior feature
or fixture exposure, records the required six-month workflow count and prior
extension-management use, and has every requested accommodation provided without
changing the measured task. Exclusions cover pre-exposure
`documented-technical-interruption` and
`required-accommodation-unavailable`; the latter records unavailable
accommodations. Each participant includes boolean
`consulted_installation_directories` and `attempted_extension_command` fields.
Schema-negative fixtures separately reject
`sc_006_clear=true` when each prohibited-action field is true.
Semantic negative fixtures cover ineligible participants, duplicate
cross-stratum IDs, incorrect aggregates, invalid replacements or exclusions,
missing or non-reproducible allocation records, and mismatched requested and
provided accommodations. They also prove that the derived SC-006 count excludes
every participant who consulted installation directories or attempted an extension
command, even when that participant rated clarity 4 or 5.

## Quality Gates

Before strict mypy or package pytest/coverage, create an owner-only external
temporary directory. Set `MYPY_CACHE_DIR`, `COVERAGE_FILE`, and
`COVERAGE_RCFILE` there; the rc
is an external minimal coverage configuration. Pass
`--cov-report=xml:<external-temp>/package-coverage.xml`; the independent coverage
parser reads that file. Replace `<external-temp>` below with the absolute path.
Never write `.coverage*`, `coverage.xml`, or `package-coverage.xml` in the
repository.

```powershell
python scripts/spec001/run_local_gates.py -- uv sync --project tools/specify-cli --extra dev --locked
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev ruff check tools/specify-cli/src tools/specify-cli/tests
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev ruff format --check tools/specify-cli/src tools/specify-cli/tests
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev ruff check --config ruff.toml tools/specify-cli/src tools/specify-cli/tests
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev ruff format --check --config ruff.toml tools/specify-cli/src tools/specify-cli/tests
$env:MYPY_CACHE_DIR = '<external-temp>/mypy-cache'
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev mypy --strict tools/specify-cli/src tools/specify-cli/tests
$env:COVERAGE_FILE = '<external-temp>/.coverage'
$env:COVERAGE_RCFILE = '<external-temp>/.coveragerc'
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev pytest -c tools/specify-cli/pyproject.toml tools/specify-cli/tests -q --cov=specify_cli --cov-branch --cov-fail-under=90 --cov-report=xml:<external-temp>/package-coverage.xml
```

```sh
python scripts/spec001/run_local_gates.py -- uv sync --project tools/specify-cli --extra dev --locked
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev ruff check tools/specify-cli/src tools/specify-cli/tests
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev ruff format --check tools/specify-cli/src tools/specify-cli/tests
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev ruff check --config ruff.toml tools/specify-cli/src tools/specify-cli/tests
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev ruff format --check --config ruff.toml tools/specify-cli/src tools/specify-cli/tests
export MYPY_CACHE_DIR='<external-temp>/mypy-cache'
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev mypy --strict tools/specify-cli/src tools/specify-cli/tests
export COVERAGE_FILE='<external-temp>/.coverage'
export COVERAGE_RCFILE='<external-temp>/.coveragerc'
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev pytest -c tools/specify-cli/pyproject.toml tools/specify-cli/tests -q --cov=specify_cli --cov-branch --cov-fail-under=90 --cov-report=xml:<external-temp>/package-coverage.xml
```

The package suite includes an AST/import-boundary test forbidding imports from
root `apps` and `packages`. Coexistence assertions distinguish the real scope
owners: root CI invokes exactly `ruff check apps tests packages` and
`ruff format --check apps tests packages`, whose command-line selections
exclude `tools`; root `ruff.toml` includes `tools/**/*.py`; and unscoped
pre-commit `ruff` and `ruff-format` hooks cover package files. Package-local
Ruff uses the same line length 120, Python 3.12, and E/F/I/UP baseline, and the
two `--config ruff.toml` commands above prove repository pre-commit semantics
without editing or running auto-fixing root hooks. Root mypy, coverage, and
import-linter scopes exclude `tools`. Root `lint-imports` and
`scripts/coverage-ratchet.ps1` do not apply to `tools`; package-local boundary
and coverage gates replace them.

The reviewed `.github/workflows/ci.yml` edit adds `specify-cli-quality` on a
pre-registered runner labelled `self-hosted`, `ama-au-sovereign`, `azure-au`,
`linux`, and `x64`. Before package work, it queries IMDS and accepts only
`australiaeast` or `australiasoutheast`. Because implementation already exists,
the job runs protected-state green and one dispatcher/root-regression self-check
green, completes sovereign preflight, starts the verified encrypted AU daemon
session, routes every package command
through that peer-authenticated session, and finalizes it. Direct package
command execution is prohibited. It runs exact locked sync, package Ruff check
and format-check, strict mypy, package pytest with branch data, wheel build,
clean external install, and both installed entry-point smokes, then parses the
machine-readable coverage report to require line coverage at least 90.00%.
`--cov-fail-under=90` alone is not independent line-coverage proof. Use
synthetic fixtures only. Upload no
artifact/evidence and print no extension inventory, source, or evidence payload;
retain only ordinary command status and minimized failure summaries. This job
is an automated PR quality gate, never platform evidence. Actual PR lint, unit,
integration, and `specify-cli-quality` results must all be green before merge.

Run root regression with the explicit selection from `.github/workflows/ci.yml`:

```text
python scripts/spec001/run_local_gates.py -- uv run --no-sync pytest tests/unit tests/contract tests/integration tests/simulation -m "not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging and not e2e and not load and not locust" --cov=apps --cov=packages --cov-report=xml --cov-report=term
```

A bare root pytest invocation is prohibited because it would recursively collect
unrelated projects. Do not modify root `pyproject.toml`, `ruff.toml`, or
`.pre-commit-config.yaml`.

Before dispatching this exact command, create a temporary directory outside the
repository. Set `COVERAGE_FILE` to a data file there and `COVERAGE_RCFILE` to a
generated owner-only rc file there. Copy root `[tool.coverage.run]` values
`source = apps,packages`, `branch = true`, and the root `omit` list, plus every
root `[tool.coverage.report]` value, then add
`[xml] output = <external-temp>/root-coverage.xml`. This preserves root coverage
semantics while redirecting the frozen `--cov-report=xml` argument. If coverage
cannot honor those external locations without changing the command arguments,
preflight blocks. Include repository `.coverage*` and `coverage.xml` paths/globs
in the guard's pre/post mutation checks; fail on creation or change and never
restore or delete a user's file.

Before any package source implementation, run that exact selection and capture
its exact exit code, normalized failure IDs, normalized collection-error IDs,
and output byte/line/SHA-256 metadata as an ephemeral external-temp object
validated by `specs/001-extension-list/contracts/root-regression-baseline.schema.json`.
The long-lived custodian daemon holds it only for the implementation session and deletes
raw output after normalization. If continuity is lost, recapture before source
edits or block. Local-synthetic loss after edits permits a new explicitly
discontinuous non-evidentiary segment from the current worktree. Sovereign daemon
or custody loss after edits is unconditionally blocking and recapture is prohibited. After
implementation, rerun exactly the same command and block on any new
normalized failure or collection error. Existing baseline failures are
documented and non-blocking for that segment only. T008 captures the actual
normalized failure and collection-error sets from the provisioned environment.
Later disappearance is allowed, but any identity absent from that baseline
blocks. Do not assume a literal count or path. A missing
baseline, command drift, or comparison
failure blocks. This behavioral guard never substitutes for protected-path
hash and raw Git-diff equality.

The external handoff requires two compliant standalone Azure VMs, IMDS, private
networking to a private AU Blob account/container, managed identities with Blob
Data Contributor scoped to that container, encryption/retention controls, and
an authorized security/compliance reviewer. This feature provisions none of
them. The operator supplies the storage-account ARM resource ID, container name,
and Blob URI, never a credential or SAS. Before its first read or write, each
mode uses managed identity to query ARM and fail closed unless the account is in
`australiaeast` or `australiasoutheast`, public network access is disabled, the
default network action is deny, and an approved private-endpoint connection
exists. It verifies that the Blob host belongs to that ARM account and resolves
only to private IP addresses, derives the standalone VM identity principal, and
requires exactly Storage Blob Data Contributor at the target container scope.
The reviewed trust bundle pins the exact private attestation endpoint, managed-
identity scope, versioned key ID, and public JWK. The script sends one closed
private-DNS HTTPS POST, no redirect/retry, under a five-second deadline and
accepts only an HTTP 200 `application/jose` response no larger than 16 KiB with
one compact JWS. It verifies signature, issuer/audience, nonce/session/resource
binding, lifetime/skew, and digest. Before every attested write it conditionally
creates a distinct immutable JTI marker; the locked container policy retains
that marker at least one day and evidence records marker creation, expiry,
policy, and operation. Any unverifiable condition blocks before evidence
access. Real collect and finalize each run only as children of their own verified
AU daemon session (bootstrap, start, guarded child, finalize); direct script
invocation is rejected. The external script emits only a value-free
success/failure summary. Collect conditionally creates one fragment per VM at
`spec001-extension-list/<validation_session_id>/fragments/<os>-<imds_vm_id>.json`.
Finalize conditionally creates the canonical document at
`spec001-extension-list/<validation_session_id>/final/platform-evidence.json`
only after both fragments and review validate. Same-key overwrite is prohibited.
No credentials or SAS tokens appear in code, configuration, evidence, or logs.
No evidence payload, command output, or review record is uploaded to GitHub,
committed, or stored outside Australia.

After T134 finalizes local custody, a human separately reviews the intended
change set, including `tools/specify-cli/uv.lock`, stages and commits it, pushes
the branch, opens a pull request, and runs the required PR and sovereign gates.
Those source-control actions are outside this implementation workflow.

The AU-resident canonical document contains the verified storage boundary and
pre-write attestation digest, the UUID session, exactly one Windows x64 standalone VM record
with product name/version and one Ubuntu x64 standalone VM record with
`distribution_id=ubuntu` and distribution version. Both records include VM
resource ID, VM ID, location, script/Python/package/lock metadata, exact command
outcomes, execution time, and RFC 8785 SHA-256 digest. Automated validation
proves internal consistency; the authorized pseudonymous reviewer records approved/rejected in
the AU store. A rejected review remains retained externally. The repository
handoff stays `pending-external` in prose only; no status JSON or platform
payload is instantiated under the repository, regardless of external approval
or rejection.

## Manual Smoke Checks

Do not run these commands from the repository root: it contains the live
`.specify/extensions` inventory and local-synthetic must reject it. Run from
either a directory with no `.specify/extensions` ancestor to exercise empty
states, or a marker-bound synthetic fixture root beneath the active session's
owner-only temporary directory with `SPEC001_TEST_MODE=synthetic`.
The following no-root examples capture absolute repository paths before moving
to a disposable external working directory, so the script and package remain
addressable without exposing the live repository inventory.

```powershell
$RepoRoot = (Resolve-Path '.').Path
$SmokeRoot = Join-Path $env:TEMP ('spec001-smoke-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $SmokeRoot | Out-Null
$env:SPEC001_TEST_MODE = 'synthetic'
Set-Location $SmokeRoot
try {
   python "$RepoRoot/scripts/spec001/run_local_gates.py" -- uv run --project "$RepoRoot/tools/specify-cli" ama-specify extension list
   python "$RepoRoot/scripts/spec001/run_local_gates.py" -- uv run --project "$RepoRoot/tools/specify-cli" ama-specify extension list --available
   python "$RepoRoot/scripts/spec001/run_local_gates.py" -- uv run --project "$RepoRoot/tools/specify-cli" ama-specify extension list --all
   python "$RepoRoot/scripts/spec001/run_local_gates.py" -- uv run --project "$RepoRoot/tools/specify-cli" ama-specify extension list --json
   python "$RepoRoot/scripts/spec001/run_local_gates.py" -- uv run --project "$RepoRoot/tools/specify-cli" ama-specify extension list --available --json
   python "$RepoRoot/scripts/spec001/run_local_gates.py" -- uv run --project "$RepoRoot/tools/specify-cli" ama-specify extension list --all --json
} finally {
   Set-Location $RepoRoot
   Remove-Item -Recurse -Force $SmokeRoot
}
```

```sh
REPO_ROOT="$(pwd -P)"
SMOKE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/spec001-smoke.XXXXXX")"
chmod 700 "$SMOKE_ROOT"
export SPEC001_TEST_MODE=synthetic
trap 'cd "$REPO_ROOT"; rm -rf "$SMOKE_ROOT"' EXIT
cd "$SMOKE_ROOT"
python "$REPO_ROOT/scripts/spec001/run_local_gates.py" -- uv run --project "$REPO_ROOT/tools/specify-cli" ama-specify extension list
python "$REPO_ROOT/scripts/spec001/run_local_gates.py" -- uv run --project "$REPO_ROOT/tools/specify-cli" ama-specify extension list --available
python "$REPO_ROOT/scripts/spec001/run_local_gates.py" -- uv run --project "$REPO_ROOT/tools/specify-cli" ama-specify extension list --all
python "$REPO_ROOT/scripts/spec001/run_local_gates.py" -- uv run --project "$REPO_ROOT/tools/specify-cli" ama-specify extension list --json
python "$REPO_ROOT/scripts/spec001/run_local_gates.py" -- uv run --project "$REPO_ROOT/tools/specify-cli" ama-specify extension list --available --json
python "$REPO_ROOT/scripts/spec001/run_local_gates.py" -- uv run --project "$REPO_ROOT/tools/specify-cli" ama-specify extension list --all --json
```

At 80x24 and 40x12 with colour disabled, and with output redirected to plain
text, verify every record appears exactly once. Every row retains literal
labels `Installed`, `Activation`, `Health`, `Commands`, and `Hooks`; disabled,
invalid, and conflict remain exact words; normalized output has no ANSI escape
sequences; wrapping preserves label/value token order; and pager/input entry
points fail the test if invoked. This is an observable output oracle, not a
claim that automated tests prove general human comprehension. The repository's
live `.specify/` tree is never read and remains byte-for-byte unchanged.

## Independent Packaging Proof

Build the wheel, install only that artifact into a clean temporary environment,
and exercise both installed entry points through the tested packaging focus:

```powershell
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev pytest -c tools/specify-cli/pyproject.toml tools/specify-cli/tests/test_packaging.py -q
```

```sh
python scripts/spec001/run_local_gates.py -- uv run --project tools/specify-cli --extra dev pytest -c tools/specify-cli/pyproject.toml tools/specify-cli/tests/test_packaging.py -q
```

The two external standalone VMs perform the equivalent with platform-native
virtual-environment executable paths on Windows and Ubuntu. Smoke tests run from
outside the source tree
so an editable checkout cannot satisfy imports accidentally. The temporary
working directory must also be outside any ancestor containing
`.specify/extensions`. With no fixture root, both JSON commands emit `[]` and
exit 0. Text smokes additionally prove installed, available, and all
scope-specific empty messages. No catalog configuration can be discovered
without an explicit project-root fixture.

## SC-002 Benchmark

Use a deterministic fixture with a non-empty fixture ID and fixture count 100,
installed-only JSON mode, and feature/public transport disabled. Start and
verify one daemon session and materialize the fixture before timing. Permit only
peer-authenticated local IPC and pinned private AU audit/control-plane traffic.
Record OS, architecture, CPU
model and logical count, total memory bytes, Python version, package version,
lock SHA-256, optional baseline runner identifier, `network_disabled=true`,
fixture ID/count, all three warmup outcomes, exactly 30 measured durations,
nearest-rank `rank=29`, computed P95, `threshold_seconds=2.000`, passed boolean,
and RFC 3339 timestamp. Measure each fresh client from cold child-process
creation through complete stdout read, including peer handshake, installed
processing, and both audit-ledger appends. Exclude daemon startup, IMDS/session
preflight, and fixture materialization. Do not reuse a client interpreter
process or include catalog configuration.

No runtime evidence is written beneath repository `artifacts/` or elsewhere in
the repository. Read-only and performance payloads exist only in external
temporary storage while schema and semantic validation run, then are deleted.
If the local machine is not verified AU-resident and authorized, retain no
runtime payload at all; show only pass/fail status. Sovereign platform and human
study evidence exist only in their pre-provisioned authorized AU-resident
stores. Until those activities occur, document `sovereign-external-platform`
and `human-study` as `pending-external` in this specification, the external
handoff, and checklists, never in a repository runtime-status JSON file.

The representative-user protocol uses exactly 20 included unique adult
participants: exactly 10 novice and exactly 10 experienced Spec Kit users. All
included participants use command-line developer tools at least monthly and
have no prior exposure to the feature or fixture. Novices have 0-2 completed
Spec Kit workflows in the prior 6 months and no prior extension-management use;
experienced participants have at least 5 completed workflows and prior
extension-management use.

Set `allocation_algorithm` to `sha256-seeded-stratified-order-v1`, record a
64-character lowercase hexadecimal seed, and declare at least two unique
non-empty task variants. Within each stratum, sort eligible anonymized IDs,
order by SHA-256 of `<seed>:<stratum>:<participant_id>` with participant ID as
the final tie-break, and assign task variants round-robin in declared order.
Record one exactly recomputable allocation per included participant.

Before collection, provide Privacy Act-compliant participant notice and record
explicit consent for the limited SC-001/SC-006 purpose. Generate pseudonymous
random participant IDs independently from names or contact data. Evidence MUST
contain no name, email, employer, precise location, medical detail, or free-text
PII. Keep the re-identification key and recruitment records separate from study
evidence in authorized AU stores with named least-privilege study-team access,
immutable access audit, and encryption in transit and at rest. Retain evidence
no longer than 90 days after review, then verify deletion unless an approved
legal hold applies. Honor withdrawal before de-identification or aggregation and
use the documented breach/incident process.

Provide every requested accessibility accommodation without changing the
measured task. Record only closed generic accommodation category codes. If
required support is unavailable, exclude the person before task exposure as
`required-accommodation-unavailable`, record only unavailable category codes,
and replace within the same stratum. Record no medical detail. A pre-exposure
`documented-technical-interruption` remains allowed. After exposure, retain
complete, incorrect, timed-out, or abandoned outcomes.
Before publishing or gating the evidence, validate it against
`usability-evidence.schema.json`, then run the AMA-local semantic validator. The
validator recomputes eligibility and allocation and requires requested and
provided accommodations to match exactly for every included participant.
It also recomputes the SC-001 truth table from separate installed-answer,
enabled-answer, and elapsed-time fields and rejects any participant or aggregate
that disagrees. SC-001 requires both answers correct within 30 seconds, with at
least 19 of the 20 included participants succeeding. For SC-006,
record required booleans `consulted_installation_directories` and
`attempted_extension_command` for every participant. Count a 4 or 5 clarity rating
only when both values are false, and require at least 18 of 20 included participants
to qualify; recompute and reject aggregate disagreement for both SC-001 and
SC-006.

Implementation creates the protocol, validates the existing schema and extends
it only if a required constraint is absent, implements the semantic validator,
and supplies an anonymized template/fixture plus handoff instructions.
Conducting the study and proving SC-001/SC-006 are external human validation;
no generated local artifact may claim they passed.

To expose the command outside `uv run` while retaining AMA-local ownership:

```powershell
python scripts/spec001/run_local_gates.py -- uv tool install --editable .\tools\specify-cli
python scripts/spec001/run_local_gates.py -- ama-specify extension list
```

```sh
python scripts/spec001/run_local_gates.py -- uv tool install --editable ./tools/specify-cli
python scripts/spec001/run_local_gates.py -- ama-specify extension list
```

This install is independent of the root AMA application environment and does
not change existing application entry points or imports.

## Root Isolation Proof

Before package synchronization, build, clean installation, or smoke execution,
capture a SHA-256 digest or `absent` for each path in this exact protected
manifest: `pyproject.toml`, optional `uv.lock`, `package.json`,
`pnpm-workspace.yaml`, `azure.yaml`, `ruff.toml`, `.pre-commit-config.yaml`,
`.github/workflows/ci.yml`, `apps/api/Dockerfile`,
`apps/api/app/main.py`, `apps/agents/Dockerfile`,
`apps/agents/dispatcher/__main__.py`,
`apps/agents/communication/__main__.py`,
`apps/agents/evacuation/__main__.py`,
`apps/agents/maf_runtime/workflow/builder.py`,
`apps/ingestion/Dockerfile`, `apps/ingestion/worker.py`, and
`apps/web/package.json`.

Build the Git pathspec once from the protected paths that exist before the
operations. Separately execute `git diff --binary --no-ext-diff -- <paths>` and
`git diff --cached --binary --no-ext-diff -- <paths>`, retain each raw stdout
byte stream only in memory, compare pre/post bytes exactly, and keep its
SHA-256 digest and equality result only in the external temporary guard state.
Never write raw diff bytes, digests, equality payloads, or Base64
representations to an artifact or log. After all operations, recapture every
manifest path and both Git streams using that original existing-path set. Every
path state, ephemeral byte stream, and persisted digest must equal its
pre-operation value. A dirty baseline is valid: never revert, stash, commit,
remove, or alter existing user changes. An optional path absent before
operations remains `absent`.

## Evidence Dependencies

Each schema/fixture stream begins after its real prerequisites and does not wait
for unrelated documentation:

1. **Platform**: package metadata and isolated smokes -> platform evidence
   schema -> schema fixtures/tests -> prose-only pending handoff -> external
   script tests -> handoff -> two operator-triggered standalone VM runs ->
   direct AU Blob write -> pseudonymous closed-coded external review in the AU store.
2. **Read-only**: protected-manifest snapshots and mutation/privacy tests ->
   read-only evidence shape -> schema fixtures/tests -> producer tests ->
   mutation spies and smoke -> ephemeral validation -> deletion.
3. **Performance**: deterministic 100-record fixture + harness + performance
   evidence schema -> schema fixtures/tests -> 3 warmups + 30 measured cold
   processes -> nearest-rank P95 -> ephemeral evidence validation -> deletion.
4. **Usability**: protocol -> existing usability schema verification or minimal
   extension -> anonymized fixture/template -> semantic tests -> semantic
   validator -> prose `pending-external` handoff -> 20-person study in an
   authorized AU store ->
   schema validation -> semantic validation -> SC-001/SC-006 evaluation.

The root-regression baseline is a local attribution guard adjacent to, but not a fifth
substitute for, these four chains. Implement and test baseline capture/compare
in one module; assemble package-local gate commands separately; integrate both
in a later orchestrator; and execute the final gate only after those units pass.
Pre-existing baseline failures may be tolerated only for attribution. This is
not merge readiness: actual pull-request lint, unit, and integration jobs must
all be green before merge.
