targetScope = 'resourceGroup'

@description('Deployment location')
param location string = 'australiaeast'

@description('Environment prefix')
param envPrefix string = 'drh'

@description('Common tags')
param tags object = {
  project: 'disaster-response-hub'
  environment: 'production'
  SecurityControl: 'Ignore'
}

@description('Container image for API app')
param apiImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container image for agent runtime')
param agentsImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container image for ingestion worker')
param ingestionImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Alert email recipient')
param actionGroupEmail string = 'ops@example.com'

@description('Alert webhook endpoint')
param actionGroupWebhook string = 'https://example.com/alerts'

@description('Developer public IP address for Cosmos DB firewall access')
param developerIpAddress string = '110.144.204.83'

@description('Spec 038 — enable evidence-harness Cosmos containers + cold-archive Blob.')
param enableEvidenceHarness bool = true

@description('SLO alert action group resource ID (empty string = no alerts, T-AMD-03).')
param sloAlertActionGroupId string = ''

module monitoring './monitoring.bicep' = {
  params: {
    location: location
    envPrefix: envPrefix
    tags: tags
    actionGroupEmail: actionGroupEmail
    actionGroupWebhook: actionGroupWebhook
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: '${envPrefix}storage'
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      ipRules: [
        { value: developerIpAddress, action: 'Allow' }
      ]
    }
  }
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: '${envPrefix}-cosmos'
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    publicNetworkAccess: 'Enabled'
    ipRules: [
      { ipAddressOrRange: developerIpAddress }  // developer machine
      { ipAddressOrRange: '0.0.0.0' }           // allow Azure services (Container Apps)
      { ipAddressOrRange: '104.42.195.92' }     // Azure Portal
      { ipAddressOrRange: '40.76.54.131' }      // Azure Portal
      { ipAddressOrRange: '52.176.6.30' }       // Azure Portal
      { ipAddressOrRange: '52.169.50.45' }      // Azure Portal
      { ipAddressOrRange: '52.187.184.26' }     // Azure Portal
    ]
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    disableKeyBasedMetadataWriteAccess: true
  }
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  name: 'disaster-hub'
  parent: cosmos
  properties: {
    resource: {
      id: 'disaster-hub'
    }
  }
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
    options: {
      autoscaleSettings: {
        maxThroughput: 4000
      }
    }
  }
}

resource simulationContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'simulation'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'simulation'
      partitionKey: {
        paths: ['/scenario_id']
        kind: 'Hash'
      }
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 400
      }
    }
  }
}

// Feature 026-sim-warp-playback: recorded simulation events, playback
// snapshots, and scheduler cursor state — partitioned by tenant_id.
resource simEventsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'sim-events'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'sim-events'
      partitionKey: {
        paths: ['/tenant_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          { path: '/*' }
        ]
        excludedPaths: [
          { path: '/"_etag"/?' }
        ]
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
    options: {
      autoscaleSettings: {
        maxThroughput: 1000
      }
    }
  }
}

resource rawPayloadsBlob 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storage.name}/default/raw-payloads'
  properties: {
    publicAccess: 'None'
  }
}

resource binaryAssetsBlob 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storage.name}/default/binary-assets'
  properties: {
    publicAccess: 'None'
  }
}

resource auditBlob 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storage.name}/default/audit'
  properties: {
    publicAccess: 'None'
  }
}

resource simulationBlob 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storage.name}/default/simulation'
  properties: {
    publicAccess: 'None'
  }
}

// spec 034 — web coverage evidence container (immutable).
// Stores coverage-trace.json/md, gap-register.json/md, review-log.md, known-good.json
// emitted by the FR-004/FR-005/FR-027 pipeline. Public access denied; data plane
// access governed by the role assignment below.
resource webCoverageEvidenceBlob 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storage.name}/default/web-coverage-evidence'
  properties: {
    publicAccess: 'None'
    metadata: {
      spec: '034-webapp-capstone-coverage'
      retention: 'long-term-evidence'
      classification: 'OFFICIAL'
    }
  }
}

// Immutability policy on web-coverage-evidence (FR-006: trace replay determinism;
// rows are append-only). 30-day legal hold; matches existing audit container policy.
resource webCoverageImmutability 'Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies@2023-05-01' = {
  name: 'default'
  parent: webCoverageEvidenceBlob
  properties: {
    immutabilityPeriodSinceCreationInDays: 30
    allowProtectedAppendWrites: true
  }
}

resource redis 'Microsoft.Cache/Redis@2024-03-01' = {
  name: '${envPrefix}-redis'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
}

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: '${envPrefix}-openai'
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: '${envPrefix}-openai'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
  }
}

resource managedEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${envPrefix}-cae'
  location: location
  tags: tags
  properties: {}
}

resource apiContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${envPrefix}-api'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          resources: {
            cpu: 1
            memory: '1Gi'
          }
          env: [
            // Spec-036 / T-B16 — staging is now post-FR-002-migration. The
            // legacy stub adapter block has been deleted from the source
            // (see T-B14 in apps/api/app/services/simulation/sub_agent_invoker.py)
            // so SIM_CONTROLLER_MODE no longer toggles behaviour at runtime;
            // the env-var stays here as a tombstone for the migration so
            // operators can confirm the post-migration setting via
            // `az containerapp show -n <env>-api --query properties.template.containers[0].env`.
            { name: 'SIM_CONTROLLER_MODE', value: 'production' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 4
      }
    }
  }
}

resource agentsContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${envPrefix}-agents'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      ingress: {
        external: false
        targetPort: 8080
      }
    }
    template: {
      containers: [
        {
          name: 'agents'
          image: agentsImage
          resources: {
            cpu: 1
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

resource apiDiagnostic 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${envPrefix}-api-diagnostics'
  scope: apiContainerApp
  properties: {
    workspaceId: monitoring.outputs.logAnalyticsId
    logs: [
      {
        category: 'ContainerAppConsoleLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource ingestionWorker 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${envPrefix}-ingestion'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      ingress: {
        external: false
        targetPort: 8081
      }
    }
    template: {
      containers: [
        {
          name: 'ingestion'
          image: ingestionImage
          resources: {
            cpu: 1
            memory: '2Gi'
          }
          env: [
            { name: 'COSMOS_ENDPOINT', value: cosmos.properties.documentEndpoint }
            { name: 'STORAGE_ACCOUNT', value: storage.name }
            { name: 'REDIS_HOST', value: redis.properties.hostName }
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
              metadata: {
                type: 'Utilization'
                value: '70'
              }
            }
          }
        ]
      }
    }
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
  name: guid(cosmos.id, ingestionWorker.id, '00000000-0000-0000-0000-000000000002')
  parent: cosmos
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: ingestionWorker.identity.principalId
    scope: cosmos.id
  }
}

// spec 034 (T012) — Storage Blob Data Contributor role on web-coverage-evidence
// container scoped to the API container app's managed identity. Enables the
// coverage-trace pipeline to upload evidence artefacts without granting any
// other storage data plane access.
resource webCoverageEvidenceBlobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(webCoverageEvidenceBlob.id, apiContainerApp.id, 'StorageBlobDataContributor')
  scope: webCoverageEvidenceBlob
  properties: {
    // Storage Blob Data Contributor — built-in role definition GUID.
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    )
    principalId: apiContainerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Spec 036 / Phase F amend-loop — Cosmos containers + RAG observability wiring.
// Both containers are EMPTY at deploy time:
//   * culturalAuthorityRegistry — population is HUMAN-IN-LOOP (T202) per FR-RAG-CA-05.
//   * conflictDetectionLog — populated at runtime by the conflict-detector (FR-RAG-COORD-01).
// Database name override: main.bicep provisions `disaster-hub`, modules default to `ama`.
module culturalAuthorityRegistry './modules/cosmos-cultural-authority.bicep' = {
  name: 'cosmos-cultural-authority'
  params: {
    cosmosAccountName: cosmos.name
    databaseName: cosmosDb.name
    tags: tags
  }
}

module conflictDetectionLog './modules/cosmos-conflict-detection.bicep' = {
  name: 'cosmos-conflict-detection'
  params: {
    cosmosAccountName: cosmos.name
    databaseName: cosmosDb.name
    tags: tags
  }
}

module foundryRagAlerts './modules/foundry-rag-alerts.bicep' = {
  name: 'foundry-rag-alerts'
  params: {
    appInsightsName: '${envPrefix}-app-insights'
    actionGroupId: monitoring.outputs.actionGroupId
    location: location
    tags: tags
  }
}

module foundryRagSuccessDashboard './modules/foundry-rag-success-criteria-dashboard.bicep' = {
  name: 'foundry-rag-success-dashboard'
  params: {
    appInsightsName: '${envPrefix}-app-insights'
    location: location
    tags: tags
  }
}

output apiContainerAppId string = apiContainerApp.id
output agentsContainerAppId string = agentsContainerApp.id
output ingestionWorkerId string = ingestionWorker.id
output cosmosAccountId string = cosmos.id
output redisId string = redis.id
output storageId string = storage.id
output openAiId string = openAi.id
output actionGroupId string = monitoring.outputs.actionGroupId
output webCoverageEvidenceContainerName string = webCoverageEvidenceBlob.name

// ────────────────────────────────────────────────────────────────────────────
// Spec 036 — Simulation realm modules (T-A09 .. T-A16, wired by T-A20).
// All modules are additive; no existing resource is mutated.
// ────────────────────────────────────────────────────────────────────────────

module simulationCosmosContainers 'modules/cosmos-simulation-containers.bicep' = {
  name: 'spec036-cosmos-sim-containers'
  params: {
    cosmosAccountName: cosmos.name
    databaseName: cosmosDb.name
    tags: tags
  }
}

module lessonsCaptureStorage 'modules/lessons-capture-storage.bicep' = {
  name: 'spec036-lessons-capture'
  params: {
    storageAccountName: storage.name
    immutabilityPeriodMonths: 84
  }
}

module jurisdictionBoundariesStorage 'modules/jurisdiction-boundaries-storage.bicep' = {
  name: 'spec036-jurisdiction-boundaries'
  params: {
    storageAccountName: storage.name
  }
}

module ttsAudioStorage 'modules/tts-audio-storage.bicep' = {
  name: 'spec036-tts-audio'
  params: {
    storageAccountName: storage.name
  }
}

module azureOpenAiSimDeployments 'modules/azure-openai-deployments.bicep' = {
  name: 'spec036-aoai-sim-deployments'
  params: {
    openAiAccountName: openAi.name
    location: 'australiaeast'
    miniTpm: 150
    fullTpm: 100
  }
}

// Optional modules — wired in environments where APIM, Event Hubs and the
// agents Container App KEDA scaling are managed through this stack.
//   - eventHubSimConsumerGroups (T-A10) → requires Event Hubs namespace
//   - apimPolicySimulationInject (T-A15) → requires APIM service
//   - containerAppsScalingSim (T-A16)   → requires named consumer groups
// Bicep `module` references kept commented to satisfy `az bicep build`
// when those resources are not present in this environment file.
// module eventHubSimConsumerGroups 'modules/eventhub-simulation-consumer-groups.bicep' = { ... }
// module apimPolicySimulationInject 'modules/apim-policy-simulation-inject.bicep' = { ... }
// module containerAppsScalingSim 'modules/container-apps-scaling.bicep' = { ... }

output spec036SimulationCosmosContainers array = [
  simulationCosmosContainers.outputs.syntheticSignalsContainer
  simulationCosmosContainers.outputs.subAgentInvocationRecordsContainer
  simulationCosmosContainers.outputs.simulationThreadsContainer
  simulationCosmosContainers.outputs.exerciseOutcomeIndexContainer
  simulationCosmosContainers.outputs.routingDecisionsContainer
]
output spec036LessonsContainer string = lessonsCaptureStorage.outputs.containerName
output spec036JurisdictionBoundariesContainer string = jurisdictionBoundariesStorage.outputs.containerName
output spec036TtsAudioContainer string = ttsAudioStorage.outputs.containerName
output spec036AoaiMiniDeployment string = azureOpenAiSimDeployments.outputs.gpt4oMiniDeploymentName
output spec036AoaiFullDeployment string = azureOpenAiSimDeployments.outputs.gpt4oDeploymentName
output culturalAuthorityRegistryContainerName string = culturalAuthorityRegistry.outputs.culturalAuthorityRegistryContainerName
output conflictDetectionLogContainerName string = conflictDetectionLog.outputs.conflictDetectionLogContainerName

// ────────────────────────────────────────────────────────────────────────────
// Spec 038 — Measurable Success-Criteria Evidence Harness (T-S01 / T-S02).
// Adds 7 Cosmos containers + 1 cold-archive Blob (7-y immutability lock) +
// 1 App Insights workbook. AU sovereignty enforced (FR-029 / SC-009).
// ────────────────────────────────────────────────────────────────────────────

module evidenceHarness 'modules/evidence-harness.bicep' = if (enableEvidenceHarness) {
  name: 'spec038-evidence-harness'
  params: {
    cosmosAccountName: cosmos.name
    auditCosmosAccountName: cosmos.name
    databaseName: cosmosDb.name
    storageAccountName: storage.name
    location: 'australiaeast'
    pairedRegion: 'australiasoutheast'
    appInsightsName: ''
    sloAlertActionGroupId: sloAlertActionGroupId
    tags: tags
  }
}

output spec038EvidenceContainerNames array = enableEvidenceHarness ? evidenceHarness!.outputs.evidenceContainerNames : []
output spec038EvidenceColdArchiveContainer string = enableEvidenceHarness ? evidenceHarness!.outputs.coldArchiveContainerName : ''
