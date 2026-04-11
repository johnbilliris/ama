// Resource Allocation Agent infrastructure for the Autonomous Disaster Response Coordination Hub
// Deploys: Cosmos DB containers, Service Bus queue, Container App, and managed identity with RBAC

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

@description('Container image name for the resource allocation agent')
param containerImageName string = 'resource-allocation-agent'

@description('Container image tag')
param containerImageTag string = 'latest'

@description('Name of the Azure Container Registry (without .azurecr.io)')
param containerRegistryName string

// ── Built-in role definition IDs ──

var serviceBusDataReceiverRoleId = '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0'

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
  name: 'id-${envPrefix}-resource-allocation'
  location: location
  tags: tags
}

// ── Cosmos DB containers ──

resource resourceDeploymentPlansContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'resource-deployment-plans'
  parent: cosmosDatabase
  properties: {
    resource: {
      id: 'resource-deployment-plans'
      partitionKey: {
        paths: ['/incident_scope_key']
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

resource resourceAllocationDecisionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'resource-allocation-decisions'
  parent: cosmosDatabase
  properties: {
    resource: {
      id: 'resource-allocation-decisions'
      partitionKey: {
        paths: ['/incident_scope_key']
        kind: 'Hash'
      }
      // Append-only audit trail — no default TTL so records persist indefinitely
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 4000
      }
    }
  }
}

// ── Service Bus queue ──

resource resourceAllocationQueue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  name: 'resource-allocation-handoffs'
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
  name: '${envPrefix}-resource-allocation'
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
        targetPort: 8083
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
          name: 'resource-allocation-agent'
          image: '${containerRegistryName}.azurecr.io/${containerImageName}:${containerImageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            { name: 'COSMOS_ENDPOINT', value: cosmosAccount.properties.documentEndpoint }
            { name: 'COSMOS_DATABASE', value: cosmosDbDatabaseName }
            { name: 'SERVICEBUS_NAMESPACE', value: '${serviceBusNamespaceName}.servicebus.windows.net' }
            { name: 'SERVICEBUS_QUEUE', value: resourceAllocationQueue.name }
            {
              name: 'AZURE_CLIENT_ID'
              value: managedIdentity.properties.clientId
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
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

// ── Outputs ──

output managedIdentityPrincipalId string = managedIdentity.properties.principalId
output containerAppName string = containerApp.name
output queueName string = resourceAllocationQueue.name
