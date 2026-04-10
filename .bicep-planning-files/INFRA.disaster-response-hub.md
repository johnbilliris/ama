---
goal: disaster-response-hub-infrastructure
---

# Infrastructure Plan: Disaster Response Hub

## Introduction

Refactored infrastructure for the Autonomous Disaster Response Hub using Azure Developer CLI (azd)
conventions with modular Bicep. All resources deploy to australiaeast per Constitution VI.

## Resources

### 1. Container Registry
- **name**: cr{env}{suffix}
- **kind**: AVM
- **module**: avm/res/container-registry/registry
- **purpose**: Private registry for API, Agents, Ingestion container images
- **dependsOn**: none
- **parameters**: sku=Basic, adminUserEnabled=true, acrAdminUserEnabled=true
- **outputs**: loginServer, name
- **docs**: https://learn.microsoft.com/en-us/azure/container-registry/

### 2. Storage Account
- **name**: st{env}{suffix}
- **kind**: Raw (blob containers require parent chaining not well-supported by AVM loops)
- **type**: Microsoft.Storage/storageAccounts@2023-05-01
- **purpose**: Raw payloads, binary assets, audit trail, simulation data
- **dependsOn**: none
- **parameters**: sku=Standard_LRS, kind=StorageV2, allowBlobPublicAccess=false, minimumTlsVersion=TLS1_2
- **blob containers**: raw-payloads, binary-assets, audit, simulation
- **outputs**: name, id
- **docs**: https://learn.microsoft.com/en-us/azure/storage/blobs/

### 3. Cosmos DB Account + Database + Containers
- **name**: cosmos-{env}-{suffix}
- **kind**: Raw (MultiHash partition keys and composite indexes require detailed config)
- **type**: Microsoft.DocumentDB/databaseAccounts@2023-11-15
- **purpose**: Operational signal store (signals, simulation, seed)
- **dependsOn**: none
- **parameters**: databaseAccountOfferType=Standard, locations=[australiaeast]
- **containers**: signals (MultiHash: scope/jurisdictionId/dataSourceId, autoscale 4000), simulation (Hash: scenario_id, autoscale 400), seed (Hash: kind, autoscale 400)
- **outputs**: documentEndpoint, name
- **docs**: https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/

### 4. Redis Cache
- **name**: redis-{env}-{suffix}
- **kind**: Raw
- **type**: Microsoft.Cache/Redis@2024-03-01
- **purpose**: Dedup hash cache, governance lookups, dashboard cache
- **dependsOn**: none
- **parameters**: sku=Basic/C/0, enableNonSslPort=false, minimumTlsVersion=1.2
- **outputs**: hostName
- **docs**: https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/

### 5. Azure OpenAI
- **name**: cog-{env}-{suffix}
- **kind**: Raw
- **type**: Microsoft.CognitiveServices/accounts@2024-10-01
- **purpose**: LLM for agent reasoning, alert drafting, misinformation detection
- **dependsOn**: none
- **parameters**: kind=OpenAI, sku=S0, publicNetworkAccess=Enabled
- **outputs**: endpoint
- **docs**: https://learn.microsoft.com/en-us/azure/ai-services/openai/

### 6. Log Analytics Workspace
- **name**: log-{env}
- **kind**: Raw
- **type**: Microsoft.OperationalInsights/workspaces@2023-09-01
- **purpose**: Centralised logging for all services
- **dependsOn**: none
- **parameters**: sku=PerGB2018, retentionInDays=90
- **outputs**: id, customerId
- **docs**: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/

### 7. Application Insights
- **name**: appi-{env}
- **kind**: Raw
- **type**: Microsoft.Insights/components@2020-02-02
- **purpose**: APM telemetry, distributed tracing
- **dependsOn**: Log Analytics
- **parameters**: Application_Type=web, WorkspaceResourceId=logAnalytics.id, DisableLocalAuth=true
- **outputs**: connectionString, id
- **docs**: https://learn.microsoft.com/en-us/azure/azure-monitor/app/

### 8. Action Group
- **name**: ag-{env}
- **kind**: Raw
- **type**: Microsoft.Insights/actionGroups@2023-01-01
- **purpose**: Alert notification routing (email + webhook)
- **dependsOn**: none
- **parameters**: enabled=true, emailReceivers, webhookReceivers
- **outputs**: id
- **docs**: https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/

### 9. Metric Alerts (x2)
- **names**: alert-errors-{env}, alert-latency-{env}
- **kind**: Raw
- **type**: Microsoft.Insights/metricAlerts@2018-03-01
- **purpose**: High error rate + API latency p99 alerts
- **dependsOn**: Application Insights, Action Group
- **docs**: https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/

### 10. Container Apps Environment
- **name**: cae-{env}
- **kind**: Raw
- **type**: Microsoft.App/managedEnvironments@2024-03-01
- **purpose**: Shared runtime for API, Agents, Ingestion containers
- **dependsOn**: Log Analytics (for log destination)
- **parameters**: appLogsConfiguration with Log Analytics integration
- **outputs**: id
- **docs**: https://learn.microsoft.com/en-us/azure/container-apps/

### 11. Container App: API
- **name**: ca-api-{env}
- **kind**: Raw
- **type**: Microsoft.App/containerApps@2024-03-01
- **purpose**: FastAPI orchestration service
- **dependsOn**: CAE, ACR, Cosmos, Storage, Redis, OpenAI, App Insights
- **tags**: azd-service-name=api
- **parameters**: external ingress port 8000, 1-4 replicas, SystemAssigned identity
- **docs**: https://learn.microsoft.com/en-us/azure/container-apps/

### 12. Container App: Agents
- **name**: ca-agents-{env}
- **kind**: Raw
- **type**: Microsoft.App/containerApps@2024-03-01
- **purpose**: Agent runtime (monitoring, risk assessment, evacuation, resource, communication)
- **dependsOn**: CAE, ACR, Cosmos, Redis, OpenAI, App Insights, API
- **tags**: azd-service-name=agents
- **parameters**: internal ingress port 8080, 1-3 replicas

### 13. Container App: Ingestion Worker
- **name**: ca-ingest-{env}
- **kind**: Raw
- **type**: Microsoft.App/containerApps@2024-03-01
- **purpose**: Background polling pipelines for 35+ data sources
- **dependsOn**: CAE, ACR, Cosmos, Storage, Redis, App Insights
- **tags**: azd-service-name=ingestion
- **parameters**: internal ingress port 8081, 1-6 replicas, CPU scaling rule at 70%

### 14. App Service Plan
- **name**: plan-{env}
- **kind**: Raw
- **type**: Microsoft.Web/serverfarms@2023-12-01
- **purpose**: Linux hosting plan for Next.js web app
- **dependsOn**: none
- **parameters**: sku=B1, kind=linux, reserved=true

### 15. Web App
- **name**: app-{env}-{suffix}
- **kind**: Raw
- **type**: Microsoft.Web/sites@2023-12-01
- **purpose**: Next.js 15 web dashboard
- **dependsOn**: App Service Plan, API Container App, App Insights
- **tags**: azd-service-name=web
- **parameters**: NODE|20-lts, httpsOnly=true

## Implementation Plan

| ID | Phase | Task | Resources |
|----|-------|------|-----------|
| TASK-001 | 1 | Create monitoring module (Log Analytics, App Insights, Action Group, Alerts) | 6, 7, 8, 9 |
| TASK-002 | 2 | Create core services module (Storage, Cosmos DB, Redis, OpenAI, ACR) | 1, 2, 3, 4, 5 |
| TASK-003 | 3 | Create compute module (CAE, 3 Container Apps, App Service Plan, Web App) | 10-15 |
| TASK-004 | 4 | Create main orchestrator referencing all modules | all |
| TASK-005 | 5 | Validate: restore, build, format, lint, dead code, secrets, naming, AU region | all |

## Design Notes

- API version upgrade: Container Apps from 2023-05-01 to 2024-03-01 for KEDA scaling and Log Analytics integration
- CAE linked to Log Analytics for centralised container logging
- ACR credentials passed via secrets (not Key Vault) for initial deployment simplicity
- Managed identities on all compute resources for future RBAC-based auth
- All outputs consumed by azd environment and seed scripts
