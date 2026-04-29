# Phase 0 Research: LLM Evaluation Framework

**Feature**: 030-llm-eval-framework
**Date**: 2026-04-27
**Status**: Complete (all `NEEDS CLARIFICATION` resolved either via spec clarifications or via the decisions below)

## Inputs

The 10 spec-level clarifications (Session 2026-04-27) resolved scope (dataset size, judge strategy, compliance frameworks, model set, gate surfaces, runtime budgets, retention, language scope, concurrent-run policy, scorecard access). The decisions below resolve the remaining technical context from the user's plan brief: "Microsoft Azure cloud, Next.js dashboard + FastAPI API + Python autonomous agents".

---

## D1. Evaluation engine and judge orchestration

**Decision**: Use the `azure-ai-evaluation` Python SDK as the in-process evaluation engine, layered behind an internal `EvaluatorRegistry` so rule-based, primary-judge, and secondary-judge tiers (FR-003a, FR-003b) are first-class. Built-in evaluators (Groundedness, Relevance, Coherence, Fluency, Similarity, Content Safety, Indirect Attack/prompt-injection) cover the bulk of FR-001; we wrap them and add custom evaluators for refusal-correctness, tone-appropriateness, escalation-trigger detection, and a "did the model decline vs fail" disambiguator (FR-025).

**Rationale**:

- It is Microsoft's first-party framework referenced by the Azure Architecture Center "RAG/LLM evaluation phase" guidance the user cited; keeps us inside the Microsoft best-practice surface.
- Native Application Insights tracing per evaluator → cleanly satisfies FR-021 audit and SC-006 traceability.
- Pluggable custom evaluators give us the disaster-domain metrics (refusal correctness, tone) without forking the framework.
- Ships with Adversarial / Indirect-Attack simulators that are useful when authoring prompt-injection cases (Edge Cases).

**Alternatives considered**:

- **PromptFlow batch flows** — heavier orchestration surface, weaker fit for ephemeral container-job runners; we still re-use its evaluator definitions transitively via `azure-ai-evaluation`.
- **Build our own scoring loop** — rejected; loses Microsoft-aligned built-in evaluators and re-implements groundedness, fluency, similarity from scratch with no compliance benefit.
- **OpenAI Evals / Ragas** — rejected as primary; not aligned to Foundry, weaker AU compliance story.

---

## D2. Foundry model invocation surface

**Decision**: Address all Models Under Test (MUT) and judges through the **Foundry / Azure AI Projects SDK** (`azure-ai-projects`) using deployed Foundry model deployments addressed by deployment name + API version. The runner authenticates with **Managed Identity** (System-assigned on the Container App Job) using `DefaultAzureCredential`.

**Rationale**:

- A single client surface for both Frontier OpenAI, mid-tier OpenAI, and Phi family models (FR-013) — Foundry catalog presents them uniformly.
- Managed identity satisfies the constitution's "no static secrets" implication and aligns with the security baseline already used elsewhere in the AMA repo.
- Model deployments are addressable by stable deployment name → straightforward to record `(model_id, version, region, sku, params)` per FR-014.

**Alternatives considered**:

- **Direct Azure OpenAI SDK per model family** — rejected; bifurcates code paths and loses the Foundry catalog metadata that we need to make FR-013's "add a model without code changes" trivially true.
- **REST calls only** — rejected; no value vs SDK and worse error handling.

---

## D3. Ephemeral provisioning approach

**Decision**: Treat each evaluation run as an **Azure Container Apps Job** invocation that:

1. Validates the run against `ProvisioningPolicy` (cost cap, region whitelist, SKU whitelist, concurrency cap, max-duration).
2. **Conditionally provisions** any missing Foundry model deployments via a deterministic Bicep module (`infra/bicep/modules/eval/foundry-deployments.bicep`) using a **What-If** gate — if a deployment already exists for the run's pinned `(model, version, region, sku)`, it is **leased** for the run's duration rather than re-created.
3. Runs the evaluation.
4. **Always deprovisions** anything it provisioned via a `finally`-style teardown, plus a separate **reconciliation cron** (daily Container Apps Job) that lists `eval-run-*` resource groups older than the policy's max-duration window and force-deletes them (FR-019).

Each run gets its own short-lived **resource group** (`rg-eval-{runId}`) when the run provisions infra; pre-existing leased deployments are tagged with the run id but live in their long-lived resource group (so leasing doesn't mutate their lifecycle).

**Rationale**:

- Container Apps Jobs are AU-region-eligible, scale to zero, and integrate cleanly with managed identity and Application Insights.
- Per-run resource group makes teardown trivially correct (FR-017): delete the RG = nothing leaks.
- Leasing avoids the worst-case where a frontier model takes >1 h to deploy, blowing the 8 h SC-002 budget on cold-start alone.
- Bicep What-If at policy time fits the AMA infra-as-code conventions and the constitution's "Bicep preferred" clause.

**Alternatives considered**:

- **AKS jobs** — rejected; orchestration overhead is wrong shape for a workload that's idle 90 % of the time.
- **Azure Batch** — rejected; richer than needed, weaker first-class identity story.
- **Always-on shared deployments** — rejected; fights FR-017/FR-018 and the cost-cap success criterion (SC-008).

---

## D4. Storage layout

**Decision**:

- **Cosmos DB (Australia East)** — already provisioned in the AMA platform; add new containers:
  - `eval_datasets` (partition key `/datasetId`) — dataset version metadata + content hashes.
  - `eval_runs` (partition key `/runId`) — run metadata, scorecards, infra-lifecycle records.
  - `eval_metric_definitions` (partition key `/metricId`) — versioned metric specs.
  - `eval_audit` (partition key `/runId`) — append-only audit events; analytical store on, TTL = **never** (retention enforced at the data-platform retention policy = 7 y per FR-021).
- **Azure Blob Storage** with **immutability policy** (legal-hold-eligible; time-based retention = 7 y) — actual large artifacts:
  - `datasets/{datasetId}/{version}/cases.jsonl` (immutable on publish; FR-009).
  - `runs/{runId}/raw-outputs.jsonl`, `scores.jsonl`, `traces/`, `report.html`, `report.json`.
- **Azure Key Vault** — Foundry endpoint URLs and provisioning secrets (managed-identity-protected; no static creds in code).
- **Application Insights / Log Analytics workspace** (AU East) — evaluator traces and run telemetry, 7 y retention table.

**Rationale**:

- Re-uses existing AMA Cosmos + Storage posture (memory: AMA repository pattern auto-wires Cosmos clients via `COSMOS_ENDPOINT`).
- Blob immutability policy satisfies FR-009 (immutably versioned dataset) at the storage layer rather than relying on application logic.
- 7-year retention (FR-021) is satisfied by storage policy + Log Analytics retention, not by ad-hoc lifecycle rules.

**Alternatives considered**:

- **Single Cosmos container with discriminator** — rejected; mixing 5,000-case dataset bodies into Cosmos burns RUs unnecessarily and works against the "blob-as-immutable-artifact" model.
- **Azure Data Lake Gen2 hierarchical namespace** — viable, but Blob with immutability gives us the exact FR-009 guarantee with less moving parts.

---

## D5. Two-tier scorecard access (Q10 / FR-022)

**Decision**: Enforce the two tiers **in the API**, not only in the UI.

- Two FastAPI routers: `/api/eval/scorecards/...` (summary) and `/api/eval/scorecards/{runId}/traces/...` (detail).
- Both require auth (Entra ID); the trace router additionally requires one of `eval-author`, `safety-reviewer`, `governance-reviewer` app roles.
- Every detail-tier read writes an `eval_audit` event (`scorecard.trace.read`, run id, sample id, principal id, timestamp).
- The Next.js dashboard mirrors the split: "Scorecard" page is universal; "Sample traces" tab gated client-side and re-checked server-side.

**Rationale**: Server-side enforcement is required for FR-022 to be defensible against a malicious client; client-side gating alone would not satisfy auditability (FR-021).

---

## D6. Release-gate integration with feature 029

**Decision**: One scorecard, two consumers (FR-024, FR-027):

1. **GitHub Actions PR check** (`.github/workflows/eval-gate.yml`): triggers when `paths` include `apps/api/app/prompts/**`, `apps/api/app/services/rag/**`, `infra/bicep/modules/ai/**`, `packages/eval/**`. Calls the FastAPI runner in **fast-subset** mode (≤30 min, FR-018). Posts the scorecard as a PR check + comment.
2. **Progressive-delivery promotion gate** (feature 029): the promotion workflow calls the same runner in **full-suite** mode (≤8 h, FR-018) when promoting from `staging` → production canary, then attaches the scorecard to the existing 029 evidence pack.

The scorecard is identified by `(changeId, runId)` and stored once; both surfaces fetch by id, so there is one source of truth.

**Rationale**: Matches Q5 ("sharing one scorecard"), avoids a second evidence pipeline, and lets feature 029's evidence-pack signing already in place (per its plan.md) cover the full-run scorecard for free.

**Alternatives considered**:

- **Two independent scorecards** — rejected; violates FR-024's single-scorecard requirement and creates evidence drift.
- **Run the eval inside the GH Actions runner directly** — rejected; runners cannot reach AU-internal Foundry endpoints with managed identity, and would re-implement provisioning policy enforcement.

---

## D7. Dataset authoring workflow

**Decision**: Author cases as JSONL committed to a controlled repo path (`packages/eval-dataset/cases/{hazard}/{caseId}.json`), with a CI workflow that:

1. Validates each case against a JSON Schema (FR-008 fields, BCP-47 language, sensitivity labels, hazard tags).
2. Runs a PII-detection step (Microsoft Presidio) on any case whose provenance is `sanitised-real`, blocking publication if PII candidates remain (FR-023).
3. Requires a `safety-reviewer` GitHub team CODEOWNERS approval (FR-011).
4. On merge to `main`, builds an **immutable** dataset version artefact (content-hashed JSONL + manifest) and publishes it to the immutable Blob container.

**Rationale**: Keeps authoring transparent, version-controlled, reviewable in PR, and lets us bootstrap to ~5,000 cases (FR-007) via batch generation scripts whose outputs go through the same review gate. Presidio is the Microsoft-recommended de-identifier and is APP 11-aligned.

**Alternatives considered**:

- **Database-only authoring UI** — rejected for v1; PR workflow gives reviewers diff-level scrutiny which is exactly what FR-011/FR-023 demand.
- **No automated PII step** — rejected; manual review at 5,000 cases is unreliable.

---

## D8. Synthetic dataset bootstrap (~5,000 cases)

**Decision**: Generate the seed corpus via a **synthetic generation harness** under `packages/eval-dataset/generation/` that:

- Uses a frontier Foundry model with a controlled prompt (committed in repo) per hazard category and per behaviour archetype (answer-with-care, refuse-and-refer, escalate, request-clarification, redirect-to-authority).
- Emits draft JSONL with `provenance: "synthetic"`, `approval_state: "draft"`.
- Each draft is then fed through the same authoring CI workflow (D7) for safety-reviewer approval before it becomes part of a published version.

Distribution target across hazard categories (FR-006, SC-005): structure fire 12 %, bushfire 12 %, flood 10 %, severe storm 8 %, building collapse 6 %, hazmat 6 %, mass-casualty 8 %, missing persons 8 %, fatality reporting 8 %, human-remains recovery 6 %, evacuation orders/refusals 8 %, public-info requests 4 %, crisis-distress 4 %. Exact percentages tuned in Phase 2.

**Rationale**: Bootstraps to the FR-007 / SC-005 numbers without waiting for sanitised real cases (User Story 6, P3). Synthetic-then-reviewed is faster and safer than asking SMEs to author 5,000 cases from scratch.

---

## D9. Frontend approach

**Decision**: Next.js 16 (App Router) under `apps/web/src/app/eval/`:

- `/eval` — runs list (status, model set, dataset version, verdict).
- `/eval/runs/[runId]` — scorecard summary view (universal access).
- `/eval/runs/[runId]/traces` — sample-level traces (gated, server-side re-checked).
- `/eval/datasets` — dataset versions browser (read-only at v1).

API client lives at `apps/web/src/lib/api/eval.ts` matching the existing API-client convention (memory: typed clients in `apps/web/src/lib/api/*.ts`, native fetch with `cache: "no-store"`).

**Rationale**: Re-uses the AMA frontend patterns; no new framework introduced.

---

## D10. Compliance evidence packaging

**Decision**: Each completed run emits an **evidence bundle** (zip) keyed to `runId` containing:

- Scorecard JSON.
- Dataset manifest (id, version, content hash, case count, hazard distribution).
- Model manifest (each model id, version, region, sku, deployment params, judge ids/versions).
- Metric-definition manifest (versions in force, scoring tier per metric).
- Infrastructure-lifecycle record (resources created/destroyed, reconciliation events).
- Audit-event projection for the run.
- Signed digest (cosign or Azure Trusted Signing) — re-uses feature 029's signing key where available.

A separate **compliance-mapping document** (`docs/compliance/eval-mapping.md`, generated from `eval_metric_definitions` and policy data) maps evidence-bundle artefacts to ISO/IEC 42001 controls and NIST AI RMF functions (Govern/Map/Measure/Manage), satisfying FR-021.

**Rationale**: ISO 42001 audits ask for "show me the evidence for this control"; the bundle gives a one-shot answer without manual reconstruction (SC-012).

---

## Resolved Technical Context

All `NEEDS CLARIFICATION` placeholders are now resolved. Final values feed `plan.md` Technical Context.

| Slot | Value |
|---|---|
| Language/Version | Python 3.13 (api+agents+packages); TypeScript 5.x / Next.js 16 (web) |
| Primary Dependencies | FastAPI, Pydantic v2, `azure-ai-evaluation`, `azure-ai-projects`, `azure-identity`, `azure-cosmos`, `azure-storage-blob`, `azure-monitor-opentelemetry`, Microsoft Presidio; React 19, Next.js 16; Bicep |
| Storage | Cosmos DB (eval_*), Azure Blob Storage (immutable), Azure Key Vault, Log Analytics |
| Testing | pytest (unit, integration, contract); Playwright (web e2e); `eval-gate` workflow as live-fire CI test |
| Target Platform | Azure (Australia East / Australia Southeast for data; Foundry model-hosting endpoints per constitution carve-out) |
| Project Type | Web app (Next.js + FastAPI) + Python worker (Container Apps Job) + IaC (Bicep) |
| Performance Goals | Full multi-model run ≤ 8 h; PR-gate fast subset ≤ 30 min; per-sample p95 latency ≤ 30 s incl. judge call |
| Constraints | AU data residency (constitution NN-2 + carve-out for model endpoints only); 7-y retention; per-run cost cap enforced before provision |
| Scale/Scope | v1 dataset ≈ 5,000 cases (growth path to 10k+); 3 MUTs at v1; 1 primary + 1 secondary judge; 6 user stories; 29 FRs |
