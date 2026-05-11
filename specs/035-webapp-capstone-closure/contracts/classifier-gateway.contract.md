# Classifier Gateway Contract (ADR-033 Layer 2)

**Spec**: [`spec.md` § FR-027](../spec.md#functional-requirements) · [Clarifications Q6](../spec.md#clarifications)
**Research**: [`research.md` § R-008](../research.md#r-008--classifier-gateway-pspf--pii-deny--mask)
**ADR**: [`docs/aidr/decisions/adr-033-phi-shadow-boundary.md`](../../../docs/aidr/decisions/adr-033-phi-shadow-boundary.md) (Layer 2, deterministic)

## Position in stack

The classifier middleware sits BEFORE auth verification in the FastAPI middleware order, because we never want to leak that an unauthenticated caller hit a regulated route. See the precedence ladder in [`production-auth-extension.contract.md`](./production-auth-extension.contract.md).

```
client → APIM (rate-limit) → FastAPI:
  1. activation_mutex                  (FR-013 / Q8)
  2. classifier_gateway                ← THIS contract
  3. entra_auth                        (FR-010 / Q1)
  4. rbac_check                        (FR-011 stage-b)
  5. rate_limit_audit                  (FR-012 / Q3 audit row writer)
  6. route handler
  7. audit_appender (always emits)
```

## Branches (closed set)

| Content class | Action | HTTP | `error_code` | Audit `outcome` |
|---|---|---|---|---|
| `pspf` (any PSPF marking present) | DENY | 403 | `sovereignty_denied` | `classifier_deny` |
| `pii` (no PSPF marking) | MASK in place + UI banner | 200 | _(no error)_ | `classifier_mask` |
| `pspf+pii` | DENY (PSPF precedence) | 403 | `sovereignty_denied` | `classifier_deny` |
| classifier failure / timeout | DENY (fail-closed) | 503 | `sovereignty_denied` | `classifier_failed` |
| `clean` | pass-through | _(downstream determines)_ | _(downstream)_ | _(downstream emits)_ |

## Detection rules (deterministic — Layer 2)

- **PSPF markings**: byte-string match for `OFFICIAL: Sensitive`, `PROTECTED`, `SECRET`, `TOP SECRET` and the legacy `IN-CONFIDENCE` marking, in any case (regex `\b(OFFICIAL:\s*Sensitive|PROTECTED|SECRET|TOP\s*SECRET|IN-CONFIDENCE)\b` with `re.IGNORECASE`).
- **PII patterns** (AU-format):
  - TFN: 9-digit grouped (e.g., `123 456 789`) with checksum
  - Medicare: 10-digit prefixed `2|3|4|5|6` with checksum
  - Phone: `04XX XXX XXX`, `+61 4XX XXX XXX`, AU landlines
  - Email: RFC 5322 simple form
  - DOB: `DD/MM/YYYY`, `D MMM YYYY`
  - Australian addresses: `\d+\s+[A-Z][a-z]+\s+(St|Street|Rd|Road|Ave|Avenue|...)`, postcodes
  - Name + DOB co-occurrence within 50 chars

## Mask transformation

For `pii` (mask path): every detected pattern is replaced with `[MASKED:{class}]`, e.g., `john.doe@example.com` → `[MASKED:email]`. The UI banner from [`apps/web/src/lib/classifier/banner.tsx`](../../../apps/web/src/lib/classifier/banner.tsx) renders **"this content was masked before processing"** with a link to the audit row.

The masking is **deterministic** — re-running the classifier on a masked payload produces zero new masks. The original payload is **never persisted** post-mask.

## Audit-row shapes

`classifier_deny`:

```json
{
  "outcome": "classifier_deny",
  "classifier_layer": 2,
  "content_class": "pspf" | "pspf+pii",
  "operator_identity": "<entra-oid-or-anonymous>",
  "persona_id": "<from-bearer-or-null>",
  "route": "...",
  "request_hash": "sha256:...",
  "extension_envelope": { "error_code": "sovereignty_denied", ... },
  "timestamp": "..."
}
```

`classifier_mask`:

```json
{
  "outcome": "classifier_mask",
  "classifier_layer": 2,
  "content_class": "pii",
  "masked_field_count": 3,
  "operator_identity": "<entra-oid>",
  "persona_id": "<from-bearer>",
  "route": "...",
  "request_hash": "sha256:...",
  "timestamp": "..."
}
```

`classifier_failed`:

```json
{
  "outcome": "classifier_failed",
  "classifier_layer": 2,
  "error": "<short reason>",
  "operator_identity": "<entra-oid-or-anonymous>",
  "persona_id": "<from-bearer-or-null>",
  "route": "...",
  "extension_envelope": { "error_code": "sovereignty_denied", ... },
  "timestamp": "..."
}
```

## Foundry carve-out interaction

The classifier emits its branch decision BEFORE any model-hosting request leaves the AU-region API process. The Foundry carve-out registry ([`research.md` § R-011](../research.md#r-011--foundry-carve-out-registry-surfacing)) records which model endpoints are allowed non-AU; classifier never relaxes its branches based on registry membership — registry only governs whether the *non-classified* path may leave AU at all.

## Admin override

Per [Clarifications Q9](../spec.md#clarifications) and [FR-011](../spec.md#functional-requirements), the `system-administrator` AppRole NEVER bypasses the classifier. PSPF→deny / PII→mask / fail→deny apply uniformly to admin-impersonated calls, with the admin's `operator_identity` recorded on the audit row.

## Tests

- One test per branch (`pspf`, `pii`, `pspf+pii`, classifier-failure, `clean`).
- One test confirming admin bypass is impossible (admin token + PSPF payload → 403 + `classifier_deny` row).
- One test confirming masking is deterministic (mask twice → zero new masks, identical hash).
- One test confirming the original payload is not persisted on mask path (assert audit `request_hash` ≠ payload-hash on the route handler's processed request).
