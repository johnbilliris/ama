# MAF Cutover Playbook (T069, spec 033)

This playbook is the operator runbook for cutting one or more of the five named MAF agents from the legacy pipeline to the MAF runtime. Cutover is **incremental** (FR-022) and **per-agent reversible** (FR-026).

## Per-environment, per-agent cutover (the canonical sequence)

For each agent in order — Monitoring → Risk → Evacuation → Resource → Communication — and for each environment (dev → staging → production):

### Pre-flight

1. Confirm the equivalence harness PASSes for the target agent: `pytest tests/equivalence/test_<agent>_equivalence.py -q`. Attach the latest report from `apps/agents/maf_runtime/equivalence/reports/<agent>-*.md` to the cutover PR description (cutover gate per FR-023).
2. Confirm SC-007 latency benchmark in the **previous** environment was within the ≤10% regression bar. Inspect `tests/load/results/maf-<env>-*.json`.
3. Confirm the spec 029 progressive-delivery flag-flip mechanism is healthy.

### Phase A — Shadow (24 hours minimum)

```bash
az containerapp update --name ca-agents-drh-<env> --resource-group rg-drh-<env> --set-env-vars FEATURE_MAF_RUNTIME_<AGENT>=shadow
```

Monitor: `apps/agents/maf_runtime/equivalence/reports/shadow/<agent>.jsonl`, App Insights "Agent runs" panel filtered by `ai.agent.name=<agent>`, reconciliation.gap metric must remain at 0. If divergence > 5% on categorical OR > 0% on populated fields, **halt cutover**.

### Phase B — Cutover

```bash
az containerapp update --name ca-agents-drh-<env> --resource-group rg-drh-<env> --set-env-vars FEATURE_MAF_RUNTIME_<AGENT>=maf
```

### Phase C — Production prerequisites

For `production` only: FR-012b load test MUST have passed in `staging` within last 7 days; T047 NN-1 invariant MUST be green on main; cutover PR MUST be co-signed by on-call SRE + platform lead.

## Rollback

See `docs/aidr/runbooks/maf-rollback.md`.
