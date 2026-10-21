@description('Existing Application Insights component name for evacuation telemetry queries.')
param appInsightsName string

@description('Existing operations action group resource ID invoked by evacuation alerts.')
param actionGroupResourceId string

@description('Deployment environment used in alert resource names.')
@minLength(1)
@maxLength(64)
param environmentName string

@description('Azure region matching the Application Insights component and its Australian data boundary.')
@allowed([
  'australiaeast'
])
param location string = 'australiaeast'

@description('Tags applied to every evacuation alert rule.')
param tags object

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

var alertRules = [
  {
    name: 'alert-evac-plan-sla-warning'
    displayName: 'Evacuation plan generation SLA warning'
    description: 'Plan-generation p95 exceeded 30 seconds over five minutes.'
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    query: 'customMetrics | where name == "evacuation.plan_generation_latency" | summarize AggregatedValue = percentile(todouble(value), 95)'
    threshold: 30000
  }
  {
    name: 'alert-evac-plan-sla-critical'
    displayName: 'Evacuation plan generation sustained SLA breach'
    description: 'Plan-generation p95 exceeded 30 seconds over fifteen minutes.'
    severity: 1
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    query: 'customMetrics | where name == "evacuation.plan_generation_latency" | summarize AggregatedValue = percentile(todouble(value), 95)'
    threshold: 30000
  }
  {
    name: 'alert-evac-replan-sla'
    displayName: 'Evacuation replan SLA warning'
    description: 'Replan p95 exceeded 15 seconds over five minutes.'
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    query: 'customMetrics | where name == "evacuation.replan_latency" | summarize AggregatedValue = percentile(todouble(value), 95)'
    threshold: 15000
  }
  {
    name: 'alert-evac-road-data-stale'
    displayName: 'Evacuation road data stale'
    description: 'The road-network source remained stale for fifteen minutes.'
    severity: 1
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    query: 'customMetrics | where name == "evacuation.road_data_stale" | summarize AggregatedValue = min(todouble(value))'
    threshold: 0
  }
  {
    name: 'alert-evac-llm-unavailable'
    displayName: 'Evacuation LLM fallback rate warning'
    description: 'More than five deterministic fallback activations occurred in five minutes.'
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    query: 'customMetrics | where name == "evacuation.fallback_mode_activations" | summarize AggregatedValue = sum(todouble(value))'
    threshold: 5
  }
  {
    name: 'alert-evac-audit-degradation'
    displayName: 'Evacuation audit storage degraded'
    description: 'The audit writer used memory/WAL or file-spill storage during the five-minute window.'
    severity: 1
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    query: 'customMetrics | where name == "evacuation.audit_tier" | summarize AggregatedValue = max(todouble(value))'
    threshold: 1
  }
  {
    name: 'alert-evac-audit-buffer-capacity'
    displayName: 'Evacuation audit buffer near capacity'
    description: 'The in-memory audit buffer exceeded 8000 records.'
    severity: 1
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    query: 'customMetrics | where name == "evacuation.audit_buffer_depth" | summarize AggregatedValue = max(todouble(value))'
    threshold: 8000
  }
  {
    name: 'alert-evac-shelter-rate'
    displayName: 'Evacuation shelter-in-place rate warning'
    description: 'More than five shelter-in-place recommendations occurred in thirty minutes.'
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT30M'
    query: 'customMetrics | where name == "evacuation.shelter_in_place_count" | summarize AggregatedValue = sum(todouble(value))'
    threshold: 5
  }
  {
    name: 'alert-evac-emergency-escalation'
    displayName: 'Evacuation emergency escalation'
    description: 'At least one immediate-threat emergency escalation occurred.'
    severity: 1
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    query: 'customMetrics | where name == "evacuation.emergency_escalation_count" | summarize AggregatedValue = sum(todouble(value))'
    threshold: 0
  }
  {
    name: 'alert-evac-no-plans'
    displayName: 'Evacuation no plans generated'
    description: 'Handoffs were received but the latest active-plan count remained zero for ten minutes.'
    severity: 1
    evaluationFrequency: 'PT5M'
    windowSize: 'PT10M'
    query: 'let Handoffs = toscalar(customMetrics | where name == "evacuation.handoff_intake_count" | summarize sum(todouble(value))); let ActivePlans = toscalar(customMetrics | where name == "evacuation.active_plans_gauge" | summarize arg_max(timestamp, value) | project todouble(value)); print AggregatedValue = iff(coalesce(Handoffs, 0.0) > 0 and coalesce(ActivePlans, 0.0) == 0, 1.0, 0.0)'
    threshold: 0
  }
  {
    name: 'alert-evac-congestion-risk'
    displayName: 'Evacuation high congestion risk'
    description: 'More than half of generated routes were congestion-risk routes in five minutes.'
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    query: 'customMetrics | where name in ("evacuation.congestion_risk_routes", "evacuation.routes_per_plan") | summarize RiskRoutes = sumif(todouble(value), name == "evacuation.congestion_risk_routes"), TotalRoutes = sumif(todouble(value), name == "evacuation.routes_per_plan") | extend AggregatedValue = iff(TotalRoutes > 0, 100.0 * RiskRoutes / TotalRoutes, 0.0) | project AggregatedValue'
    threshold: 50
  }
  {
    name: 'alert-evac-capacity-limit'
    displayName: 'Evacuation active-plan capacity warning'
    description: 'The active-plan count exceeded 40 and approached the 50-plan capacity limit.'
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    query: 'customMetrics | where name == "evacuation.active_plans_gauge" | summarize AggregatedValue = max(todouble(value))'
    threshold: 40
  }
]

@batchSize(3)
module evacuationAlertRules 'br/public:avm/res/insights/scheduled-query-rule:0.6.0' = [for alertRule in alertRules: {
  params: {
    name: take('${alertRule.name}-${environmentName}', 260)
    alertDisplayName: alertRule.displayName
    alertDescription: alertRule.description
    location: location
    tags: tags
    scopes: [
      appInsights.id
    ]
    evaluationFrequency: alertRule.evaluationFrequency
    windowSize: alertRule.windowSize
    severity: alertRule.severity
    autoMitigate: true
    skipQueryValidation: false
    actions: {
      actionGroupResourceIds: [
        actionGroupResourceId
      ]
      customProperties: {
        service: 'evacuation-agent'
        dataResidency: location
      }
    }
    criterias: {
      allOf: [
        {
          query: alertRule.query
          metricMeasureColumn: 'AggregatedValue'
          timeAggregation: 'Average'
          operator: 'GreaterThan'
          threshold: alertRule.threshold
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
  }
}]

@description('Resource IDs of all twelve evacuation scheduled-query alert rules.')
output resourceIds array = [for (alertRule, index) in alertRules: evacuationAlertRules[index].outputs.resourceId]

@description('Resource names of all twelve evacuation scheduled-query alert rules.')
output resourceNames array = [for (alertRule, index) in alertRules: evacuationAlertRules[index].outputs.name]
