# Service Level Objectives (SLO) Catalogue

**Purpose**: published SLI + objective + error budget per FR-O06. Drives Action Group routing (FR-O09) and Workbook tiles (FR-O04).

> **Convention**: `<sli>` is the metric name from `metrics-catalogue.md`. `<objective>` is the target. `<error_budget>` is computed from objective × evaluation window. `<paging>` references the severity tier.

## Severity tiers (FR-O09)

| Tier | Description | Notification |
|---|---|---|
| **P1** | Life-safety capability degraded; public alerts blocked OR audit ledger broken | PagerDuty critical + email + webhook |
| **P2** | Operator-facing capability degraded; recommendations slow OR coverage gap | PagerDuty high + email |
| **P3** | Non-blocking degradation; cost overrun OR shadow drift | Email only |
| **P4** | Capacity warning (70% of budget) | Slack channel |
| **P5** | Informational; tracking | Logs only |

## SLOs

### SLO-1 — Signal Ingestion Latency

| Field | Value |
|---|---|
| Description | Time from signal arrival at ingestion to persistence in Cosmos. |
| SLI | `signal.ingestion.lag_seconds` (histogram) |
| Objective | P95 ≤ 60 s over rolling 30 d |
| Error budget | 36 h / 30 d (1.2 h / day) |
| Paging | P2 if budget burns >50% in 24 h; P1 if budget exhausted |

### SLO-2 — Agent Handoff Success Rate

| Field | Value |
|---|---|
| Description | Successful handoffs / total handoffs across all agent pairs. |
| SLI | `agent.handoff.success_total` ÷ (`agent.handoff.success_total` + `agent.handoff.failure_total`) |
| Objective | ≥ 99.5% over rolling 30 d |
| Error budget | 0.5% (~3.6 h of full failure equivalent / 30 d) |
| Paging | P2 if budget burns >50% in 24 h; P1 if dead-letter depth ≥ 100 in any single queue |

### SLO-3 — Alert-to-Publish Time

| Field | Value |
|---|---|
| Description | Time from operator approval to first channel delivery (SMS/push/social). |
| SLI | `alert.publish.lag_seconds` (histogram) |
| Objective | P95 ≤ 90 s over rolling 30 d |
| Error budget | 36 h / 30 d |
| Paging | **P1** (life-safety) if P95 > 90 s for any 15-min window |

### SLO-4 — Dashboard Availability

| Field | Value |
|---|---|
| Description | App Insights availability tests for the public dashboard URL. |
| SLI | Availability test success rate |
| Objective | ≥ 99.9% over rolling 30 d (≤ 43 min downtime / 30 d) |
| Error budget | 43 min / 30 d |
| Paging | P2 if 3/5 locations failing for 10 min; P1 if 5/5 locations failing for 5 min |

### SLO-5 — Audit Ledger Integrity

| Field | Value |
|---|---|
| Description | Audit segment chain integrity check (FR-O5 + US1). |
| SLI | `audit.integrity_check.failures_total` |
| Objective | 0 failures per check |
| Error budget | 0 |
| Paging | **P1** on any failure (publication block + Observer-Auditor page) |

### SLO-6 — LLM Cost per Incident

| Field | Value |
|---|---|
| Description | Cumulative LLM cost (AUD) per incident envelope. |
| SLI | `llm.cost.aud_micros` aggregated by `incident_id` |
| Objective | ≤ AUD 50 per typical incident; ≤ AUD 500 per Level-3 incident |
| Error budget | n/a (cost guardrail) |
| Paging | P3 if any incident exceeds 80% of bucket; P2 at 100% |

### SLO-7 — Kill-Switch Propagation

| Field | Value |
|---|---|
| Description | Operator toggle → all agents drained. |
| SLI | `agent.killswitch.lag_seconds` (histogram) |
| Objective | P99 ≤ 30 s |
| Error budget | (counter of breaches per 30 d, target ≤ 1) |
| Paging | P2 on any breach; P1 if breached during declared incident |

### SLO-8 — RAG Retrieval Latency

| Field | Value |
|---|---|
| Description | Retrieval latency added to total recommendation latency. |
| SLI | `rag.retrieval.lag_milliseconds` (histogram) |
| Objective | P95 ≤ 400 ms over rolling 30 d |
| Error budget | (counter of breaches; target ≤ 100 / 30 d) |
| Paging | P3 on burn; P2 if continuously degraded > 30 min |

### SLO-9 — Eval Baseline Adherence

| Field | Value |
|---|---|
| Description | CI gate fails any below-baseline metric. |
| SLI | Eval scorecard pass/fail (per dataset version) |
| Objective | 100% pass for all metrics ≥ baseline |
| Error budget | 0 (it's a gate) |
| Paging | P2 on PR fail; P3 on baseline drift detection |

### SLO-10 — Public-Network Refusal (Production)

| Field | Value |
|---|---|
| Description | Probes from public IPs to data planes MUST be rejected. |
| SLI | Public-network probe success count |
| Objective | 100% rejection over rolling 24 h |
| Error budget | 0 |
| Paging | **P1** on any probe success (data exfiltration risk) |

## Burn-rate alerts

For SLOs with non-zero error budgets, multi-window burn-rate alerts:

| Alert | Window 1 | Window 2 | Trigger |
|---|---|---|---|
| Fast burn | 1 h | 5 m | Burn rate > 14.4 (consumes 100% in 50 min) |
| Slow burn | 6 h | 30 m | Burn rate > 6 (consumes 100% in 5 d) |

## Review cadence

Quarterly by SRE Engineer + Solution Architect. Any SLO objective change requires an ADR.
