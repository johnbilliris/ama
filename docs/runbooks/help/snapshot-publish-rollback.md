# Snapshot Publish + Rollback Runbook (spec-038 FR-011a / FR-011b / FR-011c)

## Prerequisites
- Branch main, latest pulled.
- Two distinct approvers signed off the snapshot publish:
  - >=1 with role help_content_owner
  - >=1 with role safety_lead OR governance_lead
- AU residency attestation (	ools/help/au_residency_attestation.py) green.

## Publish
1. Run:
   `pwsh
   python tools/help/publish_snapshot.py publish
     --manifest apps/ingest-runner/manifests/help-snapshot.yaml
     --snapshot-id <snapshot_id>
     --approver <help_content_owner_identity>=help_content_owner
     --approver <safety_or_governance_identity>=safety_lead
   `
2. The command runs:
   - dual-approval validation,
   - python -m help_snapshot --manifest ... --snapshot-id ...,
   - alias swing on help-corpus-active.
3. Verify udit.snapshot_published row in chat_audit_log carries:
   snapshot_id, index_name, both approver IDs, ISO published_at.
4. Acceptance: chat first-byte p95 stable; no udit.snapshot_publish_failed
   events in the next 30 min.

## Rollback (FR-011c - 5 min SLO)
1. Run:
   `pwsh
   python tools/help/publish_snapshot.py rollback --restored-snapshot-id <previous_snapshot_id>
   `
2. Audit verification:
   - udit.snapshot_rolled_back emitted with rom, 	o snapshot ids.
   - help-corpus-active alias re-bound (verify via Search REST API).
3. SLO check: time between udit.snapshot_rollback_initiated and
   udit.snapshot_rolled_back <= 5 min.

## Failure modes
- Dual approval missing -> publish command exits non-zero before any index build.
- Index build green but alias bind fails -> automatic rollback to prior
  snapshot triggered by publish_snapshot.py.
- Quota / region drift -> publish HALTS; emit udit.help_au_residency_violation
  and page security on-call.
