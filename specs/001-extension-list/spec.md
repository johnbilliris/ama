# Feature Specification: Extension List

**Feature Branch**: `001-extension-list`  
**Created**: 2026-09-14  
**Status**: Design Revision; Local Development Allowed; Sovereign Validation Pending  
**Input**: User description: "extension list"

## Clarifications

### Session 2026-09-20

- Q: Which entries should the available extensions view show? → A: Show all catalog entries and mark installed ones.
- Q: How should duplicate catalog entries with the same stable identifier be shown? → A: Show one conflicted entry listing all reported versions.
- Q: What should the available-only view display when catalog retrieval fails? → A: Display installed extensions with a catalog-unavailable warning.
- Q: Which activation states should an installed extension display? → A: Disabled, inactive, active, or activation-failed.

### Session 2026-09-21

- Q: Which metadata health states should an installed extension display? → A: Exactly healthy or invalid, with a diagnostic reason for invalid entries.
- Q: How should an installed record missing its stable identifier be represented? → A: Show it separately using source location as a fallback identity and never reconcile it with catalog records.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Installed Extensions (Priority: P1)

As a Spec Kit user, I want to list the extensions installed for my working environment so that I can quickly confirm which capabilities are available before starting a workflow.

**Why this priority**: The primary purpose of the feature is to make installed extensions visible. Without this view, users must inspect project files or attempt commands to determine what is available.

**Independent Test**: Install two known extensions, request the default extension list, and verify that both extensions are shown with enough identity and status information to distinguish them.

**Acceptance Scenarios**:

1. **Given** one or more extensions are installed, **When** the user requests the extension list without an availability option, **Then** every installed extension is shown once and catalog-only extensions are excluded.
2. **Given** an installed extension has complete metadata, **When** the list is displayed, **Then** the user can see its name, stable identifier, version, description, operational status, and capability summary.
3. **Given** no extensions are installed, **When** the user requests the extension list, **Then** the user receives a clear empty-state message rather than an empty or misleading result.

---

### User Story 2 - Identify Extension Problems (Priority: P2)

As a Spec Kit user troubleshooting a missing command or hook, I want the extension list to identify disabled or invalid extensions so that I know whether the extension installation needs attention.

**Why this priority**: Visibility alone is insufficient when an installed extension cannot be used. A clear health and activation state reduces troubleshooting time and prevents users from assuming that all listed extensions are operational.

**Independent Test**: Provide one valid extension and one extension with unreadable or incomplete metadata, request the installed list, and verify that the valid extension remains visible while the problematic extension is identified as invalid with a diagnostic reason.

**Acceptance Scenarios**:

1. **Given** an installed extension activated successfully and has valid metadata, **When** the list is displayed, **Then** it is explicitly identified as active and healthy.
2. **Given** an installed extension is disabled, **When** the list is displayed, **Then** it remains visible and is explicitly identified as disabled.
3. **Given** an installed extension is enabled but has not activated, **When** the list is displayed, **Then** it remains visible and is explicitly identified as inactive.
4. **Given** activation was attempted and failed, **When** the list is displayed, **Then** the extension remains visible and is explicitly identified as activation-failed.
5. **Given** an installed extension has missing or malformed required metadata, **When** the list is displayed, **Then** the extension is identified as invalid with a diagnostic reason without preventing other extensions from being listed.
6. **Given** visual styling is unavailable or cannot be perceived, **When** the list is displayed, **Then** health and activation states remain understandable from text or symbols with text equivalents rather than colour alone.
7. **Given** an installed extension record is missing its stable identifier, **When** the list is displayed, **Then** it appears as a separate invalid entry identified by its source location, includes at least one metadata-health diagnostic, and is not reconciled with any catalog record.

---

### User Story 3 - Discover Available Extensions (Priority: P3)

As a Spec Kit user, I want to view extensions available from the configured catalog and compare them with installed extensions so that I can discover capabilities without accidentally reinstalling something I already have.

**Why this priority**: Catalog discovery adds value after the installed inventory and health information are reliable. It expands the feature from local verification to informed extension selection.

**Independent Test**: Use a catalog containing one installed extension and one catalog-only extension plus one installed extension absent from the catalog, request the available and combined views, and verify that the available view shows all catalog entries with installation state while the combined view also includes the local-only extension.

**Acceptance Scenarios**:

1. **Given** the extension catalog is available, **When** the user requests available extensions, **Then** all catalog entries are shown with identity, version, summary, and installation state, including entries that are already installed.
2. **Given** an extension exists in both the installed inventory and the catalog, **When** the user requests the combined view, **Then** the extension appears once and is identified as installed.
3. **Given** the catalog cannot be reached or read, **When** the user requests an available or combined view, **Then** all locally installed extensions are shown with a catalog-unavailable warning and are not represented as catalog results.
4. **Given** the catalog contains multiple records with the same stable identifier, **When** the user requests an available or combined view, **Then** one conflicted entry is shown and lists every version reported by those records.

### Edge Cases

- No extensions are installed and no catalog entries are available.
- An installed extension is missing optional metadata such as a description or version.
- An extension record is present but its required identity metadata is missing or malformed.
- Multiple installed records without stable identifiers report the same display name or source location.
- Registry and physical records without stable identifiers refer to the same
  normalized source through path aliases, separator differences, dot segments,
  case aliases on case-insensitive platforms, or a resolvable symbolic link.
- Registry and physical observations refer to the same normalized source and
  report the same valid stable identifier.
- Registry and physical observations refer to the same normalized source but
  report contradictory valid stable identifiers.
- Distinct normalized physical sources report the same valid stable identifier.
- Distinct identifier-less source locations share the same display name but
  must remain separate rows.
- Multiple extensions have the same display name but different stable identifiers.
- The same stable identifier appears more than once in the installed inventory.
- The same stable identifier appears more than once in the catalog with matching or different reported versions.
- An installed extension and a catalog extension share an identifier but report different versions.
- An extension reports an unknown or unsupported activation-state value.
- The catalog is unavailable, times out, or returns incomplete information.
- The list contains enough extensions to exceed one screen of output.
- Terminal styling, symbols, or colour support is limited.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an extension-list action that users can invoke without changing extension installation or activation state.
- **FR-002**: By default, the extension-list action MUST show all locally installed extensions and MUST exclude extensions that are only available from the catalog.
- **FR-003**: Users MUST be able to request an available view containing all extensions from the configured catalog, including installed extensions, with each entry marked by installation state.
- **FR-004**: Users MUST be able to request a combined view of installed and catalog-available extensions.
- **FR-005**: Each extension entry MUST display its human-readable name, a valid stable identifier when present or otherwise the FR-020 fallback identity, version when known, and description when known.
- **FR-006**: Each installed extension entry MUST display exactly one activation state: disabled when explicitly disabled, inactive when enabled but not activated, active when activation succeeded, or activation-failed when activation was attempted but did not succeed. An activation-failed entry MUST project and display a non-empty activation diagnostic; disabled, inactive, active, and null activation states MUST project a null activation diagnostic. The activation diagnostic is independent of metadata health, which MUST be displayed separately as exactly healthy or invalid.
- **FR-007**: Each installed extension entry MUST summarize the user-facing capabilities it contributes, including the number of registered commands and hooks.
- **FR-008**: The list MUST communicate activation, health, and installation states without relying on colour alone.
- **FR-009**: A missing optional metadata value MUST be shown as unavailable or omitted without causing the entire list operation to fail.
- **FR-010**: A malformed or incomplete installed extension MUST remain visible as an invalid entry with a diagnostic reason, and MUST NOT prevent valid extensions from being listed.
- **FR-011**: A combined view MUST reconcile entries by stable identifier so that an installed extension also present in the catalog appears once and is marked as installed.
- **FR-012**: If installed and catalog records for the same extension report different versions, the combined view MUST distinguish the installed version from the catalog version.
- **FR-013**: Before grouping installed records by stable identifier, registry and physical observations resolving to the same normalized physical source and the same valid stable identifier MUST coalesce into one installed source record that combines registry state with manifest metadata and retains both observations as evidence. Only distinct normalized physical sources sharing a stable identifier MUST be reported as duplicate-installed conflicts. Same-source observations with contradictory valid stable identifiers MUST become one invalid local identity-conflict record and MUST NOT become separate healthy rows.
- **FR-014**: Extension entries MUST be ordered consistently by human-readable name, with stable identifier used to resolve equal names.
- **FR-015**: When a requested list contains no matching extensions, the system MUST display a clear empty-state message that identifies which view was empty.
- **FR-016**: When catalog information cannot be retrieved for an available-only view, the system MUST display all locally installed extensions with a catalog-unavailable warning and MUST NOT represent them as catalog results.
- **FR-017**: In a combined view, a catalog retrieval failure MUST display all locally installed extensions with a catalog-unavailable warning and MUST NOT represent a partial catalog result as complete.
- **FR-018**: Text-output tests MUST exercise terminals sized 80x24 and 40x12 with colour disabled, plus redirected plain text. Every rendered record MUST appear exactly once and retain the literal labels `Installed`, `Activation`, `Health`, `Commands`, and `Hooks`; disabled, invalid, and conflict states MUST remain those exact words; normalized output MUST contain no ANSI escape sequence; wrapped output MUST preserve label/value token order; and rendering MUST invoke no pager or input prompt. This observable oracle replaces any automated claim of general human comprehension.
- **FR-019**: Duplicate catalog records with the same stable identifier MUST be consolidated into one conflicted entry that lists every distinct version reported by those records.
- **FR-020**: An installed record missing its stable identifier MUST be displayed as a separate invalid entry using its source location as fallback identity, MUST include at least one metadata-health diagnostic, and MUST NOT be reconciled with any catalog record. Its independently derived `activation_diagnostic` continues to follow FR-006.
- **FR-021**: Each configured catalog source MUST have a 5-second total deadline measured with a monotonic clock from source processing start through complete schema validation. Local files MUST be rejected before parsing when their file size exceeds 1 MiB and MUST also use a bounded read of at most 1,048,577 bytes to detect a growth race. Remote sources MUST propagate the remaining deadline budget through DNS/connection establishment, each of at most 5 redirects, streamed decoded-body reads, decoding, JSON parsing, and schema validation; accept only HTTPS URLs and redirect targets; and reject decoded bodies larger than 1 MiB. HTTP loopback endpoints MAY be used only by isolated tests and MUST NOT be accepted from production catalog configuration.
- **FR-022**: Any catalog source safety-limit, retrieval, decoding, JSON, or schema-validation violation MUST be treated as a source failure; one source failure MUST discard all catalog results collected during that invocation and trigger the catalog-unavailable behavior in FR-016 and FR-017.
- **FR-023**: Catalog configuration MUST contain at most 8 sources, and each validated catalog source MUST contain at most 1,000 extension records. The 5-second deadline applies independently to each source; no separate invocation-wide deadline is required.
- **FR-024**: A schema-valid catalog-only record MUST default to `healthy`, MUST have no activation state, and MUST normalize omitted command, template, script, and hook counts to zero. Catalog version MUST be either a non-empty string or null/omitted; null/omitted normalizes to `unknown`, and empty string is invalid. A catalog duplicate conflict MUST instead be `invalid` with non-empty diagnostics.
- **FR-025**: Identifier-less installed records with the same normalized source MUST consolidate into one invalid conflict row retaining every contributing source record as evidence. Identifier-less records from distinct normalized sources MUST remain separate even when names collide, and none may reconcile with catalog records.
- **FR-026**: Duplicate catalog records MUST be ordered for preferred-field selection by ascending numeric priority, case-folded then raw catalog name, privacy-minimized canonical record SHA-256, and source ordinal only as a final tie-break for byte-identical records. Preferred fields MUST therefore be independent of source record order. Source ordinal and record SHA-256 remain retained evidence; raw canonical records, author values, and alternate free-text descriptions MUST NOT be emitted. Every differing field MUST be named by conflict reasons, every distinct version MUST remain in `available_versions`, and conflicting `install_allowed` values MUST project false.
- **FR-027**: A reconciled installed-plus-catalog row MUST use source kind `combined` and retain both installed source-location evidence and catalog source evidence.
- **FR-028**: Human-mode rows and scope-specific empty states MUST be written to stdout. Warnings and runtime errors MUST be written to stderr. A runtime failure MUST write no partial table unless FR-016 or FR-017 applies. In human mode, Typer usage errors MUST write usage/help to stderr, leave stdout empty, and exit 2. In JSON mode, usage errors MUST suppress Typer usage prose, leave stdout empty, write exactly one compact JSON error object followed by one newline to stderr, and exit 2. An explicit `--help` MUST take precedence over `--json`, use normal human help on stdout, leave stderr empty, and exit 0. Exact-output tests MUST cover every channel, newline, and exit-code rule.
- **FR-029**: The AMA-local CLI MUST be independently packageable and verifiable with `uv build`, installation of the built wheel into a clean temporary environment outside the repository root, an installed `ama-specify extension list --json` console-script smoke test, and a `python -m specify_cli extension list --json` smoke test. The package is a compatible standalone subset and MUST NOT replace, augment, or shadow an existing upstream `specify` executable. Runtime dependencies MUST use bounded compatible ranges; development dependencies MUST be declared under `[project.optional-dependencies].dev`; package metadata MUST include package-scoped `[tool.pytest.ini_options]` with package test paths, import mode, strict marker handling, and coverage defaults; `tools/specify-cli/README.md` MUST exist when declared as package metadata; and `tools/specify-cli/uv.lock` MUST be generated and consumed reproducibly. `tools/specify-cli/pyproject.toml` MUST retain repository-convention index metadata named `microsoft-package-feed-proxy`. Local-synthetic dependency bootstrap MAY contact only that configured HTTPS proxy or use an existing cache, because it processes no real or regulated data. Sovereign CI/build/install MUST use exactly `UV_OFFLINE=1 uv sync --project tools/specify-cli --extra dev --locked` through a pre-seeded cache produced by an authorized AU package mirror and MUST fail on DNS, socket, HTTP, proxy, index, or public-endpoint access. No implementation step requires committing the lock file.
- **FR-030**: Usability evidence publication and gating MUST validate document shape against the existing `usability-evidence.schema.json` and then invoke the AMA-local semantic validator. Every included participant MUST be an adult, use command-line developer tools at least monthly, and have no prior exposure to this feature or test fixture. A novice MUST have completed 0-2 Spec Kit workflows in the prior 6 months and have no prior extension-management use. An experienced participant MUST have completed at least 5 Spec Kit workflows in the prior 6 months and have prior extension-management use. Every included record MUST contain `is_adult=true`, `uses_cli_monthly=true`, `prior_feature_exposure=false`, non-negative integer `spec_kit_workflows_last_6_months`, boolean `used_extension_management`, and boolean `consulted_installation_directories` and `attempted_extension_command` evidence fields. Top-level allocation evidence MUST use `allocation_algorithm=sha256-seeded-stratified-order-v1`, a 64-character lowercase hexadecimal `allocation_seed`, and at least two unique non-empty `task_variants`. For each stratum, semantic validation MUST sort eligible anonymized IDs, order them by SHA-256 of `<seed>:<stratum>:<participant_id>` with participant ID as final tie-break, assign task variants round-robin in declared order, and require allocation records to match recomputation exactly. The validator MUST also enforce exactly 20 unique included IDs comprising exactly 10 novice and exactly 10 experienced participants, stratum membership and counts, aggregates derived from participant records, valid pre-exposure exclusions and distinct same-stratum replacements, fulfillment of every requested accommodation, and that a participant counts toward SC-006 only when the clarity rating is 4 or 5 and both prohibited-action fields are false. If a requested accommodation cannot be provided, the person MUST be excluded before task exposure with reason `required-accommodation-unavailable`, the unavailable accommodations MUST be recorded, and the person MUST be replaced within the same stratum. Pre-exposure `documented-technical-interruption` remains permitted. Every post-exposure outcome MUST remain included. The schema MUST allow each aggregate success count from 0 through 20 so a completed failed study remains valid evidence. The semantic validator MUST recompute participant booleans and aggregate counts, require stored values to equal recomputation, and separately report whether SC-001 meets 19/20 and SC-006 meets 18/20. External completion means the study was validated and reviewed, not that either criterion passed. The existing schema MUST be verified and extended only when a required shape constraint is absent; it MUST NOT be recreated merely because implementation begins.
- **FR-031**: Installed-only execution through either supported entry point MUST keep the cold client free of Requests, jsonschema, and all catalog modules; verification MUST inspect the completed cold client process's `sys.modules` and prove those modules absent. Because the pre-started daemon may already load HTTP dependencies for mandatory private AU audit, daemon verification MUST snapshot `sys.modules` before installed-only handling and prove that handling newly imports neither `specify_cli.extensions.catalogs` nor any feature catalog transport module and initiates no Requests/jsonschema import. Pre-existing audit-stack transitive modules are not an installed-path failure. Both entry points MUST preserve this boundary within SC-002.
- **FR-032**: Remote catalog supervision MUST use `multiprocessing.get_context("spawn")` on every platform and a module-level picklable worker target. Deterministic tests MUST prove spawn-context selection, timeout termination, bounded join, and process/queue/resource cleanup for success, failure, and deadline expiry.
- **FR-033**: Package setup, lock generation, build, and smoke verification MUST
  protect this exact manifest: `pyproject.toml`, optional `uv.lock`,
  `package.json`, `pnpm-workspace.yaml`, `azure.yaml`, `ruff.toml`,
  `.pre-commit-config.yaml`, `.github/workflows/ci.yml`,
  `apps/api/Dockerfile`, `apps/api/app/main.py`, `apps/agents/Dockerfile`,
  `apps/agents/dispatcher/__main__.py`,
  `apps/agents/communication/__main__.py`,
  `apps/agents/evacuation/__main__.py`,
  `apps/agents/maf_runtime/workflow/builder.py`,
  `apps/ingestion/Dockerfile`, `apps/ingestion/worker.py`, and
  `apps/web/package.json`. One intentional reviewed source edit to
  `.github/workflows/ci.yml` is permitted outside package command execution
  solely to add the `specify-cli-quality` job required by FR-034; no requirement
  treats the workflow's pre-edit bytes as the implementation artifact.
  Immediately after that edit and before any later executable operation,
  verification MUST establish the workflow's post-edit state as its protected
  baseline. Before any package operation, verification MUST record in external
  temporary guard state a SHA-256 digest or `absent` for every protected path.
  Over the protected paths that exist before operations, verification MUST
  separately capture the raw stdout bytes produced by
  `git diff --binary --no-ext-diff -- <paths>` and
  `git diff --cached --binary --no-ext-diff -- <paths>`, compare each pre/post
  byte stream exactly in memory, and keep each SHA-256 digest and equality result
  only in that external temporary state. Raw diff bytes, digests, equality
  payloads, Base64 encodings, unredacted process output, secrets, absolute paths,
  query values, and raw exceptions MUST NOT be written to repository artifacts
  or logs. Every later executable operation MUST recapture every per-path value
  and both ephemeral Git byte streams using the original existing-path set and
  MUST preserve the post-edit workflow state and all other protected state
  exactly. Existing unstaged, staged, and untracked user content is allowed and
  MUST NOT be reverted, stashed, committed, removed, or altered. An absent
  optional path MUST remain recorded as `absent` and MUST NOT fail merely because
  it was absent initially.
- **FR-034**: The independently packaged tool MUST live at `tools/specify-cli`, outside root mypy strict targets `apps packages`, coverage sources `apps,packages`, and import-linter roots `apps,packages`; root `pyproject.toml`, `ruff.toml`, `.pre-commit-config.yaml`, and their configured scopes MUST remain unchanged. Root CI continues to invoke its existing Ruff selections exactly as `ruff check apps tests packages` and `ruff format --check apps tests packages`; root `ruff.toml` and unscoped pre-commit Ruff hooks still cover `tools/**/*.py`. The intentional `.github/workflows/ci.yml` edit MUST make the existing `quality` job emit a changed-path output computed from the event base/head diff and true only for `tools/specify-cli/**`, `scripts/spec001/**`, or `specs/001-extension-list/**`; one automated job named `specify-cli-quality` MUST depend on that output and use a job-level `if` so no sovereign runner is requested for unrelated changes. The job MUST set `timeout-minutes: 30`, run only on a pre-registered sovereign self-hosted AU Linux x64 runner with labels `self-hosted`, `ama-au-sovereign`, `azure-au`, `linux`, and `x64`, unset inherited `PIP_INDEX_URL`/`UV_DEFAULT_INDEX`, set `PIP_NO_INDEX=1` and `UV_OFFLINE=1`, and reject any installer network access. Before package work, it MUST query Azure IMDS and fail unless the physical location is `australiaeast` or `australiasoutheast`. It MUST run exactly `uv sync --project tools/specify-cli --extra dev --locked`, package-local Ruff check and format-check, strict mypy, package pytest with branch coverage and at least 90% line coverage, wheel build, offline clean external installation, and both installed entry-point smokes. The job MUST use only synthetic fixtures, upload no artifact or evidence, print no extension inventory/source/evidence payload, and emit only normal status or minimized failures. It is PR quality validation, not sovereign platform evidence. Package-local Ruff MUST match line length 120, Python 3.12, and E/F/I/UP, and the package owns strict mypy, branch coverage, build, clean-install smokes, and an AST boundary forbidding root `apps` or `packages` imports. Package tests run exactly as `uv run --project tools/specify-cli pytest -c tools/specify-cli/pyproject.toml tools/specify-cli/tests -q`. Root regression MUST preserve the exact pytest argument selection `pytest tests/unit tests/contract tests/integration tests/simulation -m "not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging and not e2e and not load and not locust" --cov=apps --cov=packages --cov-report=xml --cov-report=term`. Before dispatch, the guard MUST create a temporary directory outside the repository, set `COVERAGE_FILE` and `COVERAGE_RCFILE` to files there, and write a temporary coverage rc that imports root coverage semantics while overriding `[xml] output` into that directory. If the exact command cannot honor isolated coverage output without argument changes, preflight MUST block. The guard MUST include repository `.coverage*` and `coverage.xml` paths/globs in pre/post mutation checks and fail if any such path is created or changed; it MUST NOT restore or delete user files. Before package source implementation, capture the root result and after implementation compare the same exact selection to the dirty-worktree baseline. Existing failures are attribution only; new normalized failures or collection errors block. A bare root pytest invocation is prohibited, and baseline comparison does not weaken FR-033.
- **FR-035**: Implementation MUST provide one checked-in script at `scripts/spec001/run_external_platform_validation.py` with locally tested `collect` and `finalize` modes, but MUST NOT externally execute either mode during implementation. An operator later runs `collect` once on a standalone Windows x64 Azure VM and once on a standalone Ubuntu Linux x64 Azure VM. Each VM MUST use Azure IMDS to prove a `Microsoft.Compute/virtualMachines` resource ID, VM ID, and physical location of `australiaeast` or `australiasoutheast`; VM scale sets are not admissible. Each collect run MUST validate its record and digest, then write exactly one fragment over TLS with managed identity and create-if-absent semantics to `spec001-extension-list/<validation_session_id>/fragments/<os>-<imds_vm_id>.json`; same-key overwrite is prohibited. `validation_session_id` MUST be a UUID shared by both fragments. After both fragments exist, an operator in the AU environment runs `finalize`. Finalize MUST read exactly one Windows and one Ubuntu fragment for the same validation session, package, lock, and script version; validate each fragment contract and RFC 8785 digest; assemble the canonical document; record an authorized security/compliance review using only a pseudonymous reviewer identifier and closed decision/reason codes; validate the canonical schema and hosted lifecycle semantics; and conditionally create `spec001-extension-list/<validation_session_id>/final/platform-evidence.json`. A rejected review remains retained externally and MUST NOT change repository pending status. The script MUST suppress evidence values and command payloads from terminal output and emit only a value-free success/failure summary. The private AU Blob container MUST be in Australia East or Australia Southeast, use a private endpoint and TLS, and authorize only managed identities with Blob Data Contributor scoped to that container. Credentials and SAS tokens MUST NOT appear in code, configuration, evidence, or logs. Evidence, fragments, command outputs, canonical documents, and review records MUST never be uploaded to GitHub artifacts or logs, committed to the repository, or stored on non-AU services. The existing `contracts/platform-evidence.schema.json` is the canonical finalized-document schema and MUST validate `schema_version=1.0`, `feature=001-extension-list`, `category=sovereign-external-platform`, the UUID `validation_session_id`, exactly one Windows x64 record and one Ubuntu x64 record, and top-level review; it MAY define fragment shape under `$defs`. Each record MUST contain only its standalone Azure VM resource ID, IMDS VM ID, location, OS and architecture, script version, Python/package/lock metadata, exact command outcomes, execution timestamp, and `evidence_digest`. Ubuntu MUST have `distribution_id=ubuntu` and non-empty `distribution_version`; Windows MUST have non-empty `windows_product_name` and `windows_version`. Each digest is lowercase SHA-256 over RFC 8785 canonical JSON UTF-8 bytes of the record with `evidence_digest` omitted. JSON Schema validates shape only. The hosted semantic validator MUST enforce fragment-key uniqueness, session and metadata agreement, exact OS cardinality, digest recomputation, canonical assembly, review presence, and conditional final creation. The repository retains only schema, handoff instructions, and local `pending-external` status with null evidence path and time. No external execution, infrastructure provisioning, repository platform payload, commit, or push is part of implementation; the FR-034 quality workflow is not external evidence.
- **FR-036**: Implementation MUST create the shared usability-study protocol, evidence schema verification or minimal extension, semantic validator, synthetic pseudonymous template and fixture, and handoff instructions. Conducting, validating, and reviewing the 20-person study are external human validation after implementation and MUST remain `pending-external`; completion records that the study lifecycle finished, while the semantic validator separately reports whether SC-001 and SC-006 passed. Actual study evidence MUST exist only in a pre-provisioned authorized AU-resident store. Before collection, participants MUST receive Privacy Act-compliant notice and give explicit consent for the limited SC-001/SC-006 purpose. Random pseudonymous IDs MUST be generated independently from names or contact data. Evidence MUST contain no names, email, employer, precise location, medical detail, or free-text PII. Re-identification keys and recruitment records MUST be stored separately from evidence in AU stores with named least-privilege study-team access, immutable access audit, and encryption in transit and at rest. Evidence MUST be deleted no later than 90 days after review unless an approved legal hold applies. Withdrawal before de-identification or aggregation and a breach/incident process MUST be documented. Accommodation evidence MUST use only closed generic category codes, including unavailable-category codes. Valid evidence MAY document failure of either or both criteria, and no implementation artifact may claim a criterion passed without valid participant evidence meeting its threshold.
- **FR-037**: Final implementation and verification gates MUST validate the implementation and every locally producible shape and semantic rule without retaining runtime payloads in the repository. `sovereign-external-platform` and `human-study` remain `pending-external` in this specification, handoff, and checklist only; no repository external-status JSON is instantiated. Completed external status and evidence exist only in authorized AU-resident stores and MUST NOT be committed. Pending status is neither an implementation failure nor a passed success criterion, and external lifecycle completion does not imply a success threshold passed. Local root-test baseline comparison MAY tolerate only failures proven to pre-exist for attribution and is not merge readiness; before merge, the actual pull-request lint, unit, and integration jobs, including `specify-cli-quality`, MUST all be green.
- **FR-038**: Both installed entry points MUST work when invoked from a directory for which no ancestor contains `.specify/extensions`. With no discovered project root, installed-only text output MUST exit 0 with `No extensions installed.`, and installed-only JSON MUST exit 0 with `[]`. Available-only and combined views with no discovered root and therefore no catalog configuration MUST also exit 0 with their scope-specific empty-state text or `[]` in JSON. Catalog configuration MUST be discoverable only through a discovered project root; no process-global, user-home, or current-directory fallback catalog source is permitted.
- **FR-039**: Packaging, performance, privacy, schema, and evidence-producer work MUST follow test-first sequencing. First, all nine current schemas (`agent-action-audit`, catalog config/source, extension list, external status, implementation prerequisite attestation, platform evidence, root baseline, and usability evidence) MUST compile and pass their existing valid, invalid, boundary, and category-isolation fixtures in strict Draft 2020-12 mode with zero warnings; no current schema may cause the expected red. The only schema-stage expected red conditions are the absent planned `read-only-evidence.schema.json` and `performance-evidence.schema.json`; semantic-stage expected red conditions are the absent read-only, usability, performance, and hosted fragment/finalization semantic validators. The performance semantic tests MUST require exactly 30 durations, sorted nearest-rank position 29, exact `p95_seconds`, constant `threshold_seconds=2.000`, and exact `passed == (p95_seconds <= threshold_seconds)`, and both the producer and final gate MUST invoke the semantic validator after schema validation. Read-only, hosted fragment/finalization, and usability semantic tests and implementations MUST each precede identical green reruns. Usability schema execution, any schema edit proven necessary by a schema-expressible failure, and identical green schema verification MUST be separate ordered steps before usability semantic work. Platform schema coverage MUST use one explicit fixture file and command rather than duplicate schema tasks. Every focused test or schema fixture MUST be observed failing for its intended missing implementation before that implementation or producer is added, then rerun identically green. The pre-package packaging test MUST run from the repository root exactly as `uv run pytest -c pyproject.toml tools/specify-cli/tests/test_packaging.py -q`, using only root development pytest and standard-library metadata/TOML parsing before package `conftest.py` or package metadata exists.
- **FR-040**: Planning and eventual task generation MUST keep baseline capture/comparison separate from package-gate execution, and keep local gate-sequence assembly separate from root-regression integration and final execution. One module owns dirty root-baseline capture and comparison; later orchestration invokes package gates under that guard. No single final-gate implementation unit may both define all guard semantics and execute all gates.

#### Cross-Cutting Phase 3 Refinements

These refinements govern FR-029, FR-030, and FR-033 through FR-040 wherever earlier
wording is less restrictive:

- The feature has two explicit execution profiles. `local-synthetic` is the
  default implementation/development profile and MAY run on a developer-owned
  Windows or Linux workstation without Azure IMDS, managed identity, private
  endpoints, an AU VM, or the signed prerequisite attestation. It MUST use only
  checked-in synthetic fixtures or generated fake data, MUST reject production
  remote catalogs and real external collect/finalize modes, MUST retain no
  runtime payload in the repository, and MUST make no sovereignty, performance,
  release, or external-validation claim. `sovereign` is required for normal
  non-synthetic CLI use, qualifying SC-002/read-only evidence, the CI release
  gate, and real collect/finalize; it retains all AU VM, IMDS, encrypted-volume,
  managed-identity, private-network, immutable-ledger, and attestation controls.
- `--start-session --execution-mode local-synthetic` launches the same
  peer-authenticated daemon using an owner-only local temporary directory and a
  hash-chained ephemeral audit journal. The journal uses
  `agent-action-audit.schema.json` with `execution_mode=local-synthetic` and
  `audit_sink=ephemeral-local`, is never evidence, and is logically deleted at
  finalization. `--start-session --execution-mode sovereign` requires the signed
  sovereign preflight and writes records with `execution_mode=sovereign` and
  `audit_sink=immutable-au` to the AU ledger. The handshake binds the selected
  mode and rejects cross-mode clients.
- A local-synthetic data-bearing invocation MUST set
  `SPEC001_TEST_MODE=synthetic` and either use the no-project-root empty case or
  a fixture root beneath the session's owner-only temporary directory. A fixture
  root is authorized only by a closed `.spec001-synthetic-fixture.json` marker
  containing `schema_version=1.0`, `feature=001-extension-list`, non-empty
  `fixture_id`, and lowercase SHA-256 `source_digest`. The digest is SHA-256 over
  RFC 8785 canonical JSON of an array sorted by repository-relative POSIX path,
  with `{path,sha256}` for every checked-in seed/builder file used to materialize
  that fixture. Symlinks, repository-resident
  `.specify/extensions`, missing/mismatched markers, or paths outside the session
  root fail before inventory access. Local mode never reads the developer's
  actual installed-extension inventory.
- Session startup, begin/complete, transition, finalization, and guarded commands
  whose child does not access extension data are not data-bearing and do not
  require `SPEC001_TEST_MODE` or a fixture marker. In particular, T008 may start
  from the repository root but MUST NOT perform project discovery or inventory
  access during startup.
- The local journal is owner-only NDJSON under the session temporary root. Each
  line is RFC 8785 canonical JSON UTF-8 plus LF; `append_position_bytes` is the
  pre-append file length. Writers serialize with `msvcrt.locking` on Windows or
  `fcntl.flock` on Linux, validate the complete chain/head under the lock,
  append exactly one line, flush and `fsync` before acknowledging, and use the
  same genesis/sequence/conflict/freeze rules as the sovereign ledger. The file
  is logically deleted at local finalization and never copied to the repository.
- Local development MAY install or synchronize dependencies from the repository-
  configured HTTPS package proxy before guarded test execution because it uses
  no regulated or production data. Sovereign CI/build/install remains
  `UV_OFFLINE=1` against the authorized pre-seeded AU cache. In both profiles,
  feature runtime tests deny production catalogs and unapproved network access.
- Root provisioning MUST select the optional development extra with
  `uv sync --locked --extra dev --no-install-project`. This provisions the root
  test environment without attempting to build the declared repository root
  project, which has no buildable package target.
  Every root guarded pytest command MUST use `uv run --no-sync pytest ...`;
  every package guarded pytest command MUST use
  `uv run --project tools/specify-cli --extra dev pytest ...`. These forms
  supersede every earlier literal root/package pytest command that does not
  exactly match one of these two forms, including the inline FR-039 packaging
  example and the inline FR-034 package-test example. They preserve the
  root dependencies provisioned before T001 without another root sync, and MUST remain
  byte-identical within each red/green pair.
- Tests executed by both environments (`test_ci_workflow.py`,
  `test_packaging.py`, and `test_root_regression.py`) MUST use only pytest APIs
  compatible across `pytest>=8,<10`; package metadata remains pinned to
  `pytest>=8,<9`, while the root segment records its actual pytest version.
- Every guarded child whose executable is `uv run` MUST receive
  `UV_FROZEN=1` through the dispatcher and fail before launch if it is missing
  or different. This prevents implicit lockfile updates. The deliberate T022
  package-lock generation `uv sync` is not a frozen child; T023 and all later
  sync/build/install validation use their explicit locked/offline controls.
- Every guarded `uv run --project tools/specify-cli` package-tool child MUST
  also select `--extra dev`, including Ruff, mypy, and pytest, so exact frozen
  synchronization retains the required development executables.
- Every guarded mypy child MUST set `MYPY_CACHE_DIR` beneath the active owner-
  only external temporary root. Repository `.mypy_cache` is pre/post mutation-
  checked recursively and MUST remain absent or byte-identical.
- Every guarded pytest child MUST receive
  `PYTEST_ADDOPTS=-pno:cacheprovider` through the dispatcher. Missing or changed
  values fail before launch; repository root/package `.pytest_cache` trees MUST
  remain absent or recursively byte-identical.
- T008 captures the actual normalized failure and collection-error sets produced
  by the provisioned root environment. Every captured identity is classified as
  known-pre-existing only for that segment's local attribution. A later run may
  remove a captured identity, but any identity absent from the T008 baseline
  blocks. No literal error count or path is an acceptance criterion; a nonzero
  local baseline is never merge readiness.
- Before T001, bind one Python 3.12-or-later executable, exact Python and uv
  versions, OS, and architecture in owner-only segment state. Every root/package
  gate in that segment MUST use the same interpreter/toolchain binding. Local
  baseline results are explicitly workstation-, architecture-, interpreter-,
  and segment-specific and cannot be promoted to cross-platform evidence.
- The `microsoft-package-feed-proxy` index metadata in the package project is a
  package-owned, self-contained requirement. Root index metadata, when present,
  is advisory only and may be uncommitted user content; implementation neither
  depends on nor stages it.
- The authorized FR-034 workflow edit MUST make the existing `quality` checkout
  fetch complete history with `fetch-depth: 0` before computing an event
  base/head Git diff; shallow checkout or an unverified fallback is prohibited.
- Root baseline capture MUST generate an owner-only external `COVERAGE_RCFILE`
  that reproduces root `[tool.coverage.run]` and `[tool.coverage.report]`
  settings and adds `[xml] output = <external-temp>/root-coverage.xml`.
  `COVERAGE_FILE`, XML, and process output remain external while repository
  `.coverage*` and `coverage.xml` remain absent or byte-identical.
- Every package test/coverage gate creates an owner-only external temporary
  directory, sets `COVERAGE_FILE` and `COVERAGE_RCFILE` there, and configures
  pytest-cov XML output as `<external-temp>/package-coverage.xml`. The independent
  line-coverage parser reads that XML and requires at least 90.00 percent.
  Repository `.coverage*`, `coverage.xml`, and `package-coverage.xml` are
  pre/post mutation checks and MUST never be created or changed by the gate.
- FR-040 separation is a named intra-module contract in
  `scripts/spec001/local_gate_sequence.py`: `assemble_package_commands` owns
  pure command construction, `parse_package_coverage` owns pure XML threshold
  evaluation, and `run_local_gate_sequence` owns final dependency ordering and
  execution. None owns root-baseline capture/comparison, which remains solely in
  `root_regression.py`; tests MUST enforce these boundaries.
- If a latent bootstrap defect is discovered after T008 in local-synthetic
  mode, the daemon MUST append an incomplete-session final intent/result pair,
  logically delete the local journal and temporary payloads, and terminate the
  segment. The repair occurs only afterward as pre-journal repository/tooling
  work; the protected-state and dispatcher self-checks rerun green without an
  expected red, and a new local-synthetic session then starts from the repaired
  current worktree as an explicitly discontinuous non-evidentiary segment with the same
  lost-attribution disclosure and full final root rerun. The incomplete segment
  cannot be resumed, combined, promoted, or used to waive PR/sovereign gates.
  Sovereign bootstrap defects or custody loss after product edits remain
  terminal and cannot use this recovery.
- The closed five-file bootstrap set is the only pre-journal local-development
  exception. Source authoring is a software-development operation recorded by
  repository/tooling provenance, not a disaster-response agent action governed
  by Core Principle IV (Transparency and Auditability). Because implementation
  makes no commit, local pre-T008 provenance proves only the final bootstrap
  state at session start, not an action-by-action history; it is non-evidentiary.
  At first session start the daemon computes one RFC 8785
  session manifest over those five files and the protected paths; every journal
  record repeats its `session_manifest_digest`. Sovereign bootstrap still
  requires the external AU coordinator. After
  local session start, every edit/decision uses the local journal transaction.
  A lost local session MAY start a new local segment and recapture the current
  worktree baseline, recording discontinuity and making no continuity/evidence
  claim. Sovereign custody loss after product edits remains terminal.

- The real external reviewer authorization identity is known only to the AU
  control plane. Persisted platform or study evidence MUST contain only a
  pseudonymous reviewer ID and a closed decision/reason code; names and
  free-text review notes are prohibited.

- Before sovereign execution begins, the coordinator MUST have access through
  managed identity and private networking to a pre-provisioned immutable audit
  ledger in an Azure Storage account located in `australiaeast` or
  `australiasoutheast`. Every sovereign implementation/validation edit, command,
  decision, session transition, and runtime list action MUST append one
  hash-chained record conforming to
  `contracts/agent-action-audit.schema.json` as a two-record transaction. A
  phase `intent` record with outcome `started` MUST append successfully before
  the action executes. A phase `result` record linked by `intent_event_id` with
  outcome `succeeded`, `failed`, or `blocked` MUST append successfully before
  the action is reported complete or any later action begins. If result append
  fails after execution, the daemon freezes the session and retries only that
  result append; it MUST NOT execute another action. Records contain pseudonymous principal ID, task/action/rationale
  codes, outcome, timestamps, target digest, and chain digests only; they MUST
  contain no command output, source values, human data, secrets, paths, or free
  text. The ledger MUST use TLS/private endpoint, managed identity, append-only
  or locked immutability, encryption, and AU retention. Ledger unavailability or
  append failure blocks or freezes the action lifecycle. `event_digest` is
  SHA-256 over RFC 8785 canonical JSON UTF-8 bytes with `event_digest` omitted;
  `previous_event_digest` forms the ledger chain. For both phases,
  `target_digest` is SHA-256 over RFC 8785 canonical JSON UTF-8 bytes of the
  exact schema-valid `target` object. The versioned rationale registry is the closed
  `$defs.rationaleCode` enum in schema version 1.0. The external coordinator records the closed
  sovereign bootstrap-file edits before the feature daemon exists; the daemon
  records all later sovereign actions. Local-synthetic actions use the same
  record semantics in the ephemeral local journal defined above.
- Each session uses one append-blob/local-journal partition
  `spec001-extension-list/<session_id>` whose suffix MUST equal `session_id`.
  Sequence 1 is that session's only genesis record, uses append
  position 0 and null previous digest. Every later record has the next sequence,
  previous head digest, and expected append byte position. Writers MUST use an
  Azure Blob lease plus `x-ms-blob-condition-appendpos` for atomic compare-and-
  append. On a pre-action conflict, reload and validate the complete head/chain
  and retry the intent before executing. On a post-action result conflict,
  freeze the session and retry only the linked result against the validated new
  head. Chain fork, sequence gap, invalid genesis, unreconciled lease/append
  conflict, or digest mismatch blocks. A partition admits at most 49,000 records.
  The daemon stops accepting ordinary actions after sequence 48,998, reserving
  the final two records for `session.finalize`; it never splits an intent/result
  pair or rolls a live session into another partition. A new session starts a new
  partition and cannot claim continuity with the prior session.
- The blocking sovereign preflight MUST conform to
  `contracts/implementation-prerequisite-attestation.schema.json`. It is a
  closed accepted artifact `{claims, compact_jws, attestation_digest,
  replay_protection}` whose `claims` value is the decoded closed ES256 JWS
  payload signed by a versioned Key Vault
  key pinned in an owner-only external AU trust bundle. The preflight command
  supplies an owner-only AU path for the trust bundle, generates a fresh
  challenge UUID and 256-bit nonce, and sends one closed request over the same
  pinned private control-plane transport defined for pre-write attestations.
  The request includes schema/feature, challenge, nonce, timestamp, repository
  digest, and branch; the only accepted response is one compact JWS. The
  dispatcher verifies signature/key, issuer
  `ama-security-control-plane`, audience
  `spec001-extension-list-sovereign-preflight`, repository digest, branch,
  JTI uniqueness, nonce, maximum 10-minute lifetime, 2-minute skew, audit-ledger
  controls, AU VM/encrypted IPC controls, offline AU cache, and every private
  dependency claim. The decoded JWS payload MUST equal the schema-valid
  `claims` object field-for-field; its challenge/nonce/request time
  MUST equal the generated request. `attestation_digest` is SHA-256 of compact
  JWS UTF-8 bytes. Before accepting the preflight, the dispatcher atomically
  creates immutable AU Blob marker
  `spec001-extension-list/preflight-jti/<jti>` with create-if-absent and at least
  one-day locked retention; an existing marker rejects replay. The raw
  attestation stays on encrypted AU temporary storage and is deleted after
  daemon consumption. Local-synthetic session startup MUST NOT request, accept,
  or fabricate this attestation.
- `repository_digest` is SHA-256 over RFC 8785 canonical JSON of an array sorted
  by relative POSIX `path`. The array contains `{path,state,sha256}` for every
  path in the protected manifest, closed bootstrap set,
  `.specify/memory/constitution.md`, and every regular non-symlink file currently
  under `specs/001-extension-list/`; `state` is `file` or `absent`, and `sha256`
  is lowercase file-byte SHA-256 or null for absent. Symlinks, duplicate paths,
  path escape, unreadable files, or a file-set change during hashing block.
- After session start, every repository-file mutation and every decision MUST be enclosed by
  daemon `begin-action` and `complete-action` operations. `begin-action` appends
  the intent and establishes the single active action before edit/decision;
  `complete-action` appends the linked result before another action. The daemon
  rejects edits without an active matching intent and concurrent active actions.
  A task that mutates multiple files MUST execute one complete serialized
  transaction per file, reusing its task ID but using each file's distinct
  repository-relative target identifier; no transaction may span files.
  Child commands are wrapped automatically by the dispatcher with the same
  transaction. Runtime CLI clients request the daemon to wrap each list action.
- Changes from `- [ ]` to `- [x]` in `tasks.md` are fleet orchestration
  bookkeeping, not product source/design mutations or disaster-response agent
  actions. They are excluded from the feature audit transaction and protected-
  state comparisons, remain visible in repository/tooling provenance, and MUST
  occur only after the corresponding task result succeeds. T134's checkbox is
  the sole permitted repository edit after local session finalization; it records
  orchestrator completion only and no product, contract, or evidence content may
  change with it.
- Fleet-owned `.analyze-done`, `review.md`, and `.verify-done` are likewise
  orchestration metadata outside feature audit and protected-state comparisons.
  They may be refreshed by their owning phases after local finalization, but are
  never runtime/evidence payloads and cannot alter source, requirements,
  contracts, tests, documentation, or qualifying status.
- The version-1 audit target descriptor is the exact closed `target` object in
  `agent-action-audit.schema.json`. `identifier_digest` is SHA-256 of UTF-8
  `<kind>\0<stable-identifier>`. The stable identifier is the repository-relative
  POSIX path for `repository-file`; RFC 8785 canonical JSON of the exact argv
  string array for `command`; `<task_id>\0<closed-code>` for `decision` and
  `validation`; session UUID for `session`; request UUID for `runtime-request`;
  or container-relative Blob name for `external-write`. Every state digest is
  SHA-256 over RFC 8785 canonical JSON UTF-8 bytes of one closed state object:
  repository files use `{state:"file",sha256:<file-byte-sha256>}` or
  `{state:"absent",sha256:null}`; commands use `{state:"not-started"}` then
  `{state:"completed",exit_code:<integer>}`; decisions use
  `{state:"not-recorded"}` then `{state:"recorded"}`; validations use
  `{state:"not-run"}` then `{state:"completed"}`; sessions use
  `{state:"inactive"}` or `{state:"active"}` as applicable; runtime requests
  use `{state:"not-processed"}` then `{state:"completed"}`; external writes use
  `{state:"absent"}` then `{state:"created",content_sha256:<digest>}`. An
  intent has a non-null pre-state digest and null post-state digest. Its result
  repeats the same identifier and pre-state, has a non-null post-state, and
  repeats the pre-state digest when execution is blocked, fails before a state
  change, or otherwise leaves state unchanged. For both phases, `target_digest`
  is SHA-256 over RFC 8785 canonical JSON UTF-8 bytes of that exact `target`.
- The standalone wheel MUST package `specify_cli.daemon`,
  `specify_cli.daemon_client`, and `specify_cli.daemon_protocol`. Runtime client
  discovery uses only the current-SID Windows named pipe or current-UID
  `$XDG_RUNTIME_DIR/ama-specify/daemon.sock` when `XDG_RUNTIME_DIR` exists, is
  owned by the current UID, is not a symlink, and has mode 0700. Otherwise Linux
  uses `${TMPDIR:-/tmp}/ama-specify-<uid>/daemon.sock`, creating the non-symlink
  per-UID directory atomically with mode 0700 and rejecting wrong ownership or
  mode. Startup is serialized by an
  owner-only lock, launches `python -m specify_cli.daemon`, performs a versioned
  mode-bound handshake, and fails closed on mismatch. Sovereign mode adds the
  AU/IMDS/encryption/immutable-audit preflight; local-synthetic mode instead
  verifies owner-only local temporary storage, synthetic-data policy, network
  denial, and the ephemeral journal.
- IPC and local journal locking use only the Python standard library. Windows
  named-pipe creation and current-SID+SYSTEM DACL construction use `ctypes`
  bindings to `kernel32`/`advapi32`; Linux uses Unix sockets, `SO_PEERCRED`, and
  `fcntl.flock`. No additional IPC/security package is permitted.
  The CLI never falls back to in-process inventory/catalog processing.
- Planned `read-only-evidence.schema.json` MUST be a strict closed object with
  exactly the fields defined by `ReadOnlyEvidence` in `data-model.md`: constants
  for schema, feature, category, and ephemeral lifecycle; validation UUID/time;
  view, output mode, outcome, and exit code; source, protected, and coverage
  before/after SHA-256 pairs; `execution_mode=sovereign`,
  `audit_sink=immutable-au`, sovereign session UUID, preflight attestation
  digest, execution VM resource ID, and immutable audit intent event ID/digest;
  true peer/AU-VM/encrypted-storage/audit-complete/
  raw-output-deleted flags; and false repository-payload-persisted. Semantics
  require all three digest pairs equal and `outcome=succeeded` exactly when
  `exit_code=0`; failed or blocked outcomes require a nonzero exit code. The
  session/preflight/VM/intent bindings MUST match signed claims, live IMDS, and
  the immutable ledger. Performance evidence MUST carry and cross-check the same
  seven sovereign binding fields.
- Normal non-synthetic `ama-specify` and `python -m specify_cli` execution MUST
  be a thin client to a verified AU daemon session. Installed inventory,
  project-local catalogs, command output, and temporary data MUST be read and
  processed only on the verified AU VM and encrypted ephemeral volume. Direct
  in-process inventory/catalog processing outside the daemon is prohibited.
  Sovereign dependency sync/build MUST use `UV_OFFLINE=1` with a pre-seeded
  cache produced by an authorized AU package mirror and MUST NOT contact the
  package proxy. Local-synthetic dependency bootstrap MAY use only the
  repository-configured HTTPS proxy or an existing cache.
- A production remote catalog URL MUST be an Azure Blob HTTPS URL accompanied
  by its storage-account ARM resource ID and container scope. Before retrieval,
  managed identity MUST verify the account is in an allowed AU region, public
  access is disabled, default network action is Deny, an approved private
  endpoint exists, the host matches the ARM account and resolves only privately,
  and the daemon principal has exactly one direct assignment of the required
  built-in Storage Blob Data Reader role at the target container scope. Neither
  that principal nor any transitive group may have an active or PIM-eligible
  built-in/custom role containing any Blob `DataActions` at the same container
  or any container/account/resource-group/subscription/management-group scope.
  Tests may inject fake HTTPS transports;
  production rejects any other remote catalog.
- The control-plane attestation endpoint MUST map to a pinned Azure
  `Microsoft.Web/sites` resource ID and the signing `kid` MUST map to a pinned
  Azure Key Vault resource ID in the reviewed trust bundle. Before requesting an
  attestation, managed identity MUST query ARM and require both resources in an
  allowed AU region, public network access disabled, approved private endpoints,
  endpoint/vault hosts matching the pinned resource IDs, and private-only DNS.
  Key state MUST be enabled and unexpired. Any mismatch blocks before request.
- For every storage/catalog authorization decision, managed identity MUST resolve
  the VM service principal and its transitive group memberships, enumerate
  active role assignments and PIM role-eligibility schedule instances at the
  target container, storage account, resource group, subscription, and inherited
  management-group scopes, resolve each built-in or custom role definition, and
  evaluate effective `DataActions` minus `NotDataActions`. The required policy
  is exactly one direct assignment to the VM service principal of the built-in
  Storage Blob Data Contributor role for evidence writes or Storage Blob Data
  Reader role for catalog reads at the target container, and zero other active
  or eligible assignments for the principal or transitive groups whose effective
  DataActions include any Blob data operation at the target or ancestor scopes.
  Any same-container, inherited, group, PIM, or custom-role addition therefore
  fails, as does any unresolved
  group/scope/role definition, or any inability to enumerate ancestors fails
  closed. Tests MUST include direct, group-inherited, PIM-eligible, custom-role,
  higher-scope, NotDataActions, and enumeration-failure cases.
- The closed bootstrap source set is exactly
  `scripts/spec001/protected_state_selfcheck.py`,
  `scripts/spec001/dispatcher_selfcheck_cases.py`,
  `scripts/spec001/protected_state.py`,
  `scripts/spec001/root_regression.py`, and
  `scripts/spec001/run_local_gates.py`. These files MAY be authored before the
  product baseline. In sovereign mode each edit MUST be durably recorded by the
  external AU audit coordinator; in local-synthetic mode they are the sole
  pre-journal exception and their final hashes are recorded in the local genesis.
  `--start-session` MUST hash and freeze this set together with the protected
  manifest before any product source or workflow edit; no bootstrap file may
  change within that session. All `tools/specify-cli/**`, docs,
  contracts other than pre-existing planning contracts, and workflow edits are
  product edits and occur only after baseline capture.

- No runtime, expected-red, baseline, read-only, performance, external-status,
  or other gate payload is written beneath repository `artifacts/` or elsewhere
  in the repository. The repository contains schemas, synthetic fixtures, and
  tests only. Normal local and CI output uses synthetic data and minimized
  sanitizer summaries; it contains no raw exceptions, absolute paths,
  environment values, inventory records, Git diffs, human data, or evidence
  payloads.
- The dispatcher captures stdout/stderr only in an external temporary directory,
  derives exit code, normalized test IDs, category/code, byte and line counts,
  SHA-256, and a bounded secret- and path-scrubbed summary, reports only
  minimized status in memory or terminal, and deletes raw output after
  validation. One
  sanitizer contract applies to every red and gate command. No retained `.txt`
  or runtime JSON artifact is permitted.
- The root baseline is an ephemeral shape-validated external-temp object held by
  the long-lived custodian daemon for one implementation session. Raw output is deleted
  after normalization. Within one active segment, recapture or reconstruction is
  prohibited after a feature source or workflow edit. Sovereign daemon/custody
  loss after such an edit is unconditionally blocking; local-synthetic loss may
  start only a new explicitly discontinuous non-evidentiary segment with the
  attribution limitations defined below. Read-only and performance
  payloads likewise remain external-temp only through schema and semantic
  validation, then are deleted. Local-synthetic mode may create only fake
  in-memory/test objects and cannot emit qualifying read-only or performance
  evidence. In the initial implementation segment before initial T009, exactly three synthetic bootstrap
  executions occur: the protected-state self-check passes, the dispatcher/root-
  regression self-check is observed failing for its missing implementation, and
  that byte-identical dispatcher self-check is replayed green after implementation.
  After those three executions, local-synthetic child commands may run through
  the local daemon using only synthetic data, owner-only temporary storage, and
  the ephemeral journal. Sovereign child commands and every qualifying evidence
  producer additionally require Azure IMDS proof of a standalone Windows x64 or
  Ubuntu x64 VM in `australiaeast` or `australiasoutheast`, an encrypted
  ephemeral volume (BitLocker or dm-crypt/LUKS), and owner-only DACL/modes. Real
  data and evidence never transit or rest outside Australia.
- Only the protected-state self-check and dispatcher `--self-check` red/green
  pair may execute before dispatcher proof. Dispatcher-owned modes are allowed afterward only
  when they apply identical pre/post protection. Every expected-red task later
  generated MUST define one complete canonical
  `python scripts/spec001/run_local_gates.py -- ...` command with required
  environment, test files, `-q`, selectors, and markers. Its green task repeats
  the exact string; every combined red has an exact combined green replay.
- `--start-session --execution-mode <local-synthetic|sovereign>` MUST launch one
  long-lived custodian daemon that retains the
  baseline and sanitizer state in memory. On Windows it exposes a named pipe
  whose DACL permits only the current SID and SYSTEM; on Linux it exposes a Unix
  socket beneath an owner-only runtime directory with mode 0600 and verifies
  peer UID using `SO_PEERCRED`. Later invocations select the daemon by session
  UUID and MUST pass OS peer authentication; the UUID alone grants no access.
  In sovereign mode, daemon/peer/encrypted-volume loss blocks permanently after
  product edits. In local-synthetic mode, the failed segment is finalized as
  incomplete when possible and a new owner-authenticated local session may
  capture the current worktree as a new non-evidentiary baseline.
- The `specify-cli-quality` CI job and every real external `collect` or
  `finalize` invocation occur after implementation and MUST run the protected-
  state self-check green followed by one dispatcher/root-regression self-check
  green, then complete the signed sovereign preflight, start a verified AU daemon
  session, route every payload-producing child through that
  peer-authenticated daemon, and finalize the session. Direct invocation of
  package gates or external modes outside the daemon MUST fail before payload
  creation. `SPEC001_SESSION_ID` MAY supply routing metadata to quickstart and CI
  commands after session startup; it is never an authentication credential.
- Sovereign daemon or custody loss is unconditionally blocking after the first
  source edit, and sovereign baseline reconstruction or recapture after edits is
  prohibited. Local-synthetic development may begin a new explicitly segmented
  session from the current worktree after local custody loss; segments cannot be
  combined into sovereign or release evidence.
- The deliberate `.github/workflows/ci.yml` edit MUST use one one-time
  dispatcher transition permit bound to the active daemon session, repository
  identity, the single allowed path, its exact pre-edit SHA-256, a unique
  transition UUID, and a maximum 10-minute expiry. The next dispatcher-owned
  transition-accept operation MUST prove that every other protected path and
  staged/unstaged Git-diff streams computed over the frozen path set excluding
  `.github/workflows/ci.yml` are unchanged, verify an operator-supplied
  exact post-edit SHA-256, atomically replace only that path's session baseline,
  invalidate the permit, and block on reuse, expiry, path drift, unrelated
  change, or digest mismatch before any child command runs.
- External collect and finalize require storage-account ARM resource ID,
  container name, and Blob URI, never credentials or SAS. Before first read or
  write, managed identity MUST query ARM and verify an allowed AU location,
  disabled public network access, deny-by-default network rules, and an approved
  private-endpoint connection; verify the Blob host matches the ARM account and
  resolves only to private IP addresses; derive the standalone VM principal and
  verify exactly Storage Blob Data Contributor at target container scope; and
  obtain from an authorized AU control plane a current pseudonymous authorized security/compliance
  pre-write attestation covering resource ID, private endpoint, container scope,
  reviewer, timestamp, and no broader data-plane write role. Attestation fields
  and digest MUST validate. The attestation MUST be a compact ES256 JWS signed by
  an exact versioned Azure Key Vault key ID from an out-of-band, owner-only
  allowlist; retrieved over private HTTPS with managed identity from the
  allowlisted AU control-plane audience. Claims MUST bind issuer
  `ama-security-control-plane`, audience `spec001-extension-list-prewrite`, the
  current validation session, script-generated 256-bit nonce, unique JTI,
  storage resource, private endpoint, container scope, VM principal, and role
  breadth. The script MUST verify signature and key ID, require `exp` no more
  than 10 minutes after `iat`, allow at most 2 minutes clock skew for `nbf`/`exp`,
  require nonce/session/resource equality, and reject replayed JTI values. The
  compact JWS MUST be retained in AU-only evidence and `attestation_digest` MUST
  be SHA-256 over its UTF-8 bytes. Signature verification MUST use the exact
  public JWK pinned for the versioned `kid` in the reviewed package trust bundle
  `tools/specify-cli/src/specify_cli/trusted_attestation_keys.json`. Before an
  evidence fragment is written, the script MUST atomically create an AU Blob
  replay marker `spec001-extension-list/attestation-jti/<jti>` with
  create-if-absent semantics before EVERY attested write, including each
  fragment and final canonical publication. The target container MUST have a
  locked time-based immutability policy of at least 1 day, and the evidence MUST
  retain marker URI, creation result, retention expiry, and policy mode. Each
  write requires a distinct fresh JTI/nonce/attestation; an existing marker
  rejects the attestation across processes and immutability prevents deletion
  during the replay window. Any unverifiable condition fails
  closed before evidence access. Lifecycle evidence and attestation remain AU
  Blob-only and terminal output remains value-free.
- The reviewed trust-bundle entry MUST also pin one exact private HTTPS
  attestation endpoint and managed-identity token scope
  `api://ama-security-control-plane/.default`. The script sends exactly one POST
  with no redirect or retry, a five-second total monotonic deadline, content type
  `application/json`, and a closed request containing schema version, feature,
  operation (`collect-fragment` or `finalize-canonical`), session UUID, fresh
  nonce, requested timestamp, target blob name, and repeated storage/endpoint/
  container/principal/role fields. The endpoint host/path cannot be overridden,
  MUST resolve only to private IP addresses, and the response MUST be HTTP 200,
  content type `application/jose`, at most 16 KiB, with a closed object
  containing only `compact_jws`. Any other host, redirect, response, timeout, or
  size fails closed; these rules are SSRF-resistance requirements.
- Package coverage gates MUST collect branch data and independently parse the
  machine-readable coverage report to require line coverage at least 90.00%.
  `--cov-branch --cov-fail-under=90` alone is not accepted as proof of the
  separate line-coverage threshold.

### Key Entities

- **Installed Extension**: An extension present in the user's working environment. Key attributes include stable identifier when present, source location, display name, installed version, description, activation state, health state, contributed command count, and contributed hook count. Source location serves as fallback display identity when the stable identifier is missing, but never as a catalog reconciliation key.
- **Catalog Extension**: An extension advertised by the configured catalog. Key attributes include stable identifier, display name, available version, description, and whether it is already installed.
- **Source Evidence**: A deterministic retained representation of every local
  or catalog record that contributed to an output row, including source kind,
  source-identity SHA-256, source ordinal, and record SHA-256 only; no raw source
  identity is serialized in evidence.
- **Extension List View**: The user's requested scope: installed-only, available-only, or combined. It determines which extension records are included and how installed and catalog information are reconciled.
- **Extension Activation State**: The installed extension's runtime state, represented by exactly one of disabled, inactive, active, or activation-failed. Activation failure includes an independently projected non-empty activation diagnostic; all other states use a null activation diagnostic. Activation remains independent of metadata health.
- **Extension Health State**: The installed extension's metadata assessment, represented by exactly one of healthy or invalid. An invalid state includes a diagnostic reason.
- **Project Context**: The optional project root discovered only when an ancestor contains `.specify/extensions`. A missing project context is a valid empty environment and cannot supply catalog configuration.
- **Root Regression Baseline**: An ephemeral external-temp pre-implementation object containing the frozen root CI pytest argument selection executed through `uv run --no-sync`, exit code, T008-captured normalized failure and collection-error sets, bound toolchain metadata, and output metadata used to detect only identities absent from the baseline. It is never persisted in the repository.

### Assumptions

- The phrase "extension list" refers to the Spec Kit extension inventory command already referenced by the repository's Fleet and Verify extension documentation.
- The default experience lists installed extensions, while available-only and combined catalog views are optional user selections.
- A stable extension identifier is the only authoritative identity used to reconcile installed and catalog records; source location is a fallback identity only for separately displaying an installed record whose stable identifier is missing.
- Installed-extension information remains useful even when catalog information is unavailable.
- Listing extensions is a read-only diagnostic and discovery activity; installing, updating, repairing, enabling, disabling, or removing an extension requires a separate action.
- The configured extension catalog and installed-extension inventory are trusted sources for display, but individual records may be incomplete or malformed.
- Catalog source work is bounded by 8 configured sources, 1,000 records per
  source, 1 MiB per source, and a 5-second deadline per source; no additional
  global catalog deadline is required.

### Dependencies

- Sovereign/non-synthetic runtime access to the current working environment's
  live installed-extension inventory.
- Sovereign/non-synthetic runtime access to live extension metadata sufficient
  to identify installed extensions and summarize their contributed capabilities.
- Sovereign/non-synthetic runtime access to the configured production extension
  catalog for available-only and combined views.
- Local-synthetic development replaces those live dependencies with checked-in
  synthetic seeds materialized only in an authorized marker-bound fixture root,
  or exercises the no-project-root empty state.
- Local development requires only Python 3.12+, Git, owner-only local temporary
  storage/IPC, synthetic fixtures, and access to the repository-configured HTTPS
  package proxy or an existing cache; it requires no Azure VM or Azure resource.
- Sovereign validation/release requires a pre-provisioned private immutable AU
  audit ledger, managed identity, private endpoint, locked retention policy,
  external coordinator, verified standalone AU Azure VM, encrypted ephemeral
  volume, and pre-seeded package cache from an authorized AU mirror. This
  feature provisions none of them.
- Production remote catalogs hosted only in private AU Azure Blob containers
  with ARM metadata, private endpoint, private DNS, and exact container-scoped
  Data Reader authorization available for fail-closed verification.
- Two compliant standalone Azure VMs, one Windows x64 and one Ubuntu Linux x64, physically located in `australiaeast` or `australiasoutheast`, with Azure IMDS and private network access to the AU evidence store.
- A pre-provisioned private Azure Blob account/container in Australia East or Australia Southeast with encryption and retention controls, plus managed identities granted least-privilege Blob Data Contributor scoped to that container. This feature provisions none of these resources.
- One authorized security/compliance reviewer represented in evidence only by a pseudonymous reviewer identifier, able to inspect and decide on the AU-resident evidence without publishing identity or evidence to GitHub or the repository.
- Exactly 20 eligible included adult participants, exactly 10 novice and 10 experienced, who use command-line developer tools at least monthly, have no prior feature or fixture exposure, satisfy the FR-030/SC-001/SC-006 Spec Kit workflow and extension-management criteria, and can receive every requested accessibility accommodation without changing the measured task; unavailable required accommodations or documented pre-exposure technical interruptions require same-stratum replacement.

### Out of Scope

- Installing, updating, removing, enabling, disabling, or repairing extensions.
- Executing an extension command or hook from the list.
- Publishing, moderating, or administering the extension catalog.
- Editing extension metadata.
- Providing a graphical extension marketplace or management interface.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In usability testing with exactly 20 included unique representative adult participants comprising exactly 10 novice and exactly 10 experienced Spec Kit users, every included participant uses command-line developer tools at least monthly and has no prior exposure to this feature or test fixture. Novices have completed 0-2 Spec Kit workflows in the prior 6 months and have no prior extension-management use; experienced participants have completed at least 5 workflows in that period and have prior extension-management use. Each participant separately identifies whether a named extension is installed and whether it is enabled. Task variants MUST be allocated by the deterministic FR-030 algorithm within each stratum, and requested accessibility accommodations MUST be provided without changing the measured task. A person whose required accommodation cannot be provided MUST be excluded before task exposure as `required-accommodation-unavailable`, with unavailable accommodations recorded, and replaced within the same stratum. A documented technical interruption before exposure also permits exclusion and same-stratum replacement. Excluded people do not count toward the 20 included participants; every post-exposure outcome remains included. A participant succeeds only when both answers are correct within 30 seconds; at least 19 of the 20 included participants MUST succeed.
- **SC-002**: On the documented baseline machine or named runner, start and verify one daemon session before timing. Installed-only JSON mode with feature catalog, package-index, proxy, public-endpoint, and other unapproved transport disabled, a deterministic fixture ID, and fixture count 100 MUST complete from each cold client-process start through complete stdout in P95 at or below 2.000 seconds across exactly 30 measured runs after exactly 3 warmups. Each measured run attaches to the pre-started daemon and includes peer-authenticated handshake, installed collection/rendering, and both mandatory private AU audit-ledger appends; daemon startup, IMDS/session preflight, and fixture materialization are outside the timed interval. `network_disabled=true` means only peer-authenticated local IPC and the pinned private AU audit/control-plane endpoints are allowed. Performance evidence MUST record OS, architecture, CPU model and logical count, total memory bytes, Python version, package version, lock SHA-256, optional baseline runner identifier, `network_disabled=true`, fixture ID, fixture count 100, all three warmup outcomes, exactly 30 durations, nearest-rank `rank=29`, computed P95, `threshold_seconds=2.000`, passed boolean, and RFC 3339 timestamp.
- **SC-003**: In validation tests containing every activation state and both metadata health states, 100% of entries are shown with the correct user-facing activation and health state, every invalid entry includes a diagnostic reason, and healthy entries remain accessible.
- **SC-004**: In combined-view tests, 100% of extensions that occur in both installed and catalog records appear once and clearly distinguish installed and available versions when they differ.
- **SC-005**: In available-only and combined-view tests where catalog information is unavailable, 100% of locally determinable installed extensions remain visible, are not represented as catalog results, and are accompanied by a catalog-unavailable warning.
- **SC-006**: Using the same exactly 20 included unique cohort and the same eligibility, deterministic allocation, accommodation, and pre-exposure replacement rules as SC-001, each participant rates the extension list's next-action clarity on a 1-5 scale and records boolean `consulted_installation_directories` and `attempted_extension_command` evidence. A participant qualifies only with a rating of 4 or 5 and both booleans false; at least 18 of the 20 included participants MUST qualify.
- **SC-007**: At 80x24 and 40x12 with colour disabled, and in redirected plain text, every record appears exactly once; literal labels `Installed`, `Activation`, `Health`, `Commands`, and `Hooks` remain present; disabled, invalid, and conflict states remain exact words; normalized output contains no ANSI escapes; wrapping preserves label/value token order; and no pager or input occurs. Automated tests assert only this observable readability oracle, not general human comprehension.
