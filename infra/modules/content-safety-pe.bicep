// ────────────────────────────────────────────────────────────────────────────────
// Azure AI Content Safety with Private Endpoint (spec-032 T405, FR-AI06).
//
// Wraps Microsoft.CognitiveServices/accounts kind=ContentSafety with PE wiring
// and managed identity. Disables public network access in production.
// ────────────────────────────────────────────────────────────────────────────────

@description('Content Safety account name')
param name string

@description('Location')
param location string

@description('SKU (S0 production)')
param skuName string = 'S0'

@description('Tags')
param tags object = {}

@description('Subnet resource ID for Private Endpoint (empty = no PE)')
param privateEndpointSubnetId string = ''

@description('Private DNS zone resource ID for privatelink.cognitiveservices.azure.com')
param privateDnsZoneId string = ''

@description('Disable public network access (must be true in production)')
param disablePublicNetworkAccess bool = true

resource cs 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: 'ContentSafety'
  sku: {
    name: skuName
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: disablePublicNetworkAccess ? 'Disabled' : 'Enabled'
    networkAcls: {
      defaultAction: disablePublicNetworkAccess ? 'Deny' : 'Allow'
      ipRules: []
      virtualNetworkRules: []
    }
    disableLocalAuth: true // Entra-only auth (FR-S03)
  }
}

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
          privateLinkServiceId: cs.id
          groupIds: [
            'account'
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
        name: 'privatelink-cognitiveservices'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

output contentSafetyId string = cs.id
output contentSafetyEndpoint string = cs.properties.endpoint
output principalId string = cs.identity.principalId
