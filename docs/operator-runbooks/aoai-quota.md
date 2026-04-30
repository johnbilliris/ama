# Azure OpenAI Quota Request Path

**Purpose**: documented path to request capacity reservations + quota increases for Azure OpenAI deployments. Closes spec-032 FR-AI08 + T817.

## Current quotas (production baseline)

| Deployment | Model | TPM (Tokens / Min) | Capacity reservation |
|---|---|---:|---|
| `aoai-reasoning-prod` | gpt-4o | 60,000 | optional after 75% sustained |
| `aoai-drafting-prod` | gpt-4o-mini | 200,000 | optional after 75% sustained |
| `aoai-reasoning-canary` | (variable) | 10,000 | n/a (transient) |
| `aoai-embedding-prod` | text-embedding-3-large | 50,000 | dedicated for AI Search ingest |

## Triggers for quota increase

| Signal | Action |
|---|---|
| `llm.tokens.total` sustained > 75% of TPM for 1 h | Request quota increase |
| Cost burn-down hitting monthly budget by mid-month | Review prompts AND request increase |
| New jurisdiction onboarding (national emergency) | Pre-emptive request |

## Request path

### Path A — quota increase (no capacity reservation)

1. Open Azure Portal → Azure OpenAI → quotas blade.
2. Select the deployment + region.
3. Click "Request quota increase". Fill:
   - Region: Australia East (Australia Southeast for DR).
   - Justification: include incident SLA + operator count + rough TPM estimate.
4. Microsoft typically responds within 1 business day for AU East.

### Path B — Provisioned Throughput Units (PTU)

For sustained predictable load (≥ 100 K TPM consistently), use **Provisioned Throughput Units** instead of pay-as-you-go quota:

1. Engage Microsoft account team — PTU requires a contract amendment.
2. PTU is reserved capacity (60–80% cost reduction at high utilisation).
3. PTU per region; cannot be moved cross-region without contract change.

### Path C — emergency burst

National emergencies (Level-3 AIIMS, multi-state) may need temporary 2–3× capacity:

1. Page Microsoft enterprise support (severity A).
2. Reference the platform's life-safety mission statement (Constitution Principle I).
3. Microsoft can provision an additional deployment within 4 h for declared emergencies.

## Linkage to budget tracker

The platform's budget tracker (`apps/agents/common/llm_budget_tracker.py`, FR-P02) emits `llm.budget.warning_total` at 80% burn. When triggered:
1. Open the workbook.
2. Identify the cost-driver scope (jurisdiction / agent / model).
3. Decide: prompt optimisation, model downshift, quota increase, or PTU contract.

## Cross-references

- Spec-032 FR-AI08 (this runbook), FR-O03 (cost metrics emission), FR-D03 (cost report template).
- Constitution Non-Negotiable #2 (data sovereignty) — quotas must remain inside Australian regions for prod data.
- Foundry carve-out registry (`infra/parameters/foundry-carveout.yaml`) — non-AU model deployments require additional governance.
