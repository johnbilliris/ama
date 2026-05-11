# Runbook — Spec 036 Blue-Green AI Search Rollback

**Owner**: Platform / Site Reliability  
**Spec**: 036 (Foundry RAG Grounding) — Phase F, Cluster A7  
**FR / ADR**: FR-RAG-IDX-09; ADR-16; SC-019; Pass 2 Q-P2-08  
**SLO**: Alias re-flip ≤ 5 minutes from parity-gate failure detection.  
**On-call**: `#ama-oncall` Slack; PagerDuty service `ama-platform`.

---

## 1. When this runbook fires

Use this runbook **only** when **all** of the following are true:

1. The 4-signal **parity gate** (Spec 036 T046 / `apps/parity-gate/main.py`) has signalled failure for `corpus-vN+1`.
2. The alias `corpus` has **already flipped** to `corpus-vN+1`. (Pre-flip parity failures abort the flip — no rollback is needed; see `docs/runbooks/036-foundry-rag-prefligh-failure.md`.)
3. The active retrieval queries against `corpus-vN+1` are producing **degraded user-visible signals** (citation mismatch / recall drop / Foundry refusal). One-off failures may not need rollback.

If any of (1)–(3) is **not** met → **stop**. Page the Release Manager and triage instead.

---

## 2. Pre-conditions (verify before you act)

| # | Check | Command / Evidence |
|---|-------|--------------------|
| 1 | Previous index `corpus-vN` still exists. | `az search index list -n ai-search-ama --query "[?starts_with(name,'corpus-v')].name"` — `corpus-vN` MUST be present (R-15 retention = 7 days). |
| 2 | Audit replay confirms decisions were made against `corpus-vN+1`. | Cosmos `audit_records.retrieval_index_name == 'corpus-vN+1'` for the failure window. |
| 3 | Release Manager available and reachable. | Check `#ama-oncall`; OnCall API at `/oncall/whois?service=ama-platform`. **Pass 2 Q-P2-08: a Service Principal MUST NOT approve this rollback.** |
| 4 | Foundry chat client is healthy. | `curl https://api.ama.gov.au/healthz` returns `200`. (We do not roll back unrelated outages.) |

---

## 3. Rollback procedure

> **Note**: The `IndexRollbackOrchestrator`
> (`apps/api/app/services/index_rollback.py`) automates steps 3–6 once the
> Release Manager approval is recorded. Run it directly OR step through
> manually if the orchestrator is unavailable.

### 3.1 Open the SLO timer

```powershell
$startedAt = Get-Date -AsUTC
Write-Host "SLO budget elapses at $($startedAt.AddMinutes(5).ToString('o'))"
```

The 5-minute budget begins **now**. If you exceed it, the rollback still
proceeds — but the audit record will tag `slo_breached: true` and the
on-call review will analyse why.

### 3.2 Publish `index_rollback.requested`

The orchestrator publishes this automatically. If running manually:

```bash
az servicebus queue message send \
  --resource-group rg-ama \
  --namespace ama-bus \
  --queue index_rollback \
  --body '{"state":"requested","old":"corpus-vN+1","new":"corpus-vN","reason":"<short slug>"}'
```

### 3.3 Get Release Manager approval

Per Pass 2 Q-P2-08 (Manual operator action class):

* Page `#ama-oncall` with `!rollback corpus-vN+1 → corpus-vN reason=<slug>`.
* Wait for an Entra-authenticated human in the `ama-release-managers`
  group to ack. Capture their **UPN** (e.g. `rm-jane@ama.gov.au`); the
  audit record requires `release_manager_id`.
* **DO NOT** approve as the on-call yourself unless you are also a
  Release Manager. The orchestrator rejects same-actor approvals.

### 3.4 Flip the alias

```bash
az search alias update \
  --service-name ai-search-ama \
  --name corpus \
  --indexes corpus-vN
```

The alias flip is atomic in Azure AI Search; existing in-flight queries
that already pinned `corpus-vN+1` (per the F-A7 alias-pinning protocol)
will continue to resolve to `corpus-vN+1` until they complete.

### 3.5 Publish `index_rollback.completed`

The orchestrator does this automatically. Manually:

```bash
az servicebus queue message send \
  --queue index_rollback \
  --body '{"state":"completed","completed_at":"<ISO-8601>","release_manager_id":"<upn>"}'
```

### 3.6 Append the audit record

The `IndexRollbackOrchestrator` writes this to Cosmos `audit_records`:

```json
{
  "event_type": "index_rollback",
  "old_index_name": "corpus-vN+1",
  "new_index_name": "corpus-vN",
  "parity_gate_failure_reason": "<slug>",
  "release_manager_id": "<upn>",
  "completed_at": "<ISO-8601>",
  "elapsed_seconds": <float>,
  "slo_breached": <bool>
}
```

---

## 4. Post-rollback verification

| Check | Command | Expected |
|-------|---------|----------|
| Alias points at the rolled-back index. | `az search alias show -n corpus -s ai-search-ama --query indexes` | `["corpus-vN"]` |
| Sample audit record carries the rolled-back index. | Cosmos query: `SELECT TOP 5 c.retrieval_index_name FROM c WHERE c.timestamp_utc > '<flip_completed_at>'` | All rows = `corpus-vN`. |
| Citation parity restored. | Replay 10 golden-set queries via `apps/parity-gate/main.py replay`. | ≥99% citation match (Spec 036 T046 contract). |
| `corpus-vN+1` retained, not deleted. | `az search index show -n corpus-vN+1 -s ai-search-ama` | Returns 200 — kept for ≥7 days post-flip per R-15 (`infra/scripts/cleanup-stale-indices.ps1`). |

---

## 5. Out-of-budget (SLO breach)

If `elapsed_seconds > 300` when the rollback completes:

1. The orchestrator emits `state: slo_breach` and writes `slo_breached: true`.
2. PagerDuty raises an incident in `#ama-incidents`.
3. The on-call schedules a **post-mortem review within 7 days** with the
   Release Manager who approved.
4. Capture root cause, mitigations, and update this runbook.

---

## 6. Related runbooks & references

* `docs/runbooks/036-foundry-rag-degraded-mode.md` — the user-facing badge
  shown while rollback is in flight.
* `docs/runbooks/036-foundry-rag-prefligh-failure.md` — for parity-gate
  failures **before** the alias flip (preferred path: never flip).
* `apps/api/app/services/index_rollback.py` — orchestrator implementation.
* `infra/scripts/cleanup-stale-indices.ps1` — 7-day retention enforcer.
* `infra/modules/ai-search-blue-green.bicep` — `previousIndexRetentionDays`
  output consumed by the cleanup script.
* ADR-16 — `docs/decisions/036-foundry-rag-grounding/16-blue-green-atomicity.md`.

---

## 7. Change log

| Date | Author | Change |
|------|--------|--------|
| 2025-11-18 | Platform | T172: Initial publication (Phase F amend loop). |
