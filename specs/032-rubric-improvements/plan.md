# Implementation Plan: AMA Rubric Improvements (75-item Excellence Uplift)

**Branch**: `032-rubric-improvements` | **Date**: 2026-04-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/032-rubric-improvements/spec.md`

> **Persona consultation note** — All 17 technical personas in `.github/agents/technical/` were consulted. Their inputs are reflected here:
> - **Solution Architect / Azure Principal Architect / Principal Engineer**: cross-cutting NFR governance, WAF pillar mapping, technical-debt prioritisation
> - **Security Engineer / Compliance Auditor**: CMK, Private Endpoints, OIDC supersession, OPA policy extensions, CodeQL/Defender/Sentinel
> - **AI/ML Engineer**: RAG architecture, Phi shadow path, cosign-keyless, prompt registry
> - **API Architect**: Strategy + Saga pattern materialisation, structured-output contracts
> - **Infrastructure/DevOps / Docker & Container Engineer**: Bicep modules, AVM-first, Container Apps base-image pinning, Dependabot
> - **Data Engineer**: Cosmos partitioning math, RU autoscale caps, audit-segment integrity hashing
> - **SRE Engineer**: SLO catalogue, OTel exporter, App Insights synthetics, error-budget alerts, Workbooks
> - **QA/Test Engineer / Accessibility Tester**: chaos tier, web Vitest tier, contract-test guide, WCAG validation of new UI surfaces
> - **Chaos Engineer**: Azure Chaos Studio experiments, gameday cadence
> - **Software Developer**: ruff format, import-linter, pre-commit, mypy --strict
> - **UX Designer**: governance hub consolidation, Workbook visual hierarchy
> - **Product Owner / BA**: traceability matrix per spec, requirement IDs

---

## Summary

Implement all 75 AMA Rubric improvement items as a single composite feature targeting Excellent (5) on every rubric dimension. The work spans 16 functional groups (Architecture, Patterns, Code Quality, Implementation Completeness, Testing, Logging, Observability, AI Integration, Models, Autonomy, Multi-Agent Coordination, Security, Performance, CI/CD, Day-2 Operations, Documentation) and is organised into nine implementation streams that can largely proceed in parallel after a dependency-ordered foundation phase.

The technical approach reuses the existing Azure stack (FastAPI on Container Apps, Next.js on App Service, Cosmos DB, Bicep IaC, GitHub Actions) and adds a small set of new Azure services where the rubric demands them: **Azure AI Search** (RAG over `docs/aidr/`), **Azure Chaos Studio** (resilience drills), **Microsoft Defender for Cloud + Sentinel** (security posture + SIEM), and **Application Insights availability tests** (synthetic monitoring). All new services land in **Australia East** with paired-region replication to **Australia Southeast** for the DR/BCP path. No non-Azure services introduced.

---

## Technical Context

**Language/Version**: Python 3.12 (apps/api, apps/agents, apps/ingestion, apps/eval-runner), TypeScript 5.8 (apps/web on Next.js 16.2)
**Primary Dependencies**: FastAPI, Pydantic v2, Azure SDK for Python, Azure OpenAI SDK, Next.js 16.2, React 19, openai, opentelemetry (NEW), pybreaker (NEW — replaces hand-rolled circuit breaker), import-linter (NEW), mypy (existing, now `--strict`), ruff (existing, now `format` enforced), cosign (NEW), Azure AI Search SDK (NEW)
**Storage**: Cosmos DB (existing — partition strategy expanded; CMK + Private Endpoint added), Azure Storage (CMK + Private Endpoint added), Azure AI Search (NEW — `Standard S1` AU East, indexes the `docs/aidr/` corpus + a future prompt library mirror)
**Testing**: pytest (existing) with `--cov` enforcement; new `tests/chaos/`, `tests/security/`, expanded `tests/load/` nightly; Playwright for `apps/web/e2e/` (existing infra, new specs); Vitest for `apps/web/__tests__/` (NEW)
**Target Platform**: Azure Container Apps (FastAPI + agents + ingestion + eval-runner), Azure App Service (Next.js web), Azure Functions where appropriate (NEW for cosign verify in deploy)
**Project Type**: Multi-app monorepo (web + 4 backend services + 5 packages) — see Project Structure
**Performance Goals**: per FR-O06 SLOs — signal-ingestion P95 ≤ 60 s; agent-handoff success ≥ 99.5%; alert-to-publish P95 ≤ 90 s; dashboard availability ≥ 99.9%; LLM cost per incident ≤ published budget; kill-switch propagation P99 ≤ 30 s; RAG retrieval P95 ≤ 400 ms
**Constraints**: Australia East primary, Australia Southeast paired (RPO ≤ 15 min, RTO ≤ 60 min); no public ingress to data planes in production; CMK on Cosmos + Storage; OIDC federated workload identity (Stage 2 of FR-S02); AIIMS COP integrity; constitutional Non-Negotiables hold (life safety, data sovereignty, privacy, interoperability, graceful degradation)
**Scale/Scope**: 75 functional requirements across 9 implementation streams; ~30 Bicep modules touched/added; ~40 application files touched (mostly in `apps/api`, `apps/agents/common/`, `apps/web`); 1 new package (`packages/prompts/`); 5 new ADRs

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution clause | Plan position | Status |
|---|---|---|
| **I. Primacy of Life** | All P1 user stories preserve life-safety primacy; degraded-mode fallbacks (kill-switch + template fallback) keep public warnings flowing even when LLM/RAG unavailable | ✅ Pass |
| **II. National EM Principles + AIIMS** | Decision-rights matrix (FR-AG01) makes AIIMS span-of-control explicit; consensus events (FR-AG09) and AAR gap summary (FR-AG10) reinforce continual improvement | ✅ Pass |
| **III. Multi-Hazard, Multi-Agency** | Jurisdiction-policy autonomy dial (FR-AG02), language priorities, AIIMS role overrides; OIDC migration (FR-S02) preserves multi-tenant boundaries | ✅ Pass |
| **IV. Transparency & Auditability** | US1 makes provenance + integrity-check + ledger-hash mandatory; recommendation entity expanded with `prompt_sha`, `model_version`, etc. | ✅ Pass |
| **V. Warning & Public Information (AWS, Ten Principles, Total Warning System)** | Communication agent retains template fallback under all degraded modes; PII redaction (FR-O05) protects public outputs; multilingual + accessibility (FR-DOC02 includes WCAG 2.2) | ✅ Pass |
| **VI. Evacuation Framework** | Unchanged — covered by spec 009; this feature does not regress it | ✅ Pass |
| **VII. Recovery Support** | Recovery handoff already in scope; AAR gap summary (FR-AG10) feeds lessons capture | ✅ Pass |
| **VIII. Cloud Platform** | Azure-only; AVM-first per `azure-defaults` skill; Bicep + GitHub Actions; new services (AI Search, Chaos Studio, Defender, Sentinel) all Azure-native | ✅ Pass |
| **NON-NEGOTIABLE 1: Human-in-the-loop** | Approval workflow preserved; autonomy dial cannot bypass life-safety approvals; bypasses require co-approval + audit log | ✅ Pass |
| **NON-NEGOTIABLE 2: Data sovereignty** | All data planes Australia East/Southeast; AI Search index AU East no replication; Phi shadow path constrained to Foundry carve-out (constitution §1.2.0 amendment) with data-minimisation gateway; recommendations themselves NOT routed via Phi for users | ✅ Pass — gated by carve-out controls (see Phi handling) |
| **NON-NEGOTIABLE 3: Privacy by design** | PII hash-redaction (FR-O05); CMK on Cosmos + Storage (FR-S05); content-safety unchanged | ✅ Pass |
| **NON-NEGOTIABLE 4: Interoperability** | OpenAPI (Redoc/Swagger UI host — FR-DOC02); EDXL/CAP unchanged | ✅ Pass |
| **NON-NEGOTIABLE 5: Graceful degradation** | Per-agent kill-switch (FR-AG05); degraded-mode evaluator already in middleware; circuit-breaker library swap (FR-P03) preserves behaviour | ✅ Pass |

**Phi handling clarification (Non-Negotiable #2 carve-out)**: The Phi shadow path emits inputs only via the model gateway with PII data-minimisation; outputs are stored in the AU-resident audit/eval store with `shadow=true` tag; nothing in the user-facing flow consumes Phi outputs in production until a separate carve-out promotion is approved. This is the planned interpretation; ADR-033 (Phi shadow boundary) is a Phase-0 deliverable.

**Result: ✅ GATE PASSED.** No constitution-violation justifications required in Complexity Tracking.

---

## Project Structure

### Documentation (this feature)

```text
specs/032-rubric-improvements/
├── plan.md              # This file
├── research.md          # Phase 0 — research notes & decisions
├── data-model.md        # Phase 1 — entities (Recommendation, AuditSegment, JurisdictionPolicy, EvalCase, MetricDefinition, SLO, PromptArtifact)
├── quickstart.md        # Phase 1 — local dev + smoke tests
├── contracts/           # Phase 1 — OpenAPI updates, OTel attribute schema, prompt-artifact signing schema
├── checklists/
│   ├── requirements.md  # Spec quality (Step 1)
│   └── rubric.md        # 75-item requirements quality (Step 3)
└── tasks.md             # Phase 2 — produced by /speckit.tasks (Step 5)
```

### Source Code (repository root)

```text
apps/
├── web/                          # Next.js 16.2 — adds /api/docs (Redoc), Vitest tests, Playwright e2e specs
│   ├── src/
│   │   ├── app/
│   │   │   ├── api-docs/         # NEW route hosting OpenAPI Redoc
│   │   │   └── governance/       # consolidated governance/eval hub (FR-DOC03)
│   │   └── lib/
│   ├── __tests__/                # NEW Vitest tier (FR-T02)
│   └── e2e/                      # NEW Playwright spec (FR-I03)
├── api/                          # FastAPI — adds /metrics, /api/health/sli, integrity-check endpoints
│   └── app/
│       ├── api/routes/            # + recommendations_provenance.py (US1)
│       ├── middleware/            # + otel_middleware.py (FR-O07), + integrity_validator.py (US1)
│       ├── services/              # + rag_service.py (FR-AI01), + autonomy_policy_service.py (FR-AG02)
│       ├── repositories/          # + audit_segment_repository.py (US1)
│       └── observability/         # NEW package — metric definitions, OTel setup
├── agents/                       # Python agent runtime — refactored
│   ├── common/                   # CURRENT 18-file flat → REFACTORED into 3 sub-packages (FR-A05/Q05)
│   │   ├── resilience/           # circuit_breaker, retry, dead_letter, handoff_retry
│   │   ├── safety/               # content_safety, redaction, prompt_validator
│   │   └── lifecycle/            # heartbeat, killswitch, autonomy_eval, degraded_mode
│   ├── monitoring/
│   ├── risk_assessment/
│   ├── communication/
│   ├── evacuation/
│   ├── resource_allocation/
│   ├── dependency_notifier/      # promoted to first-class agent in README (FR-AG04)
│   └── llm/                      # NEW package — strategies (Strategy pattern FR-P01), prompt registry, RAG client
├── ingestion/                    # ops surface — runbook coverage added (FR-I04)
└── eval-runner/                  # spec 030 — Phi shadow integration (FR-AI03), pytest IDs (FR-T09)

packages/
├── domain/                       # adds RecommendationProvenance, JurisdictionPolicy, AutonomyDial models
├── prompts/                      # NEW package — versioned prompt artifacts + cosign signing manifest
├── eval-core/                    # spec 030 — adds threshold gates (FR-T01 + FR-AI04 wiring)
└── ui/                           # adds workbook-card components, "why fired" panel

infra/
├── main.bicep                    # adds Cosmos PE + CMK, Storage CMK, AOAI PE, Cosmos backup, autoscale max-RU caps
├── modules/
│   ├── ai-search.bicep           # NEW — Standard S1 AU East
│   ├── chaos-studio.bicep        # NEW
│   ├── defender.bicep            # NEW
│   ├── sentinel.bicep            # NEW
│   ├── workbooks/                # NEW — JSON templates (FR-O04, FR-O08)
│   ├── monitoring.bicep          # extends with per-tier retention (FR-O01) + paging tiers (FR-O09)
│   └── private-endpoints.bicep   # extends Cosmos/Storage/AOAI/AI Search PE wiring
├── policies/                     # OPA — adds autonomy_dial.rego, killswitch.rego, prompt_signing.rego
└── parameters/                   # adds dr.parameters.<env>.json for failover drills

.github/
├── workflows/
│   ├── ci.yml                    # adds mypy --strict, ruff format --check, import-linter, codeql, pytest --cov
│   ├── cd.yml                    # adds OIDC stage-2 (post FR-S02b), cosign verify, SHA-pinned actions
│   ├── nightly-load.yml          # NEW (FR-T05/FR-R02)
│   ├── chaos-quarterly.yml       # NEW (FR-R05)
│   ├── dr-drill.yml              # NEW manual + scheduled
│   └── dora-metrics.yml          # NEW publishes DORA dashboard data
└── instructions/                 # extends bicep + terraform compliance with new policies

docs/
├── architecture/c4/              # NEW — C4 diagrams (FR-A01)
├── observability/
│   ├── slo.md                    # NEW (FR-O06)
│   └── metrics-catalogue.md      # NEW (FR-O02)
├── operator-runbooks.md          # extends with ingestion + DR/BCP + model-rollback (FR-I04, FR-D01, FR-AI07)
├── ai/
│   └── prompt-library.md         # NEW (FR-AI05)
├── agents/
│   └── decision-rights.md        # NEW (FR-AG01)
├── ci-cd/
│   ├── progressive-delivery.md   # NEW (FR-C02)
│   └── dora-metrics.md           # NEW (FR-C04)
├── disaster-response-hub/evaluation/
│   └── exercise-schedule.md      # NEW (FR-D05)
├── aidr/
│   └── INDEXING-LICENCE-NOTE.md  # NEW (FR-AI01 clarification)
└── governance-hub/               # NEW consolidated nav (FR-DOC03)

tests/
├── unit/                         # extended; coverage gate (FR-T01)
├── integration/                  # extended; coverage gate
├── contract/                     # extended; CONTRIBUTING.contract.md (FR-T08)
├── chaos/                        # NEW (FR-T03)
├── security/                     # NEW — CodeQL pseudo-tests + bicep policy unit tests (FR-T04)
├── load/                         # extended; nightly schedule (FR-T05)
└── README.md                     # NEW (FR-T06)

CONTRIBUTING.md                   # NEW (FR-DOC04)
CHANGELOG.md                      # NEW (FR-DOC05)
.pre-commit-config.yaml           # NEW (FR-Q04)
.github/dependabot.yml            # extends to base images (FR-D02)
```

**Structure Decision**: Multi-app monorepo (existing) — chosen to keep this composite uplift inside the established `apps/`, `packages/`, `infra/`, `docs/`, `tests/` layout. Rejected alternative: split into 16 sub-features (one per rubric pillar) — rejected per user's explicit "single mega-feature" choice during planning kickoff.

---

## Phase 0 — Research

Research output lives in [research.md](./research.md). Key research questions resolved:

1. **Circuit-breaker library** — chose `pybreaker` (mature, async-friendly) over `tenacity` (retry-only) and rolling our own; ADR-034.
2. **OTel exporter** — chose **OTLP/HTTP** to Azure Monitor via the official Azure Monitor OpenTelemetry Distro (`azure-monitor-opentelemetry`), supports automatic instrumentation of FastAPI + httpx + Azure SDKs.
3. **Azure AI Search SKU** — `Standard S1` AU East prod, `Basic` dev/staging; vector dim 1536 with `text-embedding-3-large` (Foundry deployment); 1 replica + 1 partition baseline.
4. **OIDC migration sequencing** — Two-stage per spec clarification: spec 031 lands first; ADR-032 supersedes ADR-031; per-environment migration `dev → staging → prod` with 7-day soak.
5. **Cosign keyless** — Sigstore Fulcio identity via GitHub OIDC; no long-lived signing keys; verification in `cd.yml` deploy step.
6. **CMK strategy** — Customer-managed keys in Key Vault with Microsoft-managed HSM-backed keys; key rotation via Azure Policy; Cosmos and Storage opt-in via Bicep parameter.
7. **Phi shadow path boundary** — ADR-033: shadow inputs are minimised at the model gateway, outputs persist AU-only with `shadow=true`, no operator-facing surfacing until carve-out promotion.
8. **Web testing tier** — Vitest (Vite-native, faster than Jest in the Next.js 16 / React 19 stack); React Testing Library for component tests.
9. **Coverage tooling** — `pytest-cov` with `--cov-fail-under` per tier; reports posted to PR via `coverage-badge`/codecov action (SHA-pinned).
10. **Synthetic monitoring** — App Insights availability tests (multi-step web tests), 5 locations: Sydney, Melbourne, Auckland, Singapore, Tokyo (closest APAC POPs).

---

## Phase 1 — Design & Contracts

Phase 1 outputs (created in this step):

- [data-model.md](./data-model.md) — entities, fields, relationships, state transitions
- [quickstart.md](./quickstart.md) — local-dev workflow + smoke tests for the major new surfaces
- [contracts/](./contracts/) — OpenAPI delta, OTel attribute schema, cosign signing manifest, RAG citation schema, JurisdictionPolicy YAML schema
- Update agent context: run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot` after merge to refresh `.github/copilot-instructions.md` and skill memories.

---

## Implementation Streams (for Phase 2 task generation)

Tasks (Step 5) will be ordered along these streams. Streams 0–2 are foundational; 3–8 can largely parallelise **EXCEPT** for the explicit cross-stream dependencies listed below.

### Cross-stream hard dependencies (must be honoured by Step 5 task ordering)

- **Spec 031 is an EXTERNAL prerequisite.** All Stream 4 OIDC Stage-2 work (FR-S02b) and the Stream 8 "land spec 031" task (FR-C01) are gated behind: (a) spec 031 merged to `main`, (b) spec 031 status `Approved`, (c) staging+production CD green for ≥ 7 consecutive days under the simplified `AZURE_CREDENTIALS` flow. Until those gates are met, Stream 4 OIDC tasks remain in `blocked` status.
- **AI Search Private Endpoint must land in Stream 4 BEFORE Stream 6 indexing tasks run.** No retrieval/ingestion task may target an internet-reachable AI Search endpoint, even in dev (dev uses the `Basic` SKU but with the same private-network posture).
- **Content Safety Private Endpoint is Stream 4 (was missing).** Required to satisfy US2 acceptance scenario (Cosmos / Storage / Azure OpenAI / Content Safety reject public connections).
- **Foundry carve-out registry (FR-AI03a) is Stream 0/4.** Restores the deploy-time NN-2 enforcement that ADR-031 documented as lost. CD MUST refuse Phi (or any non-AU model) deployment that is absent from the registry.
- **Phi shadow path (FR-AI03) blocked until** the classification-aware filter (PII + PSPF + sensitive-operational) is implemented in Stream 4 and the carve-out registry validates Phi's presence.
- **Kill-switch propagation spike is Stream 0.** A 2-day spike validates the push-based design (Cosmos change-feed → Service Bus topic → agent watcher) against the ≤ 30 s SLO before any downstream task commits to the SLO.

### Top-5 schedule-risk items (acknowledged + scoped)

The rubber-duck critique flagged five items most likely to bust scope inside one feature. We acknowledge and split each into "must-land for correctness/security" (this feature) and "evidence/maturity" (follow-up if needed):

1. **5,000-case eval dataset (FR-I02)** — must-land: scaffold `eval-dataset/v1` with at least the SC-targeted minimum subset gating CI today; evidence: ramp authoring cadence to reach 5,000 within the milestone window with weekly SME ingestion runs.
2. **OIDC Stage-2 rollout (FR-S02b)** — must-land: ADR-032 + dev migration; evidence: staging + production rollout under the 7-day soak rule.
3. **Full OTel + SLO + Workbook + synthetic monitoring** — must-land: OTel SDK + the 5 SLO metrics + 1 executive Workbook + 1 availability test; evidence: full Workbook suite + 5-location synthetic + paging routing.
4. **DR failover + PITR + RPO/RTO verification** — must-land: PITR enabled + paired-region read-only + DR runbook authored; evidence: an actual failover drill executed (post-merge gameday).
5. **Defender + Sentinel + analytics + routing** — must-land: Bicep enablement + 2 priority analytics rules + Action Group routing; evidence: full rule set + tuned-down false positives.

### Stream 0 — Foundation (T0xx)
ADR-032 (OIDC supersession), ADR-033 (Phi shadow boundary with classification-aware filter), ADR-034 (pybreaker), ADR-035 (cosign keyless), ADR-036 (Azure AI Search RAG); spec-030 + spec-031 status promotion (NOTE: spec-031 promotion is performed in spec 031's own PR — this feature only verifies the dependency state); placeholder Entra IDs resolved (FR-I05); pre-commit + CONTRIBUTING + CHANGELOG scaffolds; tests/README.md scaffold; Foundry carve-out registry skeleton (FR-AI03a); **kill-switch propagation spike** validating push-based ≤ 30 s budget.

### Stream 1 — Code-quality gates (T1xx)
mypy --strict; import-linter rules; ruff format --check; pytest --cov ratcheting enforcement (Phase A then B then C per FR-T01); pre-commit-config.yaml; CodeQL workflow; Bicep policy scan; SHA-pinning sweep across all workflows.

### Stream 2 — `apps/agents/common/` refactor (T2xx)
Move 18 modules into `resilience/`, `safety/`, `lifecycle/` sub-packages with re-exports for backward compatibility window; LLM Strategy class extraction (FR-P01); pybreaker swap (FR-P03); externalised budget tracker to Cosmos (FR-P02); typed AIIMS registry (FR-P05); classification-aware sensitive-content filter (`safety/classification.py`) used by the model gateway and the Phi shadow gate.

### Stream 3 — Audit, provenance, integrity (T3xx) — US1
Recommendation provenance fields (prompt_sha, model_version, deployment_alias, autonomy, killswitch, rag_sources, consensus_id); AuditSegment hash chain; integrity-check job + `/api/health/audit-integrity`; "why fired" panel in `apps/web`; PII hash-redaction validator (FR-O05); Saga + decision-rights doc.

### Stream 4 — Security & sovereignty (T4xx) — US2
Cosmos PE + CMK; Storage CMK; AOAI PE + private DNS; **AI Search PE + private DNS** (NEW from critique); **Content Safety PE + private DNS** (NEW from critique); CodeQL gates; Defender for Cloud + Sentinel via Bicep policy assignment (must-land subset per Top-5 split); OPA extensions (autonomy_dial, killswitch, prompt_signing, foundry_carveout); Entra group ID resolution; ADR-032 + Stage-2 OIDC rollout (gated by spec-031 prerequisite above); Foundry carve-out registry validator wired into CD.

### Stream 5 — Observability & SLOs (T5xx) — US3
Azure Monitor OpenTelemetry Distro wiring across api + agents + web; OTLP exporter; metric definitions module + customMetric emission for token cost (FR-O03); per-tier retention split (FR-O01); slo.md + metrics-catalogue.md; Workbooks JSON (must-land: executive governance; evidence: ingestion health, agent flow, LLM cost, operator runbooks); App Insights availability tests (must-land: 1 endpoint × 5 locations; evidence: 4 endpoints × 5 locations); paging severity tiers + Action Group routing.

### Stream 6 — AI quality (RAG, eval, prompts, models) (T6xx) — US4
Azure AI Search index + ingestion job for `docs/aidr/` (BLOCKED until Stream 4 PE lands; per-handbook licence inventory required); `rag_service.py` + retrieval P95 ≤ 400 ms; recommendation citations; prompt registry under `packages/prompts/` with cosign signing; prompt artifact verifier in cd.yml; **Phi shadow path in `apps/eval-runner` + audit store + classification gate (BLOCKED until Stream 2 classification filter + Stream 0 carve-out registry land)**; structured-output validation everywhere `_generate_with_fallback` is called; eval baseline gates wired to CI; spec-030 v1 dataset publication (must-land: subset gating CI; evidence: 5,000 cases per Top-5 split).

### Stream 7 — Multi-agent maturity (T7xx) — US5
Decision-rights matrix doc (FR-AG01); autonomy dial (Cosmos config + watcher; FR-AG02); kill-switch (FR-AG05) push-based with ≤ 30 s propagation + heartbeat metric (validated via Stream 0 spike); kill-switch + autonomy control surfaces with Entra+role+justification+dual-approval (FR-AG05a); "why fired" trace artifact (FR-AG03); state-graph generator producing Mermaid `stateDiagram-v2` (FR-AG06); reflection feedback loop (FR-AG07); per-handoff timeouts (FR-AG08); consensus events (FR-AG09); AAR gap summary (FR-AG10); promote dependency-notifier in README + `agents/` table (FR-AG04).

### Stream 8 — CI/CD, performance, day-2 (T8xx) — US6
Verify spec 031 landed (cross-stream prerequisite); remove `continue-on-error` on benchmarks + numeric thresholds; nightly load workflow; capacity model doc; Cosmos autoscale max-RU caps; Azure Chaos Studio quarterly workflow; DR/BCP runbook + Cosmos PITR enabled + paired-region failover drill (must-land: PITR + runbook; evidence: drill execution per Top-5 split); cost-report template; exercise schedule; Container Apps base images pinned + Dependabot; DORA dashboard publisher; progressive-delivery doc.

### Stream 9 — Documentation & reviewer story (T9xx) — US7+US8
README walkthrough video link + agent table refresh; Redoc hosting at `/api/docs`; consolidate three governance hubs into `docs/governance-hub/`; CONTRIBUTING.md + CHANGELOG.md; tests/README.md; contract-test contributor guide; per-spec requirement→test traceability matrix (start with spec 032 itself).

---

## Complexity Tracking

> All Constitution Check gates passed (no violations). This feature stays within the existing Azure-only, Bicep-IaC, multi-app monorepo paradigm. The only "new shape" is the small set of additional Azure services (AI Search, Chaos Studio, Defender, Sentinel) — all listed in the Constitution-VIII "Azure-native services preferred" allow-list and provisioned via Bicep AVM where modules exist.

| Item | Complexity Note |
|---|---|
| Azure AI Search introduction | Standard S1 only; minimal S1 footprint; offset by removing prompt-only grounding fragility |
| Cosign keyless verify in cd.yml | New tool; mitigated by GitHub OIDC reuse and an in-repo verification helper |
| OTel exporter | Adopting the official Azure Monitor distro keeps surface area small |
| Two-stage OIDC migration | Sequenced explicitly to avoid colliding with spec 031 |

---

## Re-evaluated Constitution Check (post-Phase-1)

After producing research.md, data-model.md, quickstart.md, and contracts/, the constitution check is re-run. Result: **✅ Still passing.** No new violations were introduced; the Phi shadow boundary (ADR-033) explicitly documents how the carve-out is honoured.

---

## Next Step

`/speckit.tasks` (Step 5) — generate `tasks.md` with dependency-ordered T0xx–T9xx tasks per the streams above.
