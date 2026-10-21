# Feature Evidence Ledger — Spec 005 Data Source Governance

## 2026-09-15 — AUD-025 and AUD-028 implementation

### Scope

- Implemented only AUD-025 then AUD-028.
- Preserved existing dirty workspace changes and historical task checkboxes.

### Automated Evidence

- Classifier branch regression (narrow after first edit):
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest apps/api/tests/contract/spec_035/test_classifier_branches.py -q`
  - Result: `12 passed, 2 warnings`

### Truth-Correction Notes

- T056/T057 remain historical checkboxes in `tasks.md`; current measurable rehearsal/readiness evidence remains UNVERIFIED until external governance consultation and legal/owner approval records are attached.
- PER-007 and PER-008 are downgraded to `unverified` in `spec.md` pending named qualified reviewer + date + revision + evidence links.
- PER-009 remains placeholder/deferred with existing country gates unchanged.

### External Evidence Still Required

- Legal/owner approval for AU APP/control mapping status transitions from `UNVERIFIED`.
- Human consultation/rehearsal records for SC-004/SC-005 and T056/T057 closure claims.
- Any PH/JP/BD promotion evidence requires MoU + DPIA + sovereign authorization and is not auto-approved by this implementation.

## 2026-09-15 — AUD-026 and AUD-027 implementation

### Scope

- Implemented only AUD-026 and AUD-027 automatable source/harness/readiness scaffolding.
- Preserved existing dirty worktree changes and historical checklist/task claims.

### Automated Evidence

- Narrow check after first edit:
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/contract/test_data_source_registry.py -k seed_catalogue_loads -q`
  - Result: `1 passed, 30 deselected`

### Source/Harness Changes (AUD-026)

- Isolated blocking governance request-path calls at async API boundaries using `anyio.to_thread` for lookup and dashboard handlers.
- Added shared Cosmos client lifecycle reuse and explicit shutdown close hook.
- Reworked dashboard summary to avoid per-source N+1 reads by using batched repository projections for assessments, assignments, and chains.
- Added bounded query controls (`AMA_GOVERNANCE_QUERY_PAGE_SIZE`, `AMA_GOVERNANCE_QUERY_RETRIES`, `AMA_GOVERNANCE_SUMMARY_BATCH_SIZE`).
- Extended `tests/integration/test_governance_cache.py` with:
  - staging-gated `lookup_latency` harness (`AMA_STAGING_GOVERNANCE=1` + explicit config, >=1000 lookups, concurrency, warm/cold mix, raw sample export, p95 targets)
  - local injected `registry_outage` scenarios using fake Cosmos/Redis behavior
  - outage response assertions (stale-hit serve, miss-path `503`)

### Readiness Scaffolding (AUD-027)

- Replaced hardcoded `>=40` seed assertion with required-ID intersection and exact `>=90%` coverage in `tests/contract/test_data_source_registry.py`.
- Added deterministic readiness tooling in `tools/lint/check_spec005_readiness.py`:
  - `export`: normalized source/assessment/assignment/chain/gap/audit snapshot with schema/revision/tenant scope and hashes
  - `validate`: strict thresholds and evidence completeness checks
  - `replay`: reconstruct from audit and emit exact diff
- Added validator tests for edge boundaries and required failure modes in `tests/devops/test_spec005_readiness_lint.py`.
- Added evidence templates:
  - `specs/005-data-source-governance/evidence/readiness-manifest.template.json`
  - `specs/005-data-source-governance/evidence/quickstart-rehearsal-manifest.template.json`
  - `specs/005-data-source-governance/evidence/staging-outage-scaffold.md`

### Blockers Retained (Explicit)

- External measurement remains blocked until authorized staging run captures topology/version/revision evidence.
- NFR availability remains blocked by Redis Basic C0 SKU posture; no Bicep SKU change made in this pass.
- SME panel, usability study denominator, and live reconstructive replay approvals remain open for final SC closure.

## 2026-09-15 — AUD-020 and AUD-024 implementation

### Scope

- Implemented only AUD-020 and AUD-024, in that order.
- Kept changes isolated to spec 005 implementation context and preserved unrelated dirty workspace changes.

### Automated Acceptance Evidence

- Focused connected backend suites:
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/integration/test_governance_dashboard_api.py tests/integration/test_governance_cache.py tests/integration/test_governance_grace_period.py -q`
  - Result: `22 passed, 2 warnings`
- Python syntax compile:
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile tests/integration/governance_test_client.py tests/integration/test_governance_dashboard_api.py`
  - Result: success (no output)
- TypeScript diagnostics:
  - Command: `corepack pnpm --filter @ama/web exec tsc --noEmit`
  - Result: blocked, Corepack TLS handshake failure while fetching pnpm `10.6.3` (`ERR_SSL_SSL/TLS_ALERT_HANDSHAKE_FAILURE`)
- Focused Playwright run:
  - Command: `corepack pnpm --filter @ama/web test:e2e -- tests/e2e/test_governance_dashboard.spec.ts tests/e2e/governance-dashboard.spec.ts`
  - Result: blocked by the same Corepack TLS handshake failure while fetching pnpm `10.6.3`

### Behavioral Evidence Summary

- AUD-020:
  - Completed source administration workflow in replacement governance UI for register, update, deactivate, and manage actions.
  - Normalized governance web API calls to canonical `/api` prefix for source and assignment flows.
  - Added explicit workflow error handling and stable editor/save behavior for handoff chain updates.
- AUD-024:
  - Added connected governance integration fixture with shared runtime dependencies and deterministic cache clock.
  - Replaced weak status-only integration assertions with real end-to-end register, assess, assign, chain, lookup cache, and negative mutation-guard coverage.
  - Removed vacuous conditional E2E expectations and replaced with deterministic route-mock assertions, including failed-save preservation checks.

### Files in Scope

- `apps/web/src/components/governance/DataSourceTable.tsx`
- `apps/web/src/components/governance/HandoffChainEditor.tsx`
- `apps/web/src/app/governance/[dataSourceId]/assignments/page.tsx`
- `apps/web/src/app/governance/data-sources/page.tsx`
- `apps/web/src/app/governance/dashboard/layout.tsx`
- `apps/web/src/app/governance/page.tsx`
- `tests/integration/governance_test_client.py`
- `tests/integration/test_governance_dashboard_api.py`
- `tests/e2e/test_governance_dashboard.spec.ts`
- `tests/e2e/governance-dashboard.spec.ts`

### Outstanding External Evidence (Unverified)

- Browser execution for updated Playwright specs is blocked in this environment by Corepack TLS handshake failure fetching pinned pnpm.
- TS command-level diagnostics via workspace pnpm tooling is blocked in this environment by the same TLS failure.

## 2026-09-15 — AUD-014, AUD-015, AUD-016, AUD-013, AUD-017 implementation

### Scope

- Implemented only requested AUD items in this exact sequence: 014, 015, 016, 013, 017.
- Kept work scoped to spec 005 context and preserved existing unrelated dirty workspace changes.

### Automated Evidence

- Focused contract tests:
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/contract/test_governance_assignment.py -q`
  - Result: `25 passed`
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/contract/test_data_source_registry.py -q`
  - Result: `30 passed`
- Focused integration tests:
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/integration/test_aud001_aud010_governance_auth_runtime.py -q`
  - Result: `13 passed, 2 warnings`
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/integration/test_governance_cache.py -q`
  - Result: `5 passed`
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/integration/test_governance_dashboard_api.py -q`
  - Result: `30 passed, 2 warnings`
- Python syntax compile:
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile apps/api/app/api/governance.py apps/api/app/services/governance_registry.py apps/api/app/validators/governance_validators.py apps/api/app/api/routes/signals.py tests/contract/test_governance_assignment.py tests/contract/test_data_source_registry.py`
  - Result: success (no output)
- OpenAPI parse validation:
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "import yaml, pathlib; ..."`
  - Result: `openapi-yaml-parse-ok`

### Behavioral Evidence Summary

- AUD-014:
  - Runtime assignable agent validation now loads from versioned manifest with fail-closed behavior.
  - Governance profile and dashboard surface stale agent reference findings for persisted assignment/chain drift.
- AUD-015:
  - Handoff validation now enforces primary assignment presence, positive/contiguous ordering, bounded thresholds, and payload contract compatibility.
  - Request contract and domain constraints align on `step_order >= 1` and `confidence_threshold` inclusive range `[0,1]`.
- AUD-016:
  - Introduced centralized recompute path to keep assignment, chain, and governance status consistent across lifecycle mutations.
  - Added stale agent reference metric into governance dashboard summary.
- AUD-013:
  - Deactivation now blocks when active incidents depend on active chain usage.
  - Terminal deactivation revokes active assignments/chains and invalidates publication cache.
  - Signal ingestion now rejects deactivated or non-compliant sources.
- AUD-017:
  - Precedence writes now enforce deterministic hazard/jurisdiction upsert keys and source/jurisdiction eligibility checks.
  - Added effective precedence resolver endpoint with explicit resolved vs unresolved decision outcomes.
  - OpenAPI contract updated for effective precedence and stale agent reference response payloads.

### Outstanding External Evidence (Unverified)

- Live Cosmos concurrency/race-condition behavior for precedence upsert and lifecycle mutation ordering under multi-writer load.
- Production ingestion worker parity verification for all non-HTTP ingestion entry points.

## 2026-09-15 — AUD-001, AUD-010, AUD-011, AUD-012 implementation

### Scope

- Implemented only AUD-001, AUD-010, AUD-011, AUD-012 in this spec folder context.
- Preserved existing unrelated dirty worktree changes.

### Automated Acceptance Evidence

- Focused governance tests:
  - Command: `python -m pytest tests/integration/test_aud001_aud010_governance_auth_runtime.py tests/contract/test_data_source_registry.py tests/contract/test_constitutional_compliance.py tests/integration/test_aud006_signal_semantics.py tests/integration/test_aud007_signal_accepted_workflow.py -q`
  - Result: `59 passed, 2 warnings`
- Python syntax validation:
  - Command: `python -m py_compile ...` (modified governance files and touched tests)
  - Result: success, no output
- OpenAPI parse validation (PyYAML):
  - Command: `python -c "from pathlib import Path; import yaml; ..."`
  - Result: `openapi 3.1.0`, `paths 12`

### Behavioral Evidence by AUD

- AUD-001:
  - Verified-principal dependency reads only `request.state.claims`.
  - Anonymous principals rejected; read/write role checks enforced.
  - Governance actor attribution bound to principal subject.
  - Body actor spoof mismatch returns 403.
- AUD-010:
  - Shared app-scoped governance repository/registry/cache composition used by data sources, governance, signals, authoritative ingestion, and replacement dashboard aggregation.
  - Seed import moved to lifespan helper with retry-on-next-startup behavior.
  - Existing source rows retained on repeated seed import.
  - Production-auth mode disallows implicit in-memory fallback for governance repository.
- AUD-011:
  - Required registration metadata no longer default-empty in API contract models.
  - Update status typed; merged model validation used before save.
  - Derived/platform field updates rejected; terminal deactivated transition guarded.
  - Non-blank checks added for explanation/scope/rationale and list members.
- AUD-012:
  - Legacy rank-only records decode to canonical tier.
  - Contradictory explicit tier+rank rejected.
  - Tier changes recompute rank through merged validation path.
  - `input_source_ids` plus read-only effective trust fields implemented with cycle/unknown fail-closed behavior.

### Outstanding External Evidence (Unverified)

- Real Entra token and production RBAC policy validation in deployed environment.
- Real Cosmos durability/concurrency migration evidence across existing persisted records.

## 2026-09-15 — AUD-005, AUD-006, AUD-007, AUD-009, AUD-004, AUD-003, AUD-008 implementation

### Scope

- Implemented only requested AUD items in this exact sequence: 005, 006, 007, 009, 004, 003, 008.
- No deploys, no commits, no edits to global review README files.

### Automated Evidence

- Focused governance suites:
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest tests/integration/test_aud001_aud010_governance_auth_runtime.py tests/contract/test_constitutional_compliance.py tests/contract/test_governance_assignment.py tests/contract/test_governance_dashboard.py tests/integration/test_governance_grace_period.py tests/integration/test_governance_rereview.py tests/integration/test_governance_cache.py -q`
  - Result: `54 passed, 2 warnings`
- Python syntax compile:
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -m py_compile ...`
  - Result: success (no output)
- OpenAPI parse:
  - Command: `C:/Users/prbillir/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "...yaml.safe_load..."`
  - Result: `openapi 3.1.0`, `paths 14`
- UI diagnostics:
  - Tool: file diagnostics for updated governance TSX files
  - Result: no errors in updated files

### Behavioral Evidence Summary

- AUD-005:
  - Added model-level `version`/`etag` fields for governance entities.
  - Introduced repository `ConcurrencyConflictError`, scoped partition key helper, conditional version checks, and create-only semantics for append-only audit IDs.
  - Cosmos backend now uses create/conditional replace seams instead of unconditional audit upsert paths.
- AUD-006:
  - `GovernanceAuditEntry` now frozen and schema-versioned.
  - In-memory audit persistence performs deep-copy append with duplicate-ID hard failure.
  - Service audit payloads include reconstructive before/after snapshots for key governance actions.
- AUD-007:
  - Added `tenant_id`/`agency_id` to scoped governance models.
  - Scoped repository reads/writes/queries and cache keys by tenant + source.
  - Audit trail retrieval now filtered by tenant scope.
- AUD-009:
  - Added versioned rubric mapping in `packages/domain/src/domain/governance/principle_rubric.py` anchored to constitution 1.2.0 mapping.
  - Added API endpoint `GET /api/governance/assessment-criteria`.
  - UI now renders selected principle criteria, missing-principles indicator, and historical-rubric badge.
- AUD-004:
  - Compliance derivation now requires complete required-principle coverage and rejects incomplete/duplicate sets as unassessed.
  - Updated tests that previously codified 2/6-compliant approval.
- AUD-003:
  - Grace lifecycle hardened with configurable default duration, None-safe extension handling, warning/expiry audit semantics, and clear-on-compliant transitions.
- AUD-008:
  - Assessments now persist `rereview_required`/`rereview_reason`, constitution/rubric version fields.
  - Source-change rereview limited to material fields; amendment rereview flags current assessments idempotently.
  - Dashboard `rereview_pending` now computed from persisted scoped assessment state.

### Outstanding External Evidence (Unverified)

- Real Cosmos transactional-batch behavior for multi-document mutations under concurrent load.
- External migration/repartition evidence for existing legacy scoped documents.
- External scheduler-notification transport and legal/owner approval for constitution mapping governance sign-off.

## 2026-09-15 — Aggregate Regression Result

- Corrected stale-agent projection so source registration does not require the runtime-agent manifest when no assignment or chain references exist.
- Updated the signal-workflow integration fixture to establish the finalized six-principle current-rubric eligibility state before ingestion.
- Combined spec-005 governance suite: PASS (`179 passed, 1 skipped, 2 warnings in 13.86s`).
- The skipped test is the explicit opt-in staging governance measurement; `AMA_STAGING_GOVERNANCE` was intentionally unset.
- The warnings are upstream Starlette/httpx deprecations and do not indicate behavioral failures.
- All 28 remediation tasks are checked for repository-automatable implementation or explicit measurement scaffolding.
- External Entra/Cosmos/Redis/Azure Monitor evidence, Redis SKU approval, legal control approval, SME panel, usability study, and live rehearsal measurements remain unverified.

### Final evidence-gate outcomes

- AUD-028 evidence ownership validator: PASS.
- Generated readiness audit replay: PASS.
- Generated readiness acceptance validation: EXPECTED FAIL because external evidence is absent (`source_coverage_ratio=0`, no sub-1800-second workflow result, no tested-user denominator, no approved decision, and no deactivated-history exercise).
- This fail-closed result confirms the scaffolding cannot be mistaken for completed SC-001/SC-004/SC-005 evidence.
- Evidence Markdown lint: PASS.
