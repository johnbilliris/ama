targetScope = 'resourceGroup'

@description('Deployment location')
param location string = 'australiaeast'

@description('Environment prefix')
param envPrefix string = 'drh'

@description('Common tags')
param tags object = {
  project: 'disaster-response-hub'
  environment: 'production'
}

@description('Container image for API app')
param apiImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container image for agent runtime')
param agentsImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Alert email recipient')
param actionGroupEmail string = 'ops@example.com'

@description('Alert webhook endpoint')
param actionGroupWebhook string = 'https://example.com/alerts'

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
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    disableKeyBasedMetadataWriteAccess: true
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

output apiContainerAppId string = apiContainerApp.id
output agentsContainerAppId string = agentsContainerApp.id
output cosmosAccountId string = cosmos.id
output redisId string = redis.id
output storageId string = storage.id
output openAiId string = openAi.id
output actionGroupId string = monitoring.outputs.actionGroupId
