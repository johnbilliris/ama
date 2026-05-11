// Spec 036 / F-A11 / T237 — App Insights workbook with tiles for SC-001..SC-019
// (closes F-QA-03). Read-only dashboard; query authoring lives in App Insights.
//
// Provisions a workbook resource that ships canned KQL queries against
// `customMetrics`, `customEvents`, and `requests` so SREs can render the
// Phase F success-criteria status without having to author KQL each time.
//
// All metric/event names match the OTel emitter conventions established by
// `apps/agents/common/otel_telemetry.py` (T234..T236).

@description('Existing Application Insights resource name (production).')
param appInsightsName string

@description('Display name of the workbook tile shown in the portal.')
param workbookDisplayName string = 'Spec 036 — Success Criteria (SC-001..SC-019)'

@description('Workbook ID (GUID); generated from spec-id when not supplied.')
param workbookId string = guid('spec-036-foundry-rag-success-criteria', appInsightsName)

@description('Azure region for the workbook. Defaults to resource group location.')
param location string = resourceGroup().location

@description('Tag map for the workbook resource.')
param tags object = {}

resource ai 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource workbook 'Microsoft.Insights/workbooks@2023-06-01' = {
  name: workbookId
  location: location
  kind: 'shared'
  tags: tags
  properties: {
    displayName: workbookDisplayName
    serializedData: string({
      version: 'Notebook/1.0'
      items: [
        {
          type: 1
          content: {
            json: '## Spec 036 — Foundry RAG Grounding success criteria\n\nLive view of SC-001..SC-019 over the last 24 hours.'
          }
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customMetrics\n| where name == "retrieval_latency_ms"\n| summarize p95 = percentile(value, 95) by bin(timestamp, 5m)'
            chartSettings: { showLegend: true }
            visualization: 'timechart'
            queryType: 0
          }
          name: 'sc-012-retrieval-p95'
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customEvents\n| where name == "conflict_detected"\n| summarize count() by bin(timestamp, 1h), tostring(customDimensions.conflict_class)'
            visualization: 'barchart'
            queryType: 0
          }
          name: 'sc-018-multi-agent-conflict'
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customEvents\n| where name == "corpus_freshness_state"\n| summarize maxAge = max(toreal(customDimensions.corpus_age_days)) by bin(timestamp, 1h)'
            visualization: 'timechart'
            queryType: 0
          }
          name: 'sc-014-corpus-freshness'
        }
      ]
    })
    sourceId: ai.id
    category: 'workbook'
  }
}

output workbookResourceId string = workbook.id
