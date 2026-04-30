# Model Rollback Runbook

**Purpose**: flip the Azure OpenAI deployment alias to revert to a known-good model after a regression. Closes spec-032 FR-AI07 + T811.

## When to rollback

| Trigger | Source |
|---|---|
| Eval-baseline gate fails on `production` deploy | `eval-pr-gate.yml` workflow |
| Live error rate from `llm.fallback_step_total` exceeds 25% in 30 min | App Insights alert |
| Operator reports incoherent / unsafe recommendations | Manual escalation |
| Content Safety blocks > 5% of outputs in 1 h | App Insights alert |

## Deployment alias model

The platform uses **named aliases** on Azure OpenAI deployments so application code references aliases (not raw model versions):

| Alias | Underlying deployment | Notes |
|---|---|---|
| `aoai-reasoning-prod` | e.g. `gpt-4o-2024-11-20` | reasoning agent path |
| `aoai-drafting-prod` | e.g. `gpt-4o-mini-2024-10-25` | drafting agent path |
| `aoai-reasoning-canary` | a candidate version under evaluation | canary deployment |

Every recommendation records both `deployment_alias` AND `model_version` (per data-model.md E-01 + FR-AI02), so the operator can prove which model produced an output.

## Rollback procedure

### 1. Identify the previous-known-good version

```pwsh
$AOAI = "aoai-drh-production"
$RG = "rg-drh-production"

# List historical deployments
az cognitiveservices account deployment list `
  --resource-group $RG `
  --name $AOAI `
  --output table
```

Pick the most recent version that passed eval baselines.

### 2. Repoint the alias

```pwsh
$ALIAS = "aoai-reasoning-prod"
$KNOWN_GOOD_VERSION = "gpt-4o-2024-08-06"

# Re-create the deployment under the same alias name pointing at the older version.
# (Azure OpenAI does not support in-place model swap — the deployment must be
# recreated, but because application code references the alias, no app redeploy is needed.)
az cognitiveservices account deployment delete `
  --resource-group $RG `
  --name $AOAI `
  --deployment-name $ALIAS

az cognitiveservices account deployment create `
  --resource-group $RG `
  --name $AOAI `
  --deployment-name $ALIAS `
  --model-name "gpt-4o" `
  --model-version $KNOWN_GOOD_VERSION `
  --model-format OpenAI `
  --sku-capacity 30 `
  --sku-name Standard
```

### 3. Verify

- New recommendations record `model_version: gpt-4o-2024-08-06` in their provenance fields (FR-AI02).
- `llm.fallback_step_total` rate returns to baseline within 5 min.
- Eval harness smoke run (`pytest tests/eval -q --subset smoke-100`) passes.

### 4. Audit log

The rollback writes the following events:
- `aoai.deployment.deleted` (alias, previous-version, operator)
- `aoai.deployment.created` (alias, new-version, operator)
- `aoai.alias.flipped` (alias, from → to, operator, reason)

These events are queryable via `/api/timeline?event=aoai.alias.flipped`.

### 5. Post-rollback follow-up

- Open a P1 issue tagged `model-regression`.
- Annotate the Workbook with the rollback timestamp.
- Schedule a retro within 5 business days; capture root cause + remediation.
- Update the eval baseline ONLY after root cause is understood + a fix lands.

## Forward path (canary)

After fixing the regression, repeat:
1. Deploy the candidate as `aoai-reasoning-canary`.
2. Run eval baseline + a 24 h shadow comparison.
3. If green, swap the production alias.

## Cross-references

- Spec-032 FR-AI07 (this runbook), FR-AI10 (canary deployment workflow), FR-AI09 (cosign-verified prompts).
- Workbook: LLM cost / agent flow.
- Spec-030 LLM eval framework — baseline gates.
- ADR-036 — Azure AI Search RAG (separate path; not affected by model rollback unless the prompt also changes).
