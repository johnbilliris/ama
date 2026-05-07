# Cultural-Safety Subsystem Contract

**Spec**: [`spec.md` § FR-016](../spec.md#functional-requirements) · [Clarifications Q5](../spec.md#clarifications)
**Research**: [`research.md` § R-010](../research.md#r-010--cultural-safety-subsystem)

## Trigger

Engaged on every `AwsWarningDraft` (FR-002) and on every operator-facing message destined for an ATSI community-language audience.

## Routing

1. Resolve `CulturalSafetyTemplate` for `(jurisdiction, language_pack)`.
2. Enqueue elder-approval task to the template's `elder_routing_target` (Service Bus queue or principal OID).
3. Start a `timeoutSeconds` (default 90 s, App Configuration override) timer.

## AWS-level-conditional outcome policy

| AWS level | Elder approves | Elder declines | Timeout (90 s) |
|---|---|---|---|
| `emergency_warning` | publish | block | **IC override permitted** → `cultural_safety_timeout_override` (requires IC `culturalSafetyConfirmer` OID) |
| `watch_and_act` | publish | block | hold → `cultural_safety_held`; do not publish |
| `advice` | publish | block | hold → `cultural_safety_held`; do not publish |

## Audit-row shapes

`cultural_safety_timeout_override` (only applicable on `emergency_warning`):

```json
{
  "outcome": "cultural_safety_timeout_override",
  "operator_identity": "<originator-oid>",
  "cultural_safety_confirmer": "<ic-oid>",
  "aws_level": "emergency_warning",
  "draft_id": "...",
  "language_pack": "yolngu_matha",
  "timeout_seconds": 90,
  "timestamp": "..."
}
```

`cultural_safety_held`:

```json
{
  "outcome": "cultural_safety_held",
  "operator_identity": "<originator-oid>",
  "aws_level": "watch_and_act" | "advice",
  "draft_id": "...",
  "language_pack": "yolngu_matha",
  "timeout_seconds": 90,
  "timestamp": "..."
}
```

## State transitions on `AwsWarningDraft.culturalSafetyState`

```
pending_elder ─── elder approves ──→ approved
pending_elder ─── elder declines ──→ declined
pending_elder ─── timeout (EW) ──→ timeout_lifesafety_override   [IC confirms or it remains pending]
pending_elder ─── timeout (W&A | Advice) ──→ timeout_blocked     (a.k.a. cultural_safety_held)
```

`timeout_lifesafety_override` requires a *separate* IC confirmation event before publish. It is **not** auto-publish; the IC explicitly accepts liability by confirming via the action card (FR-001), which itself appends a paired audit row.

## Configuration source

App Configuration keys:

- `cultural-safety:default-timeout-seconds` = `90`
- `cultural-safety:timeout-override-aws-levels` = `["emergency_warning"]`
- `cultural-safety:elder-routing:<jurisdiction>:<language_pack>` = `<sb-queue-name-or-oid>`
- `cultural-safety:fallback-chain:<jurisdiction>:<language_pack>` = JSON array

Feature flag `cultural-safety:enabled` (default `true`) gates the entire subsystem.

## Tests

- `emergency_warning` + 90 s timeout + IC confirms → `cultural_safety_timeout_override` row + `published` row, paired by `correlation_id`.
- `emergency_warning` + 90 s timeout + IC does NOT confirm → no publish, draft stays `timeout_lifesafety_override` until IC acts or operator withdraws.
- `watch_and_act` + 90 s timeout → `cultural_safety_held` row, draft stays `timeout_blocked`.
- `advice` + 90 s timeout → same as `watch_and_act`.
- Elder declines (any level) → `cultural_safety_held` (decline is treated as a held outcome for spec-035 metrics, distinct from timeout-held).
