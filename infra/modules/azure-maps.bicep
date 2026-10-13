// Azure Maps account for the Disaster Mapper UI
// Deploys a Gen2 Azure Maps account locked to Australia East.
// Local (subscription-key) auth is allowed in dev; staging/prod require Entra ID only.

@description('Location for the Azure Maps account — must be Australia East for data sovereignty')
@allowed([
  'australiaeast', 'global'
])
param location string

@description('Environment name for resource naming')
param envPrefix string

@description('Deployment environment — controls authentication policy')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'prod'

@description('Tags applied to the resource')
param tags object

@description('Allowed CORS origins for the web frontend')
param corsAllowedOrigins array = environment == 'dev' ? ['http://localhost:3000', 'http://127.0.0.1:3000'] : []

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
    disableLocalAuth: environment != 'dev'
    cors: {
      corsRules: empty(corsAllowedOrigins) ? [] : [
        {
          allowedOrigins: corsAllowedOrigins
        }
      ]
    }
  }
}

// ── Outputs ──

output azureMapsName string = azureMaps.name
output azureMapsId string = azureMaps.id

@description('Primary subscription key used by the development web client. Restrict browser use through CORS.')
@secure()
output azureMapsPrimaryKey string = azureMaps.listKeys().primaryKey
