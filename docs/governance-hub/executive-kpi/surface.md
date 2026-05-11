# Executive KPI Surface (spec-037 artefact 3)

- Publication: `ed610bc5-e39e-5a1e-8ea5-3a41c9558848`
- Published: 2026-05-11T17:30:00Z
- Manual-row ratio: 1.00
- Auditor sign-off: Capstone Evidence Pack v1 Author

## Capstone-criterion KPI ladder

Each of the five capstone success criteria carries ≥1 leading + ≥1 lagging KPI
(FR-019 + FR-020). Source-of-truth links point at App Insights metric names or
governance-hub Markdown files.

| KPI ID | Criterion | Kind | Name | Owner | Target | Threshold (G/A/R) | Source of truth |
|---|---|---|---|---|---|---|---|
| `KPI-CAP-001` | lives-saved | leading | Triage signals processed per day | Risk Manager | 1000 signals/day | >=1000 / 500-999 / <500 | `appinsights://customMetrics/triage_signals_daily` |
| `KPI-CAP-002` | lives-saved | lagging | Lives preserved (counterfactual model) | Executive Leader | 1000 lives/year | >=1000 / 500-999 / <500 | `docs/governance-hub/executive-kpi/surface.md` |
| `KPI-CAP-003` | response-time | leading | Signal-to-alert end-to-end latency p95 | Operations Officer | 60 seconds | <=60 / 61-120 / >120 | `appinsights://customMetrics/signal_to_alert_p95` |
| `KPI-CAP-004` | response-time | lagging | Coordinated-response time uplift vs. baseline | Executive Leader | 50 % | >=50 / 30-49 / <30 | `specs/shared/capstone-metric-trace.md` |
| `KPI-CAP-005` | evacuation-lead-time | leading | Evacuation recommendation latency | Planning Officer | 30 minutes | <=30 / 31-60 / >60 | `appinsights://customMetrics/evac_recommend_latency_p95` |
| `KPI-CAP-006` | evacuation-lead-time | lagging | Mean warning-to-evac timeline uplift | Executive Leader | 24 hours | >=24 / 12-23 / <12 | `specs/shared/capstone-metric-trace.md` |
| `KPI-CAP-007` | logistics-efficiency | leading | Resource fill-rate within 1 hour | Logistics Officer | 95 % | >=95 / 85-94 / <85 | `appinsights://customMetrics/resource_fill_rate_1h` |
| `KPI-CAP-008` | logistics-efficiency | lagging | Logistics throughput uplift vs. baseline | Executive Leader | 30 % | >=30 / 15-29 / <15 | `specs/shared/capstone-metric-trace.md` |
| `KPI-CAP-009` | economic-loss-reduction | leading | Risk-index forecast confidence band width | Risk Manager | 0.2 confidence interval | <=0.20 / 0.21-0.35 / >0.35 | `appinsights://customMetrics/risk_index_ci_width` |
| `KPI-CAP-010` | economic-loss-reduction | lagging | Sendai-aligned modelled loss reduction | Executive Leader | 30 % | >=30 / 15-29 / <15 | `specs/shared/capstone-metric-trace.md` |

## Superseded surfaces (FR-022, section-scoped)

- docs/governance-dashboard.md (executive-roll-up only)
- docs/governance-hub/observability/slo.md (executive-roll-up only)
- docs/governance-hub/observability/metrics-catalogue.md (executive-roll-up only)