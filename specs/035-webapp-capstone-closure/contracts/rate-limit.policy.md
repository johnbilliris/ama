# Rate-Limit Policy Contract

**Spec**: [`spec.md` § FR-012](../spec.md#functional-requirements) · [Clarifications Q3](../spec.md#clarifications)
**Research**: [`research.md` § R-002](../research.md#r-002--apim-rate-limit-policy-shape)
**IaC**: [`infra/modules/apim-rate-limit.bicep`](../../../infra/modules/apim-rate-limit.bicep) (NEW, AVM-composed)

## Budgets

| Scope | Limit | Window | Source |
|---|---|---|---|
| Per-`(persona_id, route)` | 10 requests | 60 seconds | App Configuration `rate-limit:perPersonaRoute:perMinute` |
| Per-`(persona_id, route)` | 600 requests | 1 hour | App Configuration `rate-limit:perPersonaRoute:perHour` |
| Global API ceiling (CI-protective) | 600 requests | 60 seconds | App Configuration `rate-limit:global:perMinute` |

## APIM policy shape (snippet)

```xml
<policies>
  <inbound>
    <base />

    <!-- Per-(persona_id, route) bucket -->
    <rate-limit-by-key
        calls="@(int.Parse(context.Variables.GetValueOrDefault('perPersonaRoutePerMinute', '10')))"
        renewal-period="60"
        counter-key="@(context.Subscription.Id + ':' + context.Request.Headers.GetValueOrDefault('X-Persona-Id', '') + ':' + context.Operation.Name)" />

    <quota-by-key
        calls="@(int.Parse(context.Variables.GetValueOrDefault('perPersonaRoutePerHour', '600')))"
        renewal-period="3600"
        counter-key="@(context.Subscription.Id + ':' + context.Request.Headers.GetValueOrDefault('X-Persona-Id', '') + ':' + context.Operation.Name + ':hour')" />

    <!-- Global CI-protective ceiling -->
    <rate-limit
        calls="@(int.Parse(context.Variables.GetValueOrDefault('globalPerMinute', '600')))"
        renewal-period="60" />

    <!-- On 429, set a header so the FastAPI rate_limit_audit middleware can append the row -->
    <on-error>
      <set-header name="X-Rate-Limit-Triggered" exists-action="override">
        <value>true</value>
      </set-header>
    </on-error>
  </inbound>
</policies>
```

## Headers contract

| Header | Direction | Semantics |
|---|---|---|
| `X-Persona-Id` | client → APIM | Required for per-persona keying. Set by SDK or web fetch wrapper from the bearer's `persona_id` claim. APIM verifies presence; absence yields the global ceiling only. |
| `X-Impersonate-Persona` | client → API | Per-request impersonation; APIM does NOT use this for keying (admin uses their own `persona_id`); used only by FastAPI for paired-row audit (Q9). |
| `Retry-After` | API → client | Set on 429; FastAPI middleware MUST also set `retry_after_seconds` in the error envelope. |
| `X-Rate-Limit-Triggered` | APIM → FastAPI | Internal signal so the FastAPI `rate_limit_audit` middleware can append the audit row. Stripped before responding to the client. |

## Audit-row shape (rate_limited)

```json
{
  "outcome": "rate_limited",
  "operator_identity": "<entra-oid>",
  "persona_id": "<from-bearer>",
  "route": "/api/outcomes/sc-001/evaluate",
  "extension_envelope": { "error_code": "rate_limited", "retry_after_seconds": 30, ... },
  "timestamp": "..."
}
```

## Tests

- A bursty 11-request loop in 60 s for the same `(persona_id, route)` MUST produce exactly one 429 + audit row.
- A 601-request loop spread across multiple `(persona_id, route)` tuples within 60 s MUST trigger the global ceiling 429.
- Admin (`system-administrator`) impersonating a different persona MUST be keyed by the admin's own `persona_id` (their identity, not the impersonated target).
- All 429s MUST emit one `extension_envelope`-shaped error body matching the production-auth extension contract.
