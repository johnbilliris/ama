// ────────────────────────────────────────────────────────────────────────────────
// AIDR Guidance Integration — Cosmos DB Containers
// Five new containers for recovery, lessons, AIIMS assignments, evacuation
// stages, and PPRR contexts. All data resides in Azure Australia East /
// Australia Southeast per NFR-015 / Constitution NN-2.
// ────────────────────────────────────────────────────────────────────────────────

@description('Cosmos DB database resource ID (parent)')
param cosmosDbName string

@description('Cosmos DB account name')
param cosmosAccountName string

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' existing = {
  name: '${cosmosAccountName}/${cosmosDbName}'
}

// Recovery environment tracker — partition by incident_id (R-013)
resource recoveryContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'recovery'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'recovery'
      partitionKey: { paths: ['/incident_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/status', order: 'ascending' }
            { path: '/updated_at', order: 'descending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// Lessons management — partition by incident_id (R-013)
resource lessonsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'lessons'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'lessons'
      partitionKey: { paths: ['/incident_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/status', order: 'ascending' }
            { path: '/created_at', order: 'descending' }
          ]
          [
            { path: '/aiims_function', order: 'ascending' }
            { path: '/pprr_phase', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// AIIMS role assignments — partition by incident_id (R-013)
resource aiimsAssignmentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'aiims-assignments'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'aiims-assignments'
      partitionKey: { paths: ['/incident_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/aiims_function', order: 'ascending' }
            { path: '/is_active', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// Evacuation stages — partition by incident_id (R-013)
resource evacuationStagesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'evacuation-stages'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'evacuation-stages'
      partitionKey: { paths: ['/incident_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/current_stage', order: 'ascending' }
            { path: '/stage_started_at', order: 'descending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// PPRR phase contexts — partition by context_reference_id (R-013)
resource pprrContextsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  name: 'pprr-contexts'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'pprr-contexts'
      partitionKey: { paths: ['/context_reference_id'], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        compositeIndexes: [
          [
            { path: '/context_type', order: 'ascending' }
            { path: '/pprr_phase', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}
