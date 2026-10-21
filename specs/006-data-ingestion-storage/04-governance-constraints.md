# 04 Governance Constraints — Spec 006

## Discovery Source

> [!IMPORTANT]
> Governance constraints discovery remains UNVERIFIED for this feature scope. Authenticated scoped and subscription-wide Azure Policy queries returned zero assignments, but management-group inheritance parity with Portal could not be confirmed.

| Query | Result | Timestamp |
| --- | --- | --- |
| REST API Total | 0 assignments returned by subscription-wide query (UNVERIFIED pending Portal parity) | 2026-09-16T03:01:23Z |
| Subscription-scope | 0 assignments returned by exact subscription-scope query | 2026-09-16T03:01:23Z |
| MG-inherited | UNVERIFIED | 2026-09-16T03:01:23Z |
| Deny-effect | 0 returned; completeness UNVERIFIED | 2026-09-16T03:01:23Z |
| Tag Policies | 0 returned; completeness UNVERIFIED | 2026-09-16T03:01:23Z |
| Security Policies | 0 returned; completeness UNVERIFIED | 2026-09-16T03:01:23Z |

Discovery Method: Azure Policy `policy_assignment_list`, exact subscription scope and subscription-wide
Subscription: AI Impact Analyzer (`879c3e12-a379-45c7-b1b1-5a44f3cc2713`)
Tenant: `72f988bf-86f1-41af-91ab-2d7cd011db47`
Scope: Subscription and inherited management-group policy scope are UNVERIFIED
Portal Validation: UNVERIFIED

## Deployment Gate

Status: GOVERNANCE-BLOCKED

Reason:

- Azure Policy API queries returned zero assignments, but inherited-assignment completeness is not established.
- Portal parity could not be established because the inspectable Portal session remained unauthenticated and no external count was available.
- Deny/Modify/DeployIfNotExists effects cannot be safely inferred from static repository contents.

Required next evidence before policy-compliant IaC changes:

- Live REST assignment inventory for AI Impact Analyzer.
- Portal parity confirmation.
- Effect-level classification with documented plan adaptations or exemption path.

## IaC Authority Decision (Non-Bicep)

- Authoritative IaC entry point is azure.yaml -> infra.path=infra, infra.module=main.
- Authoritative template is infra/main.bicep.
- Legacy/manual template infra/bicep/main.bicep is deprecated for evidence and must not be treated as authoritative deployment truth for spec-006 acceptance.

## Static Drift Findings (Non-Bicep)

- Ingestion worker drift indicators remain open:
  - Current active scaling is CPU 2-6 replicas.
  - Queue-depth scale rule is not verified in active template.
  - Probe settings are not verified in active template.
- Legacy module wiring drift remains open:
  - Orphan module references under infra/bicep/modules are detected by static tests.

This document intentionally does not claim deployment, what-if, or policy compliance success.
