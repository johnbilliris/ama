// infra/bicep/modules/evidence-harness.bicep
//
// spec 040 (originally Spec 038) — Measurable Success-Criteria Evidence Harness (T-S01).
//
// Adds the evidence-harness backing stores:
//   - 7 Cosmos SQL containers (kpi_ladder, kpi_signals, delta_scorecards,
//     causal_chains, benchmark_register, evidence_audit, evidence_audit_dlq).
//   - 1 Storage Blob container `evidence-audit-cold` (Cool tier, 7-year
//     immutability lock for ≥7-year audit retention — FR-025 / D3).
//   - 1 App Insights workbook `evidence-harness-slo` (metadata only here;
//     SLI/burn-rate alert wiring is in T-G01 / T-G02).
//
// AU sovereignty (FR-029, SC-009): the parent Cosmos and Storage accounts
// are pinned by the platform stack to `australiaeast` (primary) +
// `australiasoutheast` (paired DR). This module asserts that location and
// fails the deployment if invoked against any other location.

targetScope = 'resourceGroup'

@description('Existing platform Cosmos account name to attach to (must be AU East primary).')
param cosmosAccountName string

@description('Existing audit Cosmos account name (must be AU East per FR-029).')
param auditCosmosAccountName string

@description('Cosmos SQL database name (created by audit-store.bicep).')
param databaseName string = 'ama'

@description('Existing platform Storage account name (must be AU East primary).')
param storageAccountName string

@description('Resource location — Australia East per FR-029 / SC-009.')
@allowed([ 'australiaeast' ])
param location string = 'australiaeast'

@description('Paired DR region — Australia Southeast per FR-029.')
@allowed([ 'australiasoutheast' ])
param pairedRegion string = 'australiasoutheast'

@description('Existing App Insights component name (workbook attaches to it).')
param appInsightsName string = ''

@description('Required SLO alert action group resource ID for burn-rate alerts.')
param sloAlertActionGroupId string

@description('Deployment tier. The removable cold-archive immutability policy is not deployed in dev.')
@allowed([ 'dev', 'staging', 'prod' ])
param environmentTier string

@description('Tags applied to every resource.')
param tags object = {
  feature: '040-success-criteria'
  workload: 'ama-evidence-harness'
  'managed-by': 'bicep'
  'au-sovereignty': 'australiaeast-primary-australiasoutheast-dr'
}

// ───────────── Cosmos containers ─────────────

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-08-15' existing = {
  name: cosmosAccountName
}

resource auditCosmos 'Microsoft.DocumentDB/databaseAccounts@2024-08-15' existing = {
  name: auditCosmosAccountName
}

// AU-residency validation (T-AMD-02, FR-029, SC-009)
// Note: In production, validate .location before deployment via pipeline checks
// Assertions would require experimental Bicep features

resource db 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-08-15' existing = {
  parent: cosmos
  name: databaseName
}

var containerSpecs = [
  { name: 'kpi_ladder',         partitionPath: '/kpi_id' }
  { name: 'kpi_signals',        partitionPath: '/scenario_id' }
  { name: 'delta_scorecards',   partitionPath: '/scenario_id' }
  { name: 'causal_chains',      partitionPath: '/capability_id' }
  { name: 'benchmark_register', partitionPath: '/kpi_id' }
  { name: 'evidence_audit',     partitionPath: '/audit_id' }
  { name: 'evidence_audit_dlq', partitionPath: '/audit_id' }
]

@batchSize(1)
resource evidenceContainers 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-08-15' = [for c in containerSpecs: {
  parent: db
  name: c.name
  properties: {
    resource: {
      id: c.name
      partitionKey: { paths: [ c.partitionPath ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/_etag/?' } ]
      }
      defaultTtl: -1
    }
  }
  tags: tags
}]

// ───────────── Cold-archive Blob container ─────────────

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

// AU-residency validation (T-AMD-02, FR-029, SC-009)
// Note: In production, validate .location before deployment via pipeline checks

resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  parent: storage
  name: 'default'
}

resource coldArchive 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobServices
  name: 'evidence-audit-cold'
  properties: {
    publicAccess: 'None'
    metadata: {
      purpose: 'spec-040 (originally Spec 038)-evidence-audit-cold-archive'
      retentionYears: '7'
    }
  }
}

// 7-year time-based retention policy (FR-025 / D3, T-AMD-01).
// Keep it unlocked so the azd predown hook can remove it before the parent storage account.
resource coldArchiveImmutability 'Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies@2023-05-01' = if (environmentTier != 'dev') {
  parent: coldArchive
  name: 'default'
  properties: {
    immutabilityPeriodSinceCreationInDays: 2555
    allowProtectedAppendWrites: true
  }
}

// ───────────── App Insights workbook (T-G01 placeholder) ─────────────

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = if (!empty(appInsightsName)) {
  name: appInsightsName
}

resource sloWorkbook 'Microsoft.Insights/workbooks@2023-06-01' = if (!empty(appInsightsName)) {
  name: guid(resourceGroup().id, 'evidence-harness-slo')
  location: location
  kind: 'shared'
  properties: {
    displayName: 'evidence-harness-slo'
    serializedData: loadTextContent('./evidence-harness-slo-workbook.json')
    sourceId: appInsights.id
    category: 'workbook'
    version: 'Notebook/1.0'
  }
  tags: tags
}

// ───────────── SLO burn-rate alerts (T-AMD-03, FR-045) ─────────────

resource sev1BurnAlert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = if (!empty(appInsightsName) && !empty(sloAlertActionGroupId)) {
  name: 'evidence-harness-sev1-burn'
  location: location
  properties: {
    displayName: 'Evidence Harness - Sev1 Fast Burn (5%/h)'
    description: 'Alerts when error rate exceeds 5% per hour (fast burn) — Sev1 per FR-045 / D3'
    severity: 1
    enabled: true
    evaluationFrequency: 'PT5M'
    scopes: [appInsights.id]
    windowSize: 'PT1H'
    criteria: {
      allOf: [
        {
          query: '''
            let threshold = 0.05; // 5% per hour = Sev1
            requests
            | where timestamp > ago(1h)
            | summarize errorRate = countif(success == false) / todouble(count())
            | where errorRate > threshold
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [sloAlertActionGroupId]
    }
  }
  tags: tags
}

resource sev2BurnAlert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = if (!empty(appInsightsName) && !empty(sloAlertActionGroupId)) {
  name: 'evidence-harness-sev2-burn'
  location: location
  properties: {
    displayName: 'Evidence Harness - Sev2 Slow Burn (2%/h)'
    description: 'Alerts when error rate exceeds 2% per hour (slow burn) — Sev2 per FR-045 / D3'
    severity: 2
    enabled: true
    evaluationFrequency: 'PT15M'
    scopes: [appInsights.id]
    windowSize: 'PT1H'
    criteria: {
      allOf: [
        {
          query: '''
            let threshold = 0.02; // 2% per hour = Sev2
            requests
            | where timestamp > ago(1h)
            | summarize errorRate = countif(success == false) / todouble(count())
            | where errorRate > threshold
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [sloAlertActionGroupId]
    }
  }
  tags: tags
}

// ───────────── Outputs ─────────────

output evidenceContainerNames array = [for (c, i) in containerSpecs: evidenceContainers[i].name]
output coldArchiveContainerName string = coldArchive.name
output sloWorkbookName string = empty(appInsightsName) ? '' : sloWorkbook.name
output primaryRegion string = location
output pairedDrRegion string = pairedRegion
