# DR / BCP Runbook — Disaster Response Coordination Hub

**Purpose**: step-by-step procedures for regional failover from Australia East to Australia Southeast.
**Targets**: RPO ≤ 15 minutes · RTO ≤ 60 minutes (spec-032 FR-D01).
**Owner**: Infrastructure/DevOps + SRE personas.

## When to invoke

| Trigger | Action |
|---|---|
| Azure Service Health "Australia East" outage notification | Wait 15 min for self-healing; if no improvement → declare DR |
| App Insights availability tests fail in 5/5 locations for ≥ 10 min | Declare DR |
| Cosmos primary-region read failures > 5% sustained 10 min | Declare DR |
| Verified data corruption in audit ledger (integrity check fails) | Declare DR + page Observer-Auditor |

**Authority**: Executive Leader OR Incident Commander OR SRE on-call may declare DR. Recorded in audit log.

## RPO / RTO measurement

- **RPO** is measured as the timestamp of the latest write committed to the paired region vs. the moment the primary went unhealthy. Target: ≤ 15 minutes.
- **RTO** is measured from "DR declared" to "first successful operator workflow completion in secondary region." Target: ≤ 60 minutes.
- Both metrics are captured by `dr-drill.yml` workflow during quarterly drills (per FR-R05 + exercise schedule).

## Failover procedure

### 1. Confirm primary unhealthy

```pwsh
$apiUrl = "https://api.disaster-response-hub.example/api/health"
Invoke-WebRequest $apiUrl -TimeoutSec 30
# Expected: 200 OK in healthy state; HTTPException / timeout in DR scenarios
```

### 2. Notify stakeholders

- Page Incident Commander + Executive Leader via Action Group (P1).
- Email Observer-Auditor that DR-declared timestamp is now in the audit ledger.
- Post in the operator coordination channel.

### 3. Trigger Cosmos failover

```pwsh
$RG = "rg-drh-production"
$COSMOS = "cdb-drh-production"
az cosmosdb failover-priority-change `
  --name $COSMOS `
  --resource-group $RG `
  --failover-policies "australiasoutheast=0" "australiaeast=1"
```

**Expected duration**: 5–15 minutes for Cosmos automatic failover (single-region writes default).

### 4. Verify Container Apps healthy in paired region

Container Apps revisions are pre-warmed to 1 replica in Australia Southeast. Verify:

```pwsh
az containerapp list `
  --resource-group $RG-southeast `
  --query "[].{name:name,fqdn:properties.configuration.ingress.fqdn,replicas:properties.template.scale.minReplicas}" `
  --output table
```

### 5. Update Front Door / DNS

Front Door automatically detects backend health. Manually force traffic if needed:

```pwsh
az afd endpoint update `
  --resource-group $RG-shared `
  --profile-name afd-drh `
  --endpoint-name drh-public `
  --enabled-state Enabled
```

### 6. Smoke test critical paths

- `GET /api/health` returns 200.
- Operator can log in (Entra federated identity).
- A test signal ingestion succeeds.
- A test recommendation is produced.
- Audit ledger integrity check returns OK.

### 7. Notify operators

- Banner on dashboard: "Operating in Australia Southeast (DR mode). Some features may be degraded."
- Audit log entry: `dr.failover.completed` with operator + RTO measurement.

## Fail-back procedure

Once Australia East is restored AND Cosmos has caught up (paired-region replication lag < 1 min):

```pwsh
# Re-prioritise Cosmos to Australia East primary
az cosmosdb failover-priority-change `
  --name $COSMOS `
  --resource-group $RG `
  --failover-policies "australiaeast=0" "australiasoutheast=1"
```

Allow 15 min for replication to fully sync. Monitor:
- `recommendation.created_total` rate matches pre-DR baseline.
- Audit integrity check passes from primary region.
- App Insights availability tests green in 5/5 locations.

Audit log entry: `dr.failback.completed`.

## Post-DR review

Within 5 business days:
1. Author an after-action review under `docs/disaster-response-hub/evaluation/dr-{YYYY-MM-DD}.md`.
2. Update lessons-capture entries via the lessons agent.
3. Re-run quarterly DR drill on schedule (per exercise schedule).
4. If RPO or RTO exceeded, raise a P1 issue and propose mitigations.

## Cross-references

- Constitution Non-Negotiable #2 (Data sovereignty) — paired region Australia Southeast inside AU.
- Spec-032 FR-D01 (DR runbook), FR-D04 (Cosmos PITR), FR-R05 (chaos drills).
- `dr-drill.yml` GitHub Actions workflow (T818).
- Capacity model `docs/architecture/capacity-model.md` (T804).
- Cosmos backup/restore runbook `docs/operator-runbooks/cosmos-backup-restore.md` (T810).
