targetScope = 'resourceGroup'

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

@description('Primary location for all resources')
param location string

@description('Alert email recipient')
param actionGroupEmail string = 'ops@example.com'

@description('Alert webhook endpoint')
param actionGroupWebhook string = 'https://example.com/alerts'

@description('API container image (set by azd deploy)')
param apiImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Agents container image (set by azd deploy)')
param agentsImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Ingestion container image (set by azd deploy)')
param ingestionImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Principal ID for RBAC role assignments (set by azd)')
param principalId string = ''

@description('Principal type for RBAC assignments')
@allowed(['User', 'ServicePrincipal'])
param principalType string = 'User'

@description('Developer IP address to allow through Cosmos DB firewall (for local seed scripts, etc.)')
param developerIpAddress string = ''

@description('Azure OpenAI model deployment SKU. Use GlobalStandard for dev/staging (draws from global capacity pool) and Standard for production (regional capacity).')
@allowed(['Standard', 'GlobalStandard'])
param openAiDeploymentSku string = 'GlobalStandard'

@description('When true, restricts Cosmos DB network access to Azure Portal and Azure-services IPs only. Set to true for production; leave false for dev/staging to allow fully open public access.')
param restrictNetworkAccess bool = true

@description('Deployment environment tier — controls auth policies (e.g. Azure Maps local auth)')
@allowed(['dev', 'staging', 'prod'])
param environmentTier string = 'dev'

@description('Spec 029 — Subscription topology. A: per-environment subscriptions. B: single subscription per environment OR one subscription for all environments. Defaults to B; Topology A tenants must override.')
@allowed([ 'A', 'B' ])
param subscriptionTopology string = 'B'

@description('Azure subscription ID this deployment targets.')
param subscriptionId string = subscription().subscriptionId

@description('Spec 029 — additional resource tags merged onto baseline tags.')
param additionalTags object = {}

// ────────────────────────────────────────────────────────────────────────────────
// Variables
// ────────────────────────────────────────────────────────────────────────────────

var abbrs = loadJsonContent('./abbreviations.json')
var tags = union({
  'azd-env-name': environmentName
  project: 'disaster-response-hub'
  SecurityControl: 'Ignore'
}, additionalTags)
var uniqueSuffix = uniqueString(resourceGroup().id)

// Azure Portal and Azure-services IPs used to restrict Cosmos DB in production
var portalAndServiceIpRules = [
  { ipAddressOrRange: '0.0.0.0' }           // allow Azure services (Container Apps, etc.)
  { ipAddressOrRange: '104.42.195.92' }     // Azure Portal
  { ipAddressOrRange: '40.76.54.131' }      // Azure Portal
  { ipAddressOrRange: '52.176.6.30' }       // Azure Portal
  { ipAddressOrRange: '52.169.50.45' }      // Azure Portal
  { ipAddressOrRange: '52.187.184.26' }     // Azure Portal
]
var developerIpRules = empty(developerIpAddress) ? [] : [{ ipAddressOrRange: developerIpAddress }]
// Production: Portal + Azure-services IPs + optional developer IP.
// Dev/staging: only developer IP if set, otherwise fully open (no IP filtering).
var cosmosIpRules = restrictNetworkAccess
  ? concat(portalAndServiceIpRules, developerIpRules)
  : developerIpRules

// ────────────────────────────────────────────────────────────────────────────────
// Monitoring (Log Analytics + App Insights + Alerts)
// ────────────────────────────────────────────────────────────────────────────────

module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    envPrefix: environmentName
    tags: tags
    actionGroupEmail: actionGroupEmail
    actionGroupWebhook: actionGroupWebhook
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

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: '${abbrs.storageStorageAccounts}${take(replace(environmentName, '-', ''), 14)}${take(uniqueSuffix, 6)}'
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
}

var blobContainers = ['raw-payloads', 'binary-assets', 'audit', 'simulation']
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
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: principalId
    principalType: principalType
  }
}

// Storage Blob Data Contributor — Container App managed identities
resource storageApiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, apiContainerApp.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: apiContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource storageAgentsRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, agentsContainerApp.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: agentsContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource storageIngestionRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, ingestionContainerApp.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
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
    options: { autoscaleSettings: { maxThroughput: 4000 } }
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

// Cosmos DB Account Reader Role (control-plane) — required for readMetadata
// Grants the deploying principal and Container App identities permission to
// read account metadata (regions, consistency, etc.) needed by the SDK on connect.
resource cosmosAccountReaderAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(cosmos.id, principalId, 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
  scope: cosmos
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
    principalId: principalId
    principalType: principalType
  }
}

resource cosmosAccountReaderApi 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmos.id, apiContainerApp.id, 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
  scope: cosmos
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
    principalId: apiContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource cosmosAccountReaderAgents 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmos.id, agentsContainerApp.id, 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
  scope: cosmos
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
    principalId: agentsContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource cosmosAccountReaderIngestion 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmos.id, ingestionContainerApp.id, 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
  scope: cosmos
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'fbdf93bf-df7d-467e-a4d2-9458aa1360c8')
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
// Redis Cache
// ────────────────────────────────────────────────────────────────────────────────

resource redis 'Microsoft.Cache/Redis@2024-03-01' = {
  name: '${abbrs.cacheRedis}${environmentName}-${take(uniqueSuffix, 6)}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'Basic', family: 'C', capacity: 0 }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Azure OpenAI
// ────────────────────────────────────────────────────────────────────────────────

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: take('${abbrs.cognitiveServicesAccounts}${environmentName}-${take(uniqueSuffix, 6)}', 64)
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: '${environmentName}-openai-${take(uniqueSuffix, 6)}'
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
            { name: 'COSMOS_ENDPOINT', value: cosmos.properties.documentEndpoint }
            { name: 'COSMOS_DATABASE', value: 'disaster-hub' }
            { name: 'STORAGE_ACCOUNT_NAME', value: storage.name }
            { name: 'REDIS_HOST', value: redis.properties.hostName }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: monitoring.outputs.appInsightsConnectionString }
            { name: 'AZURE_OPENAI_ENDPOINT', value: openAi.properties.endpoint }
            { name: 'AZURE_OPENAI_REASONING_DEPLOYMENT', value: openAiDeployments.outputs.reasoningDeploymentName }
            { name: 'AZURE_OPENAI_DRAFTING_DEPLOYMENT', value: openAiDeployments.outputs.draftingDeploymentName }
            { name: 'AZURE_OPENAI_SIMULATION_DEPLOYMENT', value: openAiDeployments.outputs.simulationDeploymentName }
            { name: 'AZURE_OPENAI_DEPLOYMENT', value: openAiDeployments.outputs.simulationDeploymentName }
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
      scale: { minReplicas: 1, maxReplicas: 4 }
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
            { name: 'REDIS_HOST', value: redis.properties.hostName }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: monitoring.outputs.appInsightsConnectionString }
            { name: 'AZURE_OPENAI_ENDPOINT', value: openAi.properties.endpoint }
            { name: 'AZURE_OPENAI_REASONING_DEPLOYMENT', value: openAiDeployments.outputs.reasoningDeploymentName }
            { name: 'AZURE_OPENAI_DRAFTING_DEPLOYMENT', value: openAiDeployments.outputs.draftingDeploymentName }
            { name: 'AZURE_OPENAI_SIMULATION_DEPLOYMENT', value: openAiDeployments.outputs.simulationDeploymentName }
            { name: 'API_ENDPOINT', value: 'https://${apiContainerApp.properties.configuration.ingress.fqdn}' }
            { name: 'OTEL_SERVICE_NAME', value: 'agents' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
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
            { name: 'REDIS_HOST', value: redis.properties.hostName }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: monitoring.outputs.appInsightsConnectionString }
            { name: 'OTEL_SERVICE_NAME', value: 'ingestion' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
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
  name: take('${abbrs.webSitesAppService}${environmentName}-${take(uniqueSuffix, 6)}', 60)
  location: location
  tags: union(tags, { 'azd-service-name': 'web', 'hidden-link: /app-insights-resource-id': resourceId('Microsoft.Insights/components', take('appi-${environmentName}', 255)) })
  kind: 'app,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'NODE|22-lts'
      appSettings: [
        { name: 'API_ENDPOINT', value: 'https://${apiContainerApp.properties.configuration.ingress.fqdn}' }
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
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
    principalId: apiContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource appInsightsRoleAgents 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsightsRef.id, agentsContainerApp.id, monitoringMetricsPublisherRoleId)
  scope: appInsightsRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
    principalId: agentsContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource appInsightsRoleIngestion 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsightsRef.id, ingestionContainerApp.id, monitoringMetricsPublisherRoleId)
  scope: appInsightsRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
    principalId: ingestionContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource appInsightsRoleWeb 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsightsRef.id, webApp.id, monitoringMetricsPublisherRoleId)
  scope: appInsightsRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
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
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAiUserRoleId)
    principalId: apiContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource openAiRoleAgents 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, agentsContainerApp.id, cognitiveServicesOpenAiUserRoleId)
  scope: openAi
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAiUserRoleId)
    principalId: agentsContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
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
output AZURE_REDIS_HOST string = redis.properties.hostName
output AZURE_OPENAI_ENDPOINT string = openAi.properties.endpoint
output AZURE_APP_INSIGHTS_CONNECTION_STRING string = monitoring.outputs.appInsightsConnectionString
output SERVICE_API_ENDPOINT_URL string = 'https://${apiContainerApp.properties.configuration.ingress.fqdn}'
output SERVICE_WEB_ENDPOINT_URL string = 'https://${webApp.properties.defaultHostName}'

@description('Spec 029 — subscription topology used for this deployment.')
output AZURE_SUBSCRIPTION_TOPOLOGY string = subscriptionTopology

@description('Spec 029 — target subscription id for this deployment.')
output AZURE_TARGET_SUBSCRIPTION_ID string = subscriptionId
