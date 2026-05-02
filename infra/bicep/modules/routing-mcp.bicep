// Spec 033 — Routing-service MCP Container App (T066, ADR-033-04, FR-019)
//
// Internal-only ingress, managed identity, deployed alongside ca-agents-drh-{env}.
// Advertises semver 1.0.0 in its MCP serverInfo block; the agent runtime allow-list
// (T064) validates the major version on every call.

@description('Container Apps environment name to deploy into (existing).')
param environmentName string

@description('Azure region (must be australiaeast / australiasoutheast per Constitution NN-2).')
@allowed([
  'australiaeast'
  'australiasoutheast'
])
param location string = 'australiaeast'

@description('Container image reference (ACR-hosted).')
param imageRef string

@description('Optional resource tags.')
param tags object = {}

@description('Environment-suffix used in container app naming.')
@allowed([
  'dev'
  'staging'
  'production'
])
param env string = 'dev'

resource managedEnv 'Microsoft.App/managedEnvironments@2024-08-02-preview' existing = {
  name: environmentName
}

resource routingMcp 'Microsoft.App/containerApps@2024-08-02-preview' = {
  name: 'ca-routing-mcp-drh-${env}'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: managedEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 9000
        transport: 'http'
        traffic: [
          { latestRevision: true, weight: 100 }
        ]
      }
    }
    template: {
      containers: [
        {
          name: 'routing-mcp'
          image: imageRef
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            { name: 'PORT', value: '9000' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output routingMcpAppName string = routingMcp.name
output routingMcpFqdn string = routingMcp.properties.configuration.ingress.fqdn
