# Recovery-Handover Contract

**Spec**: [`spec.md` § FR-007](../spec.md#functional-requirements) · [Clarifications Q2](../spec.md#clarifications) · [SC-008](../spec.md#measurable-outcomes)
**Research**: [`research.md` § R-009](../research.md#r-009--signed-pdf-recovery-handover)
**IaC**: [`infra/modules/blob-immutable.bicep`](../../../infra/modules/blob-immutable.bicep) (NEW, AVM-composed)

## Endpoint

`POST /api/recovery/handover/sign`

## Request body

```json
{
  "event_id": "...",
  "gap_analysis": "<markdown>",
  "framework_modelling": { ... },
  "lessons_integration": "<markdown>",
  "baseline_loss": 12500000.00,
  "projected_loss": 8200000.00,
  "recovery_environments": {
    "social":   { "risks": [...], "actions": [...] },
    "built":    { "risks": [...], "actions": [...] },
    "economic": { "risks": [...], "actions": [...] },
    "natural":  { "risks": [...], "actions": [...] }
  },
  "claims_velocity_snapshot_id": "..."
}
```

## Validation

| Rule | Source |
|---|---|
| All four recovery environments populated (`social`, `built`, `economic`, `natural`) | [SC-008](../spec.md#measurable-outcomes) |
| `(baseline_loss − projected_loss) / baseline_loss ≥ 0.30` | [SC-008](../spec.md#measurable-outcomes) — Sendai counterfactual |
| `baseline_loss > 0` and `projected_loss ≥ 0` | numeric sanity |
| Claims-velocity snapshot resolves AND is `< 24 h` old | [FR-022](../spec.md#functional-requirements) |

## Response body (success)

```json
{
  "artefact_id": "...",
  "artefact_hash": "sha256:...",
  "signing_identity": "oid:<managed-identity>;cert:<thumbprint>",
  "blob_uri": "https://...",
  "sas_url_expires_at": "<iso-8601>",
  "sendai_ratio": 0.344,
  "audit_id": "..."
}
```

## Signing pipeline

1. Render PDF server-side ([`apps/api/app/services/recovery_handover_service.py`](../../../apps/api/app/services/recovery_handover_service.py)) carrying gap analysis, framework modelling, lessons integration, the four recovery environments, and the Sendai counterfactual.
2. Compute SHA-256 hash of PDF bytes.
3. Detached PKCS#7 signature using the Key Vault–backed certificate; signing identity = App Service managed-identity OID + cert thumbprint.
4. Upload PDF + detached signature to immutable Blob container; record `blob_uri`.
5. Append `outcome=published` audit row carrying `artefact_id`, `artefact_hash`, `signing_identity`, `sendai_ratio`.
6. Return success body with a 15-minute SAS URL.

## Out of scope (per [OOS-011](../spec.md#out-of-scope))

- Machine-ingestible JSON / structured sidecars
- Downstream automated ingestion by ICA / state recovery / NEMA
- Multi-signature workflows (single signing identity is sufficient for spec-035)

## Error envelope

Returns the production-auth extension envelope. Specific `error_code`s applicable here:

- `schema_invalid` — Sendai ratio < 0.30, missing recovery environment, claims snapshot stale
- `seed_not_ready` — claims-velocity snapshot id resolves but data not yet flushed
- `sovereignty_denied` — payload contained PSPF marking (Q6)
- `unauthorized` / `forbidden` / `rate_limited` per ladder

## Tests

- Sendai ratio < 0.30 → `422 schema_invalid`.
- Missing `economic` environment → `422 schema_invalid`.
- Hash on the audit row byte-equals the SHA-256 of the blob payload.
- Signing identity on the audit row byte-equals the OID + thumbprint of the managed-identity-bound cert.
- SAS URL is reachable for ≤ 15 minutes; subsequent fetch attempts after expiry require a re-issue.
- Blob immutability policy refuses overwrite (replay POST → second `artefact_id`, original blob untouched).
