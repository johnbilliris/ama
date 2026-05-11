// Spec 036 — Simulation realm Event Hub consumer groups (T-A10)
//
// Adds 4 consumer groups under the existing `simulation-signals` Event Hub:
//   - sim-risk-assessment
//   - sim-evacuation
//   - sim-resource-allocation
//   - sim-monitoring
//
// Pinned to `Microsoft.EventHub/namespaces/eventhubs/consumergroups@2024-05-01-preview`.

@description('Event Hubs namespace name.')
param eventHubNamespaceName string

@description('Existing simulation-signals Event Hub name (parent).')
param eventHubName string = 'simulation-signals'

resource ns 'Microsoft.EventHub/namespaces@2024-05-01-preview' existing = {
  name: eventHubNamespaceName
}

resource hub 'Microsoft.EventHub/namespaces/eventhubs@2024-05-01-preview' existing = {
  parent: ns
  name: eventHubName
}

var consumerGroupNames = [
  'sim-risk-assessment'
  'sim-evacuation'
  'sim-resource-allocation'
  'sim-monitoring'
]

resource consumerGroups 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2024-05-01-preview' = [for cg in consumerGroupNames: {
  parent: hub
  name: cg
  properties: {
    userMetadata: 'spec-036-${cg}'
  }
}]

output consumerGroupNames array = consumerGroupNames
