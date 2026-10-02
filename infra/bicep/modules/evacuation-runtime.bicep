@description('Deployment environment used for resource names and runtime behavior.')
@minLength(1)
@maxLength(64)
param environmentName string

@description('Unique suffix generated once by the root deployment.')
@minLength(5)
param uniqueSuffix string

@description('Primary Australian deployment region.')
@allowed([
  'australiaeast'
])
param location string

@description('Tags applied to evacuation runtime resources.')
param tags object

@description('Fully qualified agents image reference produced by azd.')
param containerImage string

@description('Resource ID of the existing Container Apps managed environment.')
param containerAppsEnvironmentResourceId string

@description('Name of the existing Container Apps managed environment.')
param containerAppsEnvironmentName string

@description('Existing Azure Container Registry login server.')
param containerRegistryLoginServer string

@description('Name of the existing Cosmos DB account.')
param cosmosAccountName string

@description('Authoritative endpoint of the existing Cosmos DB account.')
param cosmosEndpoint string

@description('Name of the existing Cosmos DB SQL database.')
param cosmosDatabaseName string

@description('Existing storage account name for the durable audit WAL share.')
param storageAccountName string

@secure()
@description('Storage account key required by Container Apps Azure Files environment storage.')
param storageAccountKey string

@description('Existing Log Analytics workspace resource ID for Service Bus diagnostics.')
param logAnalyticsWorkspaceResourceId string

@description('Application Insights connection string for evacuation telemetry export.')
param applicationInsightsConnectionString string

@description('Microsoft Foundry project endpoint used by the evacuation LLM client.')
param azureAiProjectEndpoint string

@description('Serialized Foundry deployment map used by the shared LLM client.')
param azureAiProjectDeployments string

@description('Foundry reasoning deployment name.')
param azureAiReasoningDeployment string

@description('Foundry reasoning model coordinate.')
param azureAiReasoningModelKey string

@description('Principal ID allowed to publish risk-assessment handoffs to the evacuation queue.')
param handoffSenderPrincipalId string

var queueName = 'evacuation-handoffs'
var auditStorageName = 'evacuation-audit-wal'
var evacuationContainerNames = [
  'evacuation-plans'
  'evacuation-decisions'
  'hazard-assessments'
  'risk-recommendations'
]
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'
var workloadRoleDefinitionIds = [
  '7f951dda-4ed3-4680-a7ca-43fe172d538d'
  '3913510d-42f4-4e42-8a64-420c390055eb'
  '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
]

module evacuationIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.6.0' = {
  params: {
    name: take('id-${environmentName}-evacuation', 128)
    location: location
    isolationScope: 'Regional'
    tags: tags
  }
}

module evacuationContainers 'br/public:avm/res/document-db/database-account/sql-database/container:0.2.1' = [for containerName in evacuationContainerNames: {
  params: {
    name: containerName
    databaseAccountName: cosmosAccountName
    sqlDatabaseName: cosmosDatabaseName
    paths: ['/incident_scope_key']
    autoscaleSettingsMaxThroughput: 4000
    defaultTtl: -1
  }
}]

module cosmosDataContributor 'br/public:avm/res/document-db/database-account/sql-role-assignment:0.2.2' = {
  params: {
    name: guid(cosmosAccountName, evacuationIdentity.outputs.principalId, cosmosDataContributorRoleId)
    databaseAccountName: cosmosAccountName
    principalId: evacuationIdentity.outputs.principalId
    roleDefinitionIdOrName: '${resourceId('Microsoft.DocumentDB/databaseAccounts', cosmosAccountName)}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'
  }
}

module evacuationServiceBus 'br/public:avm/res/service-bus/namespace:0.17.1' = {
  params: {
    name: take('sb-evac-${environmentName}-${take(uniqueSuffix, 6)}', 50)
    location: location
    tags: tags
    authorizationRules: []
    disableLocalAuth: true
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    requireInfrastructureEncryption: false
    skuObject: {
      name: 'Standard'
    }
    zoneRedundant: false
    diagnosticSettings: [
      {
        name: 'evacuation-service-bus'
        workspaceResourceId: logAnalyticsWorkspaceResourceId
      }
    ]
    queues: [
      {
        name: queueName
        deadLetteringOnMessageExpiration: true
        defaultMessageTimeToLive: 'P14D'
        duplicateDetectionHistoryTimeWindow: 'PT1H'
        lockDuration: 'PT5M'
        maxDeliveryCount: 3
        requiresDuplicateDetection: true
        requiresSession: false
        roleAssignments: [
          {
            principalId: evacuationIdentity.outputs.principalId
            principalType: 'ServicePrincipal'
            roleDefinitionIdOrName: 'Azure Service Bus Data Receiver'
          }
          {
            principalId: handoffSenderPrincipalId
            principalType: 'ServicePrincipal'
            roleDefinitionIdOrName: 'Azure Service Bus Data Sender'
          }
        ]
      }
    ]
  }
}

module auditWalShare 'br/public:avm/res/storage/storage-account/file-service/share:0.1.3' = {
  params: {
    name: auditStorageName
    storageAccountName: storageAccountName
    fileServicesName: 'default'
    accessTier: 'TransactionOptimized'
    enabledProtocols: 'SMB'
    shareQuota: 5
  }
}

// No AVM exists for Microsoft.App/managedEnvironments/storages. Raw Bicep for
// this child resource was explicitly approved on 2026-09-18 for the durable WAL.
resource managedEnvironment 'Microsoft.App/managedEnvironments@2025-01-01' existing = {
  name: containerAppsEnvironmentName
}

resource auditWalEnvironmentStorage 'Microsoft.App/managedEnvironments/storages@2025-01-01' = {
  name: auditStorageName
  parent: managedEnvironment
  properties: {
    azureFile: {
      accessMode: 'ReadWrite'
      accountKey: storageAccountKey
      accountName: storageAccountName
      shareName: auditWalShare.outputs.name
    }
  }
}

module workloadRoles 'br/public:avm/res/authorization/role-assignment/rg-scope:0.1.1' = [for roleDefinitionId in workloadRoleDefinitionIds: {
  params: {
    name: guid(resourceGroup().id, evacuationIdentity.outputs.principalId, roleDefinitionId)
    principalId: evacuationIdentity.outputs.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionIdOrName: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
  }
}]

module evacuationContainerApp 'br/public:avm/res/app/container-app:0.23.0' = {
  params: {
    name: take('ca-evacuation-${environmentName}', 32)
    location: location
    tags: union(tags, { 'azd-service-name': 'evacuation' })
    environmentResourceId: containerAppsEnvironmentResourceId
    ingressExternal: false
    ingressAllowInsecure: false
    ingressTargetPort: 8082
    managedIdentities: {
      userAssignedResourceIds: [
        evacuationIdentity.outputs.resourceId
      ]
    }
    registries: [
      {
        server: containerRegistryLoginServer
        identity: evacuationIdentity.outputs.resourceId
      }
    ]
    volumes: [
      {
        name: auditStorageName
        storageName: auditWalEnvironmentStorage.name
        storageType: 'AzureFile'
      }
    ]
    containers: [
      {
        name: 'evacuation-agent'
        image: containerImage
        resources: {
          cpu: 1
          memory: '2Gi'
        }
        env: [
          { name: 'AMA_AGENTS_RUNTIME', value: 'evacuation' }
          { name: 'AMA_ENVIRONMENT', value: environmentName }
          { name: 'PORT', value: '8082' }
          { name: 'AZURE_CLIENT_ID', value: evacuationIdentity.outputs.clientId }
          { name: 'COSMOS_ENDPOINT', value: cosmosEndpoint }
          { name: 'COSMOS_DATABASE_NAME', value: cosmosDatabaseName }
          { name: 'EVACUATION_PLANS_CONTAINER_NAME', value: 'evacuation-plans' }
          { name: 'EVACUATION_DECISIONS_CONTAINER_NAME', value: 'evacuation-decisions' }
          { name: 'ASSESSMENTS_CONTAINER_NAME', value: 'hazard-assessments' }
          { name: 'RECOMMENDATIONS_CONTAINER_NAME', value: 'risk-recommendations' }
          { name: 'AZURE_SERVICEBUS_NAMESPACE', value: '${evacuationServiceBus.outputs.name}.servicebus.windows.net' }
          { name: 'EVACUATION_HANDOFFS_QUEUE', value: queueName }
          { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: applicationInsightsConnectionString }
          { name: 'AZURE_AI_PROJECT_ENDPOINT', value: azureAiProjectEndpoint }
          { name: 'AZURE_AI_PROJECT_DEPLOYMENTS', value: azureAiProjectDeployments }
          { name: 'AZURE_AI_REASONING_DEPLOYMENT', value: azureAiReasoningDeployment }
          { name: 'AZURE_AI_REASONING_MODEL_KEY', value: azureAiReasoningModelKey }
          { name: 'ROAD_NETWORK_FILE_PATH', value: 'data/road-networks/far-north-qld-sample.json' }
          { name: 'POPULATION_DATA_FILE_PATH', value: 'data/population/sample-population.json' }
          { name: 'AUDIT_BUFFER_FILE_PATH', value: '/app/var/evacuation-agent/audit-buffer.jsonl' }
          { name: 'OTEL_SERVICE_NAME', value: 'evacuation-agent' }
        ]
        probes: [
          {
            type: 'Liveness'
            httpGet: { path: '/live', port: 8082 }
            initialDelaySeconds: 15
            periodSeconds: 30
          }
          {
            type: 'Readiness'
            httpGet: { path: '/ready', port: 8082 }
            initialDelaySeconds: 5
            periodSeconds: 10
          }
          {
            type: 'Startup'
            httpGet: { path: '/live', port: 8082 }
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 6
          }
        ]
        volumeMounts: [
          {
            mountPath: '/app/var/evacuation-agent'
            volumeName: auditStorageName
          }
        ]
      }
    ]
    scaleSettings: {
      minReplicas: 1
      maxReplicas: 4
      pollingInterval: 30
      rules: [
        {
          name: 'evacuation-queue-depth'
          custom: {
            type: 'azure-servicebus'
            metadata: {
              queueName: queueName
              namespace: evacuationServiceBus.outputs.name
              messageCount: '20'
            }
            identity: evacuationIdentity.outputs.resourceId
          }
        }
      ]
    }
  }
  dependsOn: [
    cosmosDataContributor
    workloadRoles
  ]
}

@description('Resource ID of the dedicated evacuation Container App.')
output resourceId string = evacuationContainerApp.outputs.resourceId

@description('Name of the dedicated evacuation Container App.')
output resourceName string = evacuationContainerApp.outputs.name

@description('Internal HTTPS endpoint of the evacuation service.')
output serviceEndpoint string = 'https://${evacuationContainerApp.outputs.fqdn}'

@description('Resource ID of the evacuation managed identity.')
output managedIdentityResourceId string = evacuationIdentity.outputs.resourceId

@description('Name of the evacuation Service Bus namespace.')
output serviceBusNamespaceName string = evacuationServiceBus.outputs.name

@description('Name of the evacuation handoff queue.')
output serviceBusQueueName string = queueName

@description('Resource IDs of the four evacuation Cosmos containers.')
output cosmosContainerResourceIds array = [for (containerName, index) in evacuationContainerNames: evacuationContainers[index].outputs.resourceId]
