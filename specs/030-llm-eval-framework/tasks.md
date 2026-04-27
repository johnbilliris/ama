---

description: "Tasks for feature 030-llm-eval-framework — LLM Evaluation Framework for Disaster Response"
---

# Tasks: LLM Evaluation Framework for Disaster Response

**Input**: Design documents from `C:\code\ama\specs\030-llm-eval-framework\`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅, quickstart.md ✅

**Tests**: Tests are included; the spec relies on independent test criteria per user story (Acceptance Scenarios + SC-002, SC-003, SC-004, SC-007, SC-012). TDD ordering is enforced inside each story (test → implementation).

**Organization**: Tasks are grouped by user story (US1..US6) for independent delivery. Phases 1–2 are blocking foundational work; the final phase is cross-cutting polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]** = parallelizable (different files, no dependencies on incomplete tasks)
- **[Story]** = US1..US6, mapped to spec.md user stories
- Each task includes a single file path or directory scope, and is annotated with:
  - **Agents** — which actor-specific agents (`.github/agents/...`) to consult for input/output. Multiple agents = collaborative review.
  - **Tools** — required tool kinds: `execute`, `read`, `edit`, `search`, `web`, `agent`, `todo`.

## Path Conventions

Monorepo (per plan.md Project Structure):

- Web: `apps/web/src/...`
- API: `apps/api/app/...`
- Worker: `apps/eval-runner/src/ama_eval/...`
- Shared lib: `packages/eval-core/src/ama_eval_core/...`
- Dataset content + tooling: `packages/eval-dataset/...`
- IaC: `infra/bicep/modules/eval/...`, `infra/policy/eval/...`
- Tests: `tests/unit/eval/`, `tests/integration/eval/`, `tests/contract/`, `apps/web/e2e/eval/`
- Workflows: `.github/workflows/...`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold the new packages, the worker app, the API/web feature folders, and the IaC module skeleton; wire them into the existing monorepo lint/test entrypoints.

- [X] T001 [P] Scaffold `packages/eval-core/` Python package: create `pyproject.toml` (Python 3.13, dependencies on `pydantic>=2`, `jsonschema`), `src/ama_eval_core/__init__.py`, `README.md`, and an empty `tests/` folder. Register the package as a uv/pnpm workspace member in the repo root configuration.
  - Agents: `software-developer`, `principal-engineer`
  - Tools: `read`, `edit`, `execute`
- [X] T002 [P] Scaffold `apps/eval-runner/` Python service: create `pyproject.toml` (deps on `azure-ai-evaluation`, `azure-ai-projects`, `azure-identity`, `azure-cosmos`, `azure-storage-blob`, `azure-monitor-opentelemetry`, `azure-mgmt-resource`, `azure-mgmt-cognitiveservices`, `presidio-analyzer`, `presidio-anonymizer`, `ama-eval-core` workspace dep), `src/ama_eval/__init__.py`, `Dockerfile` (slim Python 3.13, non-root user), and `.dockerignore`.
  - Agents: `software-developer`, `docker-container-engineer`, `infrastructure-devops`
  - Tools: `read`, `edit`
- [X] T003 [P] Scaffold `packages/eval-dataset/` content+tooling package: create `pyproject.toml` (deps on `presidio-analyzer`, `jsonschema`, `ama-eval-core`), folders `cases/`, `generation/`, `manifests/`, and a `README.md` describing the authoring workflow (research D7).
  - Agents: `software-developer`, `data-engineer`
  - Tools: `read`, `edit`
- [X] T004 [P] Add API feature folders in `apps/api/app/`: create empty `api/routes/eval/__init__.py`, `models/eval/__init__.py`, `services/eval/__init__.py`, `repositories/eval/__init__.py`. Do NOT yet wire into `api/router.py` (T019 covers wiring after foundational layer exists).
  - Agents: `software-developer`, `api-architect`
  - Tools: `edit`
- [X] T005 [P] Add web feature folders in `apps/web/src/`: create `app/eval/`, `components/eval/`, and a stub `lib/api/eval.ts` exporting `// TODO` placeholder types matching contracts/api.md.
  - Agents: `software-developer`, `ux-designer`
  - Tools: `edit`
- [X] T006 [P] Scaffold `infra/bicep/modules/eval/` with empty placeholder files `eval-platform.bicep`, `foundry-deployments.bicep`, `eval-rbac.bicep`, plus `infra/bicep/parameters/eval-platform.dev.json`, `eval-platform.staging.json`, `eval-platform.production.json` (with parameter schemas only, no values yet).
  - Agents: `infrastructure-devops`, `azure-principal-architect`, `solution-architect`
  - Tools: `edit`, `search`
- [X] T007 [P] Add `infra/policy/eval/provisioning-policy.dev.yaml` with placeholder fields (`allowedRegions`, `allowedSkus`, `maxConcurrentDeployments`, `maxRunCostAud`, `maxRunDurationMinutes`, `prFastSubsetMaxMinutes`, `secondaryJudgeSamplingRate`, `evaluatorRoles`) and `infra/policy/eval/promotion-gates/eval-gate.yaml` referenced by feature 029.
  - Agents: `infrastructure-devops`, `compliance-auditor`, `security-engineer`
  - Tools: `edit`, `read` (read `specs/029-progressive-delivery-pipeline/plan.md` to align gate schema)
- [X] T008 Wire all new Python packages into the repo's existing pytest and ruff configuration so `pytest -q` and `ruff check` discover them; extend `pnpm-workspace.yaml` if `apps/eval-runner` exposes any node tooling (it does not at this stage). Verify by running `ruff check apps/eval-runner packages/eval-core packages/eval-dataset` and `pytest --collect-only tests/unit/eval` — both must succeed and discover zero tests yet.
  - Agents: `software-developer`, `qa-test-engineer`
  - Tools: `read`, `edit`, `execute`

**Checkpoint**: Skeleton compiles, lints clean, no tests yet. Foundational phase can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared schemas, models, repositories, role guard, Foundry client, IaC platform module, and the API router skeleton that every user story depends on. **No user-story work may begin until this phase completes.**

- [X] T009 [P] Author JSON Schemas in `packages/eval-core/src/ama_eval_core/schemas/`: `case.schema.json`, `dataset-manifest.schema.json`, `metric-definition.schema.json`, `judge.schema.json`, `run.schema.json`, `scorecard.schema.json`, `audit-event.schema.json`, `provisioning-policy.schema.json`. Schemas MUST mirror `data-model.md` field-for-field including BCP-47 `language` validation, sensitivity-label vocabulary, hazard-tag enum, and the FR-008 "graphic ⇒ sensitivityLabels" co-occurrence rule.
  - Agents: `data-engineer`, `solution-architect`, `compliance-auditor`
  - Tools: `read`, `edit`
- [X] T010 [P] Implement Pydantic v2 models in `packages/eval-core/src/ama_eval_core/models.py` matching every entity in `data-model.md` (`EvaluationCase`, `EvaluationDatasetVersion`, `MetricDefinitionVersion`, `JudgeModelVersion`, `ModelUnderTest`, `EvaluationRun`, `Scorecard`, `SampleTrace`, `Baseline`, `ProvisioningPolicy`, `InfrastructureLifecycleRecord`, `AuditEvent`). Include `model_validator` enforcing each cross-field invariant from §"Cross-cutting invariants". Import the JSON Schemas (T009) and assert structural alignment in a test.
  - Agents: `software-developer`, `data-engineer`
  - Tools: `read`, `edit`
- [X] T011 [P] Implement audit-event vocabulary + emitter in `packages/eval-core/src/ama_eval_core/audit.py`: an `AuditAction` enum covering every action in `data-model.md` §AuditEvent; an `AuditEmitter` protocol; an in-memory test double; and the Cosmos-backed implementation will live in the API repo layer.
  - Agents: `software-developer`, `security-engineer`, `compliance-auditor`
  - Tools: `read`, `edit`
- [X] T012 [P] Implement pure `ProvisioningPolicy` evaluator in `packages/eval-core/src/ama_eval_core/policy.py`: pure functions `validate_policy(policy)`, `check_run_against_policy(run_request, policy) -> PolicyVerdict`, returning structured violations for cost/region/sku/concurrency/duration breaches per FR-018. No I/O.
  - Agents: `software-developer`, `solution-architect`, `security-engineer`
  - Tools: `read`, `edit`
- [X] T013 [P] Author `tests/unit/eval/test_eval_core_models.py` and `tests/unit/eval/test_policy_evaluator.py`: round-trip every Pydantic model against its JSON Schema, validate invariant rejections (e.g., `provenance=sanitised-real` without `sanitisationLog` is rejected), and exhaustively cover `check_run_against_policy` cost/region/duration matrices.
  - Agents: `qa-test-engineer`, `software-developer`
  - Tools: `read`, `edit`, `execute`
- [X] T014 [P] Author `infra/bicep/modules/eval/eval-platform.bicep`: deploys (in `australiaeast`) Cosmos DB containers `eval_datasets`, `eval_runs`, `eval_metric_definitions`, `eval_audit` with their partition keys per data-model.md; an immutable Storage account with **time-based retention = 7 years** (FR-021) and containers `datasets`, `runs`, `audit-archive`; Key Vault `kv-ama-eval-${env}`; Container Apps environment `cae-ama-eval-${env}`; two Container Apps Jobs `caj-eval-runner-${env}` (manual-trigger) and `caj-eval-reconciler-${env}` (cron `*/30 * * * *`); App Insights linked to existing AMA Log Analytics workspace. Use AVM modules where available; assert via `bicep build` that compilation succeeds.
  - Agents: `infrastructure-devops`, `azure-principal-architect`, `solution-architect`, `security-engineer`
  - Tools: `read`, `edit`, `execute`, `web` (look up AVM module versions if uncertain)
- [X] T015 [P] Author `infra/bicep/modules/eval/foundry-deployments.bicep`: parametrised module accepting `(modelId, version, region, sku, deploymentName, runId tag)`. Region MUST be selectable from the constitution carve-out list (no AU-region restriction for this resource only); tags MUST include `runId` and `eval-managed=true`. Used by the runner's provisioner (T035), not deployed directly by `eval-platform.bicep`.
  - Agents: `infrastructure-devops`, `azure-principal-architect`, `ai-ml-engineer`, `compliance-auditor`
  - Tools: `read`, `edit`, `execute`
- [X] T016 Author `infra/bicep/modules/eval/eval-rbac.bicep`: assigns Managed Identity for `caj-eval-runner-${env}` the roles `Cosmos DB Built-in Data Contributor` (scoped to eval containers), `Storage Blob Data Contributor` (scoped to the eval storage account), `Key Vault Secrets User`, `Azure AI Developer` over the Foundry project, and `Contributor` over a single dedicated `rg-eval-runs-${env}` resource group used for ephemeral RGs. Define Entra ID app roles `eval-author`, `safety-reviewer`, `governance-reviewer`. Depends on T014.
  - Agents: `infrastructure-devops`, `security-engineer`, `compliance-auditor`
  - Tools: `read`, `edit`, `execute`
- [X] T017 [P] Populate `infra/bicep/parameters/eval-platform.{dev,staging,production}.json` with environment-specific values; staging+production MUST set Storage `immutabilityPolicy.state=Unlocked` initially with a TODO to lock manually after first publish; dev MAY use `Disabled` for iteration.
  - Agents: `infrastructure-devops`, `compliance-auditor`
  - Tools: `read`, `edit`
- [X] T018 Implement repositories in `apps/api/app/repositories/eval/`: `dataset_repository.py`, `run_repository.py`, `metric_repository.py`, `audit_repository.py`. Follow the AMA convention (memory): auto-connect via `_build_cosmos_client()` using `DefaultAzureCredential` when `COSMOS_ENDPOINT` is set, with try/except fallback to in-memory. Each repo MUST emit an `AuditEvent` to `audit_repository` on every mutating call.
  - Agents: `software-developer`, `data-engineer`, `security-engineer`
  - Tools: `read`, `edit`, `search` (verify against `apps/api/app/repositories/governance_repository.py`)
- [X] T019 [P] Implement Foundry client wrapper in `apps/eval-runner/src/ama_eval/foundry_client.py`: a single `FoundryClient` class that holds an `AIProjectClient`, accepts a `(modelId, version, deploymentName, params)` and exposes `infer(prompt, conversation=None)` and `judge(prompt, output, rubric)` returning typed responses with `tokenUsage`, `latencyMs`, `safetyFilterTriggered`, and `rawResponse`. All authentication via `DefaultAzureCredential`.
  - Agents: `ai-ml-engineer`, `software-developer`, `security-engineer`
  - Tools: `read`, `edit`, `web` (consult Microsoft Foundry SDK docs as needed)
- [X] T020 Implement Tier-2 role guard in `apps/api/app/middleware/eval_role_guard.py`: a FastAPI dependency that checks the principal carries one of `eval-author`, `safety-reviewer`, `governance-reviewer`; on success, emits a `scorecard.trace.read` (or equivalent) audit event using the audit repository (T018). Reject with `403 insufficient-role` otherwise. Add unit tests covering both success and rejection plus the audit-emission side effect.
  - Agents: `security-engineer`, `software-developer`, `compliance-auditor`
  - Tools: `read`, `edit`, `execute`
- [X] T021 Implement `apps/eval-runner/src/ama_eval/evidence.py`: builds the per-run evidence bundle described in research D10 (scorecard, dataset manifest, model manifest, metric/judge manifest, infra-lifecycle record, audit projection) into a deterministic zip; signs the digest using the same signing flow as feature 029's evidence pack (read `specs/029-progressive-delivery-pipeline/plan.md` for the signer interface).
  - Agents: `security-engineer`, `infrastructure-devops`, `compliance-auditor`, `principal-engineer`
  - Tools: `read`, `edit`, `search`
- [X] T022 Wire the eval router skeleton: create `apps/api/app/api/routes/eval/__init__.py` exporting an empty `APIRouter(prefix="/api/eval")`, register it in `apps/api/app/api/router.py`. Add a single `GET /api/eval/health` endpoint returning `{"status":"ok"}` so wiring is verifiable end-to-end.
  - Agents: `software-developer`, `api-architect`
  - Tools: `read`, `edit`, `execute`
- [X] T023 Run `pytest tests/unit/eval -q` and `ruff check apps/eval-runner packages/eval-core apps/api/app/{api,models,services,repositories,middleware}/eval` — both MUST be green. Use the rubber-duck agent to review the foundational layer for design holes before user stories begin.
  - Agents: `qa-test-engineer`, `principal-engineer`, `solution-architect`
  - Tools: `execute`, `agent`

**Checkpoint**: Schemas, models, policy evaluator, repositories, role guard, Foundry client, IaC platform module, and router skeleton are in place and tested. User-story phases can now proceed in parallel.

---

## Phase 3: User Story 1 — Compare candidate Foundry models against disaster-domain criteria (Priority: P1) 🎯 MVP

**Goal**: Enable an evaluator to launch a multi-model comparison run and receive a single comparable scorecard with per-metric scores, sample-level traces, and an overall recommendation (Acceptance Scenarios 1.1–1.3).

**Independent Test**: Trigger a run with ≥2 registered Foundry models against a small published dataset (Phase 4 produces v1.0.0; for US1 in isolation, use a 50-case smoke dataset committed under `packages/eval-dataset/cases/_smoke/`). Confirm a scorecard returns with per-metric scores, dataset hash, model identifiers/versions, and a winner per metric and overall.

### Tests for User Story 1 ⚠️ (write FIRST, ensure failing)

- [X] T024 [P] [US1] Author contract test `tests/contract/test_eval_api_runs.py`: emits OpenAPI for the `/api/eval/runs/*` and `/api/eval/scorecards/{runId}` endpoints, and asserts shapes match `contracts/api.md` (response keys, status codes, error envelope). Also asserts retrieval metrics (FR-001(d)) appear in the scorecard schema for cases with `retrievalScope=true`. On first run the test MUST fail because the endpoints don't yet exist.
  - Agents: `qa-test-engineer`, `api-architect`
  - Tools: `read`, `edit`, `execute`
- [X] T025 [P] [US1] Author integration test `tests/integration/eval/test_run_lifecycle.py`: queues a run against the in-memory dataset (smoke 50-case fixture) with two stub Foundry models, drives it to completion through the in-process runner, and asserts the resulting scorecard has per-metric pass/fail per model and a winner. MUST fail before T029–T036 land.
  - Agents: `qa-test-engineer`, `software-developer`, `ai-ml-engineer`
  - Tools: `read`, `edit`, `execute`

### Implementation for User Story 1

- [X] T026 [P] [US1] Add a 50-case smoke fixture under `packages/eval-dataset/cases/_smoke/` covering ≥3 hazard tags and ≥2 expected actions. Build it via `python packages/eval-dataset/generation/build_smoke.py` (a small generator script) so the fixture is regenerable.
  - Agents: `data-engineer`, `software-developer`, `incident-commander`, `risk-manager`, `nsw-rfs`, `nsw-ambulance`
  - Tools: `read`, `edit`, `execute`, `agent` (consult the operational + sector agents above to ground rubric correctness for the hazard tags)
- [X] T027 [P] [US1] Implement Pydantic request/response models in `apps/api/app/models/eval/runs.py` for `POST /api/eval/runs`, `GET /api/eval/runs/{runId}`, `GET /api/eval/runs/{runId}/progress`, `POST /api/eval/runs/{runId}/cancel`, all matching `contracts/api.md`.
  - Agents: `software-developer`, `api-architect`
  - Tools: `read`, `edit`
- [X] T028 [US1] Implement `apps/api/app/services/eval/run_orchestrator.py`: validates `POST /api/eval/runs` input via the policy evaluator (T012), persists the queued run to Cosmos via `RunRepo` (T018), then either invokes the in-process runner (test mode) or kicks off the Container Apps Job (`apps/api/app/workers/eval_worker_invoker.py`). Idempotent for `(changeRef, mode)` per contracts/api.md; non-idempotent otherwise (each request → distinct `runId`). Cancel signal: `POST /api/eval/runs/{runId}/cancel` sets `runs.status="cancelling"` in Cosmos; the runner polls this flag at every case-loop iteration and on detection writes partial results, runs `provisioner.deprovision`, and exits with code `3`.
  - Agents: `software-developer`, `api-architect`, `solution-architect`
  - Tools: `read`, `edit`
- [X] T029 [US1] Implement `apps/eval-runner/src/ama_eval/runner.py` main loop: `__main__` parses `--run-id`, loads the run from Cosmos and dataset cases from Blob, invokes the provisioner stub (real provisioner ships in US3/T055), runs cases through `evaluators/` (rule_based, primary_judge, secondary_judge, retrieval, disambiguator), writes per-sample traces to Blob (`runs/{runId}/traces/{caseId}.json`), aggregates the scorecard, persists summary to Cosmos, emits terminal audit event, and exits 0/1/2/3 per contracts/api.md. Polls `runs.status` every iteration; on `cancelling` short-circuits to teardown path and exits with code `3`.
  - Agents: `software-developer`, `ai-ml-engineer`, `sre-engineer`
  - Tools: `read`, `edit`, `execute`
- [X] T030 [P] [US1] Implement `apps/eval-runner/src/ama_eval/evaluators/rule_based.py`: deterministic checks for refusal-keywords, structured-output shape, escalation-trigger detection, and exact-match factuality. Each evaluator returns `{metricId, version, tier="rule-based", value, rationale}`.
  - Agents: `ai-ml-engineer`, `software-developer`, `incident-commander`, `risk-manager`
  - Tools: `read`, `edit`
- [X] T031 [P] [US1] Implement `apps/eval-runner/src/ama_eval/evaluators/primary_judge.py`: wraps `azure-ai-evaluation` built-ins (Groundedness, Relevance, Coherence, Fluency, Similarity, Content Safety, Indirect Attack) and adds custom evaluators for refusal-correctness, tone-appropriateness, escalation-trigger correctness using a single configurable Foundry judge. Each output records `{judgeId, judgeVersion}`.
  - Agents: `ai-ml-engineer`, `software-developer`, `public-information-officer`, `compliance-auditor`
  - Tools: `read`, `edit`, `web` (consult Microsoft `azure-ai-evaluation` docs)
- [X] T031a [P] [US1] Implement `apps/eval-runner/src/ama_eval/evaluators/retrieval.py`: wraps `azure-ai-evaluation` retrieval-evaluator family (e.g., `RetrievalEvaluator`, `DocumentRetrievalEvaluator`) plus custom recall@k / precision@k / nDCG@k computation against each case's `retrievedContext` field. Gated by case-level `retrievalScope == true` (data-model.md `EvaluationCase`); cases with `retrievalScope == false` are skipped. Each output records `{metricId, version, tier, value, rationale}`. Satisfies FR-001(d).
  - Agents: `ai-ml-engineer`, `software-developer`, `data-engineer`
  - Tools: `read`, `edit`, `web` (consult `azure-ai-evaluation` retrieval-evaluator docs)
- [X] T032 [P] [US1] Implement `apps/eval-runner/src/ama_eval/evaluators/secondary_judge.py`: invoked on a configurable sampled subset (per-metric `secondarySamplingRate`); records primary-vs-secondary disagreements and surfaces them in the run report (FR-003a).
  - Agents: `ai-ml-engineer`, `qa-test-engineer`, `principal-engineer`
  - Tools: `read`, `edit`
- [X] T033 [P] [US1] Implement `apps/eval-runner/src/ama_eval/evaluators/disambiguator.py`: per-sample classifier that distinguishes `refused` / `failed-to-answer` / `answered` based on output shape, safety-filter trigger, and rule-based refusal-keyword evaluator (FR-025). Unit-tested against canonical positive/negative samples.
  - Agents: `ai-ml-engineer`, `software-developer`
  - Tools: `read`, `edit`, `execute`
- [X] T034 [US1] Implement scorecard summary builder in `apps/api/app/services/eval/scorecard_service.py`: aggregates per-sample traces into per-model per-metric mean, distribution buckets, pass/fail, regression deltas vs baseline (when supplied), winner per metric, overall winner. Persists summary to Cosmos and HTML to Blob (`runs/{runId}/report.html`).
  - Agents: `software-developer`, `ux-designer`, `data-engineer`
  - Tools: `read`, `edit`
- [X] T035 [US1] Implement endpoints in `apps/api/app/api/routes/eval/runs.py`: `POST /api/eval/runs`, `GET /api/eval/runs/{runId}`, `GET /api/eval/runs/{runId}/progress` (SSE), `POST /api/eval/runs/{runId}/cancel`, `GET /api/eval/runs?status=&dataset=&since=&changeRef=`. Wire to `RunOrchestrator` (T028); cancellation MUST trigger deprovisioning even if the run is mid-flight.
  - Agents: `software-developer`, `api-architect`, `sre-engineer`
  - Tools: `read`, `edit`, `execute`
- [X] T036 [US1] Implement Tier-1 scorecard endpoint `GET /api/eval/scorecards/{runId}` in `apps/api/app/api/routes/eval/scorecards.py`. Tier-2 detail endpoints come in US5 (T076–T077). MUST never include sample-level traces.
  - Agents: `software-developer`, `security-engineer`, `api-architect`
  - Tools: `read`, `edit`
- [X] T037 [P] [US1] Implement web typed API client in `apps/web/src/lib/api/eval.ts` for run/scorecard endpoints (replace stub from T005). Use native fetch with `cache: "no-store"` per AMA convention.
  - Agents: `software-developer`, `ux-designer`
  - Tools: `read`, `edit`
- [X] T038 [P] [US1] Implement web `apps/web/src/app/eval/page.tsx` (runs list, server component, Tier-1) and `apps/web/src/components/eval/run-row.tsx`. Columns: status, started-at, dataset version, model set, verdict, link to detail.
  - Agents: `software-developer`, `ux-designer`, `accessibility-tester`
  - Tools: `read`, `edit`
- [X] T039 [P] [US1] Implement `apps/web/src/app/eval/runs/[runId]/page.tsx`: scorecard summary view with per-model per-metric chips, winner badges, regression chips, and a live progress indicator using SSE on `/api/eval/runs/{runId}/progress`. WCAG 2.2 AA compliant.
  - Agents: `software-developer`, `ux-designer`, `accessibility-tester`
  - Tools: `read`, `edit`
- [X] T040 [US1] Author Playwright spec `apps/web/e2e/eval/run-comparison.spec.ts`: drives a comparison run end-to-end against a stubbed API, asserts the scorecard renders correctly, the live progress increments, and the trace tab is gated for unauthorised users.
  - Agents: `qa-test-engineer`, `accessibility-tester`
  - Tools: `read`, `edit`, `execute`
- [X] T041 [US1] Run T024 + T025 + T040 to confirm they now pass; run `pytest tests/unit/eval tests/integration/eval/test_run_lifecycle.py -q` and `pnpm --filter web test:e2e -- eval/run-comparison.spec.ts`. Use the rubber-duck agent to review the orchestrator + evaluators for blind spots before moving to US2.
  - Agents: `qa-test-engineer`, `principal-engineer`
  - Tools: `execute`, `agent`

**Checkpoint**: US1 deliverable — a comparable multi-model scorecard exists end-to-end. **MVP achieved.**

---

## Phase 4: User Story 2 — Curate and govern a disaster-scenario evaluation dataset (Priority: P1)

**Goal**: A safety-reviewed dataset authoring + publishing workflow producing immutable, content-hashed dataset versions of approved cases (Acceptance Scenarios 2.1–2.3, FR-006 through FR-012).

**Independent Test**: An SME authors cases and a safety reviewer approves them; the publish workflow produces an immutable v1.0.0 with `caseCount ≥ 5,000`, distribution satisfying SC-005 minimum-share, and a content hash retrievable by API.

### Tests for User Story 2 ⚠️

- [X] T042 [P] [US2] Author contract test `tests/contract/test_eval_dataset_cases.py`: validates every JSON file under `packages/eval-dataset/cases/**` against `case.schema.json`, runs Presidio over `provenance == "sanitised-real"` cases and asserts no PII candidates remain, and asserts the FR-008 graphic-tag co-occurrence rule. Initially fails because the dataset is empty.
  - Agents: `qa-test-engineer`, `compliance-auditor`, `data-engineer`
  - Tools: `read`, `edit`, `execute`
- [X] T043 [P] [US2] Author integration test `tests/integration/eval/test_dataset_publish.py`: drives the publish flow end-to-end (synthetic generation → schema validation → manifest → blob upload with immutability → API publish → version retrieval).
  - Agents: `qa-test-engineer`, `data-engineer`, `security-engineer`
  - Tools: `read`, `edit`, `execute`

### Implementation for User Story 2

- [X] T044 [P] [US2] Implement `packages/eval-dataset/generation/generate.py`: synthetic case harness (research D8). Parameters: `--total`, `--distribution distribution-v1.json`, `--provenance synthetic`. Uses a frontier Foundry model with controlled, repo-committed prompts per `(hazard, behaviour-archetype)` pair; emits drafts with `approval_state="draft"`. Includes seedable RNG for deterministic regeneration.
  - Agents: `ai-ml-engineer`, `data-engineer`, `incident-commander`, `risk-manager`, `public-information-officer`, `nsw-rfs`, `cfa-vic`, `ses-nsw`, `nema`, `bom-national`
  - Tools: `read`, `edit`, `execute`, `agent` (operational + sector agents author the per-archetype prompt seeds and validate rubric realism per jurisdiction)
- [X] T045 [P] [US2] Author `packages/eval-dataset/generation/distribution-v1.json` with the per-hazard target percentages from research D8 and the SC-005 minimum-share floor. Add a CLI validator `python packages/eval-dataset/generation/validate_distribution.py manifest.json` that fails if the manifest violates the floor.
  - Agents: `data-engineer`, `incident-commander`, `risk-manager`
  - Tools: `read`, `edit`, `execute`, `agent`
- [X] T046 [US2] Generate the v1 seed corpus: run `python packages/eval-dataset/generation/generate.py --total 5000 --distribution packages/eval-dataset/generation/distribution-v1.json --provenance synthetic`. Commit the resulting case files under `packages/eval-dataset/cases/{hazard}/{caseId}.json`. After generation, run T042 — schema-validation MUST pass.
  - Agents: `data-engineer`, `software-developer`, `compliance-auditor`
  - Tools: `execute`, `read`, `todo` (track per-hazard generation passes)
- [X] T046a [US2] Seed the v1 ModelUnderTest registry: commit `packages/eval-core/src/ama_eval_core/registries/models-v1.json` containing the three FR-013 models (frontier OpenAI on Foundry, mid-tier OpenAI on Foundry, Phi-family small-language model on Foundry) with catalog identifiers, versions, default deployment SKUs, and AU-region preferences. The runner reads this registry; adding a 4th model requires only appending a JSON entry — verifies SC-010 by construction.
  - Agents: `ai-ml-engineer`, `infrastructure-devops`, `compliance-auditor`
  - Tools: `read`, `edit`, `web`
- [X] T047 [P] [US2] Implement Pydantic models for dataset publish in `apps/api/app/models/eval/datasets.py` (`PublishDatasetVersionRequest`, `DatasetVersionResponse`) per contracts/api.md.
  - Agents: `software-developer`, `api-architect`
  - Tools: `read`, `edit`
- [X] T048 [US2] Implement dataset publish service `apps/api/app/services/eval/dataset_service.py`: requires `safety-reviewer` role; assembles canonical JSONL from `cases/`; SHA-256 hashes; uploads to Blob with the immutability policy applied; persists `EvaluationDatasetVersion` (state=`published`) to Cosmos via `DatasetRepo`; rejects on distribution-violates-min-share or version-exists.
  - Agents: `software-developer`, `data-engineer`, `security-engineer`, `compliance-auditor`
  - Tools: `read`, `edit`, `execute`
- [X] T049 [US2] Implement endpoints in `apps/api/app/api/routes/eval/datasets.py`: `POST /api/eval/datasets/{datasetId}/versions`, `GET /api/eval/datasets`, `GET /api/eval/datasets/{datasetId}/versions/{version}`, `GET /api/eval/datasets/{datasetId}/versions/{version}/cases` (Tier-2, depends on T020 role guard).
  - Agents: `software-developer`, `api-architect`, `security-engineer`
  - Tools: `read`, `edit`
- [X] T050 [P] [US2] Author GitHub Actions workflow `.github/workflows/eval-dataset-publish.yml`: triggered on `push` to `main` whose changeset includes `packages/eval-dataset/cases/**` or `packages/eval-dataset/generation/**`. Runs T042 contract tests, builds the canonical JSONL, hashes it, uploads to the immutable Blob container via federated-credential OIDC, then calls `POST /api/eval/datasets/disaster-response-core/versions`. CODEOWNERS-routes the PR to `@ama/safety-reviewers` (FR-011).
  - Agents: `infrastructure-devops`, `software-developer`, `security-engineer`
  - Tools: `read`, `edit`, `web`
- [X] T051 [P] [US2] Implement Tier-1 web `apps/web/src/app/eval/datasets/page.tsx`: lists dataset families and their published versions; click-through to per-version detail page. No case-level access at Tier-1.
  - Agents: `software-developer`, `ux-designer`, `accessibility-tester`
  - Tools: `read`, `edit`
- [X] T052 [US2] Run T042 + T043 to green; publish `disaster-response-core@1.0.0` via the workflow against the dev environment; verify `GET /api/eval/datasets/disaster-response-core/versions/1.0.0` returns `state="published"`, `caseCount >= 5000`, and a `contentHash`. Have `compliance-auditor` review evidence chain.
  - Agents: `qa-test-engineer`, `compliance-auditor`, `security-engineer`
  - Tools: `execute`, `agent`

**Checkpoint**: A v1 dataset with ~5,000 approved cases is immutable, content-hashed, and addressable by API.

---

## Phase 5: User Story 3 — Provision and deprovision evaluation infrastructure on demand (Priority: P1)

**Goal**: Each run provisions Foundry deployments + supporting infra under policy, runs the eval, and deprovisions on success/failure/cancel; orphans are reconciled automatically (FR-016–FR-020, SC-003, SC-008).

**Independent Test**: Trigger a run targeting a model not currently deployed; observe a transient resource group `rg-eval-{runId}` is created, the deployment is created and used, and the resource group is deleted on completion. The reconciler reports zero orphans.

### Tests for User Story 3 ⚠️

- [X] T053 [P] [US3] Author integration test `tests/integration/eval/test_provisioning_lifecycle.py`: with a fake ARM client, asserts that `provisioner.provision(run)` honours `ProvisioningPolicy` (rejects on cost cap breach BEFORE creating any resources), creates the expected resources, tags them with `runId` + `eval-managed=true`, and that `provisioner.deprovision(run)` removes them on success, failure, AND cancellation paths.
  - Agents: `qa-test-engineer`, `infrastructure-devops`, `chaos-engineer`
  - Tools: `read`, `edit`, `execute`
- [X] T054 [P] [US3] Author chaos-style integration test `tests/integration/eval/test_reconciler.py`: simulates an orchestrator crash mid-run (no deprovision call), advances clock past `maxRunDurationMinutes`, runs the reconciler, asserts orphaned resource group is deleted and `infra.orphan.cleaned` audit event is written.
  - Agents: `qa-test-engineer`, `chaos-engineer`, `sre-engineer`
  - Tools: `read`, `edit`, `execute`

### Implementation for User Story 3

- [X] T055 [US3] Implement `apps/eval-runner/src/ama_eval/provisioner.py`: per-run resource group `rg-eval-{runId}` (created in `australiaeast`); calls `infra/bicep/modules/eval/foundry-deployments.bicep` for each MUT not already leased; runs `What-If` first and aborts on diff that would touch resources outside the run's RG; tags every resource with `runId`, `eval-managed=true`, `created-by=caj-eval-runner`. Implements `lease(deploymentName)` for warm reuse (research D3).
  - Agents: `infrastructure-devops`, `software-developer`, `azure-principal-architect`, `security-engineer`
  - Tools: `read`, `edit`, `execute`
- [X] T056 [US3] Implement deterministic teardown: in `apps/eval-runner/src/ama_eval/runner.py`, wrap the eval body in `try/finally`; the `finally` block ALWAYS calls `provisioner.deprovision(run)` regardless of exception. On exit code `2` (failed-with-orphans) the runner emits `infra.orphans.pending` for the reconciler to pick up.
  - Agents: `software-developer`, `sre-engineer`, `chaos-engineer`
  - Tools: `read`, `edit`
- [X] T057 [US3] Implement `apps/eval-runner/src/ama_eval/reconciler.py`: cron entrypoint for `caj-eval-reconciler-${env}`; lists resource groups matching `rg-eval-*` whose tag `created-by=caj-eval-runner` and creation age > `maxRunDurationMinutes + 60min`; force-deletes each, writes `InfrastructureLifecycleRecord` events and `infra.orphan.cleaned` audit events.
  - Agents: `infrastructure-devops`, `sre-engineer`, `software-developer`
  - Tools: `read`, `edit`, `execute`
- [X] T058 [US3] Implement cost attribution computation in `apps/eval-runner/src/ama_eval/runner.py`: estimate at queue-time using a static `cost-table.yaml` keyed by `(modelId, region, sku)` for Foundry inference + judge inference + storage + provision; reject in `RunOrchestrator` (T028) when `estimated > policy.maxRunCostAud`. Reconcile actuals at run end from Azure Cost Management (best-effort; estimates are authoritative for the gate).
  - Agents: `infrastructure-devops`, `data-engineer`, `software-developer`
  - Tools: `read`, `edit`, `web` (consult current Azure pricing if needed)
- [X] T059 [P] [US3] Update web `/eval/runs/[runId]/page.tsx` to render the `costAttribution` block and the `InfrastructureLifecycleRecord` summary (resources created, when torn down, terminal state).
  - Agents: `software-developer`, `ux-designer`
  - Tools: `read`, `edit`
- [X] T060 [US3] Run T053 + T054 to green; manually trigger a real run in `dev` against a Foundry model that is NOT pre-deployed; verify via `az resource list --tag eval-managed=true` that the RG is gone post-run and the reconciler log shows zero orphans across a 24-hour window.
  - Agents: `qa-test-engineer`, `infrastructure-devops`, `sre-engineer`, `chaos-engineer`
  - Tools: `execute`, `agent`

**Checkpoint**: Ephemeral provisioning is policy-bounded and self-healing. SC-003 + SC-008 demonstrably met.

---

## Phase 6: User Story 4 — Gate releases with regression evaluation (Priority: P2)

**Goal**: Block changes that regress safety/quality vs baseline; gate is invocable from GitHub Actions PR check (≤30 min) and feature 029 progressive-delivery (≤8 h), sharing one scorecard (FR-024, FR-027, SC-007).

**Independent Test**: Submit a PR that intentionally weakens a safety prompt; the `eval-gate` check fails with a sample-level diagnostic identifying the regression and the change cannot be merged without a logged override.

### Tests for User Story 4 ⚠️

- [X] T061 [P] [US4] Author contract test `tests/contract/test_eval_gate.py`: `POST /api/eval/gate/check` shape, idempotency on `(changeRef, mode)`, regression-detection envelope, override route role-gating.
  - Agents: `qa-test-engineer`, `api-architect`
  - Tools: `read`, `edit`, `execute`
- [X] T062 [P] [US4] Author integration test `tests/integration/eval/test_gate_regression.py`: seeds a baseline scorecard; submits a deliberately weakened prompt; asserts gate verdict `fail`, returns the offending sample-level diagnostic, and that override emits the expected `gate.override.applied` audit event.
  - Agents: `qa-test-engineer`, `compliance-auditor`, `security-engineer`
  - Tools: `read`, `edit`, `execute`

### Implementation for User Story 4

- [X] T063 [US4] Implement `apps/api/app/services/eval/baseline_service.py`: designates a scorecard as baseline; supports per-`{datasetId, modelTier, environment}` baselines; supersession recorded as audit events.
  - Agents: `software-developer`, `data-engineer`, `compliance-auditor`
  - Tools: `read`, `edit`
- [X] T064 [US4] Implement `apps/api/app/services/eval/gate_service.py`: compares a candidate scorecard to its baseline per metric; fails if any safety metric drops below `passThreshold` or any quality metric regresses by more than its `regressionDelta`; returns sample-level diagnostics for offending cases; idempotent on `(changeRef, mode)`.
  - Agents: `software-developer`, `principal-engineer`, `security-engineer`
  - Tools: `read`, `edit`
- [X] T065 [US4] Implement endpoints in `apps/api/app/api/routes/eval/gate.py`: `POST /api/eval/gate/check`, `POST /api/eval/gate/{runId}/override`. Override requires `governance-reviewer` role plus a `justification` (≥50 chars), `approvers[]`, and a written-record link; emits `gate.override.applied` and notifies safety reviewer.
  - Agents: `software-developer`, `security-engineer`, `compliance-auditor`, `api-architect`
  - Tools: `read`, `edit`
- [X] T066 [P] [US4] Implement `.github/workflows/eval-gate.yml`: triggers on PRs whose changes include `apps/api/app/prompts/**`, `apps/api/app/services/rag/**`, `infra/bicep/modules/ai/**`, `packages/eval-core/**`, `packages/eval-dataset/cases/**`, or `packages/eval-dataset/generation/**`. Calls `POST /api/eval/gate/check` with `mode="pr-fast-subset"`. Posts the scorecard as a PR check + comment. Required check status. Uses federated-credential OIDC.
  - Agents: `infrastructure-devops`, `security-engineer`, `software-developer`
  - Tools: `read`, `edit`, `web`
- [X] T067 [P] [US4] Wire the progressive-delivery promotion gate: extend `infra/policy/eval/promotion-gates/eval-gate.yaml` and update feature-029's promotion pipeline to call `POST /api/eval/gate/check` with `mode="progressive-delivery-full"` between `staging` and production canary; attach the returned signed evidence bundle to the existing 029 evidence pack.
  - Agents: `infrastructure-devops`, `sre-engineer`, `compliance-auditor`, `security-engineer`
  - Tools: `read`, `edit`, `search` (cross-reference 029 plan)
- [X] T067a [P] [US4] Implement scheduled-run trigger: extend `infra/bicep/modules/eval/eval-platform.bicep` (T014) with a Container Apps Job `caj-eval-scheduler-${env}` (cron `0 18 * * SUN` overnight weekly default; configurable via parameters). Job posts `POST /api/eval/runs` with `mode="scheduled-baseline"` against the current production baseline configuration. Policy guard rejects if outside `allowedRegions` or cost cap. Satisfies FR-027 ("on a schedule").
  - Agents: `infrastructure-devops`, `sre-engineer`, `software-developer`
  - Tools: `read`, `edit`, `execute`
- [X] T068 [P] [US4] Implement `apps/web/src/app/eval/gate/[changeRef]/page.tsx`: shows the gate scorecard for a given change, regression diagnostics, current verdict, override history.
  - Agents: `software-developer`, `ux-designer`, `accessibility-tester`
  - Tools: `read`, `edit`
- [X] T069 [US4] Author live-fire validation PR: a draft PR that weakens `apps/api/app/prompts/disaster_assistant.system.md` (e.g., removes a refusal directive). Confirm the `eval-gate` check fails on first attempt with a sample-level diagnostic identifying the safety regression (SC-007).
  - Agents: `qa-test-engineer`, `security-engineer`, `principal-engineer`
  - Tools: `execute`, `agent`

**Checkpoint**: Regressing changes are blocked from merging and from production promotion; one scorecard powers both surfaces.

---

## Phase 7: User Story 5 — Audit and explain a past evaluation (Priority: P2)

**Goal**: A governance reviewer can retrieve any past run's full evidence chain (dataset version, model versions, metric/judge versions, scores, rationales, approvals, overrides) without external reconstruction (FR-021, FR-022, FR-026, SC-004, SC-012).

**Independent Test**: Pick a 30-day-old run id; download its signed evidence bundle; verify signature; confirm dataset hash matches the immutable Blob; confirm a Tier-2 reviewer can see sample-level traces while a Tier-1 viewer cannot.

### Tests for User Story 5 ⚠️

- [X] T070 [P] [US5] Author contract test `tests/contract/test_eval_evidence_bundle.py`: bundle structure, manifest fields, signature verification, that `evidence-bundle` export is Tier-2 (403 for Tier-1 principals), AND a sensitivity-leak sentinel — seed a run whose dataset includes a `sensitivityLabels=["graphic-fatality"]` case with a unique sentinel string in the case body and model output; assert the Tier-1 JSON and HTML scorecard exports contain ZERO occurrences of the sentinel string and zero raw model outputs (SC-009, FR-022).
  - Agents: `qa-test-engineer`, `security-engineer`, `compliance-auditor`
  - Tools: `read`, `edit`, `execute`
- [X] T071 [P] [US5] Author integration test `tests/integration/eval/test_audit_projection.py`: drives the daily Cosmos→Blob audit projection; asserts every audit event written during a run is present in the immutable archive within 24 h.
  - Agents: `qa-test-engineer`, `data-engineer`, `compliance-auditor`
  - Tools: `read`, `edit`, `execute`

### Implementation for User Story 5

- [X] T072 [US5] Implement evidence-bundle export endpoint `GET /api/eval/scorecards/{runId}/export?format={json|html|evidence-bundle}` in `apps/api/app/api/routes/eval/scorecards.py`. Tier gating: `json|html` Tier-1; `evidence-bundle` Tier-2. Bundle assembly delegated to `apps/eval-runner/src/ama_eval/evidence.py` (T021).
  - Agents: `software-developer`, `security-engineer`, `compliance-auditor`
  - Tools: `read`, `edit`
- [X] T073 [US5] Implement Tier-2 trace endpoints `GET /api/eval/scorecards/{runId}/traces` (paged) and `GET /api/eval/scorecards/{runId}/traces/{caseId}/{modelId}` (single sample). Each request emits a `scorecard.trace.read` audit event with principal id, runId, caseId, modelId.
  - Agents: `software-developer`, `security-engineer`, `compliance-auditor`
  - Tools: `read`, `edit`
- [X] T074 [P] [US5] Implement web Tier-2 page `apps/web/src/app/eval/runs/[runId]/traces/page.tsx`: paged sample trace browser with input/output/score/rationale per sample. Server component re-checks role server-side (FR-022); client never receives traces if role check fails.
  - Agents: `software-developer`, `ux-designer`, `accessibility-tester`, `security-engineer`
  - Tools: `read`, `edit`
- [X] T075 [US5] Implement audit projection job: a daily Container Apps Job (`caj-eval-audit-projection-${env}`, defined in `infra/bicep/modules/eval/eval-platform.bicep` — extend T014) that reads new Cosmos `eval_audit` documents and appends them to the immutable Blob archive `audit-archive/{yyyy}/{mm}/{dd}/audit-{shard}.jsonl.gz`.
  - Agents: `infrastructure-devops`, `data-engineer`, `compliance-auditor`
  - Tools: `read`, `edit`, `execute`
- [X] T076 [US5] Author `docs/compliance/eval-mapping.md` mapping evidence-bundle artefacts to: (i) ISO/IEC 42001:2023 specific clauses — minimum coverage 6.1.4 (AI risk assessment), 6.2 (AI objectives), 8.3 (AI system impact assessment), 9.1 (monitoring/measurement), A.6 (AI system lifecycle), A.7 (data for AI systems); (ii) NIST AI RMF functions Govern/Map/Measure/Manage with the specific subcategories satisfied per artefact (e.g., MEASURE 2.7 safety, MANAGE 2.4 risk treatment); (iii) APP 6 (use/disclosure) and APP 11 (security) control families. Compliance-auditor sign-off is the success criterion. Generate the matrix from `eval_metric_definitions` and policy data so it stays current.
  - Agents: `compliance-auditor`, `security-engineer`, `observer-auditor`
  - Tools: `read`, `edit`, `web`
- [X] T077 [US5] Run T070 + T071 to green; perform a live-fire audit: a `governance-reviewer` retrieves a 30-day-old run's evidence bundle; verifies signature; confirms reproducibility from artefacts (SC-004, SC-012). Record findings in `docs/compliance/eval-mapping.md` evidence section.
  - Agents: `qa-test-engineer`, `compliance-auditor`, `observer-auditor`
  - Tools: `execute`, `agent`

**Checkpoint**: Past runs are fully auditable, tier-gated, and signed.

---

## Phase 8: User Story 6 — Continuously expand the dataset from real (sanitised) operations (Priority: P3)

**Goal**: An operations lead can propose a sanitised real interaction as a candidate case; PII removal and reviewer approval are enforced before publication (FR-023, Acceptance Scenario 6.1).

**Independent Test**: Submit a candidate case with provenance `sanitised-real`; confirm the publish workflow rejects it if Presidio finds PII candidates AND if it lacks safety-reviewer approval.

### Tests for User Story 6 ⚠️

- [X] T078 [P] [US6] Author integration test `tests/integration/eval/test_sanitised_real_workflow.py`: submits a candidate with synthetic PII; asserts publication is blocked; submits a properly de-identified version; asserts it is routed to safety-reviewer; on approval, asserts it is included in the next dataset version with a sanitisation log preserved.
  - Agents: `qa-test-engineer`, `compliance-auditor`, `security-engineer`
  - Tools: `read`, `edit`, `execute`

### Implementation for User Story 6

- [X] T079 [US6] Extend `packages/eval-dataset/generation/` with `sanitise_real.py`: takes a raw interaction file, runs Presidio anonymizer, writes a candidate case with `provenance="sanitised-real"`, embeds a `sanitisationLog` listing every detection + replacement, and asserts the FR-023 invariant.
  - Agents: `data-engineer`, `compliance-auditor`, `security-engineer`
  - Tools: `read`, `edit`, `execute`
- [X] T080 [US6] Extend the publish workflow (T050) to require: (a) `provenance == "sanitised-real"` ⇒ second Presidio pass at publish time MUST find zero PII candidates; (b) PR MUST be approved by both `@ama/safety-reviewers` AND `@ama/governance-reviewers` (CODEOWNERS); (c) the resulting case retains its `sanitisationLog` in the canonical JSONL.
  - Agents: `infrastructure-devops`, `compliance-auditor`, `security-engineer`
  - Tools: `read`, `edit`
- [X] T081 [US6] Run T078 to green; have `compliance-auditor` review one published `sanitised-real` case end-to-end and sign off on the de-identification chain.
  - Agents: `qa-test-engineer`, `compliance-auditor`, `observer-auditor`
  - Tools: `execute`, `agent`

**Checkpoint**: Real-interaction-derived cases can be safely added to future dataset versions.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, observability, accessibility, performance, and quickstart validation across all user stories.

- [X] T082 [P] Define SLOs for the eval API and runner: API p95 latency, runner queue→start latency, full-run-duration p95 (≤8 h, FR-018). Author SLI/SLO docs at `docs/sre/eval-slos.md` and dashboards at `infra/observability/eval-dashboards.bicep`.
  - Agents: `sre-engineer`, `observer-auditor`, `solution-architect`
  - Tools: `read`, `edit`, `web`
- [X] T083 [P] Add Application Insights tracing across runner + API per `azure-monitor-opentelemetry`: span per case, per evaluator, per provisioning step. Attributes: `runId`, `caseId`, `modelId`, `metricId`, `judgeId`, `tier`. Ensure no PII AND no graphic case body / raw model output text in span attributes (only IDs + score deltas). Add a unit test that asserts the span exporter's filter strips known sentinel strings (SC-009). Compliance-auditor sign-off required.
  - Agents: `sre-engineer`, `software-developer`, `compliance-auditor`, `security-engineer`
  - Tools: `read`, `edit`
- [X] T084 [P] Run an accessibility audit on `/eval/*` routes against WCAG 2.2 AA. Fix any defects found.
  - Agents: `accessibility-tester`, `ux-designer`
  - Tools: `read`, `edit`, `execute`
- [X] T085 [P] Run a chaos exercise: kill the runner mid-run; saturate Foundry quota; corrupt one Blob trace file; partial-network-partition Cosmos. Confirm reconciler cleans up, partial results are preserved (FR-029), and SC-011 holds.
  - Agents: `chaos-engineer`, `sre-engineer`, `software-developer`
  - Tools: `execute`, `agent`
- [X] T086 [P] Conduct a security baseline review of the new identity, data flow, and audit chain. Validate the Foundry carve-out is invoked correctly: only model-hosting endpoints in non-AU regions, all data services in AU, data-minimisation at the model gateway is provably enforced.
  - Agents: `security-engineer`, `compliance-auditor`, `azure-principal-architect`
  - Tools: `read`, `search`, `agent`
- [X] T087 [P] Run an Azure Well-Architected review across the five pillars for the new infrastructure (`infra/bicep/modules/eval/`). Address any "should-fix" findings.
  - Agents: `azure-principal-architect`, `infrastructure-devops`, `solution-architect`
  - Tools: `read`, `edit`, `web`
- [X] T088 Performance pass: profile an end-to-end full-suite run; target full-run ≤ 8 h, PR-fast-subset ≤ 30 min, per-sample p95 ≤ 30 s (FR-018, plan.md performance goals). Tune evaluator concurrency, judge batching, and Foundry deployment scale settings.
  - Agents: `sre-engineer`, `principal-engineer`, `ai-ml-engineer`
  - Tools: `execute`, `read`, `edit`
- [X] T089 Execute `quickstart.md` end-to-end in dev as a fresh evaluator: provision platform → publish dataset → trigger 3-model run → wire gate → verify each "What 'done' looks like" bullet. Additionally: register a 4th Foundry model via configuration only (append a JSON entry to `packages/eval-core/src/ama_eval_core/registries/models-v1.json` — no code change) and confirm it appears in a fresh smoke run's scorecard — verifies SC-010. File any deltas as fixes before final sign-off.
  - Agents: `qa-test-engineer`, `software-developer`, `infrastructure-devops`, `incident-commander`
  - Tools: `execute`, `read`, `agent`
- [X] T090 Run `/speckit.analyze` against this feature directory to confirm cross-artefact consistency between spec.md, plan.md, and tasks.md. Fix any drift.
  - Agents: `speckit.analyze`, `principal-engineer`
  - Tools: `agent`, `read`, `edit`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; T001–T007 are parallel; T008 depends on T001–T007.
- **Foundational (Phase 2)**: Depends on Phase 1; T009–T012 parallel; T013 depends on T009–T012; T014–T017 parallel after T009; T016 depends on T014; T018 depends on T010 + T011; T019 parallel; T020 depends on T011 + T018; T021 parallel after T010; T022 depends on T018; T023 closes the phase. **Blocks all user stories.**
- **User Stories (Phases 3–8)**: All depend on Phase 2; otherwise independent — can be staffed in parallel.
- **Polish (Phase 9)**: Depends on US1–US5 being usable (US6 may run in parallel).

### User Story Dependencies

- **US1 (P1)** — depends only on Phase 2.
- **US2 (P1)** — depends only on Phase 2 (uses smoke fixture independently of US1).
- **US3 (P1)** — depends on Phase 2; US1's `RunOrchestrator` (T028) is enriched by US3's provisioner but US1 ships with a stub provisioner so US1 can land first.
- **US4 (P2)** — depends on US1 (needs scorecards) and US2 (needs a published baseline-eligible dataset).
- **US5 (P2)** — depends on US1 (run records exist) and on the audit infrastructure from Phase 2.
- **US6 (P3)** — depends on US2 (extends the publish workflow).

### Within Each User Story

- Tests authored FIRST (must fail before implementation).
- Models → services → endpoints → web → e2e validation.
- Story complete before next priority, unless staffed in parallel.

### Parallel Opportunities

- All `[P]` tasks within Setup (Phase 1) can run together.
- Foundational schemas, models, audit, policy, IaC modules can all run in parallel after T009.
- Once Phase 2 is done, US1 + US2 + US3 can be staffed in parallel.
- Within each user story, all `[P]`-marked tasks can run in parallel.

---

## Parallel Example: User Story 1

```bash
# After Phase 2, these tasks for US1 can run in parallel:
Task T024 [P] [US1]  Contract test for /api/eval/runs (tests/contract/test_eval_api_runs.py)
Task T025 [P] [US1]  Integration test for run lifecycle (tests/integration/eval/test_run_lifecycle.py)
Task T026 [P] [US1]  Smoke fixture (packages/eval-dataset/cases/_smoke/)
Task T027 [P] [US1]  Pydantic run models (apps/api/app/models/eval/runs.py)
Task T030 [P] [US1]  rule_based evaluators (apps/eval-runner/.../evaluators/rule_based.py)
Task T031 [P] [US1]  primary_judge evaluator (apps/eval-runner/.../evaluators/primary_judge.py)
Task T032 [P] [US1]  secondary_judge evaluator (apps/eval-runner/.../evaluators/secondary_judge.py)
Task T033 [P] [US1]  disambiguator (apps/eval-runner/.../evaluators/disambiguator.py)
Task T037 [P] [US1]  web API client (apps/web/src/lib/api/eval.ts)
Task T038 [P] [US1]  /eval list page
Task T039 [P] [US1]  /eval/runs/[runId] page
```

Sequential within US1: T028 (orchestrator) needs T027; T029 (runner) needs T030–T033; T034 (scorecard service) needs T029; T035–T036 (endpoints) need T028 + T034; T040 (e2e) and T041 (validation) close the story.

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → Phase 2 Foundational.
2. Phase 3 US1.
3. **STOP and VALIDATE**: trigger a 2-model run on the 50-case smoke fixture; verify the scorecard (Acceptance Scenarios 1.1–1.3).
4. Demo to platform leadership.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 → MVP (multi-model comparison).
3. US2 → real 5,000-case dataset; re-run US1 against it.
4. US3 → ephemeral provisioning replaces stub; full SC-003/SC-008 demonstrated.
5. US4 → release gate is enforced on PRs and promotions.
6. US5 → audit/reproducibility evidence bundles available.
7. US6 → sanitised-real cases begin entering future dataset versions.
8. Polish.

### Parallel Team Strategy

After Phase 2:

- Track A (P1, MVP): US1.
- Track B (P1, content): US2.
- Track C (P1, infra): US3.
- After US1+US2 land: Track A pivots to US4; Track B starts US5; Track C starts US6.
- Polish (Phase 9) is folded in as user stories complete.

---

## Format Validation Checklist

All tasks above:

- ✅ Use `- [X]` checkbox + sequential `T###` IDs in execution order.
- ✅ Use `[P]` only when parallelizable.
- ✅ Use `[USx]` only inside Phases 3–8; omitted in Setup/Foundational/Polish.
- ✅ Include exact file paths or directory scopes.
- ✅ Are imperative, single-outcome, and verifiable.
- ✅ Annotated with required actor agents and tool kinds.

---

## Notes

- `Agents:` annotations are advisory — pick the closest match if a task spans multiple. Operational + sector agents (e.g., `incident-commander`, `nsw-rfs`, `bom-national`) are valuable for **rubric authoring** and **dataset realism**; technical agents drive code, infra, and review.
- `Tools:` annotations: `execute` = `powershell`/`pytest`/`az`/`bicep`; `read`/`edit`/`search` = file ops; `web` = `web_fetch`/`web_search`/Microsoft Docs MCP; `agent` = `task` tool with sub-agents (rubber-duck, explore, code-review); `todo` = SQL todos table for tracking batch progress.
- Tests fail first, then pass — verify the failure mode is the *expected* failure.
- Commit after each task or each `[P]` cluster.
- Stop at any **Checkpoint** to validate independently before proceeding.
- Avoid: vague tasks, same-file conflicts within a parallel cluster, cross-story coupling that breaks independent test criteria.
