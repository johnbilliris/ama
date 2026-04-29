# Implementation Plan: LLM Evaluation Framework for Disaster Response

**Branch**: `030-llm-eval-framework` | **Date**: 2026-04-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/030-llm-eval-framework/spec.md`

## Summary

Stand up a Microsoft-best-practice LLM evaluation framework dedicated to the AMA Disaster Response Coordination Hub. The framework delivers (i) a versioned, immutable disaster-domain dataset of ~5,000 approved cases at v1, (ii) a multi-metric scoring pipeline implementing the Microsoft Research metric families (quality, factuality, groundedness, retrieval, safety, refusal correctness, tone, prompt-injection resistance, latency, cost) using a hybrid rule-based + primary-judge + sampled-secondary-judge strategy, (iii) policy-bounded ephemeral provisioning of Foundry model deployments per run with deterministic teardown plus a reconciler, (iv) a single per-change scorecard consumed by both a path-scoped GitHub Actions PR check (≤ 30 min fast subset) and the AMA progressive-delivery promotion gate (≤ 8 h full suite), and (v) two-tier scorecard access enforced server-side. The technical approach is three Azure runtimes — Next.js dashboard, FastAPI orchestration API, and a Python evaluation worker as an Azure Container Apps Job — backed by Cosmos DB + immutable Blob Storage in Australia East with the constitution-permitted carve-out for Foundry model-hosting endpoints. All run artefacts are sealed into a 7-year-retained, ISO/IEC 42001 + NIST AI RMF + APP-aligned evidence bundle.

## Technical Context

**Language/Version**: Python 3.13 (FastAPI api, evaluation worker, dataset packages); TypeScript 5.x on Next.js 16 (web)
**Primary Dependencies**: `azure-ai-evaluation`, `azure-ai-projects`, `azure-identity`, `azure-cosmos`, `azure-storage-blob`, `azure-monitor-opentelemetry`, `presidio-analyzer`, `presidio-anonymizer`, FastAPI, Pydantic v2, Pydantic Settings; React 19, Next.js 16, native fetch (no SWR/React Query, per existing AMA convention); Bicep modules + Bicep AVM where available
**Storage**: Cosmos DB (Australia East) — new containers `eval_datasets`, `eval_runs`, `eval_metric_definitions`, `eval_audit`; Azure Blob Storage with time-based 7-year immutability policy for dataset versions, run artefacts, and audit archive; Azure Key Vault for Foundry endpoint URIs; Log Analytics workspace (existing AMA workspace) for telemetry
**Testing**: pytest (unit, integration, contract — including `tests/contract/test_eval_api.py` to emit OpenAPI and `tests/contract/test_eval_dataset_cases.py` for dataset schema/Presidio invariants); Playwright for `apps/web` e2e (`/eval` routes); a live-fire CI workflow (`eval-gate.yml`) used as the integration test for the release gate
**Target Platform**: Azure (Australia East primary, Australia Southeast for paired services); Foundry model-hosting endpoints in non-AU regions only when listed on the constitution-mandated carve-out (NN-2)
**Project Type**: Web app (apps/web) + service API (apps/api) + worker job (apps/eval-runner) + IaC (infra/bicep/modules/eval) + dataset package (packages/eval-dataset) + shared eval lib (packages/eval-core)
**Performance Goals**: full multi-model run (3 MUTs × 5,000 cases × metric suite incl. secondary-judge sampling) ≤ 8 h end-to-end (FR-018, SC-002); PR-gate fast subset ≤ 30 min; per-sample p95 wall-clock ≤ 30 s including judge call; reconciler detects and removes orphans within ≤ 60 min of `maxRunDurationMinutes` (FR-019)
**Constraints**: AU data residency for all data services (constitution NN-2); Foundry model endpoints permitted on carve-out list only, with platform-side data-minimisation at the model gateway; no static credentials (managed identity end-to-end); 7-year retention via storage policy not application logic; per-run cost cap enforced **before** provisioning; published dataset versions are immutable at the storage layer
**Scale/Scope**: v1 dataset ~5,000 approved cases across 13 hazard categories (FR-006, SC-005), schema-ready to grow to 10k+ and to additional BCP-47 languages; v1 model set = frontier OpenAI + mid-tier OpenAI + Phi-family small model on Foundry (FR-013); 6 user stories; 29 functional requirements (incl. FR-003a/FR-003b); 12 success criteria

## Constitution Check

Gate evaluation against `Autonomous Disaster Response Agent Coordination Hub Constitution v1.2.0`:

| Constitution clause | This feature | Status |
|---|---|---|
| I. Primacy of Life | Evaluation explicitly scores life-safety behaviours (refusal correctness, escalation triggers, tone, AWS-aligned warnings); a regression on a safety metric blocks release (FR-024, SC-007) | **Pass** |
| II. AEMA principles / II-A. AIIMS | Hazard categories (FR-006) and warning-form rubrics derive from AIIMS public-information function; recovery cases supported as a hazard tag | **Pass** |
| III. Multi-hazard / multi-agency | 13 hazard categories spanning natural and human-caused; jurisdiction tagging at the case level | **Pass** |
| IV. Transparency and Auditability | Every action audited (FR-021); evidence bundle per run; reproducibility (FR-026, SC-004, SC-012) | **Pass** |
| V. Warnings (AWS, ten principles, total system) | Tone-appropriateness and AWS-form rubric encoded as metric definitions; refusal-correctness disambiguates safety filter from failure (FR-025) | **Pass** |
| VI. Evacuation framework | `evacuation-order` is a first-class hazard tag with five-stage rubric variants | **Pass** |
| VII. Recovery support | `remains-recovery`, `crisis-distress` tags exercise four recovery environments | **Pass** |
| VIII. Cloud Platform | Azure, Bicep IaC, GH Actions CI/CD, Azure-native services (Container Apps, Cosmos DB, Foundry, App Insights, Key Vault) | **Pass** |
| NN-1 Human-in-the-loop | Gate overrides require approver identity + justification, logged immutably (FR-024) | **Pass** |
| NN-2 Data sovereignty (incl. Foundry carve-out) | All data services in AU; Foundry endpoints permitted only via the carve-out list; data-minimisation at the model gateway is part of the runner contract; regulated platform data never persisted outside AU | **Pass** (carve-out applies) |
| NN-3 Privacy by design | Presidio PII screen on all `sanitised-real` cases (FR-023); APP-aligned access logging; two-tier scorecard access | **Pass** |
| NN-3 (dev exception, FR-022a) | Dev environment may serve `/api/eval/*` anonymously to streamline operator validation against the synthetic dataset; staging/production retain full Tier-1/Tier-2 role enforcement; the API refuses to enable anonymous mode unless `ENVIRONMENT == "dev"` | **Pass (scoped)** |
| NN-4 Interoperability | OpenAPI exposed at `/api/eval/*`; CAP/EDXL/GeoJSON not directly relevant to eval surface | **Pass (n/a some sub-formats)** |
| NN-5 Graceful degradation | Run reconciler tears down orphans on orchestrator crash; partial-result preservation (FR-029) | **Pass** |
| Quality Gates | PR check + What-If + safety-reviewer human approval on dataset versions | **Pass** |

**Gate verdict**: PASS — no constitutional violations identified. The Foundry carve-out (NN-2) is the only non-default; it is invoked exactly as written, and the Complexity Tracking table below is not required.

Re-evaluated post-Phase-1 (after data-model.md, contracts/, quickstart.md): no design choice forces a violation; carve-out is the only conditional dependency and is correctly bounded.

## Project Structure

### Documentation (this feature)

```text
specs/030-llm-eval-framework/
├── plan.md              # this file
├── research.md          # Phase 0 (10 decisions D1..D10)
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── api.md           # Phase 1 — REST contract of record
├── checklists/
│   └── requirements.md  # spec quality checklist
├── spec.md              # feature specification
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

The feature spans three runtimes plus IaC plus shared packages plus dataset content. New paths only — existing files are extended, not restructured.

```text
apps/
├── web/                                    # existing Next.js 16 app
│   └── src/
│       ├── app/eval/                       # NEW
│       │   ├── page.tsx                    # runs list (Tier-1)
│       │   ├── runs/[runId]/page.tsx       # scorecard summary (Tier-1)
│       │   ├── runs/[runId]/traces/page.tsx# sample traces (Tier-2; server re-checks role)
│       │   ├── datasets/page.tsx           # dataset versions browser
│       │   └── gate/[changeRef]/page.tsx   # change-scoped scorecard
│       ├── components/eval/                # NEW (run-status, scorecard-table, regression-badge, ...)
│       └── lib/api/eval.ts                 # NEW (typed client, native fetch, cache: "no-store")
│
├── api/                                    # existing FastAPI app
│   └── app/
│       ├── api/routes/eval/                # NEW (datasets.py, runs.py, scorecards.py, gate.py, metrics.py)
│       ├── api/router.py                   # extended: include_router(eval_router)
│       ├── models/eval/                    # NEW (Pydantic v2 models matching data-model.md)
│       ├── services/eval/                  # NEW (RunOrchestrator, ProvisioningPolicyEvaluator, ScorecardService, GateService, EvidenceBundleBuilder)
│       ├── repositories/eval/              # NEW (DatasetRepo, MetricRepo, RunRepo, AuditRepo) — same auto-Cosmos pattern
│       ├── middleware/eval_role_guard.py   # NEW (server-side Tier-2 enforcement, audit event emission)
│       └── workers/eval_worker_invoker.py  # NEW (kicks off Container Apps Job, polls status)
│
└── eval-runner/                            # NEW Python worker
    ├── pyproject.toml
    ├── src/ama_eval/
    │   ├── __main__.py                     # `python -m ama_eval.runner --run-id ...`
    │   ├── runner.py                       # main loop: load → provision → evaluate → score → emit → teardown
    │   ├── provisioner.py                  # Bicep deploy/teardown via az.identity + ARM SDK; What-If gate
    │   ├── reconciler.py                   # cron entrypoint for caj-eval-reconciler
    │   ├── evaluators/                     # adapters wrapping azure-ai-evaluation built-ins + custom
    │   │   ├── rule_based.py               # refusal-keywords, escalation-trigger detection, structured-output shape
    │   │   ├── primary_judge.py            # primary Foundry judge, per metric
    │   │   ├── secondary_judge.py          # sampled secondary judge + disagreement surface
    │   │   └── disambiguator.py            # FR-025: refused vs failed-to-answer
    │   ├── foundry_client.py               # azure-ai-projects wrapper for MUT + judge calls
    │   └── evidence.py                     # bundle assembly + signing

packages/
├── eval-core/                              # NEW shared between api + worker (Pydantic models, JSON Schemas, audit-event vocab)
│   └── src/ama_eval_core/
│       ├── schemas/                        # JSON Schemas for cases, manifests, scorecards, audit events
│       ├── models.py                       # Pydantic models (single source for api + worker)
│       └── policy.py                       # ProvisioningPolicy evaluator (pure)
│
└── eval-dataset/                           # NEW dataset content + tooling
    ├── cases/                              # JSON files per case, organised by hazard
    ├── generation/
    │   ├── generate.py                     # synthetic-case generator (research D8)
    │   └── distribution-v1.json            # hazard distribution targets
    └── manifests/                          # generated manifests per published version

infra/
├── bicep/modules/eval/                     # NEW
│   ├── eval-platform.bicep                 # Cosmos containers, Storage (immutable), Key Vault, Container Apps env, jobs, App Insights
│   ├── foundry-deployments.bicep           # parametrised Foundry MUT deployment (used by ephemeral provisioner)
│   └── eval-rbac.bicep                     # role assignments for managed identity + Entra ID app roles
├── bicep/parameters/
│   ├── eval-platform.dev.json
│   ├── eval-platform.staging.json
│   └── eval-platform.production.json
└── policy/eval/
    ├── provisioning-policy.dev.yaml
    └── promotion-gates/eval-gate.yaml      # consumed by feature-029 promotion pipeline

.github/
└── workflows/
    ├── eval-gate.yml                       # NEW — path-scoped PR check
    └── eval-dataset-publish.yml            # NEW — runs on merges that change packages/eval-dataset/cases/**

tests/
├── unit/eval/                              # NEW (per-evaluator, per-policy, per-state-transition unit tests)
├── integration/eval/                       # NEW (api + cosmos + blob in-memory or testcontainers)
├── contract/
│   ├── test_eval_api.py                    # NEW — emits openapi.json into specs/030-llm-eval-framework/contracts/
│   ├── test_eval_dataset_cases.py          # NEW — JSON schema, Presidio, label invariants
│   └── test_eval_evidence_bundle.py        # NEW — bundle shape + signature verification
└── e2e/eval/                               # NEW Playwright (apps/web/e2e/eval/*.spec.ts)
```

**Structure Decision**: Web app + API + dedicated Python worker + IaC + shared package, mirroring the AMA monorepo conventions (memory: `apps/web` Next.js 16, `apps/api` FastAPI, `packages/domain` for shared Pydantic models). The new `apps/eval-runner` is its own deployable Container Apps Job because (a) it has a fundamentally different lifecycle from the always-on API (kicked, runs to completion, exits), (b) it needs different RBAC scopes (Foundry deploy + Bicep deploy) that should not bleed into the API's identity, and (c) it isolates failure: a runner crash never destabilises the API. The shared `packages/eval-core` keeps Pydantic models, JSON schemas, and the policy evaluator as the single source of truth across api + worker.

## Complexity Tracking

> Constitution Check passed without violations; this section is intentionally empty.
