---
purpose: SLI/SLO model defining service level indicators, objectives, and error-budget burn-rate thresholds for all key platform services.
personas:
  - Technical-Quality
diagrams:
  - SEC-04
specs:
  - spec-015
  - spec-017
---

# SEC-04 — SLI/SLO Model

[→ Architecture index](../README.md)

<!-- spec-cross-ref: spec-015 -->
<!-- spec-cross-ref: spec-017 -->

![SEC-04 — SLI/SLO Model](./sli-slo-model.png)

## Service objectives (authoritative SLO-1 through SLO-10)

| SLO | Service | SLI definition | Target and windows | Burn/config | Evidence status |
| --- | --- | --- | --- | --- | --- |
| SLO-1 | Signal Ingestion Latency | `signal.ingestion.lag_seconds` P95 | `<= 60s`, rolling 30d | Fast burn `>14.4` (1h/5m), slow burn `>6` (6h/30m) | Catalogue-defined; alert parity UNVERIFIED |
| SLO-2 | Agent Handoff Success | success ratio across handoff totals | `>= 99.5%`, rolling 30d | Fast/slow burn plus DLQ depth escalation | Catalogue-defined; alert parity UNVERIFIED |
| SLO-3 | Alert-to-Publish Time | `alert.publish.lag_seconds` P95 | `<= 90s`, rolling 30d | P1 paging on any 15m breach | Catalogue-defined; alert parity UNVERIFIED |
| SLO-4 | Dashboard Availability | App Insights availability test success | `>= 99.9%`, rolling 30d | Location quorum failure thresholds | Catalogue-defined; alert parity UNVERIFIED |
| SLO-5 | Audit Ledger Integrity | `audit.integrity_check.failures_total` | `0 failures` | Zero budget; immediate P1 on breach | Catalogue-defined; alert parity UNVERIFIED |
| SLO-6 | LLM Cost per Incident | `llm.cost.aud_micros` by incident | Typical `<= 50 AUD`; L3 `<= 500 AUD` | 80%/100% budget guardrails | Catalogue-defined; measurement UNVERIFIED |
| SLO-7 | Kill-Switch Propagation | `agent.killswitch.lag_seconds` P99 | `<= 30s` | Breach count target `<= 1/30d` | Catalogue-defined; alert parity UNVERIFIED |
| SLO-8 | RAG Retrieval Latency | `rag.retrieval.lag_milliseconds` P95 | `<= 400ms`, rolling 30d | Burn-based degradation triggers | Catalogue-defined; alert parity UNVERIFIED |
| SLO-9 | Eval Baseline Adherence | evaluation scorecard pass/fail | `100% baseline pass` | Zero-budget release gate | Catalogue-defined; release evidence UNVERIFIED |
| SLO-10 | Public-Network Refusal | public probe success count | `100% rejected`, rolling 24h | Any success is P1 | Catalogue-defined; probe evidence UNVERIFIED |

Capacity numbers cited by these SLOs must be tagged as `configured`, `estimated`, `measured`, or `unverified` in capacity documentation.

## Error-budget policy

| Term | Definition | Measurement window | Purpose |
| --- | --- | --- | --- |
| SLI | The observed metric that represents user-relevant service behaviour | Rolling 15 min, 1 h, 6 h, and 24 h windows | Anchors alerting and reporting |
| SLO | The target threshold for each service's SLI | Monthly objective with short-window monitoring | Sets the reliability commitment |
| Error budget | The permitted gap between perfect service and the SLO target | Tracked per calendar month | Allows controlled change while protecting reliability |
| Burn rate | The speed at which the service consumes its remaining error budget | Fast-burn and slow-burn windows | Triggers proportional operational response |
