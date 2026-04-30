// ────────────────────────────────────────────────────────────────────────────────
// Azure Chaos Studio targets + experiments for the AMA platform
// (spec-032 T806, FR-R05).
//
// Provisions:
//   - Chaos targets for the monitoring + risk_assessment Container Apps
//     and the Cosmos DB account (extension resources scoped to each target).
//   - Sample experiment: restart monitoring agent + a timed delay step.
// Experiments are STAGING-ONLY by convention; this module is included
// only for staging via main.bicep parameter file.
// ────────────────────────────────────────────────────────────────────────────────

@description('Cosmos DB account')
param cosmosAccountName string

@description('Container App for monitoring agent')
param monitoringAppName string

@description('Tags')
param tags object = {}

@description('Location')
param location string

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' existing = {
  name: cosmosAccountName
}

resource monitoringApp 'Microsoft.App/containerApps@2024-03-01' existing = {
  name: monitoringAppName
}

resource targetCosmos 'Microsoft.Chaos/targets@2024-01-01' = {
  scope: cosmosAccount
  name: 'Microsoft-DocumentDB'
  properties: {}
}

resource targetMonitoring 'Microsoft.Chaos/targets@2024-01-01' = {
  scope: monitoringApp
  name: 'Microsoft-ContainerApp'
  properties: {}
}

resource gameDayExperiment 'Microsoft.Chaos/experiments@2024-01-01' = {
  name: 'ama-quarterly-gameday'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    selectors: [
      {
        type: 'List'
        id: 'monitoringSelector'
        targets: [
          {
            type: 'ChaosTarget'
            id: targetMonitoring.id
          }
        ]
      }
      {
        type: 'List'
        id: 'cosmosSelector'
        targets: [
          {
            type: 'ChaosTarget'
            id: targetCosmos.id
          }
        ]
      }
    ]
    steps: [
      {
        name: 'Step1-RestartMonitoring'
        branches: [
          {
            name: 'Branch1'
            actions: [
              {
                type: 'continuous'
                name: 'urn:csci:microsoft:containerApp:restart/1.0'
                duration: 'PT5M'
                selectorId: 'monitoringSelector'
                parameters: []
              }
            ]
          }
        ]
      }
      {
        name: 'Step2-CosmosDelay'
        branches: [
          {
            name: 'Branch1'
            actions: [
              {
                type: 'delay'
                name: 'urn:csci:microsoft:chaosStudio:timedDelay/1.0'
                duration: 'PT2M'
              }
            ]
          }
        ]
      }
    ]
  }
}

output experimentId string = gameDayExperiment.id
output experimentPrincipalId string = gameDayExperiment.identity.principalId

