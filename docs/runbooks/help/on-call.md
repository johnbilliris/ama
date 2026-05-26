# Help — On-call Runbook (spec-038)

> Constitution Principle III · Risks R1, R6 · CHK128

## Scope
On-call procedures for the In-Product Help docs + grounded chat assistant
(`feature/help`). Covers: chat outage, snapshot publish failure, rollback,
alias-bind issues, AI Search throttling, redaction recogniser failure.

## 1. Chat outage (`audit.chat_unavailable` / 5xx burst on `POST /help/chat/ask`)
1. Check Foundry agent `help_assistant` (AU East) health in the Azure portal.
2. Inspect App Insights workbook **help-slis** → tile "chat first-byte p95".
3. If Foundry is healthy, check AI Search index alias `help-corpus-active`
   (T-AA216 alert: `help.search.alias.broken`).
4. Switch UI into **degraded mode** by setting the feature flag
   `HELP_CHAT_DEGRADED=1` — the UI surfaces the disabled-chat banner and
   directs users to support handoff.
5. Emit `audit.help_incident_opened`; page the help-platform on-call
   secondary if first-byte p95 > 8s for >5 min.

## 2. Snapshot publish failure (`audit.snapshot_publish_failed`)
See `snapshot-publish-rollback.md` for the full procedure. Short version:
1. Inspect the latest snapshot publish or rollback activity and related audit rows.
2. Verify dual-approval gate passed (≥2 distinct approvers, ≥1
   help_content_owner, ≥1 safety_lead|governance_lead).
3. If the new index built but alias swing failed → run rollback within
   FR-011c 5-min SLO.

## 3. Rollback procedure
```pwsh
python tools/help/publish_snapshot.py rollback --restored-snapshot-id <previous_snapshot_id>
```
1. Confirm audit event `audit.snapshot_rolled_back` with prior snapshot id.
2. Verify alias `help-corpus-active` now points at the previous index.
3. Notify content owners; open follow-up ticket to triage the failed
   snapshot.

## 4. Alias-bind issues
1. `az search service list --query "[?location=='australiaeast']"` — confirm
   the Search service is online.
2. List indexes; verify the snapshot index exists in AU East only.
3. If alias points at a missing index, force-rebind:
   `python tools/help/publish_snapshot.py rollback --restored-snapshot-id <snapshot_id>`.

## 5. AI Search throttling (`429`)
1. Check Search service tier; scale up replicas in AU East (DO NOT move
   region — FR-018 / Constitution V).
2. Inspect `audit.help_search_throttled` events for tenant breakdown.
3. If a single tenant is causing the throttle, contact tenant admin to
   throttle their integrations.

## 6. Redaction recogniser failure
1. Inspect `audit.help_redaction_skipped` events.
2. If skip-rate > 0 for any tenant, the chat MUST go into degraded mode
   (chat disabled, support handoff only) per FR-017 — never silently allow
   un-redacted input.
3. Page security-engineer on-call; do not re-enable chat until the
   recogniser is validated.

## Escalation
- Help-platform on-call → SRE on-call → security-engineer on-call →
  governance lead.
- All escalations MUST emit `audit.help_incident_*` events; SLA per
  FR-023b.
