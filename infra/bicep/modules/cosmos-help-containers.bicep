// spec-038 T-AA013 — Help Cosmos containers (FR-029, FR-022a, FR-020).
//
// Provisions the seven Cosmos containers required by the spec-038 Help
// surface, all partitioned by `/tenant_id` (defence-in-depth per FR-019 / R3),
// with TTLs aligned to data-model.md and FR-029 / AR-001:
//   - help_articles            : no TTL (metadata; body in MDX + AI Search)
//   - screenshot_registry      : no TTL (manifest)
//   - chat_sessions            : 30 days  (FR-029 — user-visible transcript)
//   - chat_audit_log           : 7 years  (FR-020 — Privacy Act APP 11)
//   - snapshot_records         : no TTL (immutable; analytics store enabled)
//   - support_handoff_config   : no TTL (1 doc per tenant)
//   - content_review_backlog   : 7 years (mirrors audit retention)
//
// Autoscale RU between 400 (min) and 4,000 (max) at launch per spec-038
// research.md (revisit per spec-036 70% capacity alert pattern).
// API version pinned alongside `cosmos-simulation-containers.bicep`.

targetScope = 'resourceGroup'

@description('Existing platform Cosmos account name to attach to.')
param cosmosAccountName string

@description('SQL database name. Must already exist (created by audit-store.bicep).')
param databaseName string = 'ama'

@description('Tags applied to every container.')
param tags object = {}

@description('Autoscale max RU/s per container (default 4000; min throughput floor is 10%).')
param autoscaleMaxRu int = 4000

// TTL constants (seconds)
var ttl30days = 30 * 24 * 60 * 60          //   2,592,000
var ttl7years = 7 * 365 * 24 * 60 * 60     // 220,752,000

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-08-15' existing = {
  name: cosmosAccountName
}

resource db 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-08-15' existing = {
  parent: account
  name: databaseName
}

// Reusable container factory
func partitionKey() object => { paths: [ '/tenant_id' ], kind: 'Hash' }

resource helpArticles 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'help_articles'
  tags: tags
  properties: {
    resource: {
      id: 'help_articles'
      partitionKey: partitionKey()
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
        compositeIndexes: [
          [
            { path: '/persona_tags/[]', order: 'ascending' }
            { path: '/surface_tags/[]', order: 'ascending' }
          ]
          [
            { path: '/snapshot_id', order: 'ascending' }
            { path: '/status', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: autoscaleMaxRu } }
  }
}

resource screenshotRegistry 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'screenshot_registry'
  tags: tags
  properties: {
    resource: {
      id: 'screenshot_registry'
      partitionKey: partitionKey()
      indexingPolicy: { indexingMode: 'consistent', includedPaths: [ { path: '/*' } ] }
      uniqueKeyPolicy: { uniqueKeys: [ { paths: [ '/screen_id' ] } ] }
    }
    options: { autoscaleSettings: { maxThroughput: autoscaleMaxRu } }
  }
}

resource chatSessions 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'chat_sessions'
  tags: tags
  properties: {
    resource: {
      id: 'chat_sessions'
      partitionKey: partitionKey()
      defaultTtl: ttl30days
      indexingPolicy: { indexingMode: 'consistent', includedPaths: [ { path: '/*' } ] }
    }
    options: { autoscaleSettings: { maxThroughput: autoscaleMaxRu } }
  }
}

resource chatAuditLog 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'chat_audit_log'
  tags: tags
  properties: {
    resource: {
      id: 'chat_audit_log'
      partitionKey: partitionKey()
      defaultTtl: ttl7years
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        compositeIndexes: [
          [
            { path: '/chat_session_id', order: 'ascending' }
            { path: '/turn_index', order: 'ascending' }
          ]
        ]
      }
    }
    options: { autoscaleSettings: { maxThroughput: autoscaleMaxRu } }
  }
}

resource snapshotRecords 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'snapshot_records'
  tags: tags
  properties: {
    resource: {
      id: 'snapshot_records'
      partitionKey: partitionKey()
      indexingPolicy: { indexingMode: 'consistent', includedPaths: [ { path: '/*' } ] }
      analyticalStorageTtl: -1   // enable analytics store for governance reports
    }
    options: { autoscaleSettings: { maxThroughput: autoscaleMaxRu } }
  }
}

resource supportHandoffConfig 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'support_handoff_config'
  tags: tags
  properties: {
    resource: {
      id: 'support_handoff_config'
      partitionKey: partitionKey()
      indexingPolicy: { indexingMode: 'consistent', includedPaths: [ { path: '/*' } ] }
    }
    options: { autoscaleSettings: { maxThroughput: autoscaleMaxRu } }
  }
}

resource contentReviewBacklog 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'content_review_backlog'
  tags: tags
  properties: {
    resource: {
      id: 'content_review_backlog'
      partitionKey: partitionKey()
      defaultTtl: ttl7years
      indexingPolicy: { indexingMode: 'consistent', includedPaths: [ { path: '/*' } ] }
    }
    options: { autoscaleSettings: { maxThroughput: autoscaleMaxRu } }
  }
}

output containerIds object = {
  help_articles: helpArticles.id
  screenshot_registry: screenshotRegistry.id
  chat_sessions: chatSessions.id
  chat_audit_log: chatAuditLog.id
  snapshot_records: snapshotRecords.id
  support_handoff_config: supportHandoffConfig.id
  content_review_backlog: contentReviewBacklog.id
}
