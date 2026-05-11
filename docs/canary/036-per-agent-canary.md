# Spec 036 — Per-agent canary cutover playbook (R-12)

> **Status (Phase C handover):** code is wired and CI-green for all five
> grounded agents. **The flag flips below are deferred to the deployed
> staging environment** (Step 9 of the user's external workflow). Each
> agent's playbook is identical in structure; the agent-specific
> deviations are noted in the table at §3.

This playbook drives the per-agent canary cutover required by FR-RAG-FM-06
and Risk R-12. The canary order is:

1. Monitoring → 2. Risk Assessment → 3. Evacuation → 4. Resource
Allocation → 5. Communication

Each step gates on:

* `per_agent_canary_gate.py --threshold 0.95` (decision-equivalence ≥
  95%; schema-equivalence == 100%; citation fidelity ≥ 0.7),
* a synthetic Foundry-503 fall-through drill (spec-014 fallback chain
  must still serve),
* a rollback drill (flip the flag back, assert no audit gap, no
  operator-visible silencing).

Only after staging passes for an agent does prod flip the same flag. The
Communication step has an extra ATSI/CALD/Auslan retrieval-coverage
assertion (T097, FR-RAG-AG-06).

## 1. Pre-flight checklist (run once before any flip)

```pwsh
# 1.1 Verify carve-out (must exit 0)
pwsh ./infra/scripts/verify-carveout.ps1 -CheckDeployment $env:EMBEDDING_DEPLOYMENT

# 1.2 Apply audit-record additive migration (idempotent)
pwsh ./infra/scripts/migrate-audit-record-036.ps1

# 1.3 Verify per-agent fixtures keyed against corpus build SHA
Get-Content apps/eval-runner/fixtures/spec036/*.jsonl |
  ConvertFrom-Json |
  Where-Object { $_.corpus_build_sha -ne $env:EXPECTED_CORPUS_BUILD_SHA } |
  ForEach-Object { Write-Error "fixture $($_.id) has stale corpus_build_sha"; throw }
```

## 2. The flip itself (per agent)

Replace `<AGENT>` with the canonical agent slug
(`monitoring`, `risk_assessment`, `evacuation`, `resource_allocation`,
`communication`).

```pwsh
# 2.1 Set the env var on the staging Container App.
az containerapp update \
  --name ama-prod-<region>-aca-<agent> \
  --resource-group $env:RG_STAGING \
  --set-env-vars FEATURE_FOUNDRY_RAG_<AGENT_UPPER>=1

# 2.2 Run the per-agent canary gate.
python -m ama_eval.per_agent_canary_gate \
  --agent <AGENT_UPPER>Agent \
  --fixture apps/eval-runner/fixtures/spec036/<agent>.jsonl \
  --threshold 0.95
# → exit 0 means: ≥ 95% decision-equivalence + 100% schema + ≥ 0.7 citation fidelity.

# 2.3 Synthetic Foundry-503 drill — assert spec-014 fall-through.
python -m ama_eval.synthetic_foundry_503 --agent <AGENT_UPPER>Agent

# 2.4 Rollback drill — flip back, assert no audit gap.
az containerapp update \
  --name ama-prod-<region>-aca-<agent> \
  --resource-group $env:RG_STAGING \
  --set-env-vars FEATURE_FOUNDRY_RAG_<AGENT_UPPER>=0

# 2.5 KQL sanity — verify rag_used field present on every recent inference call.
az monitor app-insights query \
  --app $env:APPI_ID \
  --analytics-query 'audit_records | where timestamp > ago(15m) | where call_kind == "inference" | summarize missing=countif(isnull(rag_used)), total=count() by agent_name | where missing > 0'
# → empty result means no audit gap.

# 2.6 Promote to prod (only after staging passes).
az containerapp update \
  --name ama-prod-<region>-aca-<agent> \
  --resource-group $env:RG_PROD \
  --set-env-vars FEATURE_FOUNDRY_RAG_<AGENT_UPPER>=1
```

## 3. Per-agent specifics

| Step | Agent | Specific assertions | Rollback time-box |
|---|---|---|---|
| T093 | Monitoring | (none) | 5 min |
| T094 | Risk Assessment | (none) | 5 min |
| T095 | Evacuation | NSW–VIC + ACT–NSW handoff fixtures pass | 5 min |
| T096 | Resource Allocation | Logistics RAG-OPTOUT marker NOT emitted | 5 min |
| T097 | Communication | ATSI/CALD/Auslan retrieval-coverage assertion (FR-RAG-AG-06) | 10 min |

## 4. Failure protocol

* If §2.2 (canary gate) fails ⇒ flip the flag back, file a ticket
  tagged `036/canary-gate`, do NOT promote to prod.
* If §2.3 (synthetic 503 drill) fails ⇒ flip back; the spec-014 fall-through
  is broken and must be fixed before any further canary.
* If §2.5 (KQL sanity) shows missing `rag_used` ⇒ flip back; the audit
  pipeline has lost rows and the spec-036 audit invariant is broken.

## 5. Where to look when something goes sideways

* Application Insights → custom event `audit_record` filtered by
  `agent_name`.
* Container Apps log stream → `FEATURE_FOUNDRY_RAG_*` env-var changes show
  up as a new revision.
* `apps/agents/common/retrieval_client.py` — quota limiter logs (R-09).
* `apps/agents/common/citation_filter.py` — hallucinated citation logs.

---

> **Phase C status:** all of §2.1, §2.2, §2.3, §2.4, §2.5 are exercised
> by stub harnesses in `tests/integration/test_*` and the canary gate
> module. Live env-var flips against a deployed environment are deferred
> to Step 9 of the external workflow; tasks T093–T097 in `tasks.md` are
> tracked as `[~]` partial until that flip lands.
