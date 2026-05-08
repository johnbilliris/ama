// Spec 036 — Application Insights alerts for the Foundry RAG cutover
// (T030, FR-RAG-FM-06, FR-RAG-CV-03, FR-RAG-OB-04). Live deployment is
// deferred (config-as-code: this Bicep is wired by infra/main.bicep at the
// final cutover step T140).
//
// Custom table: ``customEvents`` writes from the spec-036 audit middleware
// emit ``FoundryRAGCutover`` rows. Each row carries:
//   - ``customDimensions.agent_name``
//   - ``customDimensions.gateway_decision`` (``allow|deny|redact``)
//   - ``customDimensions.citation_count``
//   - ``customDimensions.deployment_region``
//   - ``customDimensions.legacy_or_foundry`` (``legacy|foundry``)
//   - ``customDimensions.decision_equivalence`` (per canary slice)
//
// Three alerts:
//   1. Gateway-deny — any gateway DENY during cutover is high-severity
//      (privacy-impact event); life-safety paths must never be blocked
//      silently.
//   2. Citation drop — grounded calls that emit zero citations breach
//      Constitution §I.
//   3. Equivalence regression — per-agent decision_equivalence < 0.95
//      over a rolling 30-minute window stops the canary (FR-RAG-FM-06).

@description('Existing Application Insights component name.')
param appInsightsName string

@description('Azure region (AU-only — FR-RAG-CV-04).')
@allowed([
  'australiaeast'
  'australiasoutheast'
])
param location string = 'australiaeast'

@description('Action group resource id to notify on alert.')
param actionGroupId string

@description('Optional resource tags.')
param tags object = {}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// ────────────────────────────────────────────────────────────────────────── //
// Alert 1: gateway DENY rate > 0 over 5 minutes.
// ────────────────────────────────────────────────────────────────────────── //
resource gatewayDenyAlert 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'foundry-rag-gateway-deny-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 1
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    autoMitigate: false
    description: 'Spec 036 FR-RAG-CV-03 — data-minimisation gateway denied a Foundry call. Investigate immediately; PSPF-marked or sensitive-operational content was attempted.'
    scopes: [appInsights.id]
    criteria: {
      allOf: [
        {
          query: '''customEvents
| where name == "FoundryRAGCutover"
| where tostring(customDimensions["gateway_decision"]) == "deny"
| summarize denied = count() by bin(timestamp, 5m), agent_name = tostring(customDimensions["agent_name"])'''
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
      actionGroups: [actionGroupId]
    }
  }
}

// ────────────────────────────────────────────────────────────────────────── //
// Alert 2: grounded LLM calls with zero citations (Constitution §I — every
// grounded LLM call MUST carry citations).
// ────────────────────────────────────────────────────────────────────────── //
resource citationDropAlert 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'foundry-rag-citation-drop-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 1
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    autoMitigate: false
    description: 'Spec 036 Constitution §I — a grounded LLM call returned zero citations. Life-safety guarantee violated; investigate within SLA.'
    scopes: [appInsights.id]
    criteria: {
      allOf: [
        {
          query: '''customEvents
| where name == "FoundryRAGCutover"
| where tostring(customDimensions["legacy_or_foundry"]) == "foundry"
| where toint(customDimensions["citation_count"]) == 0
| summarize zero_cite = count() by bin(timestamp, 15m), agent_name = tostring(customDimensions["agent_name"])'''
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
      actionGroups: [actionGroupId]
    }
  }
}

// ────────────────────────────────────────────────────────────────────────── //
// Alert 3: per-agent decision_equivalence < 0.95 over rolling 30 minutes
// (FR-RAG-FM-06 — per-agent canary stop signal).
// ────────────────────────────────────────────────────────────────────────── //
resource equivalenceRegressionAlert 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'foundry-rag-equivalence-regression-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 2
    evaluationFrequency: 'PT15M'
    windowSize: 'PT30M'
    autoMitigate: true
    description: 'Spec 036 FR-RAG-FM-06 — per-agent decision-equivalence dropped below 0.95 over 30 minutes. Pause/rollback the canary per cutover runbook.'
    scopes: [appInsights.id]
    criteria: {
      allOf: [
        {
          query: '''customEvents
| where name == "FoundryRAGCutover"
| extend agent_name = tostring(customDimensions["agent_name"])
| extend decision_eq = todouble(customDimensions["decision_equivalence"])
| where isnotnull(decision_eq)
| summarize avg_eq = avg(decision_eq), n = count() by bin(timestamp, 30m), agent_name
| where n >= 20 and avg_eq < 0.95'''
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
      actionGroups: [actionGroupId]
    }
  }
}

// ────────────────────────────────────────────────────────────────────────── //
// Alert 4: offline-cache TTL exhaustion (T132 / FR-RAG-LS-02 / R-07).
// Field-Coordinator offline cache has a 14-day TTL with 11-day stale warning.
// Any agent reporting `offline_cache_ttl_days_remaining < 3` is approaching
// the hard-fail-closed window. Page the SRE on call so refresh can be
// sequenced before the 14-day expiry.
// ────────────────────────────────────────────────────────────────────────── //
resource offlineCacheTtlAlert 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'foundry-rag-offline-cache-ttl-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 2
    evaluationFrequency: 'PT15M'
    windowSize: 'PT15M'
    autoMitigate: true
    description: 'Spec 036 FR-RAG-LS-02 / R-07 - offline cache TTL <= 3 days remaining. Field Coordinator must re-sync before 14-day fail-closed expiry.'
    scopes: [appInsights.id]
    criteria: {
      allOf: [
        {
          query: '''customMetrics
| where name == "offline_cache_ttl_days_remaining"
| extend tenant_id = tostring(customDimensions["tenant_id"])
| extend region = tostring(customDimensions["region"])
| summarize min_days = min(value) by bin(timestamp, 15m), tenant_id, region
| where min_days < 3'''
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
      actionGroups: [actionGroupId]
    }
  }
}

output gatewayDenyAlertId string = gatewayDenyAlert.id
output citationDropAlertId string = citationDropAlert.id
output equivalenceRegressionAlertId string = equivalenceRegressionAlert.id
output offlineCacheTtlAlertId string = offlineCacheTtlAlert.id
