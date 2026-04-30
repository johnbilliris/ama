# Feature Specification: AMA Rubric Improvements (75-item Excellence Uplift)

**Feature Branch**: `032-rubric-improvements`
**Created**: 2026-04-30
**Status**: Draft
**Input**: User description: "Incorporate all 75 improvement items from the AMA Rubric Evaluation across 16 areas (Architecture, Patterns, Code Quality, Implementation Completeness, Testing, Logging, Observability, AI Integration, Models, Autonomy, Multi-Agent Coordination, Security, Performance, CI/CD, Day-2 Operations, Documentation) so that every rubric dimension scores Excellent (5)."

> **Persona consultation note** — Operational personas (Incident Commander, Operations, Planning, Logistics, PIO, Field Coordinator, Resilience Planner, Executive Leader, Observer-Auditor, Risk Manager) and sector personas (NSW/VIC/QLD/SA/WA/TAS/ACT/NT, Commonwealth, Cross-sector) were consulted in `.github/agents/operational/` and `.github/agents/sectors/` prior to drafting. Their cross-cutting requirements are reflected in the user stories and functional requirements below: life-safety primacy, AIIMS COP integrity, multi-language and CALD/ATSI accessibility, NERAG/ISO 31000 risk traceability, append-only auditability, degraded-connectivity tolerance, multi-jurisdiction reach, and NEMA/state coordination semantics.

## Clarifications

### Session 2026-04-30 (Pass 1)

- Q: How does the OIDC migration in FR-S02 reconcile with ADR-031 (`AZURE_CREDENTIALS` JSON as a time-bound MVP) and the requirement to land spec 031 (FR-C01) which depends on the JSON-secret model? → A: Two-stage migration. Stage 1: land spec 031 first with the simplified `AZURE_CREDENTIALS` flow exactly as ADR-031 documents; stabilise in production. Stage 2: a new ADR (ADR-032) supersedes ADR-031, re-introduces OIDC federated workload identity inside the simplified pipeline shape (no return to the spec-029 complexity), and migrates each environment in order `dev → staging → production`. FR-S02 is therefore decomposed into FR-S02a (ADR + plan) and FR-S02b (rollout). Constitution Principle IV (auditability) requires the supersession to be recorded with rationale and approver identities.
- Q: What is the committed v1 size for the LLM evaluation dataset under FR-I02? → A: 5,000 approved cases at v1 (matches spec 030's already-clarified target — "≈5,000 approved cases at v1, designed to grow to 10k+"). The earlier "v0 baseline ≥1,000" alternative is dropped to remove ambiguity; the v1 target is binding for this feature.
- Q: What are the published RPO/RTO targets for FR-D01 (DR/BCP runbook with Australia Southeast failover)? → A: RPO ≤ 15 minutes (data loss tolerance) and RTO ≤ 60 minutes (recovery time objective) for production response workloads. Cosmos DB continuous backup with point-in-time restore is the primary RPO mechanism; paired-region asynchronous replication satisfies RTO. These are the SLO targets the Executive Leader persona signs off against; the chaos exercise and quarterly DR drill (FR-D05, FR-R05) MUST verify them.
- Q: Does the Phi shadow path (FR-AI03) persist its side-by-side outputs and for how long? → A: Yes. Shadow outputs persist into the same evaluation/audit store as production recommendations with the same 7-year retention (aligning with spec 030's ISO/IEC 42001 + APP retention) and are tagged `shadow=true` so they do not surface in operator UI but are queryable for cost/quality regression analysis.
- Q: Are the coverage targets in FR-T01 the binding numbers, or placeholders? → A: Binding. The committed targets are 80% line coverage on `tests/unit/`, 60% line coverage on `tests/integration/`, and 50% line coverage on `tests/contract/`, measured by `pytest --cov` over `apps/` and `packages/`. CI fails any PR that drops coverage below these thresholds. A documented one-time `--coverage-bypass=incident-{id}` (Executive + Principal Engineer co-approval, audit-logged) is the only escape valve, mirroring the eval-bypass edge case.

### Session 2026-04-30 (Pass 2)

- Q: For the RAG index over `docs/aidr/` (FR-AI01), are the AIDR handbooks licensed for indexing in Azure AI Search and for retrieval-augmented prompting? → A: AIDR handbooks are published by the Australian Institute for Disaster Resilience under permissive terms for emergency-management practitioner use (and the constitution explicitly references them as the framework basis). Indexing for grounded prompting falls within practitioner use. Retrieved chunks MUST cite the handbook + page reference in the recommendation card and the index MUST stay inside the Australia East tenant (no cross-region replication, no public exposure). A `docs/aidr/INDEXING-LICENCE-NOTE.md` MUST capture this position.
- Q: Which prompt-signing toolchain satisfies FR-AI09 (sign + verify prompt-template artifacts before deploy)? → A: Sigstore `cosign` keyless signing using GitHub OIDC identity tokens, verified by the deploy step against an in-repo `cosign.pub` (or keyless verification via Fulcio identity). This is consistent with FR-S02b's OIDC direction and avoids long-lived signing keys.
- Q: Which Azure AI Search SKU and capacity is appropriate for the AIDR RAG index in production? → A: `Standard S1` in Australia East with 1 replica + 1 partition for prod (≤ 25 GB index), and `Basic` in dev/staging. Vector dimensions 1536 (text-embedding-3-large/-small to be selected by the AI/ML Engineer persona during planning). Index size will be re-evaluated after first ingest; an autoscale alert at 70% capacity is required.
- Q: What are the default autonomy-dial values per environment for FR-AG02 (`low|standard|high`)? → A: `dev = high`, `staging = standard`, `production = standard`, `rehearsal = high` (per Resilience Planner persona). Jurisdiction policy MAY override per jurisdiction; `low` is reserved for life-safety actions during heightened-risk windows declared by the Incident Commander or Executive Leader.
- Q: How quickly must a kill-switch toggle (FR-AG05) propagate to all running agent processes? → A: ≤ 30 seconds end-to-end (Cosmos config change → Container Apps watcher reload → in-flight handoff drain). A heartbeat metric `agent.killswitch.lag_seconds` MUST be emitted; SLO target P99 ≤ 30 s.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Auditable, Tamper-Evident Operational Trust (Priority: P1)

An Observer-Auditor or Compliance Auditor reviewing a major incident must be able to reconstruct **why** every agent recommendation fired, **which** model and prompt version produced it, **what** signals supported it, and **who** approved it — within minutes — and prove the audit chain has not been altered.

**Why this priority**: Constitutional Principle IV (Transparency & Auditability) is a NON-NEGOTIABLE; without complete provenance the platform cannot be trusted by any Australian jurisdiction. Closes Rubric items 1.4, 8.3, 9.2, 10.3, 11.4, 14.4.

**Independent Test**: Replay a stored ScenarioRun and verify each recommendation in the timeline carries (a) input signal IDs and trust-tier hashes, (b) prompt-template SHA + model version + deployment alias, (c) confidence and threshold passed, (d) approval state-machine transitions with operator IDs, (e) cryptographic continuity of the append-only ledger.

**Acceptance Scenarios**:

1. **Given** a completed scenario with at least 50 timeline events, **When** an auditor opens the ScenarioRun "why fired" panel for any recommendation, **Then** the panel displays input signals, trust tier, prompt SHA, model+version, confidence, threshold, approval chain, and a verifiable hash of the audit segment.
2. **Given** a tampered audit entry, **When** the integrity check runs, **Then** the system flags the break, refuses to publish recommendations from the affected window, and pages the Observer-Auditor.
3. **Given** PII fields in a structured log, **When** the log is emitted, **Then** the field is hash-redacted and the original value is never persisted in plain text.

---

### User Story 2 — Hardened, Region-Sovereign, Private Production Posture (Priority: P1)

A Security Engineer or Executive Leader needs assurance that all production data planes (Cosmos DB, Azure OpenAI, Storage, Container Apps egress) are reachable **only** through Private Endpoints inside Australia East/Southeast, with customer-managed keys, OIDC federated workload identity (no long-lived secrets), CodeQL/Defender/Sentinel coverage, and SHA-pinned third-party actions.

**Why this priority**: Constitutional NON-NEGOTIABLE #2 (Data sovereignty) and Principle IV; closes Rubric items 12.1, 12.2, 12.3, 12.4, 12.5, 16.3, 16.5. Also unblocks Commonwealth (NEMA, ABF, ADF) and state-government tenants who require Essential Eight Maturity Level 2.

**Independent Test**: From a public network, prove every production data plane refuses connections; from inside the VNet, prove operator workflows succeed. Verify GitHub Actions workflows authenticate via OIDC (no `clientSecret` in logs/secrets) and every third-party action reference is a 40-char SHA. Verify CMK is enforced on Cosmos and Storage.

**Acceptance Scenarios**:

1. **Given** the production environment, **When** a request originates from outside the VNet, **Then** Cosmos / Storage / Azure OpenAI / Content Safety reject the connection (403/network error) and the attempt is logged.
2. **Given** the CD pipeline, **When** a deploy runs, **Then** auth uses an OIDC federated identity, no `AZURE_CREDENTIALS` JSON secret is referenced, and the staged ADR documenting the change is linked from the run summary.
3. **Given** any workflow file, **When** scanned, **Then** zero `uses:` lines reference a tag — every action is pinned to a 40-character commit SHA.
4. **Given** a code push, **When** CI runs, **Then** CodeQL (Python + JavaScript + Bicep) executes and a SAST/secret-scan summary is attached to the PR.

---

### User Story 3 — Excellent Observability with SLOs and Distributed Tracing (Priority: P1)

An SRE or Operations Officer must be able to answer "is the platform healthy right now?" against published SLOs (signal-ingestion latency, agent-handoff success, alert-to-publish time, dead-letter depth, LLM cost per incident) using a single Workbook, with full OpenTelemetry traces from web request → API → agent runtime → Azure OpenAI, and continuous synthetic probes against `/api/health` and the dashboard URL.

**Why this priority**: AIIMS COP demands real-time situational awareness; the Field Coordinator persona requires degraded-mode visibility. Closes Rubric items 9.1–9.5, 10.1–10.5, 13.4. Without it the system cannot honour the public-information SLA implied by the Australian Warning System.

**Independent Test**: Trigger a synthetic incident and verify (a) the Workbook updates within one minute, (b) the trace tree shows every span end-to-end, (c) the SLO error budget metric is queryable, (d) breaching the latency SLI fires a P1/P2-tagged page through Action Group routing, (e) availability tests have at least 7 days of green history.

**Acceptance Scenarios**:

1. **Given** an in-flight signal, **When** an operator opens the trace, **Then** spans cover web → API → ingestion → monitoring agent → risk-assessment agent → communication agent → Azure OpenAI call, all correlated by a single traceId.
2. **Given** the published SLO catalogue, **When** any SLI burns 50% of its monthly budget, **Then** an alert opens an issue and notifies the action-group webhook.
3. **Given** the Azure portal, **When** an operator opens the Disaster Response Hub Workbook, **Then** they see live tiles for ingestion lag, handoff success rate, dead-letter depth, LLM cost burn-down, governance-health score, and active incidents.
4. **Given** a PII or token-cost field, **When** logged, **Then** PII is hash-redacted and cost metrics are emitted as App Insights customMetrics (not just logger.warning lines).

---

### User Story 4 — Production-Grade AI Quality with RAG, Eval Gates, Versioned Prompts, and Cost Control (Priority: P1)

An AI/ML Engineer and the LLM Evaluation framework (spec 030) need every recommendation to be grounded in the AIDR handbook corpus (RAG), validated against the v1 5,000-case eval dataset, produced by a versioned model+prompt pair recorded in the audit trail, with structured-output validation enforced everywhere, and cost-tracked via Application Insights customMetrics with budget circuit-breakers persisted across restarts.

**Why this priority**: Closes Rubric items 2.2, 2.3, 7.1, 7.2, 7.3, 7.4, 7.5, 8.1–8.4. The Public Information Officer cannot release multilingual alerts without grounded, eval-gated content; the Risk Manager cannot accept risk-informed recommendations without provenance.

**Independent Test**: Run the evaluation harness against `eval-dataset/v1` (≥5,000 cases) end-to-end; assert the published baseline thresholds (accuracy, hallucination, safety) hold. Verify every `_generate_with_fallback` call site passes a `response_model`, RAG context is attached when the prompt is grounded, and the recommendation record carries `prompt_sha`, `model_id`, `model_version`, `deployment_alias`. Restart the API and confirm the budget tracker resumes from persisted state.

**Acceptance Scenarios**:

1. **Given** a prompt requiring AIDR grounding, **When** the agent runs, **Then** the LLM call attaches retrieved chunks from `docs/aidr/` (Azure AI Search index), and the recommendation cites the source documents.
2. **Given** the v1 eval dataset, **When** the harness completes, **Then** scorecards exceed published baselines and a regression CI gate would have failed for any below-threshold metric.
3. **Given** the daily token budget, **When** consumption hits 80%, **Then** App Insights emits a `llm.budget.warning` customMetric, the budget tracker (now externalised to Cosmos/Redis) records the event, and a graceful degradation flag is set.
4. **Given** a Phi shadow path, **When** a recommendation is produced, **Then** the system also records the Phi suggestion side-by-side without affecting the user-facing output, and a comparison metric is logged.

---

### User Story 5 — Five Mature Multi-Agent Coordination Patterns Visible to Operators (Priority: P2)

An Incident Commander or Resilience Planner needs the multi-agent flow (signal → monitoring → risk-assessment → evacuation/resource-allocation/communication → approval → publish → recovery → lessons capture) to be **diagrammed, named, and operable** as a Saga / Process Manager, with named decision rights per agent, autonomy dials per jurisdiction, kill-switches, consensus capture, and recovery + dead-letter loops.

**Why this priority**: The Operations Officer persona requires AIIMS span-of-control; the Executive Leader requires jurisdiction-policy levers; the Resilience Planner requires AAR (after-action review) artifacts. Closes Rubric items 2.4, 10.1–10.5, 11.1–11.5.

**Independent Test**: Generate (or render at build time) a Mermaid `stateDiagram-v2` of the full multi-agent saga from a single source of truth and verify every state transition appears in the audit timeline of a representative ScenarioRun. Toggle the per-agent kill-switch via config and verify the system falls back to deterministic templates without dropping life-safety guarantees.

**Acceptance Scenarios**:

1. **Given** an active incident, **When** evacuation and resource-allocation agents independently flag the same corridor, **Then** the system records a `consensus_event` and surfaces it in the recommendation card.
2. **Given** a jurisdiction policy of `autonomy=low`, **When** any agent reaches a recommendation, **Then** all life-safety actions require explicit operator approval and the policy decision is included in the audit record.
3. **Given** an agent kill-switch is engaged, **When** a signal arrives, **Then** the agent operates in template-only mode, emits a degraded-mode header, and the operator sees the degraded badge.
4. **Given** a completed ScenarioRun, **When** the AAR report is generated, **Then** it includes a "coordination gap summary" listing handoff timeouts, dead-letter cycles, and consensus events.

---

### User Story 6 — Productionised CI/CD with Progressive Delivery, DR/BCP, and DORA Visibility (Priority: P2)

A Principal Engineer / Infrastructure-DevOps engineer must be able to deploy via a single, simplified pipeline (spec 031 landed) with progressive delivery gates (dev → staging → canary → prod), a documented model-rollback runbook, a DR/BCP runbook with RPO/RTO targets and Australia Southeast failover, Cosmos point-in-time restore, an exercise schedule (quarterly LLM rehearsals + biannual full-stack chaos), and DORA dashboards (deployment frequency, lead time, MTTR, change-failure rate).

**Why this priority**: Closes Rubric items 14.1–14.5, 15.1–15.5, 4.1–4.5 (Implementation Completeness gaps including spec 031 finalisation), 13.5. The Executive Leader requires ministerial-grade resilience evidence; the Field Coordinator requires guaranteed degraded-mode behaviour.

**Independent Test**: Force a regional failover drill in staging; verify Australia Southeast picks up traffic within RTO. Verify benchmarks gate the pipeline (no `continue-on-error: true`). Verify nightly load tests run on schedule and post results. Verify spec 031 is `Status: Approved` and the canary-stage workflow is removed exactly as ADR documents.

**Acceptance Scenarios**:

1. **Given** the simplified pipeline (spec 031), **When** a benchmark regresses beyond the defined threshold, **Then** the pipeline fails (no `continue-on-error: true` on the benchmark step).
2. **Given** the nightly schedule, **When** load tests run, **Then** results are posted to App Insights and a summary issue is opened on regression.
3. **Given** a DR drill, **When** the primary region is marked unhealthy, **Then** traffic shifts to Australia Southeast within the published RTO and the recovery is logged.
4. **Given** the operations dashboard, **When** an Executive Leader requests "this month's DORA stats", **Then** deployment frequency, lead time, MTTR, and change-failure rate are visible.

---

### User Story 7 — Engineering Excellence Hygiene (Strict Typing, Boundaries, Formatting, Pre-commit, Coverage) (Priority: P2)

A Principal Engineer and Software Developer need CI to enforce `mypy --strict`, import boundaries via `import-linter` (e.g. `apps/agents` MUST NOT import from `apps/api`), `ruff format` as a CI gate, a `pre-commit` config that mirrors CI gates locally, a published coverage target enforced by `pytest --cov`, and the resolution of placeholder Entra group IDs and the agent-common 18-file flatness.

**Why this priority**: Closes Rubric items 3.1–3.5, 5.1–5.2, 4.5. Improves contributor velocity; reduces the "fixed in CI" loop that the Software Developer persona flags.

**Independent Test**: Introduce a deliberate type error, an illegal cross-package import, an unformatted file, and a commit that bypasses pre-commit. CI must fail on each. Confirm `apps/agents/common/` is reorganised into `resilience/`, `safety/`, `lifecycle/` sub-packages with no broken imports. Confirm zero `00000000-…` placeholder UUIDs remain in `IDENTITY.md`.

**Acceptance Scenarios**:

1. **Given** an agent module that imports from `apps.api`, **When** CI runs `import-linter`, **Then** the build fails.
2. **Given** an unformatted Python file, **When** CI runs `ruff format --check`, **Then** the build fails.
3. **Given** the test suite, **When** `pytest --cov` runs, **Then** coverage ≥ published targets (default: 80% unit / 60% integration) or the build fails.
4. **Given** a fresh clone, **When** a developer runs `pre-commit install && pre-commit run --all-files`, **Then** the same set of checks as CI executes locally.

---

### User Story 8 — Documentation, Communication, and Reviewer Story (Priority: P3)

An evaluator/reviewer needs a 60-second walkthrough video, hosted Redoc/Swagger UI generated from `openapi.yaml`, a single consolidated governance/eval docs hub, `CONTRIBUTING.md`, `CHANGELOG.md` (or GitHub Releases), `tests/README.md`, a metrics catalogue, an SLO doc, a contract-test contributor guide, and a requirement→test traceability matrix per spec.

**Why this priority**: Closes Rubric items 6.1–6.5, 16.1–16.5, 8.5. Reviewer experience is the entry point; missing docs cap evaluator confidence regardless of code quality.

**Independent Test**: A first-time reviewer can land on the README, click through to (a) a Loom/video walkthrough, (b) hosted API docs, (c) SLO doc, (d) `CONTRIBUTING.md`, (e) `CHANGELOG.md`, and (f) `tests/README.md`, in under 60 seconds and with zero broken links.

**Acceptance Scenarios**:

1. **Given** the README, **When** a reviewer clicks "Watch the 60-second walkthrough", **Then** a video link opens.
2. **Given** the deployed web app, **When** a reviewer visits `/api/docs`, **Then** Redoc/Swagger UI renders the live `openapi.yaml`.
3. **Given** the docs tree, **When** a reviewer searches "governance", **Then** they land on a single consolidated nav, not three separate hubs.

---

### Edge Cases

- **Region failover during an active incident**: Failover must not break audit continuity; the Cosmos point-in-time restore + idempotent ingestion path must reconstruct state.
- **Azure OpenAI Private Endpoint outage**: Communication agent must auto-degrade to deterministic templates without losing AWS warning level fidelity.
- **Eval dataset regression that blocks deploy mid-incident**: The pipeline MUST permit a documented one-time `--eval-bypass=incident-{id}` with executive sign-off, recorded in the audit trail.
- **OIDC federated identity propagation lag**: New environments must surface a clear setup error and pre-flight check rather than silently using fallback secrets.
- **PII redaction false negatives**: A periodic redaction-validator job MUST scan logs for canary PII and alert on detection.
- **Kill-switch engaged for an agent during high-severity incident**: Operators must see explicit notice + degraded badge, with alternate workflow guidance.
- **CodeQL false positives on emergency hotfix**: A documented `security-bypass` label requires Principal Engineer + Security Engineer co-approval and is audit-logged.
- **Connectivity-degraded field**: Field Coordinator workflows must continue with cached COP and queue updates for replay (degraded-mode contract preserved).
- **Cross-jurisdiction language fallback**: If an Aboriginal & Torres Strait Islander language asset is unavailable, the system MUST publish in English plus the closest configured language and flag the gap to the PIO.

---

## Requirements *(mandatory)*

### Functional Requirements — Architecture (FR-A##)

- **FR-A01**: System MUST publish an explicit C4 model (System + Container + Component) under `docs/architecture/c4/` with diagrams generated from a single source of truth and linked from the README. *(Rubric 1.1)*
- **FR-A02**: System MUST publish a tenant-partitioning math document quantifying Cosmos DB RU/s budget per tenant, per jurisdiction, per workload, with worst-case projections and headroom margin. *(Rubric 1.2)*
- **FR-A03**: System MUST capture per-agent scale-out targets (HPA min/max, scaling rules, queue-depth triggers) inline in `infra/main.bicep` (or a sibling module imported by it). *(Rubric 1.3)*
- **FR-A04**: System MUST publish a formal sequence diagram covering Monitoring → Risk Assessment → Communication including retry, dead-letter, and recovery cycles. *(Rubric 1.4)*
- **FR-A05**: System MUST refactor `apps/agents/common/` into `resilience/`, `safety/`, `lifecycle/` (and any other natural seam) sub-packages with zero behaviour changes. *(Rubric 1.5 + 3.5)*

### Functional Requirements — Patterns (FR-P##)

- **FR-P01**: System MUST express the LLM fallback chain as a first-class Strategy (`LlmFallbackStrategy` interface + concrete strategies) replacing nested `if` blocks in `_generate_with_fallback`. *(Rubric 2.1)*
- **FR-P02**: System MUST externalise the LLM budget tracker to a durable store (Cosmos or Redis) with persistent counters that survive process restarts. *(Rubric 2.2)*
- **FR-P03**: System MUST replace the hand-rolled circuit breaker with a maintained library (e.g. `pybreaker`) and document the choice in an ADR. *(Rubric 2.3)*
- **FR-P04**: System MUST publish a Saga / Process Manager doc for the multi-agent approval workflow (`proposed → under_review → approved → executed`) explicitly naming the pattern. *(Rubric 2.4)*
- **FR-P05**: System MUST promote the AIIMS role-to-agent mapping to a typed registry replacing the `AIIMS_MAPPING` constants, supporting per-jurisdiction role overrides declaratively. *(Rubric 2.5)*

### Functional Requirements — Code Quality (FR-Q##)

- **FR-Q01**: CI MUST enforce `mypy --strict` over `apps/`, `packages/`, `tests/` and fail on any error. *(Rubric 3.1)*
- **FR-Q02**: CI MUST enforce import boundaries via `import-linter` with at minimum the rule `apps.agents` MUST NOT import from `apps.api`. *(Rubric 3.2)*
- **FR-Q03**: CI MUST enforce `ruff format --check` (or equivalent) as a blocking gate. *(Rubric 3.3)*
- **FR-Q04**: Repo MUST ship a `.pre-commit-config.yaml` mirroring CI gates (lint, format, secret-scan, mypy, import-linter). *(Rubric 3.4)*
- **FR-Q05**: System MUST reduce `apps/agents/common/` flatness as in FR-A05. *(Rubric 3.5)*

### Functional Requirements — Implementation Completeness (FR-I##)

- **FR-I01**: Specs 030 (LLM Eval) and 031 (Simplify CI/CD) MUST move from `Status: Draft` to `Status: Approved` (or be closed with a stated reason). *(Rubric 4.1)*
- **FR-I02**: System MUST publish the v1 eval dataset under `eval-dataset/` containing **5,000** approved cases (binding per spec 030's clarified target). *(Rubric 4.2)*
- **FR-I03**: System MUST land at least one Playwright spec under `apps/web/e2e/` covering a critical user journey. *(Rubric 4.3)*
- **FR-I04**: `docs/operator-runbooks.md` MUST cover `apps/ingestion/` operations (start/stop, observability, dead-letter recovery). *(Rubric 4.4)*
- **FR-I05**: All placeholder Entra group object IDs (`00000000-…`) in `IDENTITY.md` and downstream `setup-oidc-azure.yml` / `identity_consistency.rego` MUST be replaced with real IDs (or environment-resolved variables) before any production deploy. *(Rubric 4.5)*

### Functional Requirements — Testing (FR-T##)

- **FR-T01**: CI MUST enforce coverage targets via `pytest --cov` measured over `apps/` and `packages/`, using a **ratcheting strategy**:
  - **Phase A (immediate)**: CI fails on any coverage *regression* against the previous successful run on the same branch. Baseline (verified): unit ≈ 63%, integration ≈ 40%, contract ≈ 49%.
  - **Phase B (Stream 1 milestone)**: Floors set to baseline (63 / 40 / 49).
  - **Phase C (closing milestone)**: Floors raised to **80% / 60% / 50%** (the rubric target) once Stream 6 + Stream 7 land enough new unit tests to bridge the gap; the date for Phase C activation is recorded in the milestone tracker.
  CI uses the active phase's floors via `--cov-fail-under`. The only escape valve is a documented one-time `--coverage-bypass=incident-{id}` requiring Executive + Principal Engineer co-approval and audit logging. *(Rubric 5.1)*
- **FR-T02**: System MUST add a Web testing tier (Vitest) under `apps/web/__tests__/` and run it in CI. *(Rubric 5.2)*
- **FR-T03**: System MUST publish chaos / fault-injection tests for the resilience middleware (circuit-breaker, dead-letter) with a dedicated `tests/chaos/` tier. *(Rubric 5.3)*
- **FR-T04**: System MUST add a security test tier (SAST via CodeQL, IaC scan via Checkov/PSRule for Bicep, secret scan) gated in CI. *(Rubric 5.4)*
- **FR-T05**: System MUST run `tests/load/` on a nightly schedule against staging and post results to App Insights. *(Rubric 5.5)*
- **FR-T06**: System MUST publish a root `tests/README.md` describing each tier (purpose, run command, expected runtime). *(Rubric 6.1)*
- **FR-T07**: Each spec MUST include a requirement→test traceability matrix (FR-XXX → test file). *(Rubric 6.2)*
- **FR-T08**: System MUST publish a contract-test contributor guide. *(Rubric 6.3)*
- **FR-T09**: Spec 030 acceptance criteria MUST be encoded as concrete pytest IDs once the eval framework lands. *(Rubric 6.4)*
- **FR-T10**: Post-exercise survey outcomes MUST be cross-linked to specific test cases. *(Rubric 6.5)*

### Functional Requirements — Logging & Observability (FR-O##)

- **FR-O01**: System MUST define explicit retention policies per signal class (audit logs, operational logs, security logs) in `infra/modules/monitoring.bicep` with separate workspaces or table-level retention overrides. *(Rubric 7.1)*
- **FR-O02**: System MUST publish a `docs/observability/metrics-catalogue.md` listing every custom metric, dimension, source, and SLO usage. *(Rubric 7.2)*
- **FR-O03**: System MUST emit cost/budget metrics from `llm_mixin.py` to App Insights as customMetrics, not solely as logger warnings. *(Rubric 7.3)*
- **FR-O04**: System MUST commit Azure Monitor Workbook templates under `infra/modules/workbooks/` covering executive governance health, ingestion health, agent flow, and LLM cost. *(Rubric 7.4)*
- **FR-O05**: System MUST hash-redact PII fields in structured logs via a centralised validator (deny by default; allow-list of safe fields). *(Rubric 7.5)*
- **FR-O06**: System MUST publish an `slo.md` with explicit SLIs (signal-ingestion latency P95, agent handoff success rate, alert-to-publish time, dead-letter depth, LLM cost per incident) and error budgets. *(Rubric 8.1)*
- **FR-O07**: System MUST instrument OpenTelemetry traces from FastAPI → Container Apps → App Insights, exporting via OTLP, so the trace tree is queryable end-to-end (not just correlation IDs). *(Rubric 8.2)*
- **FR-O08**: System MUST commit Azure Monitor Workbook JSON for the operator runbooks (incident activation, recommendation→alert publication, degraded mode). *(Rubric 8.3)*
- **FR-O09**: System MUST define paging severity tiers (P1–P5) and route via Action Group rules. *(Rubric 8.4)*
- **FR-O10**: System MUST add Application Insights availability tests (synthetic monitoring) for `/api/health` and the dashboard URL with at least 5 geo-distributed locations within Australia/APAC. *(Rubric 8.5)*

### Functional Requirements — AI Integration (FR-AI##)

- **FR-AI01**: System MUST implement RAG over the `docs/aidr/` corpus using Azure AI Search (vector + hybrid index) in Australia East — `Standard S1` SKU, 1 replica + 1 partition, no cross-region replication, **Private Endpoint only with no public network access** — and inject retrieved chunks into agent prompts that ground recommendations. Retrieved chunks MUST cite handbook + page reference in the recommendation card. A `docs/aidr/INDEXING-LICENCE-NOTE.md` MUST capture the AIDR practitioner-use position **AND** an accompanying `docs/aidr/LICENCE-INVENTORY.md` MUST list each handbook with publisher, edition, citation URL, redistribution rights, and per-handbook indexing approval (signed off by Compliance Auditor + Solution Architect). Handbooks lacking explicit indexing rights MUST default to metadata-only / curated-excerpts mode (titles + chapter summaries) until per-handbook approval lands. Vector dimensions and embedding model selected during planning; index size auto-alerts at 70%. Dev/staging MAY use the `Basic` SKU. *(Rubric 9.1)*
- **FR-AI02**: System MUST capture and pin model + prompt versions per recommendation in the audit trail (`prompt_sha`, `prompt_version`, `model_id`, `model_version`, `deployment_alias`). *(Rubric 9.2)*
- **FR-AI03**: System MUST add a Phi shadow path for cost control alongside GPT-4o per spec 030 v1 model set. Shadow outputs MUST be persisted to the evaluation/audit store with `shadow=true` tag and 7-year retention (aligned with spec 030 ISO/IEC 42001 + APP), queryable for cost/quality regression analysis but NOT surfaced in operator-facing UI. **Shadow routing is deny-by-default**: every payload MUST pass a classification-aware policy (PII redaction + PSPF marking detection + sensitive-operational-content filter) at the model gateway; payloads that fail policy MUST be blocked from non-AU transit (no Phi call). This satisfies Constitution Non-Negotiable #2's requirement that personal information and PSPF-marked content are "removed, masked, or denied transit unless an explicit, auditable use-case approval exists". *(Rubric 9.3)*
- **FR-AI03a**: System MUST publish (and CI-enforce) a versioned Foundry **carve-out registry** at `infra/parameters/foundry-carveout.yaml` listing every permitted non-AU model deployment with `model_name`, `region`, `business_justification`, `approver_identities[]`, `review_date`. CD MUST refuse to deploy any non-AU model deployment not present in the registry; this restores the deploy-time enforcement that ADR-031 documented as lost. *(Rubric 9.3 + Constitution NN-2)*
- **FR-AI04**: System MUST enforce structured-output validation everywhere `_generate_with_fallback` is invoked (no `response_model=None` in production paths). *(Rubric 9.4)*
- **FR-AI05**: System MUST publish a prompt library (`packages/prompts/`) with review cadence, ownership, and change history. *(Rubric 9.5)*
- **FR-AI06**: System MUST move the Azure OpenAI deployment AND **Azure AI Content Safety AND Azure AI Search** to Private Endpoint + private DNS, disallowing public network access in production. Each MUST refuse public-network connections in 100% of probes (per US2 acceptance). *(Rubric 10.1)*
- **FR-AI07**: System MUST publish a model-rollback runbook (deployment alias flip + verification). *(Rubric 10.2)*
- **FR-AI08**: System MUST document the Azure OpenAI quota request path (capacity reservations) for production GA. *(Rubric 10.3)*
- **FR-AI09**: System MUST sign and verify prompt-template artifacts before deploy using **Sigstore `cosign` keyless signing with GitHub OIDC identity tokens**, verified by the deploy step (Fulcio identity verification, no long-lived signing keys). *(Rubric 10.4)*
- **FR-AI10**: System MUST add a canary deployment flow for new model versions before spec-031 deletes the existing canary-stage workflow (or migrate the equivalent gate into the simplified pipeline). *(Rubric 10.5)*

### Functional Requirements — Agentic Behaviour (FR-AG##)

- **FR-AG01**: System MUST publish a single decision-rights matrix per agent (decide vs escalate) under `docs/agents/decision-rights.md`. *(Rubric 11.1)*
- **FR-AG02**: System MUST add an autonomy-level dial per environment AND per jurisdiction policy (`low|standard|high`) consumed by all agents and logged into the audit trail. Defaults: `dev=high, staging=standard, production=standard, rehearsal=high`; jurisdiction policy MAY override; `low` is reserved for life-safety actions during heightened-risk windows declared by the Incident Commander or Executive Leader. *(Rubric 11.2)*
- **FR-AG03**: Every recommendation MUST carry a "why this agent fired" trace artifact (input signals + threshold passed + persona/jurisdiction context). *(Rubric 11.3)*
- **FR-AG04**: README MUST list the dependency-notifier as a first-class agent in the agent table. *(Rubric 11.4)*
- **FR-AG05**: System MUST add a kill-switch per agent (config flag, Cosmos-backed) wired into the degraded-mode evaluator so operators can drop an agent to template-only fallback. End-to-end propagation latency MUST be ≤ 30 seconds (Cosmos config change → **Cosmos change-feed push** → Service Bus topic → agent watcher → in-flight handoff drain — push-based, not polling), and a heartbeat metric `agent.killswitch.lag_seconds` MUST be emitted with SLO target P99 ≤ 30 s. A spike in Stream 0 MUST validate the propagation budget before downstream tasks commit to the SLO. *(Rubric 11.5)*

- **FR-AG05a**: The kill-switch and autonomy-dial control surfaces MUST require: (a) authenticated operator session via Entra ID, (b) `RoleAuthority` claim of `IncidentCommander` or `ExecutiveLeader`, (c) justification code drawn from a published taxonomy (`maintenance|drill|degraded_dependency|safety_incident|other`), (d) for `production` environment a **dual-approval** workflow (proposer + approver, distinct identities), (e) an audit-trail link recorded with the toggle. The OpenAPI delta in `contracts/openapi-delta.yaml` MUST be amended accordingly before implementation. *(Constitution NN-1 human-in-the-loop)*
- **FR-AG06**: System MUST render a state-graph visualisation (Mermaid `stateDiagram-v2`) of the full multi-agent flow including dead-letter and recovery loops, generated from configuration. *(Rubric 12.1)*
- **FR-AG07**: System MUST implement a reflection feedback loop ("did the recommendation actually help?") from approval outcome → agent training data store. *(Rubric 12.2)*
- **FR-AG08**: System MUST add explicit per-handoff timeouts (recovery vs lessons-capture configured separately). *(Rubric 12.3)*
- **FR-AG09**: System MUST record consensus events when multiple agents reach the same conclusion. *(Rubric 12.4)*
- **FR-AG10**: System MUST add a coordination "gap summary" output to every ScenarioRun to drive after-action review. *(Rubric 12.5)*

### Functional Requirements — Security (FR-S##)

- **FR-S01**: Production Cosmos DB MUST be Private Endpoint only (no `0.0.0.0` rule, no public network access). Dev/staging MAY differ but MUST be documented. *(Rubric 13.1, 14.5)*
- **FR-S02**: System MUST migrate to OIDC federated workload identity for GitHub Actions, removing long-lived `AZURE_CREDENTIALS` JSON secrets, in two stages aligned with ADR-031 supersession:
  - **FR-S02a**: A new ADR (ADR-032) MUST be authored that supersedes ADR-031, explains the destination state, and is approved before any environment migrates.
  - **FR-S02b**: Migration MUST roll out in order `dev → staging → production`, each stage gated by 7 days of green dev/staging telemetry; the simplified pipeline shape from spec 031 is preserved (no return to spec-029 complexity). *(Rubric 13.2)*
- **FR-S03**: CI MUST run CodeQL (Python, JavaScript/TypeScript, and Bicep where supported) on every PR. *(Rubric 13.3)*
- **FR-S04**: System MUST enable Defender for Cloud + Microsoft Sentinel hooks via Bicep policy assignments under `policies/`. *(Rubric 13.4)*
- **FR-S05**: System MUST encrypt Cosmos and Storage with customer-managed keys (extending the existing `log-analytics-key.bicep` pattern). *(Rubric 13.5)*

### Functional Requirements — Performance & Reliability (FR-R##)

- **FR-R01**: System MUST drop `continue-on-error: true` on the benchmark step in CI and define numeric regression thresholds (per-test p95 + memory). *(Rubric 14.1)*
- **FR-R02**: System MUST run `tests/load/` nightly against staging and post results to App Insights. *(Rubric 14.2)* — overlaps with FR-T05; tracked once.
- **FR-R03**: System MUST publish a capacity model (signals/sec, agents/incident, recommendations/hour) tied to success metrics. *(Rubric 14.3)*
- **FR-R04**: System MUST add Cosmos autoscale max-RU caps per container in `infra/main.bicep`. *(Rubric 14.4)*
- **FR-R05**: System MUST add a chaos-engineering exercise (Azure Chaos Studio) hitting the resilience middleware on a quarterly schedule. *(Rubric 14.5)*

### Functional Requirements — CI/CD (FR-C##)

- **FR-C01**: System MUST land spec 031 (simplify CI/CD) and remove the dual pipeline footprint. *(Rubric 15.1)*
- **FR-C02**: System MUST publish a progressive-delivery doc once 031 merges, showing the dev → staging → prod (and canary) gate matrix. *(Rubric 15.2)*
- **FR-C03**: All GitHub Actions `uses:` lines MUST be pinned to commit SHAs (40 hex chars). *(Rubric 15.3)*
- **FR-C04**: System MUST publish DORA dashboards (deployment frequency, lead time, MTTR, change-failure rate) sourced from GitHub + App Insights. *(Rubric 15.4)*
- **FR-C05**: System MUST replace the `0.0.0.0` "allow Azure services" Cosmos rule with VNet integration + Service Endpoint or Private Endpoint. *(Rubric 15.5)* — overlaps with FR-S01; tracked once.

### Functional Requirements — Day-2 Operations (FR-D##)

- **FR-D01**: System MUST publish an explicit DR/BCP runbook with **RPO ≤ 15 minutes and RTO ≤ 60 minutes** for production response workloads, including step-by-step Australia Southeast region-failover procedures and verification checklist. The quarterly DR drill (FR-D05) MUST exercise these targets. *(Rubric 16.1)*
- **FR-D02**: Container Apps base images MUST be pinned (no `:latest`) and managed by Dependabot for patching cadence. *(Rubric 16.2)*
- **FR-D03**: System MUST publish a monthly cost report template (Azure Cost Management export) and tie it to the `llm_mixin.py` budget tracker output. *(Rubric 16.3)*
- **FR-D04**: System MUST publish a Cosmos backup/restore runbook and enable point-in-time restore in `infra/main.bicep`. *(Rubric 16.4)*
- **FR-D05**: System MUST capture an exercise schedule (quarterly LLM rehearsals + biannual full-stack chaos) under `docs/disaster-response-hub/evaluation/exercise-schedule.md`. *(Rubric 16.5)*

### Functional Requirements — Documentation (FR-DOC##)

- **FR-DOC01**: README MUST link a 60-second walkthrough video (Loom or equivalent). *(Rubric 17.1)*
- **FR-DOC02**: System MUST host generated API docs (Redoc/Swagger UI) from `openapi.yaml` in the web app. *(Rubric 17.2)*
- **FR-DOC03**: System MUST consolidate the three governance/eval doc hubs (`docs/llm-evaluation/`, `docs/disaster-response-hub/evaluation/`, `governance-dashboard.md`) under a single nav. *(Rubric 17.3)*
- **FR-DOC04**: Repo MUST publish `CONTRIBUTING.md` covering branch conventions and the spec-driven workflow. *(Rubric 17.4)*
- **FR-DOC05**: Repo MUST publish `CHANGELOG.md` (or GitHub Releases) so reviewers can scan delivered slices. *(Rubric 17.5)*

### Key Entities

- **Recommendation**: a recommendation now carries `prompt_sha`, `prompt_version`, `model_id`, `model_version`, `deployment_alias`, `consensus_id` (nullable), `autonomy_level_at_decision`, `kill_switch_state`, `rag_sources[]`, plus existing fields.
- **AuditSegment**: append-only ledger record with cryptographic continuity hash; integrity-check job verifies chain.
- **JurisdictionPolicy**: declarative document keyed by jurisdiction code carrying `autonomy_level`, `kill_switch_overrides`, `language_priorities`, `aiims_role_overrides`.
- **EvalCase / EvalScorecard**: spec-030 entities; v1 dataset must reach ≥5,000 cases; scorecards drive CI gates.
- **MetricDefinition**: entries in `metrics-catalogue.md` describing every customMetric (name, dimensions, source, SLO usage).
- **SLO**: defined SLI + objective + error budget + alerting policy, published in `slo.md`.
- **PromptArtifact**: signed (cosign) prompt template with `sha`, `version`, `owner`, `review-due`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Independent re-grading against the AMA Rubric returns Excellent (5) on every dimension (16 dimensions; 80/80 score) with documented evidence per item.
- **SC-002**: Auditor opens the "why fired" panel for any recommendation in < 30 seconds and observes complete provenance (signals, prompt SHA, model version, approval chain, ledger hash).
- **SC-003**: From a public network, every production data plane (Cosmos, Storage, Azure OpenAI, Content Safety) refuses connections in 100% of probes; from inside the VNet, operator workflows succeed in 100% of probes.
- **SC-004**: SLO dashboard shows ≥99.9% availability of the public dashboard URL and ≥99.5% agent-handoff success over a rolling 30-day window.
- **SC-005**: Eval-harness scorecards meet or exceed published baselines for accuracy, hallucination, and safety on the v1 ≥5,000-case dataset; CI gate fails any below-threshold change.
- **SC-006**: Region failover drill in staging shifts traffic to Australia Southeast within the published RTO, with 0 data loss beyond the published RPO.
- **SC-007**: First-time reviewers reach the video walkthrough, API docs, SLO doc, `CONTRIBUTING.md`, `CHANGELOG.md`, and `tests/README.md` in under 60 seconds with zero broken links.
- **SC-008**: CI fails any PR introducing a new long-lived secret, an unpinned action, an unformatted file, an illegal cross-package import, or a coverage regression below the published target.
- **SC-009**: Mean time-to-detect (MTTD) for any SLI burning >50% of monthly error budget is under 5 minutes; mean time-to-page (MTTP) is under 2 minutes after MTTD.
- **SC-010**: Quarterly LLM rehearsal and biannual chaos exercise are run on schedule with published outcomes for at least one full cycle.

---

## Assumptions

- Azure-only stack remains. New services introduced (Azure AI Search for RAG, Azure Chaos Studio, Defender for Cloud, Microsoft Sentinel) deploy in Australia East with Australia Southeast paired region for DR.
- The 9-step orchestration (specify → 2× clarify → checklist → plan → tasks → analyze → implement → review → deploy) is run end-to-end on this single composite feature.
- Operational and sector personas were consulted via their `.github/agents/` reference files; their cross-cutting requirements (life-safety, AIIMS, multi-jurisdiction, multi-language, audit, degraded-connectivity) are reflected here.
- Some items overlap (e.g. FR-T05 ≡ FR-R02; FR-S01 ≡ FR-C05). Each is tracked once in the implementation plan to avoid double-counting.
- Where a Rubric improvement requires a new artifact (ADR, runbook, doc), the spec implies it must be created.
