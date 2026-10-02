// infra/bicep/modules/eval/eval-platform.bicep
//
// LLM Evaluation Framework platform module (feature 030, T014, T067a, T075).
//
// Deploys (in australiaeast):
//   - Cosmos DB containers: eval_datasets, eval_runs, eval_metric_definitions, eval_audit
//   - Storage account with **time-based 7-year immutability** (FR-021) and containers
//     `datasets`, `runs`, `audit-archive`
//   - Key Vault `kv-amaeval-${env}` for Foundry endpoint URIs
//   - Azure Container Registry for eval runner images
//   - Container Apps environment `cae-ama-eval-${env}`
//   - Container Apps Jobs:
//       * caj-eval-runner-${env}      (manual trigger)
//       * caj-eval-reconciler-${env}  (cron */30 * * * *)
//       * caj-eval-scheduler-${env}   (cron weekly Sunday 18:00 UTC by default — T067a)
//       * caj-eval-audit-projection-${env} (cron daily 03:00 UTC — T075)
//   - Log Analytics workspace and App Insights for eval telemetry
//
// AMA conventions: AVM modules where available; managed identity end-to-end; tags.

targetScope = 'resourceGroup'

@description('Environment name (dev|staging|production)')
@allowed([ 'dev', 'staging', 'production' ])
param env string

@description('Resource location — Australia East per constitution NN-2')
param location string = 'australiaeast'

@description('Container Apps Job CPU')
param jobCpu string = '1.0'

@description('Container Apps Job memory')
param jobMemory string = '2.0Gi'

@description('Storage immutability state — Disabled (dev), Unlocked (staging|production initial)')
@allowed([ 'Disabled', 'Unlocked', 'Locked' ])
param storageImmutabilityState string = (env == 'dev') ? 'Disabled' : 'Unlocked'

@description('Deploy Container Apps Jobs after the eval runner image has been published to the eval Azure Container Registry.')
param deployContainerJobs bool = true

@description('Deploy the AMA API container app once the api image has been pushed to the eval Azure Container Registry.')
param deployApi bool = false

@description('Entra ID tenant id used for AMA API JWT validation.')
param entraTenantId string = subscription().tenantId

@description('Entra ID audience the AMA API expects on inbound JWTs (defaults to the dev app appId).')
param entraAudience string = ''

@description('Scheduler cron — weekly baseline (overnight Sun 18:00 UTC default)')
param schedulerCron string = '0 18 * * 0'

@description('Optional salt appended to the Key Vault name to avoid collisions with prior soft-deleted purge-protected vaults.')
@maxLength(2)
param keyVaultNameSalt string = ''

@description('Tags applied to every resource')
param tags object = {
  feature: '030-llm-eval-framework'
  workload: 'ama-eval'
  env: env
  'managed-by': 'bicep'
}

var nameSuffix = '${env}-${uniqueString(resourceGroup().id)}'
var shortUniqueSuffix = take(uniqueString(resourceGroup().id), 6)
var storageEnvSegment = env == 'production' ? 'prod' : env
var storageAccountName = take('stamaeval${storageEnvSegment}${uniqueString(resourceGroup().id)}', 24)
var keyVaultName = 'kv-amaeval-${storageEnvSegment}-${shortUniqueSuffix}${keyVaultNameSalt}'
var logAnalyticsWorkspaceName = take('log-ama-eval-${nameSuffix}', 63)
var containerRegistryName = 'acramaeval${storageEnvSegment}${shortUniqueSuffix}'
var evalRunnerImageRepository = 'eval-runner'
var evalRunnerImageTag = env
var apiImageRepository = 'ama/api'
var apiImageTag = env
var allowPublicEvalDataPlane = env == 'dev'
var dataPlanePublicNetworkAccess = allowPublicEvalDataPlane ? 'Enabled' : 'Disabled'
var dataPlaneNetworkDefaultAction = allowPublicEvalDataPlane ? 'Allow' : 'Deny'
var acrPullRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')

// --- Cosmos DB ---------------------------------------------------------------

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' = {
  name: 'cosmos-ama-eval-${nameSuffix}'
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      { locationName: location, failoverPriority: 0, isZoneRedundant: false }
    ]
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    capabilities: [ { name: 'EnableServerless' } ]
    publicNetworkAccess: dataPlanePublicNetworkAccess
    minimalTlsVersion: 'Tls12'
    disableLocalAuth: true
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 720
        backupStorageRedundancy: 'Zone'
      }
    }
  }
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-11-15' = {
  parent: cosmos
  name: 'ama-eval'
  properties: { resource: { id: 'ama-eval' } }
}

var containers = [
  { name: 'eval_datasets',            partitionKey: '/datasetId' }
  { name: 'eval_runs',                partitionKey: '/runId' }
  { name: 'eval_metric_definitions',  partitionKey: '/metricId' }
  { name: 'eval_audit',               partitionKey: '/runId' }
]

resource cosmosContainers 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-11-15' = [for c in containers: {
  parent: cosmosDb
  name: c.name
  properties: {
    resource: {
      id: c.name
      partitionKey: { paths: [ c.partitionKey ], kind: 'Hash' }
      indexingPolicy: { indexingMode: 'consistent' }
      conflictResolutionPolicy: { mode: 'LastWriterWins', conflictResolutionPath: '/_ts' }
    }
  }
}]

// --- Storage with 7-year immutability (FR-021) -------------------------------

resource storage 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: { name: 'Standard_ZRS' }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: dataPlanePublicNetworkAccess
    networkAcls: { bypass: 'AzureServices', defaultAction: dataPlaneNetworkDefaultAction }
    encryption: {
      services: {
        blob: { enabled: true, keyType: 'Account' }
        file: { enabled: true, keyType: 'Account' }
      }
      keySource: 'Microsoft.Storage'
      requireInfrastructureEncryption: true
    }
  }
}

resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' = {
  parent: storage
  name: 'default'
  properties: {
    isVersioningEnabled: true
    changeFeed: { enabled: true, retentionInDays: 2555 }
  }
}

var blobContainerNames = [ 'datasets', 'runs', 'audit-archive' ]

resource blobContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' = [for n in blobContainerNames: {
  parent: blobServices
  name: n
  properties: {
    publicAccess: 'None'
    immutableStorageWithVersioning: {
      enabled: true
    }
  }
}]

resource blobImmutabilityPolicies 'Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies@2024-01-01' = [for (n, i) in blobContainerNames: if (storageImmutabilityState != 'Disabled') {
  parent: blobContainers[i]
  name: 'default'
  properties: {
    immutabilityPeriodSinceCreationInDays: 2555
    allowProtectedAppendWrites: true
  }
}]

// --- Key Vault ---------------------------------------------------------------

resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enablePurgeProtection: env == 'dev' ? null : true
    enableSoftDelete: true
    softDeleteRetentionInDays: env == 'dev' ? 7 : 90
    publicNetworkAccess: dataPlanePublicNetworkAccess
    networkAcls: { bypass: 'AzureServices', defaultAction: dataPlaneNetworkDefaultAction }
  }
}

// --- Container Registry ------------------------------------------------------

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2025-04-01' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
    anonymousPullEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      azureADAuthenticationAsArmPolicy: {
        status: 'enabled'
      }
    }
  }
}

// --- Observability -----------------------------------------------------------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 90
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-ama-eval-${nameSuffix}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    RetentionInDays: 90
    IngestionMode: 'LogAnalytics'
    DisableLocalAuth: true
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// --- Azure AI Services (Foundry) account + model deployments ---------------
//
// FR-013/FR-014: a real Foundry endpoint is required for the eval runner to
// produce a meaningful scorecard. This account hosts a curated set of OpenAI
// chat-completion models in Australia East. Foundry catalogue (Llama / Mistral
// / DeepSeek) needs serverlessEndpoints under MachineLearningServices and is
// tracked separately.

var foundryAccountName = take('aoai-amaeval-${storageEnvSegment}-${shortUniqueSuffix}', 32)

resource foundry 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: foundryAccountName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: foundryAccountName
    publicNetworkAccess: dataPlanePublicNetworkAccess
    networkAcls: { defaultAction: dataPlaneNetworkDefaultAction, virtualNetworkRules: [], ipRules: [] }
    disableLocalAuth: true
  }
}

@description('Curated chat-completion models deployed for the eval runner. Mix of OpenAI + Foundry catalogue.')
var foundryModelDeployments = [
  { name: 'gpt-5-4',                modelName: 'gpt-5.4',                  modelVersion: '2026-03-05', format: 'OpenAI',    sku: 'GlobalStandard', capacity: 10 }
  { name: 'gpt-5-4-mini',           modelName: 'gpt-5.4-mini',             modelVersion: '2026-03-17', format: 'OpenAI',    sku: 'GlobalStandard', capacity: 10 }
  { name: 'gpt-4o-mini',            modelName: 'gpt-4o-mini',              modelVersion: '2024-07-18', format: 'OpenAI',    sku: 'GlobalStandard', capacity: 10 }
  { name: 'phi-4',                  modelName: 'Phi-4',                    modelVersion: '7',          format: 'Microsoft', sku: 'GlobalStandard', capacity: 1  }
  { name: 'llama-3-3-70b-instruct', modelName: 'Llama-3.3-70B-Instruct',   modelVersion: '9',          format: 'Meta',      sku: 'GlobalStandard', capacity: 1  }
  { name: 'mistral-large-3',        modelName: 'Mistral-Large-3',          modelVersion: '1',          format: 'Mistral AI',sku: 'GlobalStandard', capacity: 1  }
  { name: 'deepseek-v3-2',          modelName: 'DeepSeek-V3.2',            modelVersion: '1',          format: 'DeepSeek',  sku: 'GlobalStandard', capacity: 1  }
]

@batchSize(1)
resource foundryDeployments 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = [for d in foundryModelDeployments: {
  parent: foundry
  name: d.name
  sku: { name: d.sku, capacity: d.capacity }
  properties: {
    model: { format: d.format, name: d.modelName, version: d.modelVersion }
    versionUpgradeOption: 'NoAutoUpgrade'
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}]

var cognitiveServicesOpenAIUserRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')

resource runnerFoundryAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundry.id, runnerIdentity.id, 'CognitiveServicesOpenAIUser')
  scope: foundry
  properties: {
    roleDefinitionId: cognitiveServicesOpenAIUserRoleId
    principalId: runnerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// --- Container Apps environment + Jobs --------------------------------------

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-ama-eval-${nameSuffix}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      { name: 'Consumption', workloadProfileType: 'Consumption' }
    ]
    zoneRedundant: env != 'dev'
  }
}

resource runnerIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-caj-eval-runner-${nameSuffix}'
  location: location
  tags: tags
}

resource cosmosSqlRoleAssignmentRunner 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = {
  parent: cosmos
  name: guid(cosmos.id, runnerIdentity.id, 'cosmos-data-contributor')
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: runnerIdentity.properties.principalId
    scope: cosmos.id
  }
}

var storageBlobDataReaderRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')

resource runnerStorageBlobReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, runnerIdentity.id, 'StorageBlobDataReader')
  scope: storage
  properties: {
    roleDefinitionId: storageBlobDataReaderRoleId
    principalId: runnerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource acrPullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, runnerIdentity.id, 'AcrPull')
  scope: containerRegistry
  properties: {
    roleDefinitionId: acrPullRoleDefinitionId
    principalId: runnerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

var jobNames = [
  { name: 'caj-eval-runner-${env}',            triggerType: 'Manual',   cron: ''                 }
  { name: 'caj-eval-reconciler-${env}',        triggerType: 'Schedule', cron: '*/30 * * * *'     }
  { name: 'caj-eval-scheduler-${env}',         triggerType: 'Schedule', cron: schedulerCron      }
  { name: 'caj-eval-audit-projection-${env}',  triggerType: 'Schedule', cron: '0 3 * * *'        }
]

resource jobs 'Microsoft.App/jobs@2024-03-01' = [for j in jobNames: if (deployContainerJobs) {
  name: j.name
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${runnerIdentity.id}': {} }
  }
  properties: {
    environmentId: cae.id
    workloadProfileName: 'Consumption'
    configuration: {
      replicaTimeout: 28800
      replicaRetryLimit: 0
      triggerType: j.triggerType
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: runnerIdentity.id
        }
      ]
      manualTriggerConfig: j.triggerType == 'Manual' ? { parallelism: 1, replicaCompletionCount: 1 } : null
      scheduleTriggerConfig: j.triggerType == 'Schedule' ? {
        cronExpression: j.cron
        parallelism: 1
        replicaCompletionCount: 1
      } : null
    }
    template: {
      containers: [
        {
          name: 'runner'
          image: '${containerRegistry.properties.loginServer}/${evalRunnerImageRepository}:${evalRunnerImageTag}'
          resources: { cpu: json(jobCpu), memory: jobMemory }
          env: [
            { name: 'COSMOS_ENDPOINT',          value: cosmos.properties.documentEndpoint }
            { name: 'COSMOS_DATABASE',          value: 'ama-eval' }
            { name: 'EVAL_BLOB_ACCOUNT',        value: storage.name }
            { name: 'EVAL_KEY_VAULT',           value: kv.name }
            { name: 'AZURE_CLIENT_ID',          value: runnerIdentity.properties.clientId }
            { name: 'AZURE_AI_PROJECT_ENDPOINT', value: foundry.properties.endpoint }
            { name: 'AZURE_AI_PROJECT_DEPLOYMENTS', value: join(map(foundryModelDeployments, d => '${d.modelName}@${d.modelVersion}=${d.name}'), ',') }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
            { name: 'EVAL_JOB_ROLE',            value: split(j.name, '-')[2] }
          ]
        }
      ]
    }
  }
  dependsOn: [
    acrPullAssignment
    runnerFoundryAccess
  ]
}]

// --- AMA API container app ---------------------------------------------------

var storageBlobDataContributorRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
var keyVaultSecretsUserRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
var cosmosBuiltinDataContributorId = guid(cosmos.id, 'cosmos-data-contributor')

resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = if (deployApi) {
  name: 'id-app-ama-api-${nameSuffix}'
  location: location
  tags: tags
}

resource apiAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployApi) {
  name: guid(containerRegistry.id, 'api', 'AcrPull')
  scope: containerRegistry
  properties: {
    roleDefinitionId: acrPullRoleDefinitionId
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource apiStorageBlob 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployApi) {
  name: guid(storage.id, 'api', 'StorageBlobDataContributor')
  scope: storage
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleId
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource apiKvSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployApi) {
  name: guid(kv.id, 'api', 'KeyVaultSecretsUser')
  scope: kv
  properties: {
    roleDefinitionId: keyVaultSecretsUserRoleId
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource cosmosSqlRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = if (deployApi) {
  parent: cosmos
  name: cosmosBuiltinDataContributorId
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: apiIdentity.properties.principalId
    scope: cosmos.id
  }
}

resource apiContainerApp 'Microsoft.App/containerApps@2024-03-01' = if (deployApi) {
  name: 'app-ama-api-${env}'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${apiIdentity.id}': {} }
  }
  properties: {
    environmentId: cae.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: apiIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${containerRegistry.properties.loginServer}/${apiImageRepository}:${apiImageTag}'
          resources: { cpu: json('0.5'), memory: '1Gi' }
          // Base env vars common to all environments.
          // FR-022a (dev exception): EVAL_ALLOW_ANONYMOUS is appended below
          // **only** when env == 'dev'. Staging and production deployments must
          // never carry EVAL_ALLOW_ANONYMOUS, so the role guard cannot honour
          // it there even if an operator sets the env var by mistake.
          env: concat(
            [
              { name: 'ENVIRONMENT',                            value: env }
              { name: 'COSMOS_ENDPOINT',                        value: cosmos.properties.documentEndpoint }
              { name: 'COSMOS_DATABASE',                        value: 'ama-eval' }
              { name: 'EVAL_STORAGE_ACCOUNT',                   value: storage.name }
              { name: 'EVAL_TRACES_CONTAINER',                  value: 'runs' }
              { name: 'AZURE_KEY_VAULT_URI',                    value: kv.properties.vaultUri }
              { name: 'EVAL_EVIDENCE_SIGNING_KEY',              value: 'eval-signing-key' }
              { name: 'ENTRA_TENANT_ID',                        value: entraTenantId }
              { name: 'ENTRA_AUDIENCE',                         value: entraAudience }
              { name: 'AZURE_CLIENT_ID',                        value: apiIdentity.properties.clientId }
              { name: 'AZURE_SUBSCRIPTION_ID',                  value: subscription().subscriptionId }
              { name: 'EVAL_RUNNER_JOB_RESOURCE_GROUP',         value: resourceGroup().name }
              { name: 'EVAL_RUNNER_JOB_NAME',                   value: 'caj-eval-runner-${env}' }
              { name: 'EVAL_RUNNER_JOB_IMAGE',                  value: '${containerRegistry.properties.loginServer}/${evalRunnerImageRepository}:${evalRunnerImageTag}' }
              { name: 'AZURE_AI_PROJECT_ENDPOINT',              value: foundry.properties.endpoint }
              { name: 'AZURE_AI_PROJECT_DEPLOYMENTS',           value: join(map(foundryModelDeployments, d => '${d.modelName}@${d.modelVersion}=${d.name}'), ',') }
              { name: 'EVAL_ALLOW_DEV_TOKENS',                  value: env == 'dev' ? '1' : '' }
              { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING',  value: appInsights.properties.ConnectionString }
            ],
            env == 'dev' ? [
              // FR-022a: dev-only anonymous access to /api/eval/* against the
              // synthetic dev dataset (disaster-response-core). MUST NOT be
              // present on staging/production.
              { name: 'EVAL_ALLOW_ANONYMOUS', value: '1' }
            ] : []
          )
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
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
  dependsOn: [
    apiAcrPull
    apiStorageBlob
    apiKvSecretsUser
    cosmosSqlRoleAssignment
  ]
}

// Allow the API managed identity to start the runner Container Apps Job (data-plane).
var containerAppsJobsOperatorRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b9a307c4-5aa3-4b52-ba60-2b17c136cd7b')

resource apiJobsOperator 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployApi) {
  name: guid(resourceGroup().id, 'api', 'ContainerAppsJobsOperator')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: containerAppsJobsOperatorRoleId
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// --- Outputs -----------------------------------------------------------------

output cosmosEndpoint string = cosmos.properties.documentEndpoint
output cosmosAccountName string = cosmos.name
output storageAccountName string = storage.name
output keyVaultName string = kv.name
output containerRegistryName string = containerRegistry.name
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output evalRunnerImage string = '${containerRegistry.properties.loginServer}/${evalRunnerImageRepository}:${evalRunnerImageTag}'
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output runnerIdentityResourceId string = runnerIdentity.id
output runnerIdentityPrincipalId string = runnerIdentity.properties.principalId
output runnerIdentityClientId string = runnerIdentity.properties.clientId
output containerAppsEnvironmentId string = cae.id
output apiFqdn string = deployApi ? apiContainerApp.properties.configuration.ingress.fqdn : ''
output foundryAccountName string = foundry.name
output foundryEndpoint string = foundry.properties.endpoint
output foundryDeploymentNames string = join(map(foundryModelDeployments, d => d.name), ',')
output foundryModelMap string = join(map(foundryModelDeployments, d => '${d.modelName}@${d.modelVersion}=${d.name}'), ',')
output apiImage string = '${containerRegistry.properties.loginServer}/${apiImageRepository}:${apiImageTag}'
