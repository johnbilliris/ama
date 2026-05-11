# Chaos Drill — Snapshot Rollback (R6 · FR-011c)

Quarterly drill. Validates the 5-minute rollback SLO.

## Scenario
While a snapshot publish is in-flight, kill the alias-bind step
(simulated by setting a Search-service ACL deny on the alias for 60s).

## Drill steps
1. Pick a non-prod environment in AU East.
2. Trigger `help-snapshot.yml` workflow with `snapshot_id=YYYY-MM-DD-drill`.
3. At "swing alias" step, run:
   ```pwsh
   az search service update --resource-group <rg> --name <search> --disable-local-auth true
   ```
4. Confirm `audit.snapshot_publish_failed` emitted.
5. Initiate rollback:
   ```pwsh
   python tools/help/publish_snapshot.py --rollback --to <prev>
   ```
6. Re-enable auth:
   ```pwsh
   az search service update --resource-group <rg> --name <search> --disable-local-auth false
   ```
7. Confirm `audit.snapshot_rolled_back` within 5 min of step 4.

## Pass criteria
- Rollback completed within FR-011c 5-min SLO.
- `help-corpus-active` alias rebound to prior snapshot.
- No tenant-visible chat outage during drill (chat falls back to prior
  index automatically).
- Drill outcome logged in `audit.help_chaos_drill_executed`.

## Cadence
Quarterly. Owner: SRE + chaos-engineer personas.
