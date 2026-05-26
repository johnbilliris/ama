// T-J07 — 5 plan-canonical SLI/SLO alerts for the simulation realm.
//
// Per plan.md §SLI/SLO table the simulation realm tracks 5 canonical SLIs:
//
//   1. Telemetry-injection parse-to-pipeline ≤ 5 s p95   → SEV-2 fast-burn
//   2. Risk-Assessment auto-fan-out ≤ 15 s p95           → SEV-2 fast-burn
//   3. Cascade fan-out completion ≤ 30 s p95 (FR-043)    → SEV-2 fast-burn
//   4. Map-overlay update ≤ 15 s hazard / ≤ 10 s weather → SEV-3
//   5. SC-006 zero-real-comms egress                     → SEV-0 immediate page
//
// Each rule lands in Azure Monitor as a scheduledQueryRule against the
// shared Application Insights workspace (`appInsightsName`) and is wired
// to the action group at `actionGroupId`. SEV-0 alerts also wire to
// `pagerDutyActionGroupId` per T-J08.
//
// Canonical references:
//   plan.md:421-428 (SLI table)
//   spec.md SC-006/010 (egress + overlay SLOs)
//   audit-envelope.md (egress block_reason literals)

@description('Existing Application Insights component name (sim-realm shared workspace).')
param appInsightsName string

@description('Azure region — must match the App Insights component.')
@allowed([
  'australiaeast'
  'australiasoutheast'
])
param location string = 'australiaeast'

@description('Action group resource id for ordinary SEV-2/SEV-3 alerts.')
param actionGroupId string

@description('Action group resource id for SEV-0 PagerDuty paging (T-J08).')
param pagerDutyActionGroupId string

@description('Optional resource tags.')
param tags object = {}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// SLI 1 — Telemetry-injection parse-to-pipeline latency ≤ 5 s p95.
resource sliParseToPipeline 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-parse-to-pipeline-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT1H'
    autoMitigate: true
    description: 'plan.md SLI 1: parse-to-pipeline p95 ≤ 5 s. Fast-burn 4× → SEV-2.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customMetrics | where name == "simulation.parse_to_pipeline_ms" | summarize p95=percentile(value, 95)'
          timeAggregation: 'Average'
          operator: 'GreaterThan'
          threshold: 20000
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ actionGroupId ] }
  }
}

// SLI 2 — Risk-Assessment auto-fan-out latency ≤ 15 s p95 (FR-043).
resource sliRiskFanOut 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-risk-fanout-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT1H'
    autoMitigate: true
    description: 'plan.md SLI 2: risk-fan-out p95 ≤ 15 s over 200-sample window. Fast-burn 4× → SEV-2.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customMetrics | where name == "simulation.risk_fanout_ms" | summarize p95=percentile(value, 95)'
          timeAggregation: 'Average'
          operator: 'GreaterThan'
          threshold: 60000
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ actionGroupId ] }
  }
}

// SLI 3 — Cascade fan-out completion ≤ 30 s p95.
resource sliCascadeFanOut 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-cascade-fanout-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT1H'
    autoMitigate: true
    description: 'plan.md SLI 3 / FR-043: cascade-fanout p95 ≤ 30 s. Fast-burn 4× → SEV-2.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customMetrics | where name == "simulation.cascade_fanout_ms" | summarize p95=percentile(value, 95)'
          timeAggregation: 'Average'
          operator: 'GreaterThan'
          threshold: 120000
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ actionGroupId ] }
  }
}

// SLI 4 — Map-overlay update latency (≤ 15 s hazard / ≤ 10 s weather).
resource sliOverlayLatency 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-overlay-latency-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 3
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    autoMitigate: true
    description: 'plan.md SLI 4: overlay update p95 > 20 s → SEV-3.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customMetrics | where name in ("simulation.overlay_update_hazard_ms", "simulation.overlay_update_weather_ms") | summarize p95=percentile(value, 95)'
          timeAggregation: 'Average'
          operator: 'GreaterThan'
          threshold: 20000
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ actionGroupId ] }
  }
}

// SLI 5 — SC-006 zero-real-comms egress. Any single block-reason
// `simulation_tenant_egress_blocked` → SEV-0 immediate page.
resource sliEgressBlock 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-egress-block-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 0
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    autoMitigate: false
    description: 'spec.md SC-006: ANY simulation_tenant_egress_blocked → SEV-0 page. Runbook: docs/runbooks/sc006-egress-incident.md'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customEvents | where name == "audit.egress_blocked" or customDimensions["block_reason"] == "simulation_tenant_egress_blocked" | summarize count()'
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ pagerDutyActionGroupId, actionGroupId ] }
  }
}

output sliParseToPipelineId string = sliParseToPipeline.id
output sliRiskFanOutId string = sliRiskFanOut.id
output sliCascadeFanOutId string = sliCascadeFanOut.id
output sliOverlayLatencyId string = sliOverlayLatency.id
output sliEgressBlockId string = sliEgressBlock.id

// ---------------------------------------------------------------------------
// Cycle 2 / T-AA18 / A2-02 — staging-promotion gate alerts (Z6 + Z7).
//
// These alerts are INFORMATIONAL (severity 3 — warn-only Slack via the
// shared action group). The breach action is implemented by
// `tests/staging_gates.py::assert_sli_thresholds` (T-AA17): the
// the release-gate procedure refuses promotion when the 24 h
// trailing-window SLI either starves below the 30-sample CLT floor or
// breaches the threshold from `contracts/sli-thresholds.md` rows 6/7.
//
// NO PagerDuty receiver — SLI-4 / SLI-5 own the operational pages; Z6
// and Z7 are gate signals not run-time SEV-1/SEV-0 incidents.
// ---------------------------------------------------------------------------

resource sliZ6SubAgentLatency 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-z6-sub-agent-latency-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 3
    evaluationFrequency: 'PT15M'
    windowSize: 'P1D'
    autoMitigate: true
    description: 'Cycle 2 A2-02: P95 sub-agent reply latency over 24 h. Warn at 4 s (gpt-4o) / 1.5 s (gpt-4o-mini). Breach blocks staging promotion via tests/staging_gates.py.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customEvents | where timestamp > ago(24h) | where name == "sub_agent.invocation.complete" | extend latency_ms = todouble(customDimensions["latency_ms"]) | extend model_deployment = tostring(customDimensions["model_deployment"]) | summarize p95_latency_ms = percentile(latency_ms, 95), sample_count = count() by model_deployment | where (model_deployment == "gpt-4o" and p95_latency_ms > 4000) or (model_deployment == "gpt-4o-mini" and p95_latency_ms > 1500)'
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ actionGroupId ] }
  }
}

resource sliZ7MapOverlayDrift 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'sli-z7-map-overlay-drift-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 3
    evaluationFrequency: 'PT15M'
    windowSize: 'P1D'
    autoMitigate: true
    description: 'Cycle 2 A2-02: SSE map-overlay drift error budget over 24 h. Breach below 99.5 percent within 1500 ms blocks staging promotion via tests/staging_gates.py.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'customEvents | where timestamp > ago(24h) | where name == "sse.map_overlay.delivered" | extend delivery_ms = todouble(customDimensions["delivery_ms"]) | summarize delivered_within_budget = countif(delivery_ms <= 1500), total = count() | where total >= 30 | extend drift_budget_pct = 100.0 * todouble(delivered_within_budget) / total | where drift_budget_pct < 99.5'
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [ actionGroupId ] }
  }
}

output sliZ6SubAgentLatencyId string = sliZ6SubAgentLatency.id
output sliZ7MapOverlayDriftId string = sliZ7MapOverlayDrift.id
