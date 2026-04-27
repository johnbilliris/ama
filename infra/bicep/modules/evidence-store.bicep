// Spec 029 — Evidence Store (T027)
// Immutable Blob storage container with legal-hold + time-based retention for
// the FR-013 evidence packs.
@description('Environment slug.')
param environmentName string
param location string = resourceGroup().location
param tags object = {}

@description('Retention in days for legal-hold immutability policy.')
@minValue(2555) // 7 years (regulatory baseline)
param retentionDays int = 2555

var account = toLower(replace('stamaev${environmentName}${uniqueString(resourceGroup().id)}', '-', ''))

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: take(account, 24)
  location: location
  sku: { name: 'Standard_GZRS' }
  kind: 'StorageV2'
  tags: union(tags, { spec: '029', purpose: 'evidence-store' })
  properties: {
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Disabled'
    allowSharedKeyAccess: false
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    encryption: {
      requireInfrastructureEncryption: true
      services: { blob: { enabled: true }, file: { enabled: true } }
      keySource: 'Microsoft.Storage'
    }
  }
}

resource blob 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: { isVersioningEnabled: true, changeFeed: { enabled: true } }
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blob
  name: 'evidence'
  properties: {
    publicAccess: 'None'
    immutableStorageWithVersioning: { enabled: true }
  }
}

resource immutability 'Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies@2023-05-01' = {
  parent: container
  name: 'default'
  properties: {
    immutabilityPeriodSinceCreationInDays: retentionDays
    allowProtectedAppendWrites: true
  }
}

output accountName string = storage.name
output containerUrl string = '${storage.properties.primaryEndpoints.blob}evidence'
