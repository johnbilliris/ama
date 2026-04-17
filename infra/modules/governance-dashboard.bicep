// ─────────────────────────────────────────────────────────
// Bicep module: Governance Dashboard infrastructure (T093-T094)
// Creates Cosmos DB indexes and Blob Storage for audit exports.
// ─────────────────────────────────────────────────────────

@description('Location for all resources')
param location string = resourceGroup().location

@description('Unique suffix for resource names (e.g. from uniqueString)')
param suffix string

@description('Cosmos DB account name to add indexing policy')
param cosmosAccountName string

@description('Cosmos DB database name')
param cosmosDatabaseName string = 'governance'

@description('Storage account name for audit exports')
param storageAccountName string

@description('Tags for all resources')
param tags object = {}

// ─── Cosmos DB: Governance Dashboard Container ───

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' existing = {
  name: cosmosAccountName
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' existing = {
  parent: cosmosAccount
  name: cosmosDatabaseName
}

resource dashboardContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDatabase
  name: 'governance-dashboard'
  properties: {
    resource: {
      id: 'governance-dashboard'
      partitionKey: {
        paths: ['/tenant_id']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          { path: '/tenant_id/?' }
          { path: '/type/?' }
          { path: '/status/?' }
          { path: '/calculated_at/?' }
          { path: '/gate_number/?' }
          { path: '/compliance_status/?' }
          { path: '/timestamp/?' }
          { path: '/actor_id/?' }
          { path: '/action/?' }
          { path: '/severity/?' }
          { path: '/domain/?' }
        ]
        excludedPaths: [
          { path: '/*' }
          { path: '/"_etag"/?' }
        ]
        compositeIndexes: [
          [
            { path: '/tenant_id', order: 'ascending' }
            { path: '/type', order: 'ascending' }
            { path: '/calculated_at', order: 'descending' }
          ]
          [
            { path: '/tenant_id', order: 'ascending' }
            { path: '/timestamp', order: 'descending' }
          ]
          [
            { path: '/tenant_id', order: 'ascending' }
            { path: '/severity', order: 'ascending' }
            { path: '/status', order: 'ascending' }
          ]
        ]
      }
      defaultTtl: -1 // No automatic expiration
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: ['/id']
          }
        ]
      }
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 4000
      }
    }
  }
  tags: tags
}

// ─── Cosmos DB: Health Score History Container ───

resource healthScoreContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDatabase
  name: 'health-score-history'
  properties: {
    resource: {
      id: 'health-score-history'
      partitionKey: {
        paths: ['/tenant_id']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          { path: '/tenant_id/?' }
          { path: '/calculated_at/?' }
          { path: '/status/?' }
        ]
        excludedPaths: [
          { path: '/*' }
          { path: '/"_etag"/?' }
        ]
      }
      defaultTtl: 7776000 // 90 days
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 1000
      }
    }
  }
  tags: tags
}

// ─── Blob Storage: Audit Export Container ───

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  parent: storageAccount
  name: 'default'
}

resource auditExportContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'audit-exports'
  properties: {
    publicAccess: 'None'
    metadata: {
      purpose: 'governance-dashboard-audit-exports'
      retention: '90-days'
    }
  }
}

// ─── Lifecycle Management Policy: Auto-delete exports after 90 days ───

resource lifecyclePolicy 'Microsoft.Storage/storageAccounts/managementPolicies@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    policy: {
      rules: [
        {
          name: 'delete-old-audit-exports'
          enabled: true
          type: 'Lifecycle'
          definition: {
            actions: {
              baseBlob: {
                delete: {
                  daysAfterModificationGreaterThan: 90
                }
              }
            }
            filters: {
              prefixMatch: ['audit-exports/']
              blobTypes: ['blockBlob']
            }
          }
        }
      ]
    }
  }
}

// ─── Outputs ───

output dashboardContainerName string = dashboardContainer.name
output healthScoreContainerName string = healthScoreContainer.name
output auditExportContainerUrl string = '${storageAccount.properties.primaryEndpoints.blob}audit-exports'
