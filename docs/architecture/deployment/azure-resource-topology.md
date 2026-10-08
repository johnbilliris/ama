---
purpose: Azure resource topology showing the branch-mapped resource group and the named platform resources.
personas:
  - Technical-Build
diagrams:
  - DEPLOY-02
specs:
  - spec-001
  - spec-017
---

# DEPLOY-02 — Azure Resource Topology

[→ Architecture index](../README.md)

<!-- spec-cross-ref: spec-001 -->
<!-- spec-cross-ref: spec-017 -->

![DEPLOY-02 — Azure Resource Topology](./azure-resource-topology.png)

## Key Elements

- Current CD resource-group naming: `rg-drh-<env>` (for `dev`, `staging`, `production`).
- Historical architecture snapshot naming: `rg-ama` and resource aliases such as `ca-api`, `ca-agents`, `ca-ingest`.
- `api`, `agents`, and `ingestion` are deployed as Azure Container Apps.
- `web` is hosted on Azure App Service (`host: appservice` in `azure.yaml`).
- Core platform dependencies: Cosmos DB, Azure AI Search, Service Bus, Event Hubs, Application Insights, Key Vault.

The diagram includes intended release topology for orientation. Exact deployed resource instance names and gate enforcement status must be validated from CI run evidence and Azure inventory.
