// Spec 036 / F-A11 / T238 — Foundry RAG latency alerts (FR-RAG-OBS-03).
//
// Provisions:
//   1. Retrieval-only p95 alert — fires if p95 retrieval latency >500ms for >5 min.
//      (Pass 1 Q-P1-06 — degraded performance, NOT a hard failure.)
//   2. Foundry inference latency alert — separate metric, governed by SC-012.
//
// Both metrics ship via the OTel-to-App-Insights bridge (spec 014 FR-016).
// Direct App-Insights SDK calls are forbidden in production paths.

@description('Existing Application Insights resource name.')
param appInsightsName string

@description('Action group resource id to notify on alert.')
param actionGroupId string

@description('Tag map applied to alert resources.')
param tags object = {}

resource ai 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// 1) Retrieval-only p95 latency alert.
resource retrievalP95Alert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = {
  name: 'spec-036-retrieval-p95-degraded'
  location: ai.location
  tags: tags
  properties: {
    displayName: 'Spec 036 — Retrieval p95 latency >500ms (degraded)'
    description: 'Retrieval-only p95 latency exceeded 500ms for >5 min. Pass 1 Q-P1-06 — degraded, NOT hard failure.'
    severity: 3
    enabled: true
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    scopes: [ ai.id ]
    criteria: {
      allOf: [
        {
          query: 'customMetrics | where name == "retrieval_latency_ms" | summarize p95 = percentile(value, 95)'
          operator: 'GreaterThan'
          threshold: 500
          timeAggregation: 'Average'
          metricMeasureColumn: 'p95'
          dimensions: []
          failingPeriods: {
            numberOfEvaluationPeriods: 5
            minFailingPeriodsToAlert: 5
          }
        }
      ]
    }
    actions: {
      actionGroups: [ actionGroupId ]
    }
  }
}

// 2) Foundry inference latency — independent metric; SC-012 governs threshold.
resource foundryInferenceP95Alert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = {
  name: 'spec-036-foundry-inference-p95'
  location: ai.location
  tags: tags
  properties: {
    displayName: 'Spec 036 — Foundry inference p95 latency exceeded (SC-012)'
    description: 'Foundry inference p95 latency exceeded the SC-012 threshold for >5 min. End-to-end SLO; degrades both eval p95 and SC-012 acceptance.'
    severity: 3
    enabled: true
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    scopes: [ ai.id ]
    criteria: {
      allOf: [
        {
          query: 'customMetrics | where name == "foundry_inference_latency_ms" | summarize p95 = percentile(value, 95)'
          operator: 'GreaterThan'
          threshold: 3000
          timeAggregation: 'Average'
          metricMeasureColumn: 'p95'
          dimensions: []
          failingPeriods: {
            numberOfEvaluationPeriods: 5
            minFailingPeriodsToAlert: 5
          }
        }
      ]
    }
    actions: {
      actionGroups: [ actionGroupId ]
    }
  }
}

output retrievalAlertResourceId string = retrievalP95Alert.id
output foundryInferenceAlertResourceId string = foundryInferenceP95Alert.id
