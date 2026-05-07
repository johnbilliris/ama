# Quickstart — Web Application Capstone Closure (spec-035)

**Spec**: [`spec.md`](./spec.md) · **Plan**: [`plan.md`](./plan.md) · **Data model**: [`data-model.md`](./data-model.md) · **Contracts**: [`contracts/`](./contracts/)

This quickstart shows reviewers how to run the production-reachable evaluator and audit-list endpoints, how to exercise persona panels in the web app, and how to verify the 12 success criteria. Times are not estimated.

---

## Prerequisites

- Node ≥ 20, pnpm ≥ 9
- Python 3.13 (managed by `uv` or your preferred tool)
- Azure CLI logged in to the AMA tenant (`az login`)
- Read access to App Service `app-ama-zo6bb5` (Australia East)
- An Entra app registration with one of the 11 AppRoles (see [Clarifications Q1](./spec.md#clarifications)) granted to your principal

## Repository setup

```pwsh
pnpm install
uv sync
```

## Configuration

Two modes are supported in production:

### Mode A — production-reachable (default after this spec ships)

```pwsh
$env:AMA_ENABLE_PRODUCTION_AUTH = "1"
$env:AMA_TEST_SUPPORT = "0"          # MUST be 0 in prod
$env:ENTRA_TENANT_ID = "<tenant>"
$env:ENTRA_API_AUDIENCE = "api://ama-api-prod"
$env:COSMOS_ENDPOINT = "https://cos-ama-zo6bb5.documents.azure.com:443/"
$env:APP_CONFIG_ENDPOINT = "https://appcs-ama-zo6bb5.azconfig.io"
```

### Mode B — dev/test (test-support routes registered alongside)

```pwsh
$env:AMA_TEST_SUPPORT = "1"          # spec-034 dual-guard reactivates the test-support copies
$env:AMA_ENABLE_PRODUCTION_AUTH = "1"
```

In Mode B, both `/api/outcomes/sc-001/evaluate` (production-auth) and `/_test/outcomes/sc-001/evaluate` (test-support) are reachable. Mode A serves only the production path.

## Run the API locally

```pwsh
cd apps/api
uv run uvicorn app.main:app --reload --port 8000
```

## Run the web app locally

```pwsh
cd apps/web
pnpm dev
```

Open `http://localhost:3000`. Sign in with an Entra account holding one of the 11 AppRoles.

---

## Verify the production-reachable evaluator (FR-009 / SC-001)

```pwsh
$token = az account get-access-token --resource api://ama-api-prod --query accessToken -o tsv

# Replace persona id with one for which your AppRole is scoped
curl -X POST http://localhost:8000/api/outcomes/sc-001/evaluate `
  -H "Authorization: Bearer $token" `
  -H "X-Persona-Id: incident_commander_au_east" `
  -H "Content-Type: application/json" `
  -d '{"correlation_id":"11111111-2222-3333-4444-555555555555","payload":{...}}'
```

Expected: `200 OK` with the **spec-034 success body verbatim** (no envelope wrapping). Confirm the `audit_id` is reachable via:

```pwsh
curl -H "Authorization: Bearer $token" `
  "http://localhost:8000/api/audit/list?correlation_id=11111111-2222-3333-4444-555555555555"
```

## Verify the error envelope (FR-009 / Q10)

```pwsh
# Force schema-invalid
curl -X POST http://localhost:8000/api/outcomes/sc-001/evaluate `
  -H "Authorization: Bearer $token" -H "X-Persona-Id: incident_commander_au_east" `
  -H "Content-Type: application/json" -d '{}'
```

Expected `422`:

```json
{ "error_code": "schema_invalid", "retry_after_seconds": null,
  "audit_id": "...", "correlation_id": "..." }
```

## Verify rate-limit (FR-012 / Q3)

Loop 11 calls in under 60 s for the same `(persona_id, route)`:

```pwsh
1..11 | ForEach-Object {
  curl -s -o /dev/null -w "%{http_code}`n" -X POST http://localhost:8000/api/outcomes/sc-001/evaluate `
    -H "Authorization: Bearer $token" -H "X-Persona-Id: incident_commander_au_east" `
    -H "Content-Type: application/json" -d '{"correlation_id":"...","payload":{...}}'
}
```

Expected: ten `200`s then one `429` with `Retry-After` header and the envelope shape.

## Verify impersonation pairing (FR-011 / Q9)

With a `system-administrator` token:

```pwsh
curl -X POST http://localhost:8000/api/outcomes/sc-001/evaluate `
  -H "Authorization: Bearer $admin_token" `
  -H "X-Persona-Id: system_admin_global" `
  -H "X-Impersonate-Persona: incident_commander_au_east" `
  -H "Content-Type: application/json" `
  -d '{"correlation_id":"22222222-...","payload":{...}}'
```

Expected: two audit rows under one `correlation_id`:

1. `outcome=admin_override`, `persona_id=*`, `impersonated_persona_id=incident_commander_au_east`
2. `outcome=approved` (or whichever), `persona_id=incident_commander_au_east`, `impersonated_by=<admin-oid>`

## Verify offline replay (FR-006 / Q4 + Q7)

1. In the web app, open the persona workspace and perform an action while online (banner = green).
2. Open DevTools → Application → Service Workers → check **Offline**.
3. Perform two more actions; the offline banner appears and the IndexedDB queue grows.
4. Toggle network back online; observe the SW drains the life-safety entry first, then the routine entries in 50-entry batches; tiered SLOs honoured.
5. Confirm `/api/audit/list` shows three rows preserving the original `captured_ts` ([SC-007](./spec.md#measurable-outcomes)).

## Verify cultural-safety subsystem (FR-016 / Q5)

1. As a `public-information-officer`, draft an `emergency_warning` AWS warning targeting an ATSI language pack.
2. Wait 90 s without elder approval.
3. As an `incident-commander`, confirm the `cultural_safety_timeout_override`.
4. Audit shows `outcome=cultural_safety_timeout_override` with `cultural_safety_confirmer = <ic-oid>`, paired with the `published` row.

For `watch_and_act` and `advice` levels, repeat: the draft remains `timeout_blocked` and audit shows `outcome=cultural_safety_held` (no IC override path).

## Verify recovery-handover signed PDF (FR-007 / Q2)

```pwsh
curl -X POST http://localhost:8000/api/recovery/handover/sign `
  -H "Authorization: Bearer $resilience_planner_token" `
  -H "X-Persona-Id: resilience_planner_qld" `
  -H "Content-Type: application/json" `
  -d @recovery_payload.json
```

Inspect the response: the `artefact_hash` should byte-equal the SHA-256 of the PDF at `blob_uri`. The `signing_identity` should reference the App Service managed-identity OID + cert thumbprint.

---

## Accessibility verification (Constitution NN-3)

```pwsh
cd tests/e2e/web-coverage
pnpm dlx playwright install chromium --with-deps
pnpm test:a11y
```

`@axe-core/playwright` runs the **Standard** rule-set against every persona workspace; the suite fails on any **critical** violation. Output is written to `tests/e2e/web-coverage/coverage-trace.json` (consumed by SC-002).

## Activation-mutex CI gate ([Q8](./spec.md#clarifications))

```pwsh
pwsh -ExecutionPolicy Bypass -File ./scripts/verify-activation-mutex.ps1
```

The script forks two child processes that both call the API health endpoint with `AMA_ACTIVATION=1`; the second MUST observe a `409 activation_mutex_violation` response and an audit row with `outcome=activation_mutex_violation` MUST be appended before the loser exits non-zero.

---

## Verification matrix (SC-001..SC-012 → artefact)

| Success criterion | Source artefact |
|---|---|
| SC-001 (every Code-Phase outcome production-reachable) | `tests/e2e/web-coverage/coverage-trace.json` |
| SC-002 (axe-core critical = 0) | `tests/e2e/web-coverage/a11y-report.json` |
| SC-003 (gap register zero CRITICAL/HIGH) | `tests/e2e/web-coverage/gap-register.json` |
| SC-004 (audit append < 2 s p95) | `apps/api/tests/perf/audit_p95.json` |
| SC-005 (offline replay tiered SLO honoured) | `tests/e2e/web-coverage/offline-replay.json` |
| SC-006 (rate-limit budgets enforced) | `apps/api/tests/contract/spec_035/test_rate_limit.py` |
| SC-007 (offline `captured_ts` preserved) | `tests/e2e/web-coverage/offline-replay.json` |
| SC-008 (Sendai counterfactual ≥ 0.30) | `apps/api/tests/contract/spec_035/test_recovery_handover.py` |
| SC-009 (audit append < 2 s p95) | shared with SC-004 |
| SC-010 (cultural-safety AWS-level outcomes) | `apps/api/tests/contract/spec_035/test_cultural_safety.py` |
| SC-011 (90-day Foundry carve-out review) | `.github/workflows/foundry-carveout-review.yml` artefact |
| SC-012 (impersonation paired-row invariant) | `apps/api/tests/contract/spec_035/test_impersonation_pairing.py` |

---

## Troubleshooting

- **`401 unauthorized` even with a fresh token**: confirm `AMA_ENABLE_PRODUCTION_AUTH=1`. Mode B requires the `AMA_TEST_SUPPORT=1` flag separately.
- **`403 sovereignty_denied` on a payload you did not expect to be PSPF**: the deterministic Layer-2 classifier matched a marker; inspect `extension_envelope.audit_id` and call `/api/audit/list?audit_id=...` to see the matched class. Strip the marker and retry.
- **`429 rate_limited`**: read `retry_after_seconds` from the envelope; do not hammer-retry, you will only fill the audit log with `rate_limited` rows.
- **Offline queue stuck at 500 entries**: this is the cap (Q7). Reconnect; if a life-safety action is queued, the oldest routine entry is displaced. Operator UI banner ≥ 80% utilisation should give early warning.
- **Cultural-safety draft stuck pending**: confirm the elder-routing target in App Configuration; for `emergency_warning` the IC override is permitted after 90 s, for `watch_and_act`/`advice` it is not.
