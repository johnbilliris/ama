# Snapshot Publish + Rollback Runbook (spec-038 FR-011a / FR-011b / FR-011c)

## Prerequisites
- Branch `main`, latest pulled.
- Two distinct approvers signed off the snapshot PR:
  - ≥1 with role `help_content_owner`
  - ≥1 with role `safety_lead` OR `governance_lead`
- AU residency attestation (`tools/help/au_residency_attestation.py`) green.

## Publish
1. Trigger workflow `.github/workflows/help-snapshot.yml` via
   `workflow_dispatch` with `snapshot_id` (UTC date, e.g. `2026-05-12`).
2. Workflow runs:
   - dual-approval verifier (`tests/contract/help/test_codeowners_dual_approval.py`),
   - `python -m help_snapshot.index_builder`,
   - `python tools/help/publish_snapshot.py --snapshot-id <id>`,
   - alias swing on `help-corpus-active`.
3. Verify `audit.snapshot_published` row in `chat_audit_log` carries:
   `snapshot_id`, `index_name`, both approver IDs, ISO published_at.
4. Acceptance: chat first-byte p95 stable; no `audit.snapshot_publish_failed`
   events in the next 30 min.

## Rollback (FR-011c — 5 min SLO)
1. Trigger workflow with `rollback: true` and `to: <previous_snapshot_id>`.
2. CLI fallback:
   ```pwsh
   python tools/help/publish_snapshot.py --rollback --to <previous_snapshot_id>
   ```
3. Audit verification:
   - `audit.snapshot_rolled_back` emitted with `from`, `to` snapshot ids.
   - `help-corpus-active` alias re-bound (verify via Search REST API).
4. SLO check: time between `audit.snapshot_rollback_initiated` and
   `audit.snapshot_rolled_back` ≤ 5 min.

## Failure modes
- Dual approval missing → workflow exits non-zero before any index build.
- Index build green but alias bind fails → automatic rollback to prior
  snapshot triggered by `publish_snapshot.py`.
- Quota / region drift → publish HALTS; emit `audit.help_au_residency_violation`
  and page security on-call.
