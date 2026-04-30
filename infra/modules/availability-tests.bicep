// ────────────────────────────────────────────────────────────────────────────────
// Application Insights availability tests (synthetic monitoring)
// (spec-032 T507, FR-O10). Multi-step web tests across 5 APAC POPs.
// ────────────────────────────────────────────────────────────────────────────────

@description('Application Insights component name')
param appInsightsName string

@description('Location of the App Insights component')
param location string

@description('Public dashboard URL to probe')
param dashboardUrl string

@description('Public API health URL')
param apiHealthUrl string

@description('Tags')
param tags object = {}

@description('Test frequency in seconds (default 300 = every 5 min)')
param testFrequencySeconds int = 300

@description('Test timeout in seconds')
param testTimeoutSeconds int = 30

@description('Geo-distributed test locations')
param testLocations array = [
  { Id: 'apac-au-syd-edge' }     // Sydney, AU
  { Id: 'apac-jp-kaw-edge' }     // Kawaguchi, JP
  { Id: 'apac-sg-sin-azr' }      // Singapore
  { Id: 'apac-hk-hkn-azr' }      // Hong Kong
  { Id: 'us-ca-sjc-azr' }        // San Jose (5th location for redundancy)
]

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource availDashboard 'Microsoft.Insights/webtests@2022-06-15' = {
  name: 'avail-dashboard-${appInsightsName}'
  location: location
  tags: union(tags, {
    'hidden-link:${appInsights.id}': 'Resource'
  })
  kind: 'standard'
  properties: {
    SyntheticMonitorId: 'avail-dashboard-${appInsightsName}'
    Name: 'Disaster Response Dashboard availability'
    Description: 'Spec-032 FR-O10 must-land probe of public dashboard URL.'
    Enabled: true
    Frequency: testFrequencySeconds
    Timeout: testTimeoutSeconds
    Kind: 'standard'
    RetryEnabled: true
    Locations: testLocations
    Request: {
      RequestUrl: dashboardUrl
      HttpVerb: 'GET'
      ParseDependentRequests: false
      FollowRedirects: true
    }
    ValidationRules: {
      ExpectedHttpStatusCode: 200
      SSLCheck: true
      SSLCertRemainingLifetimeCheck: 30
    }
  }
}

resource availApi 'Microsoft.Insights/webtests@2022-06-15' = {
  name: 'avail-api-${appInsightsName}'
  location: location
  tags: union(tags, {
    'hidden-link:${appInsights.id}': 'Resource'
  })
  kind: 'standard'
  properties: {
    SyntheticMonitorId: 'avail-api-${appInsightsName}'
    Name: 'Disaster Response API /api/health availability'
    Description: 'Spec-032 FR-O10 must-land probe of API health endpoint.'
    Enabled: true
    Frequency: testFrequencySeconds
    Timeout: testTimeoutSeconds
    Kind: 'standard'
    RetryEnabled: true
    Locations: testLocations
    Request: {
      RequestUrl: apiHealthUrl
      HttpVerb: 'GET'
      ParseDependentRequests: false
      FollowRedirects: false
    }
    ValidationRules: {
      ExpectedHttpStatusCode: 200
      SSLCheck: true
    }
  }
}

output dashboardWebTestId string = availDashboard.id
output apiWebTestId string = availApi.id
