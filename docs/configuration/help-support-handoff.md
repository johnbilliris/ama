# Help — Support Handoff Configuration (spec-038)

> FR-023a · FR-023a-AMEND · FR-023b · CHK122–CHK125

Each tenant configures a `SupportHandoffRecord` describing how the Help
surface escalates to human support. The record is partitioned by
`/tenant_id` in Cosmos.

## Fields
| Field | Type | Notes |
|---|---|---|
| `id` | string | uuid |
| `tenant_id` | string | partition key |
| `channel_kind` | enum | `email` · `shared_mailbox` · `on_call_rotation` · `chat_link` |
| `address` | string | non-empty, channel-specific (mailto:, URL, etc.) |
| `business_hours_window` | string | e.g. `"Mon-Fri 08:00-18:00 AEST"`, default `"24x7"` |
| `incident_mode_channel` | nested record | optional override during incident |
| `auto_activate_on_nema_level3` | bool | default `true` |
| `manual_override_active` | bool | tenant-admin toggle |
| `sla_routine_business_hours` | int | default `4` (hours) |
| `sla_incident_minutes` | int | default `5` (minutes) |

## SLA semantics (FR-023b)
- **Routine mode**: ack within `sla_routine_business_hours` business hours.
- **Incident mode**: ack within `sla_incident_minutes` minutes.
- Breach emits `audit.support_handoff_unack_timeout`.

## Incident-mode activation (FR-023a-AMEND)
- Auto-activates when NEMA banner reaches Level 3 and
  `auto_activate_on_nema_level3=true`.
- Manual toggle: tenant admin POSTs to `/api/help/support-handoff/{id}`.

## Validation
- `address` must be non-empty.
- `incident_mode_channel.tenant_id` must equal parent `tenant_id`.
- AU-only destinations recommended (gov.au, .net.au) — not enforced.

## Audit
- `audit.support_handoff_configured` on create / update.
- `audit.support_handoff_incident_mode_activated` on activation.
