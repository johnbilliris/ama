# Cost Reporting Template

**Purpose**: monthly cost rollup tied to the LLM budget tracker output. Closes spec-032 FR-D03 + T812.

## Source data

- **Azure Cost Management export** (subscription-scoped, daily granularity).
- **Application Insights customMetrics** `llm.cost.aud_micros` (per-scope, per-incident granularity).
- **Cosmos `llm_budgets` container** (per-month rollup per scope; FR-P02).

## Report sections

### Section 1 — Headline

| Metric | Value | vs. last month | Notes |
|---|---:|---:|---|
| Total Azure spend (AUD) | ${total} | ${delta_pct}% | All resource groups in scope. |
| LLM-only spend (AUD) | ${llm_total} | ${llm_delta}% | From `llm.cost.aud_micros`. |
| LLM share of total | ${llm_pct}% | — | Trend metric. |
| Recommendations created | ${rec_count} | ${rec_delta}% | Cost denominator. |
| LLM cost / recommendation | ${llm_per_rec} | ${unit_delta}% | Efficiency metric. |

### Section 2 — Breakdown by service

| Service | AUD | % of total |
|---|---:|---:|
| Azure OpenAI | ${aoai_aud} | ${aoai_pct}% |
| Cosmos DB | ${cosmos_aud} | ${cosmos_pct}% |
| Container Apps | ${ca_aud} | ${ca_pct}% |
| Azure AI Search | ${search_aud} | ${search_pct}% |
| Application Insights / Log Analytics | ${ai_aud} | ${ai_pct}% |
| Service Bus + Event Hubs | ${msg_aud} | ${msg_pct}% |
| Storage | ${storage_aud} | ${storage_pct}% |
| Other | ${other_aud} | ${other_pct}% |

### Section 3 — LLM scope analysis

| Scope (jurisdiction / global) | AUD | Recommendations | AUD/rec | Budget burn |
|---|---:|---:|---:|---:|
| `global` | ... | ... | ... | ${pct}% |
| `jurisdiction:nsw` | ... | ... | ... | ${pct}% |
| `jurisdiction:vic` | ... | ... | ... | ${pct}% |
| ... | | | | |

(Drawn from the `llm_budgets` Cosmos container and the LLM-cost workbook.)

### Section 4 — Variance + actions

- Top 3 cost drivers vs. last month.
- Any scopes that hit > 80% budget burn (triggered `llm.budget.warning_total` events).
- Any quota-increase requests in flight (linked to the AOAI quota runbook).
- Any planned mitigations (prompt optimisation, model downshift, PTU evaluation).

### Section 5 — Forecast

- 30-day forward projection based on rolling 30-day baseline.
- Probability of breaching the published monthly budget (per scope).
- Recommended actions if forecast > 100%.

## Generation

A first version is hand-authored each month using the workbook + `az consumption usage list`. Future enhancement (post spec-032): a daily aggregator (`scripts/cost_report_publish.py`) emits `cost.report.{section}.aud_total` customMetrics so the monthly report can be auto-rendered from a workbook.

## Distribution

- Monday-after-month-end: Executive Leader + Finance + SRE + AI/ML lead.
- Stored under `docs/disaster-response-hub/cost-reports/cost-report-{YYYY-MM}.md`.

## Cross-references

- Spec-032 FR-D03 (this runbook), FR-O03 (cost metrics emission), FR-P02 (budget tracker), FR-AI08 (quota path).
- Workbook: LLM cost burn-down (T509).
- Capacity model (`docs/architecture/capacity-model.md`).
