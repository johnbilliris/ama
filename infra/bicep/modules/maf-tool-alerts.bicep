// Spec 033 — Application Insights alert: tool.outcome=version_mismatch (T068, FR-019a)

@description('Existing Application Insights component name.')
param appInsightsName string

@description('Azure region (must match the App Insights component).')
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

resource versionMismatchAlert 'Microsoft.Insights/scheduledQueryRules@2024-01-01-preview' = {
  name: 'maf-tool-version-mismatch-${appInsightsName}'
  location: location
  tags: tags
  properties: {
    enabled: true
    severity: 1
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    autoMitigate: true
    description: 'FR-019a: an MCP tool advertised a major version that did not match the agent allow-list pin.'
    scopes: [ appInsights.id ]
    criteria: {
      allOf: [
        {
          query: 'traces | where customDimensions["error_code"] == "tool_version_mismatch" | summarize count()'
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

output alertId string = versionMismatchAlert.id
