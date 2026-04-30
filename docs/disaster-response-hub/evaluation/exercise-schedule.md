# Disaster Response Hub — Exercise Schedule

**Purpose**: published cadence of LLM rehearsals, chaos exercises, and full-stack drills. Closes FR-D05.

## Cadence

| Exercise | Frequency | Owner | Scope | Output |
|---|---|---|---|---|
| **LLM rehearsal** | Quarterly (Q1, Q2, Q3, Q4) | AI/ML Engineer + PIO persona | Run the spec-030 eval harness against latest model set; SME walkthrough of 50 sample recommendations | `quickstart-rehearsal-results-{date}.md` + scorecard delta |
| **Chaos gameday** | Biannual (Apr, Oct) | Chaos Engineer + SRE | Azure Chaos Studio: Container App restart on monitoring agent; Cosmos throttling on audit container; AOAI region drop; Service Bus DLQ inundation | `chaos-gameday-{date}.md` + SLO impact report |
| **DR/BCP failover drill** | Quarterly (staging) | Infra/DevOps + SRE | Force Australia East primary unhealthy; verify Australia Southeast picks up within RTO | `dr-drill-{date}.md` + RPO/RTO measurements |
| **Multi-jurisdiction tabletop** | Annual (Aug) | Resilience Planner + Operational personas | Cross-state coordination scenario with NEMA + 3 state agencies | After-Action Review |
| **Public-network probe** | Continuous (CI workflow) | Security Engineer | All data planes refuse public IP probes | Telemetry + page-on-success |
| **Eval-baseline regression** | Per PR (CI gate) | AI/ML Engineer | Eval scorecards meet/exceed published baselines | PR pass/fail |

## 2026 calendar (reference)

| Date | Exercise |
|---|---|
| 2026-Q1 (Mar) | LLM rehearsal #1 + DR drill #1 |
| 2026-Q2 (Jun) | LLM rehearsal #2 + DR drill #2 + Chaos gameday #1 |
| 2026-Q3 (Sep) | LLM rehearsal #3 + DR drill #3 |
| 2026-Q4 (Dec) | LLM rehearsal #4 + DR drill #4 + Chaos gameday #2 |
| 2026-Aug | Multi-jurisdiction tabletop |

## Cancellation policy

Exercises MAY be deferred (not cancelled) only when:
- An active Level-3 incident is in progress, or
- Critical infrastructure (paired-region) is unavailable.

Cancellation requires Executive Leader approval; re-scheduled within 30 days.

## Trace + audit

Every exercise produces:
- A timestamped artefact in `docs/disaster-response-hub/evaluation/`.
- App Insights events with `exercise.kind`, `exercise.outcome`, `exercise.slo_breaches`.
- Lessons-capture handoff to the Resilience Planner persona.

## Related

- [Spec 030 — LLM Evaluation](../../../specs/030-llm-eval-framework/spec.md)
- [DR/BCP runbook](../../operator-runbooks/dr-bcp.md) *(spec-032 T809)*
- [Chaos quarterly workflow](../../../.github/workflows/chaos-quarterly.yml) *(spec-032 T807)*
