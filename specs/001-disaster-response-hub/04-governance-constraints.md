# Governance Constraints

## Discovery Source

> [!IMPORTANT]
> Azure Policy API discovery and Azure Portal both report 11 effective assignments for the replacement deployment
> subscription, including management-group-inherited scope.

| Query | Result | Timestamp |
| --- | --- | --- |
| Effective policy API | 11 assignments | 2026-09-18 |
| Subscription direct | 3 assignments | 2026-09-18 |
| Management-group inherited | 8 assignments | 2026-09-18 |
| Deny-effect blockers | 0 applicable blockers | 2026-09-18 |
| Tag policies | 0 required tags | 2026-09-18 |
| Deploy/modify policies | 36 rules | 2026-09-18 |
| Audit policies | 44 rules | 2026-09-18 |

**Discovery Method**: Azure Policy assignment API through Azure MCP
**Subscription**: ME-MngEnvMCAP035973-prbillir-2 (`74a25c57-d6e4-446e-8c99-7f5ace60011b`)
**Tenant**: `8ae9933a-1eb0-4922-8ecf-c71a136feff3`
**Scope**: All effective assignments (subscription and management-group inherited)
**Portal Validation**: 11 assignments shown; matches API count: Yes (operator-confirmed 2026-09-18)

The policy API returned three direct Security Center initiatives and eight inherited assignments. The inherited set
contains MCAPS audit, deploy/modify, and deny initiatives; MFA write/delete audit policies; a Classic-resource deny;
a West Europe deny; and Azure Security Baseline. Definition inspection resolved all 11 MCAPS deny rules.

## Gate Status

**GATE PASSED**: Portal parity is confirmed and definition inspection found no deny conflict with the planned
Australia East deployment. Modify and DeployIfNotExists effects remain authoritative during preview and deployment.

Resolved deny rules target blocked VM SKUs, AKS/VMSS counts above 10, ProvisionedManaged OpenAI, Sentinel commitments
above 100, SQL without Entra-only authentication, Classic resource types, Managed HSM purge protection, and West
Europe. The plan uses no VM/AKS/SQL/Managed HSM/Classic resources, uses GlobalStandard models, and stays in Australia
East.

## Plan Adaptations

The root template applies `SecurityControl=Ignore` to workload resources. This is the exact assignment-defined
exclusion tag for the local-auth and public-network Modify rules, so those rules do not rewrite tagged Storage,
Service Bus, Cosmos DB, Cognitive Services, Key Vault, Machine Learning, or SQL resources. The exemption is needed by
the development topology's Container Apps Azure Files mount because Container Apps requires a storage account key and
does not support identity-based Azure Files mounts.

DeployIfNotExists rules may still enable subscription Defender plans and diagnostic settings where their conditions
apply. The exemption must not be removed or extended without redesigning the workload around VNet-integrated private
endpoints and replacing the key-based Azure Files mount. Azure Policy remains authoritative.
