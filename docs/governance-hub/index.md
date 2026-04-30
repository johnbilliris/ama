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
