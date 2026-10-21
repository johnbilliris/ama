# Governance Constraints

## Discovery Source

> [!CAUTION]
> Governance discovery is incomplete. Azure Policy queries returned zero assignments, but Azure Portal parity and management-group inheritance could not be verified. Bicep changes and deployment remain blocked.

| Query | Result | Timestamp |
| --- | --- | --- |
| Subscription-scoped policy API | 0 assignments | 2026-09-15 |
| Unscoped subscription policy API | 0 assignments | 2026-09-15 |
| Management-group inherited | UNVERIFIED | 2026-09-15 |
| Deny-effect blockers | UNVERIFIED | 2026-09-15 |
| Tag policies | UNVERIFIED | 2026-09-15 |
| Security policies | UNVERIFIED | 2026-09-15 |

**Discovery Method**: Azure Policy assignment API through Azure MCP
**Subscription**: AI Impact Analyzer (`879c3e12-a379-45c7-b1b1-5a44f3cc2713`)
**Tenant**: `72f988bf-86f1-41af-91ab-2d7cd011db47`
**Scope**: Subscription query requested; management-group inheritance not independently confirmed
**Portal Validation**: Not available; REST-to-Portal count match is UNVERIFIED

## Gate Status

**GATE BLOCKED**: AUD-020 and AUD-021 Bicep changes cannot proceed because effective Azure Policy requirements have not been fully discovered and Portal parity has not been confirmed.

No policy constraints are inferred from the zero-result query. Baseline Azure best practices cannot substitute for live governance discovery.

## Required Resolution

1. Confirm the effective policy-assignment count in Azure Portal for the selected subscription.
2. Confirm whether management-group inherited assignments are visible in the API result.
3. Re-run discovery and inspect every applicable policy definition, effect, scope, enforcement mode, and assignment parameter.
4. Populate the companion JSON with verified `azurePropertyPath`, `bicepPropertyPath`, and `requiredValue` entries before changing Bicep.
