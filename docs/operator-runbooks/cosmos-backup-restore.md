# Cosmos DB Backup + Restore Runbook

**Purpose**: point-in-time restore of the production Cosmos account using continuous-backup mode (7-day window). Closes spec-032 FR-D04 + T810.

## Backup mode

- Production runs **Continuous (7-day) backup mode** (set in `infra/main.bicep` per FR-D04 / T808).
- No manual backup snapshots are required — every write is captured continuously.
- 7-day retention is the default for continuous mode; 30-day mode available if business requires (review with Compliance Auditor).

## Restore scenarios

### Scenario A — accidental data deletion (single container)

A test or operator has accidentally deleted documents from a single container.

```pwsh
$RG = "rg-drh-production"
$ACCT = "cdb-drh-production"
$RESTORE_TS = "2026-04-30T03:15:00Z"   # UTC; just before the deletion

# Restore the entire account into a NEW account (Cosmos PITR semantics).
az cosmosdb restore `
  --target-database-account-name "${ACCT}-restore" `
  --account-name $ACCT `
  --resource-group $RG `
  --restore-timestamp $RESTORE_TS `
  --location "australiaeast"
```

Then copy the affected documents from the restored account back into prod:

```pwsh
# Use Cosmos Data Migration Tool or a small Python script
python scripts/cosmos_copy_documents.py `
  --source-account "${ACCT}-restore" `
  --target-account $ACCT `
  --container <container-name> `
  --query "SELECT * FROM c WHERE c.deleted_at >= '$RESTORE_TS'"
```

Audit log entry: `cosmos.restore.partial` with operator + scope + count.

### Scenario B — full account corruption

Restore the entire account, fail over the application:

1. Restore via `az cosmosdb restore` (as above; ~30 min).
2. Update Container Apps environment variables to point to the restored endpoint (`COSMOS_ENDPOINT`).
3. Smoke test (DR runbook § 6).
4. Once verified, decommission the corrupted account.

### Scenario C — cross-region restore

If Australia East is unavailable, restore into Australia Southeast:

```pwsh
az cosmosdb restore `
  --target-database-account-name "${ACCT}-restore" `
  --account-name $ACCT `
  --resource-group $RG `
  --restore-timestamp $RESTORE_TS `
  --location "australiasoutheast"
```

## Restore validation

After every restore:
- Verify document count per container matches expected baseline.
- Run the audit-integrity job (`/api/health/audit-integrity`) — must return `ok=true`.
- Replay one stored ScenarioRun and verify the timeline reconstruction matches.
- Update `CHANGELOG.md` + a post-incident issue.

## Limitations

- **Cosmos PITR is account-wide.** Cannot restore an individual container in place; restored account is a full copy.
- **Restore latency**: typically 15–30 min for accounts < 100 GB; longer for larger accounts.
- **Throughput cost**: restored account starts with the same provisioned RU/s as the source (autoscale max preserved).

## Cross-references

- Spec-032 FR-D04, T808 (PITR enablement), T810 (this runbook).
- DR/BCP runbook (`dr-bcp.md`) — invoked when restore is part of a regional failover.
- Audit integrity check (`/api/health/audit-integrity`) — runs after every restore.
