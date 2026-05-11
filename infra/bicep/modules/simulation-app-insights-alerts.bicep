// Spec-036 Wave 4 — T-Z01 / ADR-036-008 SLI thresholds applied as
// Azure Monitor scheduledQueryRules.
//
// Five canonical SLIs from `specs/036-sim-agent-extend/contracts/sli-thresholds.md`:
//
//   1. Injection P95 latency (parse → fan-out)
//   2. Audit sequence retry rate (gap-free invariant)
//   3. DLQ depth (sequence-uncertainty fail-closed entries)
//   4. RU consumption headroom (Cosmos throttling guard)
//   5. Cascade degraded-to-annotation rate (T-Q03 affinity ladder fallback)
//
// This module ships alongside the legacy `observability-alerts.bicep`
// (T-J07) which covers the plan.md SLIs 1-5. ADR-036-008 SLIs are the
// FR-063 staging-promotion gates and are evaluated by
// `tests/e2e/test_staging_promotion_gates.py`.
//
// Canonical references:
//   ADR-036-008 (SLI thresholds rationale)
//   contracts/sli-thresholds.md (KQL queries + thresholds)
//   tasks.md T-Z01..Z05 (Wave 4 dispatch).

@description('Existing Application Insights component name (sim-realm).')
param appInsightsName string

@description('Azure region — must match the App Insights component.')
@allowed([
  'australiaeast'
  'australiasoutheast'
])
param location string = 'australiaeast'

@description('Action group resource id for warn-tier alerts (Slack).')
param warnActionGroupId string

@description('Action group resource id for breach-tier alerts (PagerDuty).')
param breachActionGroupId string

@description('Optional resource tags.')
param tags object = {}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// SLI-Z1 — Injection P95 latency.
// Threshold: warn > 1500 ms, breach > 2000 ms over rolling 5 min.
resource sliZ1Latency 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-z1-injection-latency-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 3
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    autoMitigate: true
    description: 'ADR-036-008 SLI-1: P95 inject→fan-out latency > 2000 ms.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customEvents | where name == "inject_telemetry.fan_out_complete" | extend latency_ms = todouble(customDimensions["fan_out_latency_ms"]) | summarize p95_ms = percentile(latency_ms, 95)'
          timeAggregation: 'Average'
          metricMeasureColumn: 'p95_ms'
          operator: 'GreaterThan'
          threshold: 2000
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ breachActionGroupId ] }
  }
}

// SLI-Z2 — Audit sequence retry rate (gap-free invariant breach).
// Threshold: any gap detected in rolling 7-day window → SEV-2.
resource sliZ2GapFree 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-z2-audit-gap-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 2
    evaluationFrequency: 'PT15M'
    windowSize: 'P7D'
    autoMitigate: true
    description: 'ADR-036-008 SLI-2: Audit sequence gap detected (zero-tolerance).'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customEvents | where name == "audit.sequence.uncertainty" | summarize gappy = count()'
          timeAggregation: 'Total'
          metricMeasureColumn: 'gappy'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ breachActionGroupId ] }
  }
}

// SLI-Z3 — DLQ depth.
// Threshold: any DLQ entry within 1 h → SEV-3 (sequence-uncertainty fail-closed).
resource sliZ3DlqDepth 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-z3-dlq-depth-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 3
    evaluationFrequency: 'PT5M'
    windowSize: 'PT1H'
    autoMitigate: true
    description: 'ADR-036-008 SLI-3: DLQ depth (audit_sequence_uncertainty) > 0 in 1h.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customEvents | where name == "audit.sequence.uncertainty" | summarize dlq_depth = count()'
          timeAggregation: 'Total'
          metricMeasureColumn: 'dlq_depth'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ warnActionGroupId, breachActionGroupId ] }
  }
}

// SLI-Z4 — RU consumption headroom (Cosmos throttling guard).
// Threshold: warn at 70 %, breach at 90 % of provisioned RU/s.
resource sliZ4RuHeadroom 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-z4-ru-headroom-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 3
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    autoMitigate: true
    description: 'ADR-036-008 SLI-4: Cosmos RU consumption > 90% provisioned.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'AzureDiagnostics | where ResourceProvider == "MICROSOFT.DOCUMENTDB" | where Category == "DataPlaneRequests" | summarize p95_ru = percentile(todouble(requestCharge_s), 95)'
          timeAggregation: 'Average'
          metricMeasureColumn: 'p95_ru'
          operator: 'GreaterThan'
          threshold: 90
          failingPeriods: { numberOfEvaluationPeriods: 2, minFailingPeriodsToAlert: 2 }
        }
      ]
    }
    actions: { actionGroups: [ breachActionGroupId ] }
  }
}

// SLI-Z5 — Cascade degraded-to-annotation rate.
// Threshold: warn > 5 %, breach > 10 % of cascades over rolling 1 h
// (per T-Q03 affinity ladder; high rate signals capacity exhaustion).
resource sliZ5DegradedRate 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-z5-degraded-rate-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 3
    evaluationFrequency: 'PT5M'
    windowSize: 'PT1H'
    autoMitigate: true
    description: 'ADR-036-008 SLI-5: cascade.degraded_to_annotation rate > 10%.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customEvents | where name in ("cascade.degraded_to_annotation", "cascade.fan_out_complete") | summarize degraded_pct = 100.0 * countif(name == "cascade.degraded_to_annotation") / count()'
          timeAggregation: 'Average'
          metricMeasureColumn: 'degraded_pct'
          operator: 'GreaterThan'
          threshold: 10
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ warnActionGroupId, breachActionGroupId ] }
  }
}

// Output the alert rule ids so the staging-promotion workflow can poll
// them via Azure Monitor REST API for the FR-063 gate.
output sliAlertRuleIds object = {
  z1Latency: sliZ1Latency.id
  z2GapFree: sliZ2GapFree.id
  z3DlqDepth: sliZ3DlqDepth.id
  z4RuHeadroom: sliZ4RuHeadroom.id
  z5DegradedRate: sliZ5DegradedRate.id
}
