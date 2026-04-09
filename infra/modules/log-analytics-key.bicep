// Helper module to retrieve Log Analytics shared key
// Required because listKeys() cannot reference module outputs directly in the parent template

param logAnalyticsId string

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: last(split(logAnalyticsId, '/'))
}

@secure()
output sharedKey string = logAnalytics.listKeys().primarySharedKey
