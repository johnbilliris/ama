// ────────────────────────────────────────────────────────────────────────────────
// Emergency Planning — Cosmos DB Containers
// Three new containers for emergency plans, recovery programmes (M&E),
// and the immutable AIDR recovery catalogue. All data resides in Azure
// Australia East / Australia Southeast per NFR-008 / Constitution NN-2.
// ────────────────────────────────────────────────────────────────────────────────

@description('Cosmos DB database resource ID (parent)')
param cosmosDbName string

@description('Cosmos DB account name')
param cosmosAccountName string

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' existing = {
  name: '${cosmosAccountName}/${cosmosDbName}'
}

// Emergency Plans — partition by region_id (plan hierarchy queries)
resource emergencyPlansContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'emergency-plans'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'emergency-plans'
      partitionKey: { paths: ['/region_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/lifecycle_state', order: 'ascending' }
            { path: '/updated_at', order: 'descending' }
          ]
          [
            { path: '/hierarchy_level', order: 'ascending' }
            { path: '/lifecycle_state', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// Recovery Programmes — partition by incident_id (M&E frameworks, program logic, eval reports)
resource recoveryProgrammesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'recovery-programmes'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'recovery-programmes'
      partitionKey: { paths: ['/incident_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/status', order: 'ascending' }
            { path: '/created_at', order: 'descending' }
          ]
          [
            { path: '/incident_id', order: 'ascending' }
            { path: '/status', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// Recovery Catalogue — partition by domain (immutable AIDR reference data, ~561 documents)
resource recoveryCatalogueContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'recovery-catalogue'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'recovery-catalogue'
      partitionKey: { paths: ['/domain'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/domain', order: 'ascending' }
            { path: '/objective_type', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}
