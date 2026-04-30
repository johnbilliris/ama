# Spec 032 — Requirement → Test Traceability Matrix

**Purpose**: Per FR-T07, every spec ships a matrix linking each FR to its test coverage. This file is the matrix for spec 032 itself, populated incrementally as Stream tasks land.

**Status**: scaffold (T009). Filled in as tests land in Streams 1–9.

## Conventions
- "Test" column lists the canonical test file(s) for the FR. Multiple tests separated by `;`.
- "Status": `pending` (no test yet) | `partial` (some coverage) | `complete` (CI gate covers acceptance scenarios) | `n/a` (docs-only FR; verification via review).
- "Acceptance link": user story acceptance scenario(s) the test maps to.

## Matrix

| FR | Test(s) | Status | Acceptance link |
|---|---|---|---|
| FR-A01 | Manual review of `docs/architecture/c4/` | n/a (docs) | US-Arch |
| FR-A02 | Manual review of `docs/architecture/cosmos-partitioning.md` | n/a (docs) | US-Arch |
| FR-A03 | Manual review of main.bicep header table (T023) | complete (docs) | US-Arch |
| FR-A04 | Manual review of sequence diagram | n/a (docs) | US-Arch |
| FR-A05 | `tests/unit/test_spec032_agent_subpackages.py` (sub-package re-exports verified) | complete | US7 |
| FR-P01 | `tests/unit/test_spec032_llm_and_aiims.py::TestLlmStrategies` (5 tests) | complete | US4 |
| FR-P02 | `tests/unit/test_spec032_llm_and_aiims.py::TestBudgetTracker` (5 tests; in-memory; Cosmos path covered by smoke) | complete | US4 |
| FR-P03 | `tests/unit/test_spec032_agent_subpackages.py::TestPyBreakerAdapter` (fallback path) | complete (adapter + ADR-034) | US3 |
| FR-P04 | Manual review of `docs/agents/saga-approval-workflow.md` | n/a (docs) | US5 |
| FR-P05 | `tests/unit/test_spec032_llm_and_aiims.py::TestAiimsRegistry` (4 tests) | complete | US5 |
| FR-Q01 | `.github/workflows/ci.yml` mypy --strict step (Phase-A grace) | partial (continue-on-error during Phase A) | US7 |
| FR-Q02 | `.github/workflows/ci.yml` import-linter step + 4 contracts in `pyproject.toml` | complete | US7 |
| FR-Q03 | `.github/workflows/ci.yml` ruff format --check step | complete | US7 |
| FR-Q04 | Manual: `pre-commit run --all-files` | n/a | US7 |
| FR-Q05 | (= FR-A05) | pending | US7 |
| FR-I01 | Manual: spec 030 status check | complete (spec 030 status now Approved) | US-Impl |
| FR-I02 | `tests/eval/test_dataset_v1_size.py` (asserts ≥ subset; ramp tracked in manifest) | pending | US4 |
| FR-I03 | `apps/web/e2e/operator-journey.spec.ts` | pending | US-Impl |
| FR-I04 | Manual review of operator-runbooks | n/a (docs) | US-Impl |
| FR-I05 | `tests/devops/test_no_placeholder_uuids.py` | complete via deletion (see T008-fr-i05-status.md) | US2 |
| FR-T01 | `.github/workflows/ci.yml` + `scripts/coverage-ratchet.ps1` (Phase A active per coverage-phase-tracker.md) | complete (Phase A) | US7 |
| FR-T02 | `apps/web/__tests__/smoke.test.tsx` + `vitest.config.ts` | complete (smoke) | US7 |
| FR-T03 | `tests/chaos/` suite | pending | US3, US6 |
| FR-T04 | `.github/workflows/codeql.yml`, `.github/workflows/security-scan.yml` (gitleaks + PSRule + Trivy) | complete | US2 |
| FR-T05 | `.github/workflows/nightly-load.yml` (cron daily 16:00 UTC) | complete | US6 |
| FR-T06 | `tests/README.md` review | complete (T002) | US8 |
| FR-T07 | This file | complete (scaffold) | US7 |
| FR-T08 | `tests/contract/CONTRIBUTING.contract.md` | pending | US8 |
| FR-T09 | `tests/eval/test_acceptance_ids.py` | pending | US4 |
| FR-T10 | Cross-link in `docs/.../post-exercise-survey.md` | pending | US-Impl |
| FR-O01 | `tests/devops/test_monitoring_retention.py` | pending | US3 |
| FR-O02 | `docs/observability/metrics-catalogue.md` + `apps/api/app/observability/metrics.py` | complete | US3 |
| FR-O03 | `apps/agents/common/llm_budget_tracker.py` emits llm.cost.aud_micros + llm.budget.warning_total | complete | US3 |
| FR-O04 | Manual review of Workbook JSON | pending | US3 |
| FR-O05 | `tests/security/test_pii_redaction.py` + canary scan job | pending | US1 |
| FR-O06 | `docs/observability/slo.md` (10 SLOs + paging tiers) | complete (docs) | US3 |
| FR-O07 | `apps/api/app/observability/__init__.py` (Azure Monitor OTel Distro bootstrap) | complete (bootstrap) | US3 |
| FR-O08 | Manual review of operator runbook Workbooks | pending | US3 |
| FR-O09 | `tests/devops/test_action_group_routing.py` | pending | US3 |
| FR-O10 | `infra/modules/availability-tests.bicep` (5 APAC POPs) | complete (Bicep must-land) | US3 |
| FR-AI01 | `tests/unit/test_spec032_jurisdiction_and_rag.py::TestRagServiceStub` (3 tests) + ai-search.bicep | complete (skeleton) | US4 |
| FR-AI02 | `tests/unit/test_recommendation_provenance.py` | pending | US1 |
| FR-AI03 | `tests/integration/test_phi_shadow.py` | pending | US4 |
| FR-AI03a | `tests/security/test_foundry_carveout.py` (6 tests; verify-carveout.ps1) | complete | US2 |
| FR-AI04 | `tests/unit/test_structured_output_enforcement.py` | pending | US4 |
| FR-AI05 | `tests/unit/test_prompt_registry.py` | pending | US4 |
| FR-AI06 | Bicep modules ai-search.bicep, content-safety-pe.bicep, cosmos-cmk.bicep, private-endpoints.bicep (all compile) | complete (Bicep) | US2 |
| FR-AI07 | Manual review of model-rollback runbook | n/a (docs) | US6 |
| FR-AI08 | Manual review of AOAI quota runbook | n/a (docs) | US6 |
| FR-AI09 | `.github/workflows/prompts-publish.yml` cosign keyless + cosign.manifest.yaml + ADR-035 | complete (workflow) | US4 |
| FR-AI10 | `tests/devops/test_canary_workflow.py` | pending | US6 |
| FR-AG01 | Manual review of decision-rights matrix | n/a (docs) | US5 |
| FR-AG02 | `tests/unit/test_spec032_agent_subpackages.py::TestAutonomy` (6 tests) + `tests/unit/test_spec032_jurisdiction_and_rag.py::TestJurisdictionGovernancePolicy` (6 tests) | complete | US5 |
| FR-AG03 | `tests/integration/test_why_fired.py` | pending | US1 |
| FR-AG04 | Manual review of README agent table | complete (T010) | US8 |
| FR-AG05 | `tests/unit/test_spec032_agent_subpackages.py::TestKillSwitch` (5 tests) + spike doc T016 | complete (in-process; SLO test deferred to Stream 7 prod wiring) | US5 |
| FR-AG05a | `tests/contract/test_killswitch_authz.py` (asserts dual-approval in production) | pending | US5 |
| FR-AG06 | `tests/unit/test_state_graph_renderer.py` | pending | US5 |
| FR-AG07 | `tests/integration/test_reflection_feedback.py` | pending | US5 |
| FR-AG08 | `tests/unit/test_handoff_timeouts.py` | pending | US5 |
| FR-AG09 | `tests/integration/test_consensus_event.py` | pending | US5 |
| FR-AG10 | `tests/integration/test_aar_gap_summary.py` | pending | US5 |
| FR-S01 | Bicep modules (cosmos-cmk.bicep, private-endpoints.bicep, content-safety-pe.bicep, ai-search.bicep) | complete (Bicep) | US2 |
| FR-S02a | Manual review of ADR-032 | n/a (docs) | US2 |
| FR-S02b | `tests/devops/test_oidc_workflow.py` (BLOCKED until spec-031 prereq) | pending | US2 |
| FR-S03 | `.github/workflows/codeql.yml` Python + JS/TS | complete | US2 |
| FR-S04 | Bicep modules defender.bicep, sentinel.bicep (must-land subset, both compile) | complete (Bicep must-land) | US2 |
| FR-S05 | Bicep module cosmos-cmk.bicep (HSM RSA-4096 + 90d rotation) | complete (Bicep) | US2 |
| FR-R01 | `.github/workflows/ci.yml` benchmark step (continue-on-error removed) | complete | US6 |
| FR-R02 | (= FR-T05) | pending | US6 |
| FR-R03 | Manual review of capacity model | n/a (docs) | US6 |
| FR-R04 | `tests/devops/test_cosmos_autoscale_caps.py` | pending | US6 |
| FR-R05 | `.github/workflows/chaos-quarterly.yml` + `infra/modules/chaos-studio.bicep` | complete | US6 |
| FR-C01 | External (spec 031); verified at T801 | pending | US6 |
| FR-C02 | Manual review of progressive-delivery doc | n/a (docs) | US6 |
| FR-C03 | SHA-pin sweep complete (2026-04-30); 12 workflows updated; SHA_PIN_TRACKER.md | complete | US6 |
| FR-C04 | `.github/workflows/dora-metrics.yml` + `scripts/dora_metrics_publish.py` | complete | US6 |
| FR-C05 | (= FR-S01) | pending | US6 |
| FR-D01 | `docs/operator-runbooks/dr-bcp.md` + `.github/workflows/dr-drill.yml` (RPO<=15min RTO<=60min) | complete (runbook + drill workflow) | US6 |
| FR-D02 | `tests/devops/test_dockerfile_pinning.py` | pending | US6 |
| FR-D03 | Manual review of cost-report template | n/a (docs) | US6 |
| FR-D04 | `tests/devops/test_cosmos_pitr_enabled.py` | pending | US6 |
| FR-D05 | Manual review of exercise schedule | n/a (docs) | US6 |
| FR-DOC01 | Manual: README link reachable | pending | US8 |
| FR-DOC02 | `apps/web/e2e/api-docs.spec.ts` | pending | US8 |
| FR-DOC03 | Manual review of governance-hub | pending | US8 |
| FR-DOC04 | Manual review of CONTRIBUTING.md | complete (T003) | US8 |
| FR-DOC05 | Manual review of CHANGELOG.md | complete (T004 scaffold) | US8 |

## Polish gate (T1005)

Before merging the spec-032 PR series, every row above must be either `complete` or have an explicit `out-of-scope` decision recorded with rationale.
