// Azure Maps account for the Disaster Mapper UI
// Deploys a Gen2 Azure Maps account locked to Australia East
// with local auth disabled (Entra-only access)

@description('Location for the Azure Maps account — must be Australia East for data sovereignty')
@allowed([
  'australiaeast'
])
param location string

@description('Environment name for resource naming')
param envPrefix string

@description('Tags applied to the resource')
param tags object

@description('Allowed CORS origins for the web frontend')
param corsAllowedOrigins array = []

// ── Azure Maps account ──

resource azureMaps 'Microsoft.Maps/accounts@2024-07-01-preview' = {
  name: take('maps-${envPrefix}', 98)
  location: location
  tags: tags
  sku: {
    name: 'G2'
  }
  kind: 'Gen2'
  properties: {
    disableLocalAuth: true
    cors: {
      corsRules: [for origin in corsAllowedOrigins: {
        allowedOrigins: [origin]
      }]
    }
  }
}

// ── Outputs ──

output azureMapsName string = azureMaps.name
output azureMapsId string = azureMaps.id
