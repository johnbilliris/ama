// spec-038 T-AA016 — App Insights workbook for Help SLIs.
//
// Charts (per SC-002, SC-003, SC-007, SC-012, FR-023b):
//   - Chat first-byte latency p95 (SC-007)
//   - Refusal rate (FR-013)
//   - Fabrication-audit hit count (SC-003)
//   - Snapshot publish duration (FR-011c)
//   - Snapshot rollback duration (FR-011c)
//   - Screenshot staleness backlog age (SC-012)
//   - Support-handoff acknowledgement latency (FR-023b)

targetScope = 'resourceGroup'

@description('Existing Application Insights resource name.')
param appInsightsName string

@description('Workbook display name.')
param workbookName string = 'help-slis'

@description('Tags applied to the workbook.')
param tags object = {}

resource ai 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource workbook 'Microsoft.Insights/workbooks@2023-06-01' = {
  name: guid(resourceGroup().id, 'help-slis', appInsightsName)
  location: resourceGroup().location
  kind: 'shared'
  tags: tags
  properties: {
    displayName: workbookName
    serializedData: string({
      version: 'Notebook/1.0'
      items: [
        {
          type: 1
          content: { json: '## spec-038 Help SLIs\n\nSee `docs/runbooks/help/on-call.md` for thresholds + alerts.' }
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customMetrics | where name == "help.chat.first_byte_ms" | summarize percentile(value, 95) by bin(timestamp, 5m)'
            size: 0
            title: 'Chat first-byte p95 (ms) — SC-007'
            timeContext: { durationMs: 86400000 }
          }
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customEvents | where name == "audit.chat_refusal" | summarize count() by bin(timestamp, 15m), tostring(customDimensions.refusal_reason)'
            size: 0
            title: 'Chat refusal rate (FR-013)'
            timeContext: { durationMs: 86400000 }
          }
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customEvents | where name == "audit.fabrication_audit_hit" | summarize count() by bin(timestamp, 1d)'
            size: 0
            title: 'Fabrication-audit hits (SC-003)'
          }
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customMetrics | where name == "help.snapshot.publish_duration_ms" | summarize avg(value), max(value) by bin(timestamp, 1d)'
            size: 0
            title: 'Snapshot publish duration (FR-011c)'
          }
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customMetrics | where name == "help.snapshot.rollback_duration_ms" | summarize max(value) by bin(timestamp, 1d)'
            size: 0
            title: 'Snapshot rollback duration (FR-011c, R6)'
          }
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customMetrics | where name == "help.staleness.backlog_age_days" | summarize max(value) by bin(timestamp, 1d)'
            size: 0
            title: 'Screenshot staleness backlog age (SC-012)'
          }
        }
        {
          type: 3
          content: {
            version: 'KqlItem/1.0'
            query: 'customMetrics | where name == "help.support_handoff.ack_latency_s" | summarize percentile(value, 95) by bin(timestamp, 1h)'
            size: 0
            title: 'Support-handoff ack latency p95 (FR-023b)'
          }
        }
      ]
    })
    sourceId: ai.id
    category: 'workbook'
  }
}

output workbookId string = workbook.id
