# 04 Governance Constraints - Spec 008

## Discovery Source

> [!IMPORTANT]
> Governance constraints remain UNVERIFIED for this feature scope. Authenticated exact-scope and subscription-wide Azure Policy queries returned zero assignments, but management-group inheritance and Azure Portal parity could not be confirmed.

| Query | Result | Timestamp |
| --- | --- | --- |
| Subscription-wide API | 0 assignments returned; completeness unverified | 2026-09-16T23:47:42Z |
| Exact subscription scope | 0 assignments returned | 2026-09-16T23:47:42Z |
| Management-group inherited | UNVERIFIED | 2026-09-16T23:47:42Z |
| Portal parity | UNVERIFIED | 2026-09-16T23:47:42Z |
| Deny/Modify/DeployIfNotExists effects | 0 returned; completeness unverified | 2026-09-16T23:47:42Z |

Discovery Method: Azure Policy `policy_assignment_list`, exact subscription scope and subscription-wide
Subscription: AI Impact Analyzer (`879c3e12-a379-45c7-b1b1-5a44f3cc2713`)
Tenant: `72f988bf-86f1-41af-91ab-2d7cd011db47`
Portal Validation: UNVERIFIED

## Deployment Gate

Status: GOVERNANCE-BLOCKED

The disconnected `infra/modules/communication-agent.bicep` module must not be integrated or have its account-wide Cosmos role narrowed until inherited assignments and Portal parity are verified. No deployment, what-if, regional-boundary, or RBAC compliance success is claimed.

## Blocked Finding

- AUD-008-031: compose the communication runtime with policy-cleared identity, scoped Cosmos data-plane roles, Service Bus roles, provider configuration, scaling, and Australian regional boundaries.

## Required Evidence

- Portal-visible assignment count with inherited scope enabled.
- Complete effective assignment inventory and effect analysis if the Portal count is nonzero.
- Approved database/container-level Cosmos role scope and any required exemption.
- Bicep build and what-if output after governance clearance.
- Deployment evidence showing the communication runtime, queue scaling, managed identity, and regional placement.
