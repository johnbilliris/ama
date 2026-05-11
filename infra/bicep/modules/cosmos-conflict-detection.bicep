// Spec 036 / Phase F (T227) — Multi-agent conflict detection log Cosmos container.
//
// Provisions a new SQL container `conflictDetectionLog` inside the existing
// `ama` database in the platform Cosmos account. Source-of-truth for the
// reactive, post-return, deterministic, rule-based conflict detector defined
// in ADR-18 / FR-RAG-COORD-01 (Pass 2 Q-P2-06).
//
// Key design notes:
//   - Partition key: `/conflict_group_id` — every implicated `AuditRecord`
//     carries the same `conflict_group_id`, so cross-table trace stitching
//     fans out to a single partition without a JOIN.
//   - Region: AU-East via the parent account (Constitution NN-2 + FR-RAG-CV-04).
//   - `defaultTtl = -1` — conflict log entries are audit-grade and retained
//     indefinitely (per AGD/PSPF retention guidance + ADR-18).
//   - Composite index on `(conflict_class asc, detected_at desc)` powers the
//     escalation dashboard's "open conflicts by class" query at low cost.
//   - No unique-key policy — UUID v7 partition keys are inherently unique.

@description('Existing platform Cosmos account name to attach to.')
param cosmosAccountName string

@description('SQL database name. Must already exist (created by audit-store.bicep).')
param databaseName string = 'ama'

@description('Tag map applied to the container.')
param tags object = {}

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-08-15' existing = {
  name: cosmosAccountName
}

resource db 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-08-15' existing = {
  parent: account
  name: databaseName
}

resource conflictDetectionLog 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'conflictDetectionLog'
  properties: {
    resource: {
      id: 'conflictDetectionLog'
      partitionKey: { paths: [ '/conflict_group_id' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
        compositeIndexes: [
          [
            { path: '/conflict_class', order: 'ascending' }
            { path: '/detected_at', order: 'descending' }
          ]
          [
            { path: '/escalation_state', order: 'ascending' }
            { path: '/detected_at', order: 'descending' }
          ]
        ]
      }
      defaultTtl: -1
    }
  }
  tags: tags
}

output conflictDetectionLogContainerName string = conflictDetectionLog.name
