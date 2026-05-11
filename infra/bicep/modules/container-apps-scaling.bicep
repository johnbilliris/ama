// Spec 036 — Container Apps KEDA scaling for sim consumer groups (T-A16)
//
// Adds KEDA `azure-eventhub` triggers for the 4 simulation consumer groups
// provisioned in T-A10. Targets the agents Container App (single replica per
// thousand-event lag, max 10).

@description('Container App name to attach scaling rules to.')
param containerAppName string

@description('Event Hubs namespace name.')
param eventHubNamespaceName string

@description('Event Hub name.')
param eventHubName string = 'simulation-signals'

@description('Lag threshold per consumer group.')
param unprocessedEventThreshold int = 100

var consumerGroups = [
  'sim-risk-assessment'
  'sim-evacuation'
  'sim-resource-allocation'
  'sim-monitoring'
]

resource containerApp 'Microsoft.App/containerApps@2024-03-01' existing = {
  name: containerAppName
}

resource scalingPatch 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerApp.name
  location: containerApp.location
  properties: {
    template: {
      scale: {
        minReplicas: 0
        maxReplicas: 10
        rules: [for (cg, i) in consumerGroups: {
          name: 'sim-${cg}-keda'
          custom: {
            type: 'azure-eventhub'
            metadata: {
              eventHubNamespace: eventHubNamespaceName
              eventHubName: eventHubName
              consumerGroup: cg
              unprocessedEventThreshold: '${unprocessedEventThreshold}'
              checkpointStrategy: 'blobMetadata'
            }
          }
        }]
      }
    }
  }
}

output appName string = containerApp.name
