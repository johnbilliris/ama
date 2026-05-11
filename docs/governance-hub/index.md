# Governance Hub

**Purpose**: single navigation entry point for everything governance, evaluation, and compliance for the Disaster Response Coordination Hub. Replaces the prior split across three locations (FR-DOC03).

## Sections

### Operational Governance
- [Governance Dashboard](../governance-dashboard.md) — live operational governance KPIs.
- [Decision-Rights Matrix](agents/decision-rights.md) *(spec-032 T027)*
- [Saga / Approval Workflow](agents/saga-approval-workflow.md) *(spec-032 T311)*

### LLM Evaluation
- [Spec 030 — LLM Evaluation Framework](../../specs/030-llm-eval-framework/spec.md)
- [Baseline metrics](../disaster-response-hub/evaluation/baseline-metrics.md)
- [Live LLM rehearsal runbook](../disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md)
- [Quickstart rehearsal results (2026-03-16)](../disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md)
- [UX rubric](../disaster-response-hub/evaluation/ux-rubric.md)
- [Exercise schedule](../disaster-response-hub/evaluation/exercise-schedule.md) *(spec-032 T030)*
- [Post-exercise survey](../disaster-response-hub/evaluation/post-exercise-survey.md)

### Observability & SLOs
- [SLO catalogue](observability/slo.md) *(spec-032 T025)*
- [Metrics catalogue](observability/metrics-catalogue.md) *(spec-032 T026)*

### Architecture
- [C4 model — System](architecture/c4/system.md) *(spec-032 T021)*
- [C4 model — Container](architecture/c4/container.md) *(spec-032 T021)*
- [Cosmos partitioning math](architecture/cosmos-partitioning.md) *(spec-032 T022)*
- [Capacity model](architecture/capacity-model.md) *(spec-032 T804)*
- [Monitoring → Risk → Communication sequence](architecture/sequence/monitoring-risk-comms.md) *(spec-032 T024)*

### Security & Sovereignty
- [ADR-032 — OIDC supersession](../aidr/decisions/adr-032-oidc-supersession.md)
- [ADR-033 — Phi shadow boundary](../aidr/decisions/adr-033-phi-shadow-boundary.md)
- [Foundry carve-out registry](../../infra/parameters/foundry-carveout.yaml)
- [Sensitive-content classification taxonomy](../safety/classification-taxonomy.md)

### CI/CD
- [Progressive delivery](../ci-cd/progressive-delivery.md) *(spec-032 T815)*
- [DORA metrics](../ci-cd/dora-metrics.md) *(spec-032 T816)*

### Day-2 Operations
- [DR/BCP runbook](../operator-runbooks/dr-bcp.md) *(spec-032 T809)*
- [Cosmos backup/restore runbook](../operator-runbooks/cosmos-backup-restore.md) *(spec-032 T810)*
- [Model rollback runbook](../operator-runbooks/model-rollback.md) *(spec-032 T811)*
- [AOAI quota request](../operator-runbooks/aoai-quota.md) *(spec-032 T817)*
- [Cost reporting](../operator-runbooks/cost-reporting.md) *(spec-032 T812)*

> Files marked *(spec-032 T###)* are in scope for spec-032 and may be `[Stub]` until the relevant task lands.

### Capstone Evidence Pack (spec-037)

- [Risk Register](../risk-register/index.md) — Systematic Risk Register (artefact 1, FR-010..FR-014)
- [Adoption Roadmap](adoption-roadmap/roadmap.md) — phased jurisdictional onboarding (artefact 2, FR-015..FR-018)
- [Executive KPI Surface](executive-kpi/surface.md) — single-page roll-up against the five capstone success criteria (artefact 3, FR-019..FR-023)
- [Responsible AI Register](rai-register/responsible-ai-register.md) — per-component AI posture across 4 frameworks × 8 principles (artefact 4, FR-024..FR-029)
- [Feature-to-Value Ledger](../../specs/shared/feature-value-ledger.md) — inverse of `capstone-metric-trace.md` (artefact 5a, FR-030..FR-034)
- [Decision/Tradeoff Log](feature-value-ledger/tradeoff-log.md) — paired ADR log (artefact 5b, FR-032 + FR-036)
- Read-only [Executive page](../../apps/web/src/app/governance/executive/page.tsx) at `/governance/executive`
- CI publication gate: `evidence-pack-publication-gate` (RES-04, FR-008/009/037/038)
- ADRs: [ADR-037-01](../aidr/decisions/adr-037-01-text-first-evidence-pack.md), [ADR-037-02](../aidr/decisions/adr-037-02-executive-shell-reuse.md), [ADR-037-03](../aidr/decisions/adr-037-03-manual-evidence-cap.md), [ADR-037-04](../aidr/decisions/adr-037-04-three-layer-append-only.md)
