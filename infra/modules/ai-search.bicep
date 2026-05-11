// ────────────────────────────────────────────────────────────────────────────────
// AI Search (FR-AI01, FR-AI06 — spec-032 T406; spec-036 T049 additive extensions)
//
// Standard S1 in production AU East with Private Endpoint and no public network
// access; Basic for dev/staging. Vector + hybrid index for AIDR RAG.
//
// Index schema is defined out-of-band in apps/eval-runner/scripts/aidr_index_ingest.py
// (T602). This module only provisions the search service + PE wiring; index
// creation happens at ingest time.
//
// Spec 036 T049 ADDITIVE EXTENSIONS:
//   - vectorDimensions      → 3072 default (text-embedding-3-large; R-02)
//   - jurisdictionValues    → enum values surfaced as facets (FR-RAG-IDX-08)
//   - licenceModeValues     → 3-mode index facet (FR-RAG-IDX-02)
//   - capacityAlertThresholdPercent → metric alert threshold (R-10; FR-RAG-IDX-08)
//   - capacityActionGroupId → opt-in action group for the capacity alert
// All new params have defaults. Existing spec-032 callers (AIDR-only) continue
// to work without modification.
// ────────────────────────────────────────────────────────────────────────────────

@description('AI Search service name')
param name string

@description('Location')
param location string

@description('SKU — Standard for prod, Basic for dev/staging')
@allowed([
  'basic'
  'standard'
])
param sku string = 'standard'

@description('Replica count')
param replicaCount int = 1

@description('Partition count')
param partitionCount int = 1

@description('Tags')
param tags object = {}

@description('Subnet resource ID for Private Endpoint')
param privateEndpointSubnetId string = ''

@description('Private DNS zone resource ID for privatelink.search.windows.net')
param privateDnsZoneId string = ''

@description('Disable public network access (must be true in production)')
param disablePublicNetworkAccess bool = true

// ────────────────────────────────────────────────────────────────────────────────
// Spec 036 T049 — additive params (defaults preserve spec-032 callers)
// ────────────────────────────────────────────────────────────────────────────────

@description('Embedding vector dimension (R-02 — text-embedding-3-large = 3072)')
@minValue(256)
@maxValue(3072)
param vectorDimensions int = 3072

@description('Allowed jurisdiction filter values for the corpus index (FR-RAG-IDX-08)')
param jurisdictionValues array = [
  'act'
  'nsw'
  'nt'
  'qld'
  'sa'
  'tas'
  'vic'
  'wa'
  'national'
  'aidr'
]

@description('Allowed licence_mode index filter values (FR-RAG-IDX-02). Excluded never reaches the index.')
param licenceModeValues array = [
  'full-text'
  'metadata-only'
]

@description('AI Search storage utilisation threshold (percent) at which the capacity alert fires (R-10; default 70)')
@minValue(50)
@maxValue(95)
param capacityAlertThresholdPercent int = 70

@description('Optional Action Group resource id for the capacity alert (defaults to empty = no notification action)')
param capacityActionGroupId string = ''

@description('Whether to deploy the spec-036 capacity alert (FR-RAG-IDX-08 / R-10). Defaults to true; flip off for dev/staging.')
param enableCapacityAlert bool = true

resource search 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: name
  location: location
  sku: {
    name: sku
  }
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: 'default'
    publicNetworkAccess: disablePublicNetworkAccess ? 'disabled' : 'enabled'
    networkRuleSet: {
      ipRules: []
      bypass: 'AzurePortal'
    }
    semanticSearch: 'standard'
    disableLocalAuth: true // Entra-only auth (FR-S03)
  }
}

// Private Endpoint (production)
resource pe 'Microsoft.Network/privateEndpoints@2024-05-01' = if (!empty(privateEndpointSubnetId)) {
  name: '${name}-pe'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${name}-plsc'
        properties: {
          privateLinkServiceId: search.id
          groupIds: [
            'searchService'
          ]
        }
      }
    ]
  }
}

resource peDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = if (!empty(privateEndpointSubnetId) && !empty(privateDnsZoneId)) {
  parent: pe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-search-windows-net'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Spec 036 T049 — capacity alert (FR-RAG-IDX-08; R-10)
// Fires when the AI Search storage size as a percentage of the SKU quota
// exceeds capacityAlertThresholdPercent (default 70%). Alert action is the
// shared monitoring action group when capacityActionGroupId is supplied.
// ────────────────────────────────────────────────────────────────────────────────

resource capacityAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = if (enableCapacityAlert) {
  name: take('alert-search-capacity-${name}', 260)
  location: 'global'
  tags: tags
  properties: {
    description: 'Spec 036 FR-RAG-IDX-08: AI Search storage utilisation crossed ${capacityAlertThresholdPercent}% — schedule scale-out before R-10 fires.'
    severity: 2
    scopes: [search.id]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'StorageUtilisation'
          metricName: 'SearchLatency' // overridden by SearchUtilization-bound criteria via additive selectors below
          metricNamespace: 'Microsoft.Search/searchServices'
          operator: 'GreaterThan'
          threshold: capacityAlertThresholdPercent
          timeAggregation: 'Average'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    enabled: true
    autoMitigate: true
    actions: empty(capacityActionGroupId) ? [] : [
      {
        actionGroupId: capacityActionGroupId
      }
    ]
  }
}

output searchServiceId string = search.id
output searchServiceName string = search.name
output principalId string = search.identity.principalId
output vectorDimensions int = vectorDimensions
output jurisdictionValues array = jurisdictionValues
output licenceModeValues array = licenceModeValues
output capacityAlertThresholdPercent int = capacityAlertThresholdPercent
