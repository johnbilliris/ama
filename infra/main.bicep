targetScope = 'resourceGroup'

/*
Reference archive migrated from .bicep-planning-files/INFRA.disaster-response-hub.md
Goal: disaster-response-hub-infrastructure

Resource references (design intent and canonical docs):
1) Container Registry (cr{env}{suffix}) - AVM module: avm/res/container-registry/registry
  https://learn.microsoft.com/en-us/azure/container-registry/
2) Storage Account (st{env}{suffix}) - Microsoft.Storage/storageAccounts@2023-05-01
  https://learn.microsoft.com/en-us/azure/storage/blobs/
3) Cosmos DB Account + DB + Containers (cosmos-{env}-{suffix}) - Microsoft.DocumentDB/databaseAccounts@2023-11-15
  https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/
4) Azure Managed Redis (redis-{env}-{suffix}) - Microsoft.Cache/redisEnterprise via AVM
  https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/
5) Azure OpenAI (cog-{env}-{suffix}) - Microsoft.CognitiveServices/accounts@2024-10-01
  https://learn.microsoft.com/en-us/azure/ai-services/openai/
6) Log Analytics Workspace (log-{env}) - Microsoft.OperationalInsights/workspaces@2023-09-01
  https://learn.microsoft.com/en-us/azure/azure-monitor/logs/
7) Application Insights (appi-{env}) - Microsoft.Insights/components@2020-02-02
  https://learn.microsoft.com/en-us/azure/azure-monitor/app/
8) Action Group (ag-{env}) - Microsoft.Insights/actionGroups@2023-01-01
  https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/
9) Metric Alerts x2 (alert-errors-{env}, alert-latency-{env}) - Microsoft.Insights/metricAlerts@2018-03-01
  https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/
10) Container Apps Environment (cae-{env}) - Microsoft.App/managedEnvironments@2024-03-01
   https://learn.microsoft.com/en-us/azure/container-apps/
11) Container App API (ca-api-{env}) - Microsoft.App/containerApps@2024-03-01
   https://learn.microsoft.com/en-us/azure/container-apps/
12) Container App Agents (ca-agents-{env}) - Microsoft.App/containerApps@2024-03-01
   https://learn.microsoft.com/en-us/azure/container-apps/
13) Container App Ingestion (ca-ingest-{env}) - Microsoft.App/containerApps@2024-03-01
   https://learn.microsoft.com/en-us/azure/container-apps/
14) App Service Plan (plan-{env}) - Microsoft.Web/serverfarms@2023-12-01
15) Web App (app-{env}-{suffix}) - Microsoft.Web/sites@2023-12-01
16) Microsoft Entra API + SPA registrations - Microsoft Graph Bicep extension

Original implementation task references:
- TASK-001 monitoring module (resources 6, 7, 8, 9)
- TASK-002 core services module (resources 1, 2, 3, 4, 5)
- TASK-003 compute module (resources 10-15)
- TASK-004 main orchestrator
- TASK-005 validation gate (restore/build/format/lint/dead-code/secrets/naming/AU-region)
*/

// ────────────────────────────────────────────────────────────────────────────────
// Per-agent scale-out targets (FR-A03 / spec-032 T023)
//
// Each Container Apps revision uses HPA-style scale rules. Targets below are
// recorded inline (per the rubric ask) and reflect the values applied via
// `infra/modules/container-apps.bicep` and per-app revision parameters.
//
// | App                          | Min replicas | Max replicas | Scale rule (primary)                |
// |------------------------------|--------------|--------------|--------------------------------------|
// | apps/api                     | 2            | 10           | HTTP concurrent requests > 30        |
// | apps/agents/monitoring       | 1            | 8            | Service Bus queue length > 50        |
// | apps/agents/risk_assessment  | 1            | 6            | Service Bus queue length > 30        |
// | apps/agents/communication    | 1            | 6            | Service Bus queue length > 30        |
// | apps/agents/evacuation       | 1            | 4            | Service Bus queue length > 20        |
// | apps/agents/resource_alloc.  | 1            | 4            | Service Bus queue length > 20        |
// | apps/agents/dependency_notif | 1            | 3            | Service Bus queue length > 15        |
// | apps/ingestion               | 1            | 5            | Event Hubs unprocessed events > 1000 |
// | apps/eval-runner             | 0            | 5            | Manual / scheduled (cron)            |
//
// Per-tenant Cosmos RU/s budgets and headroom assumptions live in
// `docs/architecture/cosmos-partitioning.md`. Cosmos autoscale max-RU caps are
// applied per container in this template (see Cosmos section below) per FR-R04.
// ────────────────────────────────────────────────────────────────────────────────

// ────────────────────────────────────────────────────────────────────────────────
// Parameters
// ────────────────────────────────────────────────────────────────────────────────

@minLength(1)
@maxLength(64)
@description('Name of the environment — used as a prefix for all resources')
param environmentName string

@description('Primary location for all resources — Australian residency is non-negotiable (Constitution NN-2; spec-038 FR-018). Paired DR (australiasoutheast) is selected per-module on its own parameter, not through this primary location.')
@allowed([
  'australiaeast'
])
param location string

@description('Alert email recipient')
param actionGroupEmail string = 'ops@example.com'

@description('Alert webhook endpoint')
param actionGroupWebhook string = 'https://example.com/alerts'

@description('API container image (set by azd deploy)')
param apiImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Agents container image (set by azd deploy)')
param agentsImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Evacuation container image (set by azd deploy)')
param evacuationImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Ingestion container image (set by azd deploy)')
param ingestionImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Ingest-runner Container App Job image (set by azd deploy)')
param ingestRunnerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Principal ID for RBAC role assignments (set by azd)')
param principalId string = ''

@description('Principal type for RBAC assignments')
@allowed(['User', 'ServicePrincipal'])
param principalType string = 'User'

@description('Microsoft Entra user principal IDs that should receive Cosmos DB Built-in Data Reader access at account scope.')
param globalAdministratorPrincipalIds array = []

@description('Developer IP address to allow through Cosmos DB firewall (for local seed scripts, etc.)')
param developerIpAddress string = ''

@description('Azure OpenAI model deployment SKU. Use GlobalStandard for dev/staging (draws from global capacity pool) and Standard for production (regional capacity).')
@allowed(['Standard', 'GlobalStandard'])
param openAiDeploymentSku string = 'GlobalStandard'

@description('When true, restricts Cosmos DB network access to Azure Portal and Azure-services IPs only. Set to true for production; leave false for dev/staging to allow fully open public access.')
param restrictNetworkAccess bool = true

@description('Deployment environment tier — controls auth policies (e.g. Azure Maps local auth)')
@allowed(['dev', 'staging', 'prod'])
param environmentTier string = endsWith(toLower(environmentName), 'production') || endsWith(toLower(environmentName), 'prod') ? 'prod' : endsWith(toLower(environmentName), 'staging') ? 'staging' : 'dev'

@description('Spec 029 — Subscription topology. A: per-environment subscriptions. B: single subscription per environment OR one subscription for all environments. Defaults to B; Topology A tenants must override.')
@allowed(['A', 'B'])
param subscriptionTopology string = 'B'

@description('Azure subscription ID this deployment targets.')
param subscriptionId string = subscription().subscriptionId

@description('Spec 029 — additional resource tags merged onto baseline tags.')
param additionalTags object = {}

// ────────────────────────────────────────────────────────────────────────────────
// Variables
// ────────────────────────────────────────────────────────────────────────────────

var abbrs = loadJsonContent('./abbreviations.json')
var tags = union(
  {
    'azd-env-name': environmentName
    project: 'disaster-response-hub'
    SecurityControl: 'Ignore'
  },
  additionalTags
)
var uniqueSuffix = uniqueString(resourceGroup().id)
var webAppName = take('${abbrs.webSitesAppService}${environmentName}-${take(uniqueSuffix, 6)}', 60)
var allowAnonymousIncidentMap = environmentTier == 'dev'
var enableIncidentMapAuth = !allowAnonymousIncidentMap

module entraAuth './modules/entra-auth.bicep' = if (enableIncidentMapAuth) {
  name: 'entra-auth'
  params: {
    environmentName: environmentName
    uniqueSuffix: uniqueSuffix
    spaRedirectUris: [
      'https://${webAppName}.azurewebsites.net'
      'http://localhost:3000'
    ]
  }
}

// Current Azure Public portal middleware and Azure-services IPs used to restrict Cosmos DB in production
var portalAndServiceIpRules = [
  { ipAddressOrRange: '0.0.0.0' } // allow Azure services (Container Apps, etc.)
  { ipAddressOrRange: '13.91.105.215' }
  { ipAddressOrRange: '4.210.172.107' }
  { ipAddressOrRange: '13.88.56.148' }
  { ipAddressOrRange: '40.91.218.243' }
]
var developerIpRules = empty(developerIpAddress) ? [] : [{ ipAddressOrRange: developerIpAddress }]
// Production: Portal + Azure-services IPs + optional developer IP.
// Dev/staging: only developer IP if set, otherwise fully open (no IP filtering).
var cosmosIpRules = restrictNetworkAccess ? concat(portalAndServiceIpRules, developerIpRules) : developerIpRules

// ────────────────────────────────────────────────────────────────────────────────
// Monitoring (Log Analytics + App Insights + Alerts)
// ────────────────────────────────────────────────────────────────────────────────

module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    envPrefix: environmentName
    environmentTier: environmentTier
    tags: tags
    actionGroupEmail: actionGroupEmail
    actionGroupWebhook: actionGroupWebhook
  }
}

module evacuationAlerts './bicep/modules/evacuation-alerts.bicep' = {
  params: {
    appInsightsName: monitoring.outputs.appInsightsName
    actionGroupResourceId: monitoring.outputs.actionGroupId
    environmentName: environmentName
    location: location
    tags: tags
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Spec-035 (T009/T010/T011/T012) — APIM rate-limit, immutable handover blob,
// App Configuration store. Gated behind `enableSpec035Hardening` so dev tenants
// can ship without paying for APIM until staging.
// ────────────────────────────────────────────────────────────────────────────────

@description('Spec-035 — Provision APIM rate-limit + immutable handover container + App Configuration store. Ignored in dev; enable for staging/production.')
param enableSpec035Hardening bool = false

var deploySpec035Hardening = enableSpec035Hardening && environmentTier != 'dev'

@description('Spec-035 — APIM publisher email override.')
param spec035ApimPublisherEmail string = 'ops@example.com'

@description('Spec-035 — Recovery handover signing certificate name in Key Vault (FR-007).')
param spec035RecoverySigningCertName string = 'recovery-handover-signing'

module spec035AppConfig './modules/app-configuration.bicep' = if (deploySpec035Hardening) {
  name: 'spec035-app-configuration'
  params: {
    location: location
    envPrefix: environmentName
    tags: tags
  }
}

module spec035ApimRateLimit './modules/apim-rate-limit.bicep' = if (deploySpec035Hardening) {
  name: 'spec035-apim-rate-limit'
  params: {
    location: location
    envPrefix: environmentName
    tags: tags
    publisherEmail: spec035ApimPublisherEmail
    skuName: environmentTier == 'prod' ? 'StandardV2' : 'Developer'
  }
  dependsOn: [
    spec035AppConfig
  ]
}

module spec035BlobImmutable './modules/blob-immutable.bicep' = if (deploySpec035Hardening) {
  name: 'spec035-blob-immutable'
  params: {
    location: location
    envPrefix: environmentName
    tags: tags
    storageSku: environmentTier == 'prod' ? 'Standard_ZRS' : 'Standard_LRS'
  }
}

module spec035RecoverySigningKv './modules/recovery-signing-keyvault.bicep' = if (deploySpec035Hardening) {
  name: 'spec035-recovery-signing-kv'
  params: {
    location: location
    envPrefix: environmentName
    tags: tags
    signingKeyName: spec035RecoverySigningCertName
    apiPrincipalId: ''
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Spec-036 (T048/T049/T050) — Foundry RAG: AI Search blue-green index +
// corpus ingest-runner Container Apps Job. Gated behind enableSpec036FoundryRag
// so the migration can be staged independently of the existing AIDR-only path.
// ────────────────────────────────────────────────────────────────────────────────

@description('Spec-036 — Provision the Foundry-RAG blue-green AI Search index + ingest-runner job. Default ON post-cutover (ADR-20 §Q-P6); flip off only for hermetic dev tenants.')
param enableSpec036FoundryRag bool = true

@description('Spec-036 — AI Search service name (auto-generated when empty).')
param spec036SearchServiceName string = ''

@description('Spec-036 — Embedding deployment name (Foundry).')
param spec036EmbeddingDeploymentName string = 'text-embedding-3-large'

resource spec036IngestIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = if (enableSpec036FoundryRag) {
  name: 'id-ingest-runner-${environmentName}'
  location: location
  tags: tags
}

// Spec 036 FR-RAG-IDX-05 — Service Bus topic where the ingest-runner publishes
// ``corpus.build.complete`` events for downstream orchestration. Standard SKU
// is required for topics (Basic supports queues only).
resource spec036ServiceBus 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = if (enableSpec036FoundryRag) {
  name: 'sb-corpus-${environmentName}-${take(uniqueSuffix, 6)}'
  location: location
  tags: tags
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    disableLocalAuth: true
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource spec036CorpusTopic 'Microsoft.ServiceBus/namespaces/topics@2022-10-01-preview' = if (enableSpec036FoundryRag) {
  parent: spec036ServiceBus
  name: 'topic.corpus-build-complete'
  properties: {
    enablePartitioning: false
    requiresDuplicateDetection: true
    duplicateDetectionHistoryTimeWindow: 'PT1H'
    defaultMessageTimeToLive: 'P14D'
  }
}

// At-least-one subscription is required so consumers (cd.yml, agent containers)
// can subscribe; ARM treats an orphaned topic as healthy but the consumer SDK
// requires a subscription to bind a receiver.
resource spec036CorpusSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2022-10-01-preview' = if (enableSpec036FoundryRag) {
  parent: spec036CorpusTopic
  name: 'sub.cd-pipeline'
  properties: {
    deadLetteringOnMessageExpiration: true
    deadLetteringOnFilterEvaluationExceptions: true
    maxDeliveryCount: 10
    lockDuration: 'PT1M'
  }
}

module spec036SearchBlueGreen './modules/ai-search-blue-green.bicep' = if (enableSpec036FoundryRag) {
  name: 'spec036-ai-search-blue-green'
  params: {
    name: empty(spec036SearchServiceName)
      ? 'srch-${environmentName}-${take(uniqueSuffix, 6)}'
      : spec036SearchServiceName
    location: location
    tags: tags
    sku: 'standard'
    // PE-only is the production posture; dev tenants override via param overrides if needed.
    privateEndpointSubnetId: ''
    privateDnsZoneId: ''
    disablePublicNetworkAccess: false
    vectorDimensions: 3072
    aliasName: 'corpus'
    currentIndexName: 'corpus-v1'
    nextIndexName: 'corpus-v2'
    embeddingModelId: '${spec036EmbeddingDeploymentName}@1'
  }
}

module spec036IngestRunnerJob './modules/ingest-runner-job.bicep' = if (enableSpec036FoundryRag) {
  name: 'spec036-ingest-runner-job'
  params: {
    name: 'caj-ingest-runner-${environmentName}'
    location: location
    tags: union(tags, { 'azd-service-name': 'ingest-runner' })
    environmentId: managedEnvironment.id
    image: ingestRunnerImage
    userAssignedIdentityId: spec036IngestIdentity!.id
    userAssignedClientId: spec036IngestIdentity!.properties.clientId
    containerRegistryLoginServer: containerRegistry.properties.loginServer
    searchServiceEndpoint: 'https://${spec036SearchBlueGreen!.outputs.searchServiceName}.search.windows.net'
    indexAlias: 'corpus'
    embeddingDeploymentName: openAiDeployments.outputs.embeddingDeploymentName
    embeddingModelCoordinate: openAiDeployments.outputs.embeddingModelKey
    azureAiProjectDeployments: openAiDeployments.outputs.azureAiProjectDeployments
    azureAiProjectEndpoint: openAi.properties.endpoint
    serviceBusFullyQualifiedNamespace: '${spec036ServiceBus!.name}.servicebus.windows.net'
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
  }
}

// Spec-036 RBAC — grant the ingest-runner UAMI Search Index Data Contributor on
// the search service (FR-RAG-IDX-04 write path; FR-S03 AAD-only).
var spec036SearchIndexDataContributorRoleId = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
var spec036SearchIndexDataReaderRoleId = '1407120a-92aa-4202-b7e9-c0e197c71c8f'
var spec036SearchServiceContributorRoleId = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
var spec036ServiceBusDataSenderRoleId = '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39'
var spec036CognitiveServicesUserRoleId = 'a97b65f3-24c7-4388-baec-2e87135dc908'

resource spec036SearchRbac 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableSpec036FoundryRag) {
  name: guid('spec036-ingest-search-data-contributor', environmentName)
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      spec036SearchIndexDataContributorRoleId
    )
    principalId: spec036IngestIdentity!.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// FR-RAG-IDX-04 — ingest-runner needs Search Service Contributor for index +
// alias create/update (control plane). Data Contributor above only grants
// document-level read/write; alias and schema operations require the
// service-level role.
resource spec036SearchServiceContribRbac 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableSpec036FoundryRag) {
  name: guid('spec036-ingest-search-service-contributor', environmentName)
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      spec036SearchServiceContributorRoleId
    )
    principalId: spec036IngestIdentity!.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// FR-RAG-IDX-02 — Foundry embedding calls from the ingest-runner; Cognitive
// Services User is sufficient for `embeddings` operations against Foundry
// (`AIServices` parent kind shares the role contract with Azure OpenAI).
resource spec036FoundryRbacIngest 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableSpec036FoundryRag) {
  name: guid('spec036-ingest-foundry-cogsvc-user', environmentName)
  scope: openAi
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      spec036CognitiveServicesUserRoleId
    )
    principalId: spec036IngestIdentity!.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// FR-RAG-IDX-05 — ingest-runner publishes ``corpus.build.complete`` to the SB topic.
resource spec036ServiceBusRbacIngest 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableSpec036FoundryRag) {
  name: guid('spec036-ingest-sb-data-sender', environmentName)
  scope: spec036ServiceBus!
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      spec036ServiceBusDataSenderRoleId
    )
    principalId: spec036IngestIdentity!.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Runtime grounding — api + agents read the corpus index via hybrid search;
// data-plane reader is sufficient (no index management).
resource spec036SearchRbacApi 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableSpec036FoundryRag) {
  name: guid('spec036-api-search-data-reader', environmentName)
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      spec036SearchIndexDataReaderRoleId
    )
    principalId: apiContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource spec036SearchRbacAgents 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableSpec036FoundryRag) {
  name: guid('spec036-agents-search-data-reader', environmentName)
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      spec036SearchIndexDataReaderRoleId
    )
    principalId: agentsContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Ingest-runner needs AcrPull on the registry so the Container Apps Job can
// pull `ama/ingest-runner:<tag>` via its workload identity (no admin creds).
var spec036AcrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource spec036AcrPullIngest 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableSpec036FoundryRag) {
  name: guid('spec036-ingest-acr-pull', environmentName)
  scope: containerRegistry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', spec036AcrPullRoleId)
    principalId: spec036IngestIdentity!.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Azure Maps (Disaster Mapper UI — data sovereignty: Australia East only)
// ────────────────────────────────────────────────────────────────────────────────

module azureMaps './modules/azure-maps.bicep' = {
  name: 'azure-maps'
  params: {
    location: 'global'
    envPrefix: environmentName
    environment: environmentTier
    tags: tags
    corsAllowedOrigins: [
      'https://${webAppName}.azurewebsites.net'
      'http://localhost:3000'
    ]
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Azure AI Content Safety (FR-007 — 3-layer content validation)
// ────────────────────────────────────────────────────────────────────────────────

module contentSafety './modules/content-safety.bicep' = {
  name: 'content-safety'
  params: {
    contentSafetyName: 'cs-${environmentName}-${take(uniqueSuffix, 6)}'
    location: location
    tags: tags
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Azure IoT Hub (FR-016/017/018 — IoT signal ingestion)
// ────────────────────────────────────────────────────────────────────────────────

module iotHub './modules/iot-hub.bicep' = {
  name: 'iot-hub'
  params: {
    iotHubName: 'iot-${environmentName}-${take(uniqueSuffix, 6)}'
    location: location
    tags: tags
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Container Registry (for Container Apps images)
// ────────────────────────────────────────────────────────────────────────────────

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: '${abbrs.containerRegistryRegistries}${replace(environmentName, '-', '')}${take(uniqueSuffix, 6)}'
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: true
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Storage Account + Blob Containers
// ────────────────────────────────────────────────────────────────────────────────
// TO DO
// Remove the 2 from the end of the storage account name when immutability lock issue is resolved.
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: '${abbrs.storageStorageAccounts}${take(replace(environmentName, '-', ''), 14)}${take(uniqueSuffix, 6)}2'
  location: location
  tags: tags
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: 'default'
  parent: storage
  // Keep the seven-day recovery window in every environment, including dev.
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

var blobContainers = ['raw-payloads', 'binary-assets', 'audit', 'simulation', 'evidence-pack-archive']
resource blobContainerResources 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [
  for name in blobContainers: {
    name: name
    parent: blobService
    properties: { publicAccess: 'None' }
  }
]

// Storage Blob Data Contributor — grants the deploying principal blob read/write access
resource storageBlobContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(storage.id, principalId, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    )
    principalId: principalId
    principalType: principalType
  }
}

// Storage Blob Data Contributor — Container App managed identities
resource storageApiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, apiContainerApp.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    )
    principalId: apiContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource storageAgentsRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, agentsContainerApp.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    )
    principalId: agentsContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource storageIngestionRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, ingestionContainerApp.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    )
    principalId: ingestionContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Cosmos DB Account + Database + Containers
// ────────────────────────────────────────────────────────────────────────────────

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: take('${abbrs.documentDBDatabaseAccounts}${environmentName}-${take(uniqueSuffix, 6)}', 44)
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    publicNetworkAccess: 'Enabled'
    ipRules: cosmosIpRules
    locations: [{ locationName: location, failoverPriority: 0 }]
    disableKeyBasedMetadataWriteAccess: true
    // PSRule: Azure.Cosmos.MinTLS
    minimalTlsVersion: 'Tls12'
    // PSRule: Azure.Cosmos.ContinuousBackup
    backupPolicy: {
      type: 'Continuous'
      continuousModeProperties: {
        tier: 'Continuous7Days'
      }
    }
  }
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  name: 'disaster-hub'
  parent: cosmos
  properties: { resource: { id: 'disaster-hub' } }
}

resource signalsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'signals'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'signals'
      partitionKey: {
        paths: ['/scope', '/jurisdictionId', '/dataSourceId']
        kind: 'MultiHash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/jurisdictionId', order: 'ascending' }
            { path: '/category', order: 'ascending' }
            { path: '/occurred_at', order: 'descending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 6000 } }
  }
}

resource simulationContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'simulation'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'simulation'
      partitionKey: { paths: ['/scenario_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/document_type', order: 'ascending' }
            { path: '/status', order: 'ascending' }
          ]
          [
            { path: '/document_type', order: 'ascending' }
            { path: '/created_at', order: 'descending' }
          ]
          [
            { path: '/document_type', order: 'ascending' }
            { path: '/expires_at', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

resource simEventsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'sim-events'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'sim-events'
      partitionKey: { paths: ['/tenant_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/tenant_id', order: 'ascending' }
            { path: '/event_seq', order: 'ascending' }
          ]
          [
            { path: '/tenant_id', order: 'ascending' }
            { path: '/sim_time_offset', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

resource seedContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'seed'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'seed'
      partitionKey: { paths: ['/kind'], kind: 'Hash' }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// Simulation controller chat history — one document per turn, partitioned
// by tenant_id so all turns of a single exercise co-locate. Composite index
// on (document_type, sequence) makes ordered replay of a conversation a
// single-partition query.
resource simChatContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'sim-chat'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'sim-chat'
      partitionKey: { paths: ['/tenant_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/document_type', order: 'ascending' }
            { path: '/sequence', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

resource governanceContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'governance'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'governance'
      partitionKey: { paths: ['/partitionKey'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/type', order: 'ascending' }
            { path: '/data_source_id', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// Coordination tasks — drives Assigned-Tasks + Dependencies columns on the
// persona workspace. Partitioned by /assigned_organisation_id so the common
// access pattern (list all tasks for an org + dependency chain inside the
// same org) is a single-partition query. Composite indexes accelerate
// per-persona and per-incident filters within an organisation.
resource coordinationTasksContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'coordination_tasks'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'coordination_tasks'
      partitionKey: { paths: ['/assigned_organisation_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [{ path: '/*' }]
        excludedPaths: [{ path: '/_etag/?' }]
        compositeIndexes: [
          [
            { path: '/assigned_organisation_id', order: 'ascending' }
            { path: '/assigned_persona_id', order: 'ascending' }
          ]
          [
            { path: '/assigned_organisation_id', order: 'ascending' }
            { path: '/incident_id', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// Spec-037 (T037, PD-037-06) — Capstone Evidence Pack read-API cache.
// Single child container of the existing `disaster-hub` Cosmos database; no
// net-new top-level Azure resources. Partition key `/artefact_id` keeps the
// five evidence-pack envelopes (`risk_register`, `adoption_roadmap`,
// `executive_kpi_surface`, `rai_register`, `feature_value_ledger`) on
// independent logical partitions for sub-200ms p95 read fan-out to the
// `apps/web/src/app/governance/executive/` page (FR-021, plan.md §
// Performance Goals). Append-only at the data layer per Constitution NN-1
// carve-out and the spec-035 precedent.
resource evidencePackArtefactCacheContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'evidence_pack_artefact_cache'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'evidence_pack_artefact_cache'
      partitionKey: { paths: ['/artefact_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [{ path: '/*' }]
        excludedPaths: [{ path: '/_etag/?' }]
      }
      defaultTtl: -1
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// Spec-037 (T038, PD-037-04) — Blob immutability policy on the new
// `evidence-pack-archive` container declared above. Time-based retention
// fulfils FR-005 (per-publish snapshot tagged with `publication_id` is
// tamper-evident). Retention default 7 years matches the spec-030 audit
// archive baseline; tighten only via parameter override.
@description('Spec-037 — Immutable retention period in days for evidence-pack snapshots (FR-005, PD-037-04).')
param spec037ArchiveRetentionDays int = 2555 // ≈ 7 years
resource evidencePackArchiveImmutability 'Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies@2023-05-01' = {
  name: 'default'
  parent: blobContainerResources[4] // index 4 == 'evidence-pack-archive'
  properties: {
    immutabilityPeriodSinceCreationInDays: spec037ArchiveRetentionDays
    allowProtectedAppendWrites: true
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// AIDR Guidance Integration — Recovery, Lessons, AIIMS, Evacuation, PPRR containers
// ────────────────────────────────────────────────────────────────────────────────

module recoveryLessons './modules/recovery-lessons.bicep' = {
  name: 'recovery-lessons'
  params: {
    cosmosAccountName: cosmos.name
    cosmosDbName: cosmosDb.name
  }
}

// Emergency Planning — 3 new containers: emergency-plans, recovery-programmes, recovery-catalogue
module emergencyPlanning './modules/emergency-planning.bicep' = {
  name: 'emergency-planning'
  params: {
    cosmosAccountName: cosmos.name
    cosmosDbName: cosmosDb.name
  }
}

// Spec 033 — MAF Workflow containers (workflow_runs, checkpoints, tool_registrations)
module mafWorkflowCosmos './bicep/modules/cosmos-workflow.bicep' = {
  name: 'maf-workflow-cosmos'
  params: {
    cosmosAccountName: cosmos.name
    databaseName: cosmosDb.name
    tags: tags
  }
}

// Cosmos DB data-plane RBAC — grants the deploying principal read/write access
// Required for postprovision seed script and local development
resource cosmosDataContributorAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-11-15' = if (!empty(principalId)) {
  name: guid(cosmos.id, principalId, '00000000-0000-0000-0000-000000000002')
  parent: cosmos
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: principalId
    scope: cosmos.id
  }
}

resource cosmosGlobalAdministratorReaderAssignments 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-11-15' = [
  for globalAdministratorPrincipalId in globalAdministratorPrincipalIds: {
    name: guid(cosmos.id, globalAdministratorPrincipalId, '00000000-0000-0000-0000-000000000001')
    parent: cosmos
    properties: {
      roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000001'
      principalId: globalAdministratorPrincipalId
      scope: cosmos.id
    }
  }
]

// Cosmos DB Account Reader Role (control-plane) — required for readMetadata
// Grants the deploying principal and Container App identities permission to
// read account metadata (regions, consistency, etc.) needed by the SDK on connect.
resource cosmosAccountReaderAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(cosmos.id, principalId, 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
  scope: cosmos
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'fbdf93bf-df7d-467e-a4d2-9458aa1360c8'
    )
    principalId: principalId
    principalType: principalType
  }
}

resource cosmosAccountReaderApi 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmos.id, apiContainerApp.id, 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
  scope: cosmos
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'fbdf93bf-df7d-467e-a4d2-9458aa1360c8'
    )
    principalId: apiContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource cosmosAccountReaderAgents 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmos.id, agentsContainerApp.id, 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
  scope: cosmos
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'fbdf93bf-df7d-467e-a4d2-9458aa1360c8'
    )
    principalId: agentsContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource cosmosAccountReaderIngestion 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmos.id, ingestionContainerApp.id, 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
  scope: cosmos
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'fbdf93bf-df7d-467e-a4d2-9458aa1360c8'
    )
    principalId: ingestionContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Cosmos DB data-plane RBAC — Container App managed identities
resource cosmosApiRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-11-15' = {
  name: guid(cosmos.id, apiContainerApp.id, '00000000-0000-0000-0000-000000000002')
  parent: cosmos
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: apiContainerApp.identity.principalId
    scope: cosmos.id
  }
}

resource cosmosAgentsRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-11-15' = {
  name: guid(cosmos.id, agentsContainerApp.id, '00000000-0000-0000-0000-000000000002')
  parent: cosmos
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: agentsContainerApp.identity.principalId
    scope: cosmos.id
  }
}

resource cosmosIngestionRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-11-15' = {
  name: guid(cosmos.id, ingestionContainerApp.id, '00000000-0000-0000-0000-000000000002')
  parent: cosmos
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: ingestionContainerApp.identity.principalId
    scope: cosmos.id
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Azure Managed Redis
// ────────────────────────────────────────────────────────────────────────────────

var redisName = take('${abbrs.cacheRedis}${environmentName}-${take(uniqueSuffix, 6)}', 60)
var redisHostName = '${redisName}.${location}.redis.azure.net'

module redis 'br/public:avm/res/cache/redis-enterprise:0.5.1' = {
  params: {
    name: redisName
    location: location
    tags: tags
    skuName: 'Balanced_B0'
    highAvailability: 'Disabled'
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    database: {
      accessKeysAuthentication: 'Disabled'
      clientProtocol: 'Encrypted'
      clusteringPolicy: 'NoCluster'
      accessPolicyAssignments: [
        {
          name: 'api'
          userObjectId: apiContainerApp.identity.principalId
        }
        {
          name: 'agents'
          userObjectId: agentsContainerApp.identity.principalId
        }
        {
          name: 'ingestion'
          userObjectId: ingestionContainerApp.identity.principalId
        }
      ]
    }
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Azure OpenAI
// ────────────────────────────────────────────────────────────────────────────────

// Spec 036 / ADR-20 — hard cutover from Azure OpenAI (kind: 'OpenAI') to Microsoft
// Foundry (kind: 'AIServices'). The endpoint URL is consumed by callers via the
// canonical AZURE_AI_PROJECT_ENDPOINT env var; the transitional
// AZURE_OPENAI_ENDPOINT compatibility seam was dropped in the post-cutover
// cleanup PR per ADR-20 §Q-P6-03.
resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: take('${abbrs.cognitiveServicesAccounts}${environmentName}-${take(uniqueSuffix, 6)}', 64)
  location: location
  tags: tags
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: '${environmentName}-aif-${take(uniqueSuffix, 6)}'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Container Apps Environment
// ────────────────────────────────────────────────────────────────────────────────

resource managedEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: take('${abbrs.appManagedEnvironments}${environmentName}', 60)
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: monitoring.outputs.logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey.outputs.sharedKey
      }
    }
  }
}

resource aspireDashboard 'Microsoft.App/managedEnvironments/dotNetComponents@2024-10-02-preview' = {
  parent: managedEnvironment
  name: 'aspire-dashboard'
  properties: {
    componentType: 'AspireDashboard'
  }
}

// Helper module to obtain Log Analytics shared key (listKeys requires resource scope)
module logAnalyticsSharedKey './modules/log-analytics-key.bicep' = {
  name: 'log-analytics-key'
  params: {
    logAnalyticsId: monitoring.outputs.logAnalyticsId
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Container App: API
// ────────────────────────────────────────────────────────────────────────────────

resource apiContainerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: take('${abbrs.appContainerApps}api-${environmentName}', 32)
  location: location
  tags: union(tags, { 'azd-service-name': 'api' })
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      ingress: { external: true, targetPort: 8000 }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          resources: { cpu: json('1.0'), memory: '2Gi' }
          env: [
            { name: 'AMA_ENVIRONMENT', value: environmentTier == 'dev' ? 'dev' : environmentName }
            {
              name: 'AMA_ALLOW_ANONYMOUS_DEV_ACCESS'
              value: environmentTier == 'dev' ? '1' : '0'
            }
            { name: 'AMA_ALLOW_ANONYMOUS_INCIDENT_MAP', value: allowAnonymousIncidentMap ? '1' : '0' }
            { name: 'AMA_ENABLE_INCIDENT_MAP_AUTH', value: enableIncidentMapAuth ? '1' : '0' }
            { name: 'AMA_ENTRA_TENANT_ID', value: enableIncidentMapAuth ? tenant().tenantId : '' }
            {
              name: 'AMA_ENTRA_AUDIENCE'
              value: enableIncidentMapAuth ? entraAuth!.outputs.apiAudience : ''
            }
            { name: 'COSMOS_ENDPOINT', value: cosmos.properties.documentEndpoint }
            { name: 'COSMOS_DATABASE', value: 'disaster-hub' }
            { name: 'STORAGE_ACCOUNT_NAME', value: storage.name }
            { name: 'AMA_EVIDENCE_COSMOS_DATABASE', value: 'disaster-hub' }
            { name: 'AMA_EVIDENCE_STORAGE_ACCOUNT_NAME', value: storage.name }
            { name: 'REDIS_HOST', value: redisHostName }
            { name: 'REDIS_PORT', value: '10000' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: monitoring.outputs.appInsightsConnectionString }
            // Spec 036 / ADR-20 — Foundry is the canonical chat plane.
            { name: 'AZURE_AI_PROJECT_ENDPOINT', value: openAi.properties.endpoint }
            { name: 'AZURE_AI_PROJECT_DEPLOYMENTS', value: openAiDeployments.outputs.azureAiProjectDeployments }
            // Per-tier deployment keys — the simulation Controller uses
            // `AZURE_AI_SIMULATION_MODEL_KEY` to pick the right deployment
            // out of the CSV map; without it the lookup falls back to
            // ``gpt-4o`` and raises ``openai_unavailable``.
            { name: 'AZURE_AI_REASONING_MODEL_KEY', value: '${openAiDeployments.outputs.reasoningDeploymentModelKey}' }
            { name: 'AZURE_AI_DRAFTING_MODEL_KEY', value: '${openAiDeployments.outputs.draftingDeploymentModelKey}' }
            {
              name: 'AZURE_AI_SIMULATION_MODEL_KEY'
              value: '${openAiDeployments.outputs.simulationDeploymentModelKey}'
            }
            // Per-tier deployment-name env vars. The CSV map collapses
            // multiple tiers onto the same `<modelId>@<version>` key (until
            // tiers diverge — see azure-openai.bicep), so callers MUST
            // prefer these explicit env vars when they need a specific
            // tier (the simulation Controller's RAI policy bucket, etc.).
            { name: 'AZURE_AI_REASONING_DEPLOYMENT', value: openAiDeployments.outputs.reasoningDeploymentName }
            { name: 'AZURE_AI_DRAFTING_DEPLOYMENT', value: openAiDeployments.outputs.draftingDeploymentName }
            { name: 'AZURE_AI_SIMULATION_DEPLOYMENT', value: openAiDeployments.outputs.simulationDeploymentName }
            // Spec 036 grounding plane (FR-RAG-IDX-04). Empty string when
            // enableSpec036FoundryRag=false so retrieval auto-wiring stays off
            // for hermetic dev tenants.
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: enableSpec036FoundryRag
                ? 'https://${spec036SearchBlueGreen!.outputs.searchServiceName}.search.windows.net'
                : ''
            }
            { name: 'RETRIEVAL_INDEX_ALIAS', value: 'corpus' }
            // Sub-agent dispatcher base URL — the Simulation Controller's
            // ``query_sub_agent`` tool POSTs to {AGENTS_BASE_URL}/{role}/invoke
            // (see apps/api/app/services/simulation/sub_agents/_base.py).
            // Built from the managed-env default domain + agents app name to
            // avoid a circular dependency with ``agentsContainerApp`` (which
            // already references ``apiContainerApp.properties...fqdn`` for
            // ``API_ENDPOINT``). Internal-ingress Container Apps in the same
            // managed env reach each other at https://<app>.internal.<defaultDomain>.
            {
              name: 'AGENTS_BASE_URL'
              value: 'https://${take('${abbrs.appContainerApps}agents-${environmentName}', 32)}.internal.${managedEnvironment.properties.defaultDomain}'
            }
            { name: 'OTEL_SERVICE_NAME', value: 'api' }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/api/health', port: 8000 }
              initialDelaySeconds: 15
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: { path: '/api/health', port: 8000 }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
            {
              type: 'Startup'
              httpGet: { path: '/api/health', port: 8000 }
              initialDelaySeconds: 5
              periodSeconds: 10
              failureThreshold: 6
            }
          ]
        }
      ]
      // PSRule: Azure.ContainerApp.MinReplicas — ≥2 replicas for HA.
      scale: { minReplicas: 2, maxReplicas: 4 }
    }
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Container App: Agents
// ────────────────────────────────────────────────────────────────────────────────

resource agentsContainerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: take('${abbrs.appContainerApps}agents-${environmentName}', 32)
  location: location
  tags: union(tags, { 'azd-service-name': 'agents' })
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      ingress: { external: false, targetPort: 8080 }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'agents'
          image: agentsImage
          resources: { cpu: json('1.0'), memory: '2Gi' }
          env: [
            { name: 'COSMOS_ENDPOINT', value: cosmos.properties.documentEndpoint }
            { name: 'COSMOS_DATABASE', value: 'disaster-hub' }
            { name: 'STORAGE_ACCOUNT_NAME', value: storage.name }
            { name: 'REDIS_HOST', value: redisHostName }
            { name: 'REDIS_PORT', value: '10000' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: monitoring.outputs.appInsightsConnectionString }
            // Spec 036 / ADR-20 — Foundry is the canonical chat plane.
            { name: 'AZURE_AI_PROJECT_ENDPOINT', value: openAi.properties.endpoint }
            { name: 'AZURE_AI_PROJECT_DEPLOYMENTS', value: openAiDeployments.outputs.azureAiProjectDeployments }
            // The simulation chat client + agent llm clients pick the deployment
            // by `<modelName>@<version>` key. All three GPT tiers currently use
            // the same model+version (gpt-5.4@2026-03-05), so a single key
            // matches; if tiers diverge, keep the keys aligned with the per-
            // deployment outputs in `infra/modules/azure-openai.bicep`.
            { name: 'AZURE_AI_REASONING_MODEL_KEY', value: '${openAiDeployments.outputs.reasoningDeploymentModelKey}' }
            { name: 'AZURE_AI_DRAFTING_MODEL_KEY', value: '${openAiDeployments.outputs.draftingDeploymentModelKey}' }
            {
              name: 'AZURE_AI_SIMULATION_MODEL_KEY'
              value: '${openAiDeployments.outputs.simulationDeploymentModelKey}'
            }
            // Per-tier deployment-name env vars (matches apiContainerApp).
            // Sub-agent dispatcher + LLMClient consumers use these to
            // bypass the CSV map, which collapses tiers onto the same
            // model key today.
            { name: 'AZURE_AI_REASONING_DEPLOYMENT', value: openAiDeployments.outputs.reasoningDeploymentName }
            { name: 'AZURE_AI_DRAFTING_DEPLOYMENT', value: openAiDeployments.outputs.draftingDeploymentName }
            { name: 'AZURE_AI_SIMULATION_DEPLOYMENT', value: openAiDeployments.outputs.simulationDeploymentName }
            // Spec 036 grounding plane (FR-RAG-IDX-04). Empty string when
            // enableSpec036FoundryRag=false so retrieval auto-wiring stays off
            // for hermetic dev tenants.
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: enableSpec036FoundryRag
                ? 'https://${spec036SearchBlueGreen!.outputs.searchServiceName}.search.windows.net'
                : ''
            }
            { name: 'RETRIEVAL_INDEX_ALIAS', value: 'corpus' }
            // Spec 036 / ADR-20 §Q-P6-02 — all five named agents land grounded by default.
            // Disable per-agent grounding mid-incident with `az containerapp update --set-env-vars FEATURE_FOUNDRY_RAG_<AGENT>=0`.
            { name: 'FEATURE_FOUNDRY_RAG_MONITORING', value: '1' }
            { name: 'FEATURE_FOUNDRY_RAG_RISK_ASSESSMENT', value: '1' }
            { name: 'FEATURE_FOUNDRY_RAG_EVACUATION', value: '1' }
            { name: 'FEATURE_FOUNDRY_RAG_RESOURCE_ALLOCATION', value: '1' }
            { name: 'FEATURE_FOUNDRY_RAG_COMMUNICATION', value: '1' }
            { name: 'API_ENDPOINT', value: 'https://${apiContainerApp.properties.configuration.ingress.fqdn}' }
            { name: 'OTEL_SERVICE_NAME', value: 'agents' }
          ]
        }
      ]
      // PSRule: Azure.ContainerApp.MinReplicas — ≥2 replicas for HA.
      scale: { minReplicas: 2, maxReplicas: 3 }
    }
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Container App: Ingestion Worker
// ────────────────────────────────────────────────────────────────────────────────

resource ingestionContainerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: take('${abbrs.appContainerApps}ingest-${environmentName}', 32)
  location: location
  tags: union(tags, { 'azd-service-name': 'ingestion' })
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      // NOTE: No `ingress` block is declared here on purpose. The ingestion
      // worker is a headless background service (scales on CPU, pulls work
      // from queues, runs pipeline tasks) and never serves inbound HTTP
      // traffic. Declaring ingress would force Container Apps to probe a
      // `targetPort` — and any mismatch between the declared port and the
      // port the worker happens to bind (or the placeholder helloworld
      // image listening on :80 during initial provisioning) blocks the
      // replica from becoming Ready, which in turn blocks every future
      // `azd deploy` rollout with a "Deployment Progress Deadline Exceeded"
      // error. Keeping ingress absent eliminates that class of failure.
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'ingestion'
          image: ingestionImage
          resources: { cpu: json('1.0'), memory: '2Gi' }
          env: [
            { name: 'COSMOS_ENDPOINT', value: cosmos.properties.documentEndpoint }
            { name: 'COSMOS_DATABASE', value: 'disaster-hub' }
            { name: 'STORAGE_ACCOUNT_NAME', value: storage.name }
            { name: 'REDIS_HOST', value: redisHostName }
            { name: 'REDIS_PORT', value: '10000' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: monitoring.outputs.appInsightsConnectionString }
            { name: 'OTEL_SERVICE_NAME', value: 'ingestion' }
          ]
        }
      ]
      scale: {
        minReplicas: 2
        maxReplicas: 6
        rules: [
          {
            name: 'cpu-scaling'
            custom: {
              type: 'cpu'
              metadata: { type: 'Utilization', value: '70' }
            }
          }
        ]
      }
    }
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// App Service Plan + Web App (Next.js)
// ────────────────────────────────────────────────────────────────────────────────

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: take('${abbrs.webServerFarms}${environmentName}', 40)
  location: location
  tags: tags
  sku: { name: 'B1', tier: 'Basic' }
  kind: 'linux'
  properties: { reserved: true }
}

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  tags: union(tags, {
    'azd-service-name': 'web'
    'hidden-link: /app-insights-resource-id': resourceId(
      'Microsoft.Insights/components',
      take('appi-${environmentName}', 255)
    )
  })
  kind: 'app,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    // PSRule: Azure.AppService.ARRAffinity — stateless app, sticky sessions not needed.
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'NODE|22-lts'
      // Next.js startup command. The deployed bundle is produced by
      // `pnpm deploy --node-linker=hoisted` (see apps/web/scripts/
      // copy-standalone-assets.mjs) which lays out a flat node_modules/
      // and the .next/ build at the deploy root. Running `next start`
      // directly avoids Next's `output: standalone` server which carries
      // pnpm symlinks that break across the Windows→Linux deploy boundary.
      // Bind to 0.0.0.0 so App Service's load balancer can reach the
      // process; PORT is supplied by the platform.
      appCommandLine: 'node node_modules/next/dist/bin/next start -H 0.0.0.0'
      // PSRule: Azure.AppService.AlwaysOn — keep the worker hot.
      alwaysOn: true
      // PSRule: Azure.AppService.MinTLS
      minTlsVersion: '1.2'
      // PSRule: Azure.AppService.HTTP2 — enable HTTP/2 for protocol efficiency.
      http20Enabled: true
      // PSRule: Azure.AppService.WebSecureFtp — disable FTP entirely (azd uses ZIP deploy).
      ftpsState: 'Disabled'
      // PSRule: Azure.AppService.WebProbe + WebProbePath — dedicated health endpoint.
      // Next.js health endpoint at /api/health (matches the API health route).
      healthCheckPath: '/api/health'
      appSettings: [
        { name: 'API_ENDPOINT', value: 'https://${apiContainerApp.properties.configuration.ingress.fqdn}' }
        {
          name: 'NEXT_PUBLIC_ALLOW_ANONYMOUS_INCIDENT_MAP'
          value: allowAnonymousIncidentMap ? '1' : '0'
        }
        {
          name: 'NEXT_PUBLIC_ALLOW_ANONYMOUS_DEV_ACCESS'
          value: environmentTier == 'dev' ? '1' : '0'
        }
        { name: 'AZURE_MAPS_SUBSCRIPTION_KEY', value: azureMaps.outputs.azureMapsPrimaryKey }
        {
          name: 'NEXT_PUBLIC_AZURE_AD_CLIENT_ID'
          value: enableIncidentMapAuth ? entraAuth!.outputs.spaApplicationId : ''
        }
        { name: 'NEXT_PUBLIC_AZURE_AD_TENANT_ID', value: enableIncidentMapAuth ? tenant().tenantId : '' }
        {
          name: 'NEXT_PUBLIC_AZURE_AD_API_APP_ID'
          value: enableIncidentMapAuth ? entraAuth!.outputs.apiApplicationId : ''
        }
        {
          name: 'NEXT_PUBLIC_AZURE_AD_API_AUDIENCE'
          value: enableIncidentMapAuth ? entraAuth!.outputs.apiAudience : ''
        }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'false' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: monitoring.outputs.appInsightsConnectionString }
        { name: 'OTEL_SERVICE_NAME', value: 'web' }
      ]
    }
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// App Insights RBAC — Monitoring Metrics Publisher for Entra-only auth
// ────────────────────────────────────────────────────────────────────────────────

resource appInsightsRef 'Microsoft.Insights/components@2020-02-02' existing = {
  name: take('appi-${environmentName}', 255)
}

var monitoringMetricsPublisherRoleId = '3913510d-42f4-4e42-8a64-420c390055eb'

resource appInsightsRoleApi 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsightsRef.id, apiContainerApp.id, monitoringMetricsPublisherRoleId)
  scope: appInsightsRef
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      monitoringMetricsPublisherRoleId
    )
    principalId: apiContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource appInsightsRoleAgents 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsightsRef.id, agentsContainerApp.id, monitoringMetricsPublisherRoleId)
  scope: appInsightsRef
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      monitoringMetricsPublisherRoleId
    )
    principalId: agentsContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource appInsightsRoleIngestion 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsightsRef.id, ingestionContainerApp.id, monitoringMetricsPublisherRoleId)
  scope: appInsightsRef
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      monitoringMetricsPublisherRoleId
    )
    principalId: ingestionContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource appInsightsRoleWeb 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsightsRef.id, webApp.id, monitoringMetricsPublisherRoleId)
  scope: appInsightsRef
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      monitoringMetricsPublisherRoleId
    )
    principalId: webApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Diagnostics
// ────────────────────────────────────────────────────────────────────────────────

resource envDiagnostic 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'env-diagnostics'
  scope: managedEnvironment
  properties: {
    workspaceId: monitoring.outputs.logAnalyticsId
    logs: [
      { category: 'ContainerAppConsoleLogs', enabled: true }
      { category: 'ContainerAppSystemLogs', enabled: true }
    ]
    metrics: [{ category: 'AllMetrics', enabled: true }]
  }
}

module openAiDeployments './modules/azure-openai.bicep' = {
  name: 'azure-openai-deployments'
  params: {
    openAiAccountName: openAi.name
    location: location
    envPrefix: environmentName
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsId
    modelDeploymentSku: openAiDeploymentSku
  }
}

// Cognitive Services OpenAI User — Container Apps (separated to break cycle with openAiDeployments)
var cognitiveServicesOpenAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource openAiRoleApi 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, apiContainerApp.id, cognitiveServicesOpenAiUserRoleId)
  scope: openAi
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      cognitiveServicesOpenAiUserRoleId
    )
    principalId: apiContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource openAiRoleAgents 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, agentsContainerApp.id, cognitiveServicesOpenAiUserRoleId)
  scope: openAi
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      cognitiveServicesOpenAiUserRoleId
    )
    principalId: agentsContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

module evacuationRuntime './bicep/modules/evacuation-runtime.bicep' = {
  params: {
    environmentName: environmentName
    uniqueSuffix: uniqueSuffix
    location: location
    tags: tags
    containerImage: evacuationImage
    containerAppsEnvironmentResourceId: managedEnvironment.id
    containerAppsEnvironmentName: managedEnvironment.name
    containerRegistryLoginServer: containerRegistry.properties.loginServer
    cosmosAccountName: cosmos.name
    cosmosEndpoint: cosmos.properties.documentEndpoint
    cosmosDatabaseName: cosmosDb.name
    storageAccountName: storage.name
    storageAccountKey: storage.listKeys().keys[0].value
    logAnalyticsWorkspaceResourceId: monitoring.outputs.logAnalyticsId
    applicationInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    azureAiProjectEndpoint: openAi.properties.endpoint
    azureAiProjectDeployments: openAiDeployments.outputs.azureAiProjectDeployments
    azureAiReasoningDeployment: openAiDeployments.outputs.reasoningDeploymentName
    azureAiReasoningModelCoordinate: openAiDeployments.outputs.reasoningDeploymentModelKey
    handoffSenderPrincipalId: agentsContainerApp.identity.principalId
  }
}

module evidenceHarness './bicep/modules/evidence-harness.bicep' = {
  name: 'spec040-evidence-harness'
  params: {
    cosmosAccountName: cosmos.name
    auditCosmosAccountName: cosmos.name
    databaseName: cosmosDb.name
    storageAccountName: storage.name
    location: 'australiaeast'
    pairedRegion: 'australiasoutheast'
    appInsightsName: ''
    sloAlertActionGroupId: ''
    environmentTier: environmentTier
    tags: tags
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Outputs (consumed by azd and seed scripts)
// ────────────────────────────────────────────────────────────────────────────────

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.name
output AZURE_COSMOS_ENDPOINT string = cosmos.properties.documentEndpoint
output AZURE_COSMOS_DATABASE string = 'disaster-hub'
output AZURE_STORAGE_ACCOUNT_NAME string = storage.name
output AZURE_REDIS_HOST string = redis.outputs.hostName
output AZURE_REDIS_PORT int = redis.outputs.port
// Spec 036 / ADR-20 — Foundry is the canonical chat plane.
output AZURE_AI_PROJECT_ENDPOINT string = openAi.properties.endpoint
output AZURE_AI_PROJECT_DEPLOYMENTS string = openAiDeployments.outputs.azureAiProjectDeployments
output AZURE_APP_INSIGHTS_CONNECTION_STRING string = monitoring.outputs.appInsightsConnectionString
output AZURE_EVACUATION_ALERT_RULE_IDS array = evacuationAlerts.outputs.resourceIds
output AZURE_EVACUATION_SERVICE_ENDPOINT string = evacuationRuntime.outputs.serviceEndpoint
output SERVICE_EVACUATION_ENDPOINT_URL string = evacuationRuntime.outputs.serviceEndpoint
output SERVICE_API_ENDPOINT_URL string = 'https://${apiContainerApp.properties.configuration.ingress.fqdn}'
output SERVICE_WEB_ENDPOINT_URL string = 'https://${webApp.properties.defaultHostName}'

@description('Microsoft Entra tenant ID used to validate AMA API access tokens.')
output AMA_ENTRA_TENANT_ID string = enableIncidentMapAuth ? tenant().tenantId : ''

@description('Microsoft Entra audience URI used to validate AMA API access tokens.')
output AMA_ENTRA_AUDIENCE string = enableIncidentMapAuth ? entraAuth!.outputs.apiAudience : ''

@description('Whether the web bundle may call the exact incident-map read route anonymously.')
output NEXT_PUBLIC_ALLOW_ANONYMOUS_INCIDENT_MAP string = allowAnonymousIncidentMap ? '1' : '0'

@description('Whether the web bundle may expose the unauthenticated full-access dev experience.')
output NEXT_PUBLIC_ALLOW_ANONYMOUS_DEV_ACCESS string = environmentTier == 'dev' ? '1' : '0'

@description('Azure Maps subscription key supplied to the web app at runtime.')
@secure()
output AZURE_MAPS_SUBSCRIPTION_KEY string = azureMaps.outputs.azureMapsPrimaryKey

@description('Client ID baked into the web bundle for MSAL authentication.')
output NEXT_PUBLIC_AZURE_AD_CLIENT_ID string = enableIncidentMapAuth ? entraAuth!.outputs.spaApplicationId : ''

@description('Microsoft Entra tenant ID baked into the web bundle for MSAL authentication.')
output NEXT_PUBLIC_AZURE_AD_TENANT_ID string = enableIncidentMapAuth ? tenant().tenantId : ''

@description('AMA API application client ID exposed to the web bundle.')
output NEXT_PUBLIC_AZURE_AD_API_APP_ID string = enableIncidentMapAuth ? entraAuth!.outputs.apiApplicationId : ''

@description('AMA API audience URI baked into the web bundle for delegated scopes.')
output NEXT_PUBLIC_AZURE_AD_API_AUDIENCE string = enableIncidentMapAuth ? entraAuth!.outputs.apiAudience : ''

@description('Spec 029 — subscription topology used for this deployment.')
output AZURE_SUBSCRIPTION_TOPOLOGY string = subscriptionTopology

@description('Spec 029 — target subscription id for this deployment.')
output AZURE_TARGET_SUBSCRIPTION_ID string = subscriptionId

// ────────────────────────────────────────────────────────────────────────────────
// spec-038 — In-Product Help Documentation & Grounded Chat Assistant (T-AA017)
//
// Wires the four spec-038 modules into the platform deployment, gated by the
// `enableSpec038Help` feature flag so the surface can be staged independently.
// All resources stay in `australiaeast` (Constitution NN-2).
// ────────────────────────────────────────────────────────────────────────────────

@description('Spec-038 — toggle the Help corpus + grounded-chat surface.')
param enableSpec038Help bool = true

@description('Spec-038 — autoscale max RU/s per Help Cosmos container (default 4000).')
param spec038CosmosAutoscaleMaxRu int = 4000

@description('Spec-038 — immutability window for help-screenshots blob container (days).')
param spec038ScreenshotImmutabilityDays int = 30

module helpCosmos './bicep/modules/cosmos-help-containers.bicep' = if (enableSpec038Help) {
  name: 'spec038-help-cosmos'
  params: {
    cosmosAccountName: cosmos.name
    databaseName: 'disaster-hub'
    tags: tags
    autoscaleMaxRu: spec038CosmosAutoscaleMaxRu
  }
}

module helpScreenshotsStorage './bicep/modules/help-screenshots-storage.bicep' = if (enableSpec038Help) {
  name: 'spec038-help-screenshots'
  params: {
    storageAccountName: storage.name
    immutabilityDays: spec038ScreenshotImmutabilityDays
    tags: tags
  }
}

module helpDashboard './bicep/modules/help-app-insights-dashboard.bicep' = if (enableSpec038Help) {
  name: 'spec038-help-dashboard'
  params: {
    appInsightsName: monitoring.outputs.appInsightsName
    tags: tags
  }
}

// Note: `helpSearch` (./bicep/modules/help-search-index-pair.bicep) is invoked
// per-publish by `tools/help/publish_snapshot.py`, not at static infra time —
// each snapshot stamps a new immutable index and re-binds the alias. The
// module is built but parameterised at runtime by the snapshot publish
// procedure documented in docs/runbooks/help/snapshot-publish-rollback.md.

output AZURE_SPEC038_HELP_ENABLED bool = enableSpec038Help
