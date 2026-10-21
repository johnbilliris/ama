# 04 Governance Constraints - Spec 007

## Discovery Source

> [!IMPORTANT]
> Governance constraints remain UNVERIFIED for this feature scope. Authenticated exact-scope and subscription-wide Azure Policy queries returned zero assignments, but management-group inheritance and Azure Portal parity could not be confirmed.

| Query | Result | Timestamp |
| --- | --- | --- |
| Subscription-wide API | 0 assignments returned; completeness unverified | 2026-09-16T03:01:23Z |
| Exact subscription scope | 0 assignments returned | 2026-09-16T03:01:23Z |
| Management-group inherited | UNVERIFIED | 2026-09-16T11:41:52Z |
| Portal parity | UNVERIFIED | 2026-09-16T11:41:52Z |
| Deny/Modify/DeployIfNotExists effects | 0 returned; completeness unverified | 2026-09-16T11:41:52Z |
| Required tags/security controls | 0 returned; completeness unverified | 2026-09-16T11:41:52Z |

Discovery Method: Azure Policy `policy_assignment_list`, exact subscription scope and subscription-wide
Subscription: AI Impact Analyzer (`879c3e12-a379-45c7-b1b1-5a44f3cc2713`)
Tenant: `72f988bf-86f1-41af-91ab-2d7cd011db47`
Scope: Effective subscription and inherited management-group scope is UNVERIFIED
Portal Validation: UNVERIFIED

## Deployment Gate

Status: GOVERNANCE-BLOCKED

Reason:

- API results cannot establish inherited-assignment completeness without Portal parity.
- Deny, Modify, and DeployIfNotExists effects cannot be safely inferred from an unverified empty result.
- Repository instructions prohibit Bicep changes until the discovery and parity gate is complete.

## Blocked Findings

- AUD-004: narrow Cosmos data-plane role assignments from account-wide scope to the approved database/container boundary.
- AUD-019: apply the approved immutable retention policy to the actual simulation audit destination.
- AUD-022: verify archived report/audit/seed evidence on the approved immutable storage destination.

## Required Evidence

- Portal-visible assignment count with inherited scope enabled.
- Complete effective assignment inventory if the Portal count is nonzero.
- Effect-level policy definition analysis and any required plan adaptation or approved exemption.
- Policy-cleared Bicep build and what-if evidence for the selected storage and RBAC controls.

No Bicep, deployment, what-if, or Azure compliance success is claimed by this artifact.
