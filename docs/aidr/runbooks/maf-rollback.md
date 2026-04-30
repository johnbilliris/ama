# MAF Rollback Runbook (T070, FR-026)

Per-agent reversible. To roll back a single agent mid-incident, flip the agent feature flag back to `legacy` and the next workflow run that touches that step dispatches to the legacy pipeline.

## When to roll back

- Equivalence harness regression detected post-cutover (categorical drift > 5%).
- Agent-failure rate spike (App Insights alert "agent.outcome=failed > 1% over 5 min").
- New content-safety incident (Constitution V violation surface) — roll back IMMEDIATELY.

## Step-by-step

```bash
az containerapp update --name ca-agents-drh-<env> --resource-group rg-drh-<env> --set-env-vars FEATURE_MAF_RUNTIME_<AGENT>=legacy
```

Wait ~30s for new revision to take traffic.

## Operator-visible signals during rollback

- App Insights "Agent runs" panel: sharp drop in MAF traffic for `ai.agent.name`, corresponding rise in legacy.
- `audit_entries` stream: `agent_version="legacy-..."` records reappear.
- Operator dashboard `/operations/workflows` continues normal lifecycle states (rollback is invisible to consumers).

## Time-to-recovery target

< 5 minutes wall-clock from decision to flag-flip completion. Container Apps revision activation ~30s; the rest is administrative.

## Post-rollback follow-up

1. Open P1 ticket capturing rollback reason + offending traffic sample.
2. `pytest tests/equivalence/test_<agent>_equivalence.py -q` against the offending fixtures.
3. Land fix on `033-maf-adoption` (or follow-up branch); re-run cutover from Phase A (shadow).

## Operator authority

Non-prod: any operator in `EmergencyOperator` Entra group. **Production**: requires on-call SRE co-sign.
