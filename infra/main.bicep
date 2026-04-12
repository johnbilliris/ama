targetScope = 'resourceGroup'

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

// ────────────────────────────────────────────────────────────────────────────────
// Variables
// ────────────────────────────────────────────────────────────────────────────────

var abbrs = loadJsonContent('./abbreviations.json')
var tags = {
  'azd-env-name': environmentName
  project: 'disaster-response-hub'
  SecurityControl: 'Ignore'
}
var uniqueSuffix = uniqueString(resourceGroup().id)

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
    ipRules: concat([
      { ipAddressOrRange: '0.0.0.0' }           // allow Azure services (Container Apps, Functions, etc.)
      { ipAddressOrRange: '104.42.195.92' }     // Azure Portal
      { ipAddressOrRange: '40.76.54.131' }      // Azure Portal
      { ipAddressOrRange: '52.176.6.30' }       // Azure Portal
      { ipAddressOrRange: '52.169.50.45' }      // Azure Portal
      { ipAddressOrRange: '52.187.184.26' }     // Azure Portal
    ], empty(developerIpAddress) ? [] : [{ ipAddressOrRange: developerIpAddress }])
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
    disableLocalAuth: false
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
            { name: 'OTEL_SERVICE_NAME', value: 'api' }
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
      ingress: { external: false, targetPort: 8081 }
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
  tags: union(tags, { 'azd-service-name': 'web' })
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
