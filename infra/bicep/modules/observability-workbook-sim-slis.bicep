// Cycle 2 / T-AA18 / A2-02 — Azure Monitor workbook: simulation SLIs
// dashboard with the "SC-013 release gate" row group containing
// Z6 + Z7. The workbook is a serialised JSON template (Microsoft.Insights/
// workbooks). Operators access it via the Azure portal or pinned to a
// shared dashboard.
//
// Aligns with sli-thresholds.md §7.4 dashboard requirement.

@description('Application Insights component name (existing).')
param appInsightsName string

@description('Azure region — defaults to australiaeast per ADR-036-002.')
param location string = 'australiaeast'

@description('Resource tags applied to the workbook.')
param tags object = {}

@description('Stable workbook display name — referenced from runbooks.')
param workbookDisplayName string = 'Simulation SLIs (spec-036)'

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// Single deterministic GUID per Application Insights component so
// re-deployment is idempotent. The 'sim-slis' literal is a stable salt
// keyed off the workbook's logical identity.
var workbookId = guid(resourceGroup().id, 'sim-slis', appInsightsName)

resource simSlisWorkbook 'Microsoft.Insights/workbooks@2023-06-01' = {
  name: workbookId
  location: location
  tags: tags
  kind: 'shared'
  properties: {
    displayName: workbookDisplayName
    sourceId: appInsights.id
    category: 'workbook'
    serializedData: string({
      version: 'Notebook/1.0'
      items: [
        {
          type: 1
          content: {
            json: '## Simulation SLIs — spec-036 Cycle 2\\n\\n### SC-013 release gate\\n\\nThis row group surfaces SLI-Z6 + SLI-Z7. Both gates must pass over a trailing 24 h window with sample_count ≥ 30 (CLT floor) for a release to proceed.'
          }
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customEvents | where timestamp > ago(24h) | where name == "sub_agent.invocation.complete" | extend latency_ms = todouble(customDimensions["latency_ms"]) | extend model_deployment = tostring(customDimensions["model_deployment"]) | summarize p95_latency_ms = percentile(latency_ms, 95), sample_count = count() by model_deployment | project model_deployment, p95_latency_ms, sample_count'
            size: 0
            title: 'SLI-Z6 — P95 sub-agent reply latency (per model)'
            queryType: 0
            resourceType: 'microsoft.insights/components'
            visualization: 'table'
          }
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customEvents | where timestamp > ago(24h) | where name == "sse.map_overlay.delivered" | extend delivery_ms = todouble(customDimensions["delivery_ms"]) | summarize delivered_within_budget = countif(delivery_ms <= 1500), total = count() | extend drift_budget_pct = 100.0 * todouble(delivered_within_budget) / total | extend sample_count = total | project drift_budget_pct, sample_count'
            size: 0
            title: 'SLI-Z7 — Map-overlay drift error budget'
            queryType: 0
            resourceType: 'microsoft.insights/components'
            visualization: 'table'
          }
        }
      ]
    })
  }
}

output workbookId string = simSlisWorkbook.id
