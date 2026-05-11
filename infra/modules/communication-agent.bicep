// Communication Agent infrastructure for the Autonomous Disaster Response Coordination Hub
// Deploys: Cosmos DB containers, Service Bus queues, Container App, and managed identity with RBAC

@description('Location for all resources')
param location string

@description('Environment name for resource naming')
param envPrefix string

@description('Tags applied to all resources')
param tags object

@description('Name of the existing Cosmos DB account')
param cosmosDbAccountName string

@description('Name of the Cosmos DB SQL database')
param cosmosDbDatabaseName string = 'disaster-response'

@description('Name of the existing Service Bus namespace')
param serviceBusNamespaceName string

@description('Resource ID of the existing Container Apps Environment')
param containerAppsEnvironmentId string

@description('Container image name for the communication agent')
param containerImageName string = 'communication-agent'

@description('Container image tag')
param containerImageTag string = 'latest'

@description('Name of the Azure Container Registry (without .azurecr.io)')
param containerRegistryName string

@description('Foundry (AIServices) endpoint URL — consumed as AZURE_AI_PROJECT_ENDPOINT (ADR-20 §Q-P6-03).')
param azureOpenAiEndpoint string

@description('Azure OpenAI deployment name')
param azureOpenAiDeployment string

// ── Built-in role definition IDs ──

var serviceBusDataReceiverRoleId = '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0'
var serviceBusDataSenderRoleId = '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39'
var cognitiveServicesOpenAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

// ── Existing resources ──

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' existing = {
  name: cosmosDbAccountName
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' existing = {
  name: cosmosDbDatabaseName
  parent: cosmosAccount
}

resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2024-01-01' existing = {
  name: serviceBusNamespaceName
}

// ── Managed Identity ──

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${envPrefix}-communication'
  location: location
  tags: tags
}

// ── Cosmos DB containers ──

resource publicAlertsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'public-alerts'
  parent: cosmosDatabase
  properties: {
    resource: {
      id: 'public-alerts'
      partitionKey: {
        paths: ['/tenant_id']
        kind: 'Hash'
      }
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 4000
      }
    }
  }
}

resource communicationDecisionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'communication-decisions'
  parent: cosmosDatabase
  properties: {
    resource: {
      id: 'communication-decisions'
      partitionKey: {
        paths: ['/tenant_id']
        kind: 'Hash'
      }
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 4000
      }
    }
  }
}

resource deliveryRecordsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'delivery-records'
  parent: cosmosDatabase
  properties: {
    resource: {
      id: 'delivery-records'
      partitionKey: {
        paths: ['/tenant_id']
        kind: 'Hash'
      }
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 4000
      }
    }
  }
}

// ── Service Bus queues ──

resource communicationHandoffsQueue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  name: 'communication-handoffs'
  parent: serviceBusNamespace
  properties: {
    lockDuration: 'PT30S'
    maxDeliveryCount: 10
    deadLetteringOnMessageExpiration: true
    requiresDuplicateDetection: false
    requiresSession: false
  }
}

resource commanderApprovalQueue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  name: 'commander-approval-queue'
  parent: serviceBusNamespace
  properties: {
    lockDuration: 'PT30S'
    maxDeliveryCount: 10
    deadLetteringOnMessageExpiration: true
    requiresDuplicateDetection: false
    requiresSession: false
  }
}

// ── Container App ──

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${envPrefix}-communication'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    configuration: {
      ingress: {
        external: false
        targetPort: 8084
      }
      registries: [
        {
          server: '${containerRegistryName}.azurecr.io'
          identity: managedIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'communication-agent'
          image: '${containerRegistryName}.azurecr.io/${containerImageName}:${containerImageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            { name: 'AZURE_AI_PROJECT_ENDPOINT', value: azureOpenAiEndpoint }
            { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
            { name: 'COSMOS_ENDPOINT', value: cosmosAccount.properties.documentEndpoint }
            { name: 'COSMOS_DATABASE_NAME', value: cosmosDbDatabaseName }
            { name: 'SERVICE_BUS_NAMESPACE', value: '${serviceBusNamespaceName}.servicebus.windows.net' }
            { name: 'COMMUNICATION_HANDOFF_QUEUE', value: communicationHandoffsQueue.name }
            { name: 'COMMANDER_APPROVAL_QUEUE', value: commanderApprovalQueue.name }
            { name: 'SUPPORTED_LANGUAGES', value: 'en-AU,zh-Hans,ar,vi,el,it' }
            { name: 'DELIVERY_CHANNELS', value: 'sms,push,broadcast' }
            { name: 'MAX_CONCURRENT_ALERTS', value: '50' }
            { name: 'PORT', value: '8084' }
            {
              name: 'AZURE_CLIENT_ID'
              value: managedIdentity.properties.clientId
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          // Service Bus KEDA scaler replaced with HTTP concurrent requests
          // scaler — original had empty secretRef which breaks auth at runtime.
          {
            name: 'http-concurrency'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// ── RBAC: Cosmos DB Data Contributor (built-in SQL role) ──

resource cosmosRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-11-15' = {
  name: guid(cosmosAccount.id, managedIdentity.id, '00000000-0000-0000-0000-000000000002')
  parent: cosmosAccount
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: managedIdentity.properties.principalId
    scope: cosmosAccount.id
  }
}

// ── RBAC: Service Bus Data Receiver ──

resource serviceBusReceiverRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespace.id, managedIdentity.id, serviceBusDataReceiverRoleId)
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', serviceBusDataReceiverRoleId)
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── RBAC: Service Bus Data Sender ──

resource serviceBusSenderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespace.id, managedIdentity.id, serviceBusDataSenderRoleId)
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', serviceBusDataSenderRoleId)
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── RBAC: Cognitive Services OpenAI User ──

resource cognitiveServicesOpenAiRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, managedIdentity.id, cognitiveServicesOpenAiUserRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAiUserRoleId)
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Outputs ──

output managedIdentityPrincipalId string = managedIdentity.properties.principalId
output containerAppName string = containerApp.name
output communicationHandoffsQueueName string = communicationHandoffsQueue.name
output commanderApprovalQueueName string = commanderApprovalQueue.name
