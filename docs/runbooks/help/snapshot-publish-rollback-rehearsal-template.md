# Help snapshot publish + rollback rehearsal — runbook

**Spec:** spec-038 / T-AA173
**SLO:** alias swing ≤ 5 min (FR-011c).

## Pre-flight
1. Ensure dev environment has all spec-038 Bicep modules deployed:
   ```pwsh
   az bicep build --file infra/main.bicep --outdir specs/038-help-docs-chat/build
   ```
2. Confirm AI Search admin key is in your shell.

## Publish rehearsal
```pwsh
python tools/help/publish_snapshot.py publish `
  --manifest apps/ingest-runner/manifests/help-snapshot.yaml `
  --approver alice@ama.gov.au=help_content_owner `
  --approver bob@ama.gov.au=safety_lead `
  --dry-run
```
Verify:
- new index `help-corpus-{snapshot_id}` created
- alias `help-corpus-active` re-bound atomically
- audit event `audit.snapshot_published` emitted (check App Insights)

## Rollback rehearsal
```pwsh
python tools/help/publish_snapshot.py rollback `
  --restored-snapshot-id <previous-snapshot-id>
```
Verify ≤5 min total elapsed (FR-011c).

## Sign-off
| Date | Operator | Outcome | Elapsed (mm:ss) |
| --- | --- | --- | --- |
| 2026-…-… | (TBD) | (TBD) | (TBD) |
