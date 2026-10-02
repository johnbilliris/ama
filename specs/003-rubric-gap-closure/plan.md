# Implementation Plan: Rubric Gap Closure — AI Integration, CI/CD, and Agent Depth

**Branch**: `003-rubric-gap-closure` | **Date**: 2026-03-16 | **Spec**: `c:\code\ama\specs\003-rubric-gap-closure\spec.md`
**Input**: Feature specification from `/specs/003-rubric-gap-closure/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Close all remaining AMA rubric gaps (current 55/60 → target 60/60) by integrating Azure OpenAI into the Risk Assessment and Communication agents with template fallback and content safety; completing the CI/CD pipeline with full test execution, linting, type-checking, and lightweight performance regression checks; deepening agent orchestration with event-driven handoff chaining, dead-letter handling, and retry policies; adding Dockerfiles and application-level Bicep IaC; producing executive demo artifacts; hardening error handling with structured responses, exponential-backoff retries, alert action groups, and dead-letter stores; and validating performance targets with a load test suite.

## Technical Context

**Language/Version**: Python 3.12 for API and agent runtime; TypeScript 5.6 for responsive web UI  
**Primary Dependencies**: FastAPI, Pydantic v2, openai (Azure OpenAI Python SDK), tenacity (retry/backoff), Locust (load testing), Microsoft Agent Framework for Python; Next.js 15, React 19, Tailwind CSS, Playwright  
**Storage**: Azure Cosmos DB (operational state); Azure Blob Storage (audit + dead-letter); Azure Cache for Redis (dashboard cache); in-memory implementations for local development  
**Testing**: pytest (contract, integration, simulation), Playwright e2e, Locust load tests, lightweight CI benchmark via pytest-benchmark  
**Target Platform**: Azure Container Apps (API + agent runtime), Azure App Service (web); GitHub Actions CI  
**Project Type**: Multi-service web application with LLM-augmented agent orchestration backend  
**Performance Goals**: Dashboard load <2s p95; read API <500ms p95; signal ingestion 50,000/hour; hazard update visibility <60s; CI pipeline <10 minutes; CI benchmark <60s  
**Constraints**: Australian Azure regions only (non-AU model endpoints require the named, version-controlled Foundry carve-out plus required approval quorum); human approval for safety-critical outputs; content safety validation on LLM outputs; template fallback on model failure; dead-letter for failed handoffs; non-root container images; no embedded secrets  
**Scale/Scope**: 1,000 concurrent operators, 50,000 signals/hour burst, 100+ organisations, 6 languages per alert draft

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate Review

- **Life Safety First**: INTENT CHECK (evidence pending). LLM-generated content for public alerts requires content safety validation (FR-006) and human approval before publication. Template fallback (FR-004) ensures no silent degradation. Dead-letter handling (FR-014, FR-025) prevents lost safety-critical handoffs.
- **Multi-Agent Coordination With Clear Roles**: INTENT CHECK (evidence pending). Agent roles remain unchanged. Handoff chaining (FR-011, FR-012) uses explicit typed events through the event bus. No agent silently mutates shared state.
- **Data Trust, Provenance, and Freshness**: INTENT CHECK (evidence pending). LLM outputs include correlation IDs, model deployment identifiers, and token usage logs (FR-005). Template-fallback outputs are explicitly marked. Provenance tracking is preserved for all recommendation sources.
- **Privacy, Security, and Regional Policy Compliance**: INTENT CHECK (evidence pending). Foundry deployments must remain in Australian regions unless an approved constitution-bound carve-out exists. Dockerfiles use non-root users with no embedded secrets (FR-015, FR-016). IaC intends managed identity and Australian data residency (FR-019, FR-020). No new PII collection.
- **Multilingual, Accessible, and Actionable Communication**: INTENT CHECK (evidence pending). Communication agent drafts all 6 supported languages (FR-002). Content safety validation ensures outputs meet plain-language guidelines (FR-006).
- **Cloud Platform**: INTENT CHECK (evidence pending). All new infrastructure targets Azure services in approved regions.
- **Quality Gates and Operational Readiness**: INTENT CHECK (evidence pending). CI pipeline runs all tests on every PR (FR-007). Load tests validate performance targets (FR-028, FR-029). Lightweight regression benchmark in CI (FR-030). Dead-letter store enables operator review of failures (FR-025).

## Project Structure

### Documentation (this feature)

```text
specs/003-rubric-gap-closure/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
apps/
├── api/
│   ├── Dockerfile                          # NEW — API container definition (FR-015)
│   └── app/
│       ├── api/
│       │   ├── handoffs.py                # NEW — handoff status API route (FR-013)
│       │   ├── dead_letters.py            # NEW — dead-letter API routes (FR-025)
│       │   └── health.py                  # NEW — container health check endpoint (FR-015)
│       ├── services/
│       │   └── dead_letter_service.py      # NEW — dead-letter store (FR-025)
│       └── middleware/
│           ├── error_handler.py           # NEW — structured error handler (FR-023)
│           └── resilience.py              # MODIFY — add retry policies (FR-024)
├── agents/
│   ├── Dockerfile                          # NEW — agent runtime container (FR-016)
│   ├── common/
│   │   ├── handoffs.py                    # MODIFY — add delivery status, retry, dead-letter (FR-013, FR-014)
│   │   ├── llm_client.py                 # NEW — Azure OpenAI wrapper (FR-001–006)
│   │   ├── llm_mixin.py                  # NEW — shared LLM call + fallback + safety (FR-003–006)
│   │   ├── content_safety.py             # NEW — rule-based content safety validator (FR-006)
│   │   └── dependency_notifier.py         # EXISTING
│   ├── monitoring/agent.py                # MODIFY — publish handoff on high-risk signal (FR-011)
│   ├── risk_assessment/agent.py           # MODIFY — use LLM for explanations (FR-001), publish handoff (FR-012)
│   └── communication/agent.py             # MODIFY — use LLM for multilingual drafts (FR-002)
└── web/                                    # EXISTING — no structural changes

packages/
├── domain/src/domain/models/
│   ├── model_deployment.py                # NEW — ModelDeployment entity
│   ├── dead_letter_entry.py               # NEW — DeadLetterEntry entity
│   └── load_test_result.py                # NEW — LoadTestResult entity
└── schemas/                                # EXISTING

infra/
├── bicep/
│   ├── monitoring.bicep                   # MODIFY — add action groups (FR-026), complete latency alert (FR-027)
│   └── main.bicep                         # NEW — application resources IaC (FR-018–020)
└── policies/                               # EXISTING

tests/
├── contract/                               # EXISTING + new LLM contract tests
├── integration/                            # EXISTING + new handoff chain tests
├── simulation/                             # EXISTING
├── e2e/                                    # EXISTING
├── benchmark/                              # NEW — CI lightweight performance regression (FR-030)
└── load/                                   # NEW — Locust load test suite (FR-028–029)

.github/workflows/
└── ci.yml                                  # MODIFY — full pipeline (FR-007–010, FR-030)

docs/
└── disaster-response-hub/
    ├── demo/                               # NEW — demo walkthrough + slides (FR-021–022)
    └── evaluation/                         # EXISTING
```

**Structure Decision**: Extend the existing monorepo structure from feature 001. No new top-level projects are added. New files slot into existing application directories (Dockerfiles at app roots, new services alongside existing ones, new domain models in the shared package). The load test suite lives under `tests/load/` following the existing test directory convention. Demo artifacts live under `docs/disaster-response-hub/demo/`. Application IaC is added as `infra/bicep/main.bicep` alongside the existing monitoring template.

## Complexity Tracking

> No constitution violations. All changes extend existing structure within established boundaries.

### Post-Design Gate Review

- **Life Safety First**: EVIDENCE PENDING. The data model introduces `generationMethod` tracking on Recommendation and PublicAlert, ensuring human reviewers can distinguish LLM-generated from template-generated content. Content safety validation (FR-006) with `safety_fallback` marking prevents unsafe LLM outputs from reaching public alerts. Dead-letter handling (DeadLetterEntry) prevents lost safety-critical handoffs and provides operator review workflow. Template fallback ensures no silent degradation of safety-critical outputs.
- **Multi-Agent Coordination With Clear Roles**: EVIDENCE PENDING. AgentHandoffEvent extends the existing AgentHandoff with full delivery lifecycle tracking. Handoff chaining (Monitoring → Risk Assessment → Communication) uses explicit typed events through the EventBus with subscriber registration, with two logical edges (Monitoring→Risk and Risk→Communication) irrespective of retry attempts. No agent silently mutates shared state — all transitions are auditable via TimelineEvents.
- **Data Trust, Provenance, and Freshness**: EVIDENCE PENDING. Recommendation and PublicAlert now carry `generationMethod`, `modelDeploymentId`, and `tokenUsage` fields, making the generation provenance fully transparent. LLM call events are recorded as timeline entries with deployment identifier, latency, and token counts. Template-fallback and safety-fallback outputs are explicitly distinguished from LLM-generated content.
- **Privacy, Security, and Regional Policy Compliance**: EVIDENCE PENDING. ModelDeployment entity enforces HTTPS endpoints and configurable content safety policies. Dockerfiles specify non-root users and use no embedded secrets. IaC intends Australian residency with constitution-bound carve-out controls where required. Dead-letter entries are tenant-scoped (`tenantScopeKey`) for multi-tenant access control. No new PII is collected or stored.
- **Multilingual, Accessible, and Actionable Communication**: EVIDENCE PENDING. PublicAlert `content_blocks` dictionary is keyed by all 6 language codes. The Communication agent generates all languages in every draft. Content safety validation applies before human review. Fallback templates maintain multi-language support when the LLM is unavailable.
- **Cloud Platform**: EVIDENCE PENDING. All infrastructure defined in Bicep targets Azure services, with regional compliance verified via evidence manifests and deployment outputs.
- **Quality Gates and Operational Readiness**: EVIDENCE PENDING. The quickstart defines a phased test-first validation flow (Phases A–H) covering every functional requirement. Load test scenarios validate documented performance targets. The CI pipeline includes all quality gates. Dead-letter management provides a review and resolution workflow for operational failures.
