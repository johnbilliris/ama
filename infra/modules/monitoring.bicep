// Monitoring infrastructure for the Autonomous Disaster Response Coordination Hub
// Deploys: Log Analytics workspace, Application Insights, alert rules, and action group

@description('Location for all monitoring resources')
param location string

@description('Environment name for resource naming')
param envPrefix string

@description('Email recipient for alert notifications')
param actionGroupEmail string = 'ops@example.com'

@description('Webhook endpoint for alert notifications')
param actionGroupWebhook string = 'https://example.com/alerts'

@description('Tags applied to all resources')
param tags object

// ── Log Analytics workspace ──

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: take('log-${envPrefix}', 63)
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 90
    features: { enableLogAccessUsingOnlyResourcePermissions: true }
  }
}

// ── Application Insights ──

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: take('appi-${envPrefix}', 255)
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    RetentionInDays: 90
    IngestionMode: 'LogAnalytics'
    DisableLocalAuth: true
  }
}

// ── Action Group ──

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: take('ag-${envPrefix}', 260)
  location: 'global'
  tags: tags
  properties: {
    enabled: true
    groupShortName: take('drh${envPrefix}', 12)
    emailReceivers: [
      {
        name: 'OperationsEmail'
        emailAddress: actionGroupEmail
        useCommonAlertSchema: true
      }
    ]
    webhookReceivers: [
      {
        name: 'OperationsWebhook'
        serviceUri: actionGroupWebhook
        useCommonAlertSchema: true
      }
    ]
  }
}

// ── Alert: high error rate ──

resource highErrorRateAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: take('alert-errors-${envPrefix}', 260)
  location: 'global'
  tags: tags
  properties: {
    severity: 1
    scopes: [appInsights.id]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighServerErrors'
          metricName: 'requests/failed'
          metricNamespace: 'microsoft.insights/components'
          operator: 'GreaterThan'
          threshold: 10
          timeAggregation: 'Count'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    enabled: true
    autoMitigate: true
    actions: [{ actionGroupId: actionGroup.id }]
  }
}

// ── Alert: API latency p99 ──

resource latencyAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: take('alert-latency-${envPrefix}', 260)
  location: 'global'
  tags: tags
  properties: {
    severity: 2
    scopes: [appInsights.id]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighLatency'
          metricName: 'requests/duration'
          metricNamespace: 'microsoft.insights/components'
          operator: 'GreaterThan'
          threshold: 5000
          timeAggregation: 'Maximum'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    enabled: true
    autoMitigate: true
    actions: [{ actionGroupId: actionGroup.id }]
  }
}

// ── Alert: simulation tenant high error rate (filtered by tenant_id custom dimension) ──

resource simulationErrorAlert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = {
  name: take('alert-sim-errors-${envPrefix}', 260)
  location: location
  tags: tags
  properties: {
    displayName: 'Simulation Tenant Errors'
    description: 'Fires when a simulation tenant exceeds error threshold; filtered by tenant_id custom dimension'
    severity: 2
    enabled: true
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    scopes: [appInsights.id]
    criteria: {
      allOf: [
        {
          query: 'requests | where customDimensions.tenant_id startswith "sim-" | where success == false | summarize FailedCount = count() by tostring(customDimensions.tenant_id) | where FailedCount > 20'
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          dimensions: [
            { name: 'customDimensions.tenant_id', operator: 'Include', values: ['*'] }
          ]
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [actionGroup.id] }
  }
}

// ── Outputs ──

output logAnalyticsId string = logAnalytics.id
output logAnalyticsCustomerId string = logAnalytics.properties.customerId
output appInsightsId string = appInsights.id
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output actionGroupId string = actionGroup.id
