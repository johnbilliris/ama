// Spec 036 / Phase F (T196) — Cultural Authority Registry Cosmos container.
//
// Provisions a new SQL container `culturalAuthorityRegistry` inside the
// existing `ama` database in the platform Cosmos account. Container is
// EMPTY at deploy time; population is HUMAN-IN-LOOP (T202) per FR-RAG-CA-05
// and requires sign-off from NEMA + AFAC + Indigenous community
// representatives.
//
// Key design notes:
//   - Partition key: `/operator_id` — co-locates an operator's consent
//     records on a single physical partition for low-latency single-operator
//     lookup at retrieval time (Pass 2 Q-P2-02).
//   - Region: AU-East via the parent account (Constitution NN-2 + FR-RAG-CV-04).
//   - No defaultTtl: revoked records remain as audit anchors; the gate
//     evaluates `revocation_reason != null` and `expires_at < now()`.
//   - Unique key on (operator_id, land_council_id, scope) prevents duplicate
//     consent rows for the same operator/council/scope tuple.

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

resource culturalAuthorityRegistry 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'culturalAuthorityRegistry'
  properties: {
    resource: {
      id: 'culturalAuthorityRegistry'
      partitionKey: { paths: [ '/operator_id' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
        compositeIndexes: [
          [
            { path: '/operator_id', order: 'ascending' }
            { path: '/expires_at', order: 'descending' }
          ]
        ]
      }
      defaultTtl: -1
      uniqueKeyPolicy: {
        uniqueKeys: [
          { paths: [ '/operator_id', '/land_council_id', '/scope' ] }
        ]
      }
    }
  }
  tags: tags
}

output culturalAuthorityRegistryContainerName string = culturalAuthorityRegistry.name
