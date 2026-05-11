# Metric Alerts — Help (T-AA216)

| Alert | Metric / event | Threshold | Severity |
|---|---|---|---|
| `help.chat.first_byte.slow` | `help.chat.first_byte_ms` p95 | >4000 for 5m | Sev2 |
| `help.snapshot.publish_slow` | `help.snapshot.publish_duration_s` | >900 single event | Sev2 |
| `help.snapshot.publish_failed` | `audit.snapshot_publish_failed` | count>0/5m | Sev1 |
| `help.staleness.backlog_age` | `audit.screenshot_staleness_detected` oldest | >14d | Sev3 |
| `help.support_handoff.sla_breach` | `audit.support_handoff_unack_timeout` | count>0/5m | Sev2 |
| `help.tenant_filter.violation` | `audit.help_tenant_filter_violation` | count>0 ever | Sev1 (page) |
| `help.au_residency.violation` | `audit.help_au_residency_violation` | count>0 ever | Sev1 (page) |

## Action group
`ag-help-oncall-aue` (AU East). Primary: help-platform on-call.
Secondary: SRE on-call. Escalation: security-engineer for Sev1.

## Verification (post-deploy)
1. `az monitor metrics alert list -g <rg-help>`
2. Page-test: force a synthetic `audit.help_tenant_filter_violation` and
   confirm pager receipt within 2 minutes.
