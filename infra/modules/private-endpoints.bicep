// ────────────────────────────────────────────────────────────────────────────────
// Private Endpoints + Private DNS for the platform's data planes (spec-032 T401, T404, T405, T406).
//
// Provides PE wiring for Cosmos DB, Storage, Azure OpenAI, AI Content Safety, AI Search.
// Each consumer module also accepts the relevant DNS zone IDs to wire its own PE.
// This module centralises the DNS zones + a small per-zone "private link" subnet helper.
//
// Per FR-S01 + FR-AI06 + FR-S04: production data planes refuse public connections.
// ────────────────────────────────────────────────────────────────────────────────

@description('Location')
param location string

@description('Tags')
param tags object = {}

@description('Hub VNet resource ID into which DNS zones are linked')
param vnetId string

// Private DNS zones (one per service)
var dnsZoneNames = [
  'privatelink.documents.azure.com'         // Cosmos DB
  'privatelink.blob.${environment().suffixes.storage}'    // Storage Blob
  'privatelink.queue.${environment().suffixes.storage}'   // Storage Queue
  'privatelink.table.${environment().suffixes.storage}'   // Storage Table
  'privatelink.openai.azure.com'            // Azure OpenAI
  'privatelink.cognitiveservices.azure.com' // AI Content Safety
  'privatelink.search.windows.net'          // AI Search
  'privatelink.servicebus.windows.net'      // Service Bus
  'privatelink.vaultcore.azure.net'         // Key Vault
]

resource dnsZones 'Microsoft.Network/privateDnsZones@2024-06-01' = [for zone in dnsZoneNames: {
  name: zone
  location: 'global'
  tags: tags
}]

resource dnsZoneVnetLinks 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = [for (zone, i) in dnsZoneNames: {
  parent: dnsZones[i]
  name: '${replace(zone, '.', '-')}-vnet-link'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}]

// Outputs — consumers map by service group ID.
output dnsZoneIds object = {
  cosmosDocuments: dnsZones[0].id
  storageBlob: dnsZones[1].id
  storageQueue: dnsZones[2].id
  storageTable: dnsZones[3].id
  openai: dnsZones[4].id
  cognitiveservices: dnsZones[5].id
  searchService: dnsZones[6].id
  serviceBus: dnsZones[7].id
  keyVault: dnsZones[8].id
}
