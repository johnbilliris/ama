// Monitoring Agent infrastructure — Cosmos DB container, Service Bus queue,
// Container Apps scaling, and managed identity assignments.
// Spec: specs/010-monitoring-agent/plan.md §Azure Resources

@description('Location for all monitoring agent resources')
param location string = 'australiaeast'

@description('Environment prefix')
param envPrefix string = 'drh'

@description('Existing Cosmos DB account name')
param cosmosAccountName string

@description('Existing Cosmos DB database name')
param cosmosDbName string = 'disaster-hub'

@description('Tags applied to all resources')
param tags object = {
  project: 'disaster-response-hub'
  component: 'monitoring-agent'
}

@description('Monitoring agent managed identity principal ID')
param monitoringAgentPrincipalId string = ''

@description('Existing Service Bus namespace name')
param serviceBusNamespaceName string = ''

@description('Existing Azure OpenAI account name')
param openAiAccountName string = ''

// ── Cosmos DB container: monitoring-decisions (append-only audit trail) ──

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' existing = {
  name: cosmosAccountName
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' existing = {
  name: cosmosDbName
  parent: cosmosAccount
}

resource monitoringDecisionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'monitoring-decisions'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'monitoring-decisions'
      partitionKey: {
        paths: ['/incident_scope_key']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/tenant_id', order: 'ascending' }
            { path: '/timestamp', order: 'descending' }
          ]
          [
            { path: '/signal_id', order: 'ascending' }
            { path: '/decision', order: 'ascending' }
          ]
        ]
      }
      // No TTL — infinite retention, append-only per spec
    }
    // Serverless — no throughput settings needed
  }
}

// ── Service Bus queue: monitoring-signals (session-based delivery) ──

resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' existing = if (!empty(serviceBusNamespaceName)) {
  name: serviceBusNamespaceName
}

resource monitoringSignalsQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = if (!empty(serviceBusNamespaceName)) {
  name: 'monitoring-signals'
  parent: serviceBusNamespace
  properties: {
    requiresSession: true // Session ID = signal_id for dedup affinity
    maxDeliveryCount: 5
    lockDuration: 'PT30S'
    defaultMessageTimeToLive: 'P1D'
    deadLetteringOnMessageExpiration: true
    maxSizeInMegabytes: 5120
  }
}

// ── Managed identity role assignments ──

// Cosmos DB Data Contributor (data-plane) for audit writes
resource cosmosDataContributorForMonitoring 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-11-15' = if (!empty(monitoringAgentPrincipalId)) {
  name: guid(cosmosAccount.id, monitoringAgentPrincipalId, '00000000-0000-0000-0000-000000000002')
  parent: cosmosAccount
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: monitoringAgentPrincipalId
    scope: cosmosAccount.id
  }
}

// Service Bus Data Receiver for signal intake
resource serviceBusReceiverForMonitoring 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(monitoringAgentPrincipalId) && !empty(serviceBusNamespaceName)) {
  name: guid(serviceBusNamespace.id, monitoringAgentPrincipalId, '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0')
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0')
    principalId: monitoringAgentPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Azure OpenAI Cognitive Services User for LLM access
resource openAiUserForMonitoring 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(monitoringAgentPrincipalId) && !empty(openAiAccountName)) {
  name: guid(openAiAccount.id, monitoringAgentPrincipalId, 'a97b65f3-24c7-4388-baec-2e87135dc908')
  scope: openAiAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
    principalId: monitoringAgentPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = if (!empty(openAiAccountName)) {
  name: openAiAccountName
}

// ── Outputs ──

output monitoringDecisionsContainerId string = monitoringDecisionsContainer.id
output monitoringSignalsQueueName string = !empty(serviceBusNamespaceName) ? monitoringSignalsQueue.name : ''
