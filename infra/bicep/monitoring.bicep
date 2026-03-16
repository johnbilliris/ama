// Monitoring infrastructure for the Autonomous Disaster Response Coordination Hub
// Deploys: Log Analytics workspace, Application Insights, alert rules, and diagnostic settings

@description('Location for all monitoring resources')
param location string = 'australiaeast'

@description('Environment prefix')
param envPrefix string = 'drh'

@description('Email recipient for alert notifications')
param actionGroupEmail string = 'ops@example.com'

@description('Webhook endpoint for alert notifications')
param actionGroupWebhook string = 'https://example.com/alerts'

@description('Tags applied to all resources')
param tags object = {
  project: 'disaster-response-hub'
  environment: 'production'
}

// ── Log Analytics workspace ──

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${envPrefix}-log-analytics'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 90
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// ── Application Insights ──

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${envPrefix}-app-insights'
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

resource incidentActionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: '${envPrefix}-ops-ag'
  location: 'global'
  tags: tags
  properties: {
    enabled: true
    groupShortName: 'drhops'
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

// ── Alert rule: high error rate ──

resource highErrorRateAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${envPrefix}-high-error-rate'
  location: 'global'
  tags: tags
  properties: {
    severity: 1
    scopes: [
      appInsights.id
    ]
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
    actions: [
      {
        actionGroupId: incidentActionGroup.id
      }
    ]
  }
}

// ── Alert rule: API latency p99 ──

resource latencyAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${envPrefix}-api-latency-p99'
  location: 'global'
  tags: tags
  properties: {
    severity: 2
    scopes: [
      appInsights.id
    ]
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
    actions: [
      {
        actionGroupId: incidentActionGroup.id
      }
    ]
  }
}

// ── Outputs ──

output logAnalyticsId string = logAnalytics.id
output appInsightsId string = appInsights.id
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output actionGroupId string = incidentActionGroup.id
