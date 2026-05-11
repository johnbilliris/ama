# Help SLIs — App Insights Workbook (SC-007)

> Provisioning instructions for the `help-slis` workbook pinned to SRE
> dashboards. Operator step at deploy time.

## Tiles
1. **Chat first-byte p95** (target ≤ 4s) — `customMetrics` table where
   `name == "help.chat.first_byte_ms"`.
2. **Chat answer-completion p95** (target ≤ 12s) — `name == "help.chat.complete_ms"`.
3. **Snapshot publish duration** — `name == "help.snapshot.publish_duration_s"`.
4. **Staleness backlog age** — `customEvents` where
   `name == "audit.screenshot_staleness_detected"` aggregated by route_id.
5. **Support handoff SLA breach count** — `customEvents` where
   `name == "audit.support_handoff_unack_timeout"`.
6. **Tenant filter mismatches (must be 0)** — `customEvents` where
   `name == "audit.help_tenant_filter_violation"`.

## Workbook JSON
A minimal workbook JSON is available at
`infra/workbooks/help-slis.workbook.json` (created at deploy step).

## Alert wiring
See `T-AA216` runbook — alerts wired to action group
`ag-help-oncall-aue` in Australia East.
