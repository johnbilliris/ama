// Spec 033 — MAF Workflow Cosmos containers (T008, FR-006/007/011a/012a/019/019a)
//
// Adds three new SQL containers to the existing platform Cosmos account:
//   - workflow_runs        : durable workflow run records (no TTL; FR-011)
//   - checkpoints          : MAF workflow checkpoints (defaultTtl=2592000 = 30 days; FR-012a)
//   - tool_registrations   : per-agent MCP tool allow-list with semver (FR-019, FR-019a)
//
// All containers live in the same `ama` database under the existing account
// so they inherit AU-region placement (Constitution NN-2), managed-identity
// RBAC, backup, and the deny-delete OPA policy that protects audit_entries.

@description('Existing platform Cosmos account name to attach to.')
param cosmosAccountName string

@description('SQL database name. Must already exist (created by audit-store.bicep).')
param databaseName string = 'ama'

@description('TTL in seconds for the checkpoints container default; the retention helper re-stamps documents on terminal-state transition (FR-012a).')
param checkpointsDefaultTtlSeconds int = 2592000

param tags object = {}

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-08-15' existing = {
  name: cosmosAccountName
}

resource db 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-08-15' existing = {
  parent: account
  name: databaseName
}

// -------- workflow_runs ------------------------------------------------------

resource workflowRunsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'workflow_runs'
  properties: {
    resource: {
      id: 'workflow_runs'
      partitionKey: { paths: [ '/incident_id' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
        compositeIndexes: [
          [
            { path: '/incident_id', order: 'ascending' }
            { path: '/is_active', order: 'ascending' }
          ]
        ]
      }
      defaultTtl: -1
    }
  }
  tags: tags
}

// -------- checkpoints --------------------------------------------------------

resource checkpointsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'checkpoints'
  properties: {
    resource: {
      id: 'checkpoints'
      partitionKey: { paths: [ '/run_id' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      defaultTtl: checkpointsDefaultTtlSeconds
      uniqueKeyPolicy: {
        uniqueKeys: [
          { paths: [ '/run_id', '/sequence' ] }
        ]
      }
    }
  }
  tags: tags
}

// -------- tool_registrations -------------------------------------------------

resource toolRegistrationsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'tool_registrations'
  properties: {
    resource: {
      id: 'tool_registrations'
      partitionKey: { paths: [ '/tool_name' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      defaultTtl: -1
      uniqueKeyPolicy: {
        uniqueKeys: [
          { paths: [ '/pinned_major_version' ] }
        ]
      }
    }
  }
  tags: tags
}

output workflowRunsContainerName string = workflowRunsContainer.name
output checkpointsContainerName string = checkpointsContainer.name
output toolRegistrationsContainerName string = toolRegistrationsContainer.name
