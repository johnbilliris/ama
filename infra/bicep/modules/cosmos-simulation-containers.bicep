// Spec 036 — Simulation realm Cosmos containers (T-A09 + T-A09 [AMEND])
//
// Adds the per-simulation Cosmos containers needed for the Telemetry-Injection
// agent and cascade orchestrator:
//   - simulation_synthetic_signals          (PK: /simulationId)
//   - sub_agent_invocation_records          (PK: /simulationId)
//   - simulation_threads                    (PK: /simulationId)
//   - exercise_outcome_index                (PK: /simulationId)
//   - routing_decisions                     (PK: /simulationId)
//   - simulation_audit_sequence_counters    (PK: /simulation_id)   [AMEND ADR-036-007]
//   - simulation_idempotency_cache          (PK: /simulation_id)   [AMEND ADR-036-009]
//   - simulation_audit_dlq                  (PK: /simulation_id)   [AMEND]
//
// Pinned to the same `Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15`
// API version as `cosmos-workflow.bicep` for AVM-aligned parity.
//
// Consistency: the parent account is configured for Session consistency in
// `audit-store.bicep`; per ADR-036-001, that level is sufficient for the new
// simulation realm containers (cross-region read replicas inherit
// bounded-staleness from the account-level setting).
//
// AMEND-cycle note (T-A09 [AMEND] / cohort review):
// The three new containers introduced for the amendment cycle (sequence
// counters, idempotency cache, audit DLQ) use the **snake_case** partition
// path `/simulation_id` to align with the Pydantic envelopes from
// `packages/domain/src/domain/models/telemetry_injection_audit_entry.py`
// (which serialises `simulation_id`). The original containers above kept
// `/simulationId` for backwards-compatibility with the spec-035 ingestion
// surface; both forms are partitioned per-simulation so no cross-cutting
// rebalance is needed.

@description('Existing platform Cosmos account name to attach to.')
param cosmosAccountName string

@description('SQL database name. Must already exist (created by audit-store.bicep).')
param databaseName string = 'ama'

@description('Tags applied to every container.')
param tags object = {}

// Cycle 3 / T-AA38 / A3-02 / PD-C3-03 isolation guarantee (v) — the
// ``Simulation.Coordinator`` test identity is granted Cosmos Data
// Contributor scoped EXCLUSIVELY to the ``tnt-stg-smoke`` test tenant.
// The smoke-injection job in ``.github/workflows/staging-promotion.yml``
// runs as this principal; without scope-isolation, a leaked credential
// could write into production-tenant containers. The role-assignment
// resource below is asserted by
// ``tests/contract/test_smoke_tenant_isolation.py`` (T-AA39) to ensure
// the principal has exactly one assignment with the smoke-tenant
// scope and zero production-tenant assignments.
@description('Object id of the `Simulation.Coordinator` test-identity Entra ID enterprise app. Required for the `tnt-stg-smoke`-scoped role assignment that authorises the staging-promotion smoke-injection job (T-AA38). Set to empty string to skip provisioning the assignment in non-staging deployments.')
param coordinatorPrincipalId string = ''

@description('Tenant id of the dedicated smoke-injection test tenant. Defaults to the contract value `tnt-stg-smoke`. Used as the partition-key scope for the `Simulation.Coordinator` role assignment.')
param smokeTenantId string = 'tnt-stg-smoke'

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-08-15' existing = {
  name: cosmosAccountName
}

resource db 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-08-15' existing = {
  parent: account
  name: databaseName
}

// -------- simulation_synthetic_signals --------------------------------------

resource syntheticSignals 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'simulation_synthetic_signals'
  properties: {
    resource: {
      id: 'simulation_synthetic_signals'
      partitionKey: { paths: [ '/simulationId' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
        compositeIndexes: [
          [
            { path: '/simulationId', order: 'ascending' }
            { path: '/observed_at', order: 'descending' }
          ]
          [
            { path: '/simulationId', order: 'ascending' }
            { path: '/category', order: 'ascending' }
          ]
        ]
      }
      defaultTtl: -1
    }
  }
  tags: tags
}

// -------- sub_agent_invocation_records --------------------------------------

resource subAgentInvocationRecords 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'sub_agent_invocation_records'
  properties: {
    resource: {
      id: 'sub_agent_invocation_records'
      partitionKey: { paths: [ '/simulationId' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      defaultTtl: -1
    }
  }
  tags: tags
}

// -------- simulation_threads (cascade thread-cap) ---------------------------

resource simulationThreads 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'simulation_threads'
  properties: {
    resource: {
      id: 'simulation_threads'
      partitionKey: { paths: [ '/simulationId' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      defaultTtl: -1
    }
  }
  tags: tags
}

// -------- exercise_outcome_index --------------------------------------------

resource exerciseOutcomeIndex 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'exercise_outcome_index'
  properties: {
    resource: {
      id: 'exercise_outcome_index'
      partitionKey: { paths: [ '/simulationId' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      defaultTtl: -1
    }
  }
  tags: tags
}

// -------- routing_decisions -------------------------------------------------

resource routingDecisions 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'routing_decisions'
  properties: {
    resource: {
      id: 'routing_decisions'
      partitionKey: { paths: [ '/simulationId' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      defaultTtl: -1
    }
  }
  tags: tags
}

output syntheticSignalsContainer string = syntheticSignals.name
output subAgentInvocationRecordsContainer string = subAgentInvocationRecords.name
output simulationThreadsContainer string = simulationThreads.name
output exerciseOutcomeIndexContainer string = exerciseOutcomeIndex.name
output routingDecisionsContainer string = routingDecisions.name

// =============================================================================
// AMEND — additional containers introduced by the spec-036 amendment cycle.
//
// These three containers replace process-local state that broke in any
// multi-replica deployment of the API container app:
//   * sequence counters: replaces audit_writer._sequence_counters dict
//     (ADR-036-007 distributed sequence allocator).
//   * idempotency cache: deduplicates retried inject-telemetry / lifecycle
//     POSTs over a 24h window (ADR-036-009).
//   * audit DLQ: receives audit envelopes that exhausted the optimistic
//     concurrency retry budget (Phase Q DLQ).
//
// All three use `/simulation_id` (snake_case) to align with the canonical
// Pydantic envelope models in `packages/domain/src/domain/models`.
// =============================================================================

// -------- simulation_audit_sequence_counters --------------------------------

resource simulationAuditSequenceCounters 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'simulation_audit_sequence_counters'
  properties: {
    resource: {
      id: 'simulation_audit_sequence_counters'
      partitionKey: { paths: [ '/simulation_id' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      defaultTtl: -1
    }
    options: {
      throughput: 400
    }
  }
  tags: tags
}

// -------- simulation_idempotency_cache --------------------------------------

resource simulationIdempotencyCache 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'simulation_idempotency_cache'
  properties: {
    resource: {
      id: 'simulation_idempotency_cache'
      partitionKey: { paths: [ '/simulation_id' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      // ADR-036-009 — 24h TTL anchored on Cosmos `_ts`.
      defaultTtl: 86400
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 4000
      }
    }
  }
  tags: tags
}

// -------- simulation_audit_dlq ----------------------------------------------

resource simulationAuditDlq 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = {
  parent: db
  name: 'simulation_audit_dlq'
  properties: {
    resource: {
      id: 'simulation_audit_dlq'
      partitionKey: { paths: [ '/simulation_id' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      defaultTtl: -1
    }
    options: {
      throughput: 400
    }
  }
  tags: tags
}

output simulationAuditSequenceCountersContainer string = simulationAuditSequenceCounters.name
output simulationIdempotencyCacheContainer string = simulationIdempotencyCache.name
output simulationAuditDlqContainer string = simulationAuditDlq.name

// -------- Simulation.Coordinator → tnt-stg-smoke role assignment ------------
//
// Cycle 3 / T-AA38 / A3-02 / PD-C3-03 isolation guarantee (v) — exactly
// one ``Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments`` entry
// scoped to the ``tnt-stg-smoke`` test tenant. The assignment is
// conditional on a non-empty ``coordinatorPrincipalId`` so the module
// remains usable in deployments that do NOT run the smoke-injection job
// (e.g. local development, ephemeral CI fixtures). The conditional
// pattern is asserted by ``tests/contract/test_smoke_tenant_isolation.py``
// (T-AA39) — when the principal id is set, exactly one assignment must
// be emitted; the assignment's ``scope`` MUST resolve to the smoke
// tenant's partition-key path; NO production-tenant assignments may
// reference the same principal.
//
// Role definition id ``00000000-0000-0000-0000-000000000002`` is the
// built-in ``Cosmos DB Built-in Data Contributor`` (read + write +
// metadata) — sufficient for the smoke-injection job to write
// ``simulation_synthetic_signals`` rows but NOT to alter container
// definitions.

var smokeRoleAssignmentName = guid(account.id, coordinatorPrincipalId, smokeTenantId)

resource smokeCoordinatorRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-08-15' = if (!empty(coordinatorPrincipalId)) {
  parent: account
  name: smokeRoleAssignmentName
  properties: {
    // Built-in Cosmos DB Data Contributor (NOT the management-plane
    // role; this is the data-plane RBAC surface — see
    // https://learn.microsoft.com/azure/cosmos-db/how-to-setup-rbac).
    roleDefinitionId: '${account.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: coordinatorPrincipalId
    // Cycle 5 / A5-01 (spec.md:4943, 4947-4992; Pass-1 Q1 ordering at
    // spec.md:5067-5096) — four-clause ordering aligned with
    // ADR-036-011:172-184 and the Cycle 4 A4-02 sub-block below:
    //
    // (1) Database-level scope statement — the assignment is scoped at
    //     the database level; the ``scope:`` line below resolves to
    //     ``${account.id}/dbs/${databaseName}``, which is the narrowest
    //     scope supported by the Cosmos data-plane RBAC API 2024-08-15
    //     (database-level Cosmos data-plane RBAC).
    // (2) Compensating defence-in-depth — the database-level scope is
    //     a **compensating defence-in-depth control** rather than a
    //     partition-level guarantee, because the Cosmos data-plane
    //     RBAC API 2024-08-15 does not yet expose a ``partitionKey``
    //     selector.
    // (3) Joint enforcement — tenant isolation is jointly enforced by
    //     (a) the SLI-Z6 / SLI-Z7 query-time
    //     ``where tenant_id == "tnt-stg-smoke"`` filter (per
    //     ``contracts/sli-thresholds.md`` §6a / §6b), (b) the
    //     ``customDimensions["tenant_id"]`` envelope discriminator,
    //     and (c) the Pass-1 Q2 isolation guarantees (i)–(v). The
    //     ``smokeTenantId`` parameter participates in the assignment
    //     name's ``guid()`` so the assignment is unambiguously the
    //     smoke-tenant assignment for contract-test discovery.
    // (4) The partition-scope upgrade is tracked at
    //     [backlog issue: #84].
    //
    // Cycle 4 / A4-02 (spec.md:3896-3915, ADR-036-011:172-173):
    // The database-level scope below is a **compensating defence-in-depth
    // control** rather than a partition-level guarantee — Cosmos
    // data-plane RBAC API 2024-08-15 does not yet expose a
    // `partitionKey` selector. Tenant isolation is jointly enforced
    // by (a) the SLI-Z6 / SLI-Z7 query-time
    // `where tenant_id == "tnt-stg-smoke"` filter, (b) the
    // `customDimensions["tenant_id"]` envelope discriminator, and
    // (c) Pass-1 Q2 isolation guarantees (i)–(v). The
    // partition-scope upgrade is tracked at [backlog issue: #84]
    // (filed via T-AA55).
    scope: '${account.id}/dbs/${databaseName}'
  }
}

output smokeCoordinatorRoleAssignmentName string = !empty(coordinatorPrincipalId) ? smokeCoordinatorRoleAssignment.name : ''
output smokeTenantIdValue string = smokeTenantId
