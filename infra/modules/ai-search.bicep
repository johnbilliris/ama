// ────────────────────────────────────────────────────────────────────────────────
// AI Search (FR-AI01, FR-AI06 — spec-032 T406)
//
// Standard S1 in production AU East with Private Endpoint and no public network
// access; Basic for dev/staging. Vector + hybrid index for AIDR RAG.
//
// Index schema is defined out-of-band in apps/eval-runner/scripts/aidr_index_ingest.py
// (T602). This module only provisions the search service + PE wiring; index
// creation happens at ingest time.
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

output searchServiceId string = search.id
output searchServiceName string = search.name
output principalId string = search.identity.principalId
