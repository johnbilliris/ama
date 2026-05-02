// Spec 029 — Audit Store (T028)
// Cosmos DB container for the canonical FR-015 deployment audit events.
@description('Existing Cosmos account name to attach to.')
param cosmosAccountName string
param tags object = {}

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-08-15' existing = {
  name: cosmosAccountName
}

resource db 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-08-15' = {
  parent: account
  name: 'ama'
  properties: {
    resource: { id: 'ama' }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'audit_events'
  properties: {
    resource: {
      id: 'audit_events'
      partitionKey: { paths: [ '/environment' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      defaultTtl: -1
    }
  }
}

output containerName string = container.name
