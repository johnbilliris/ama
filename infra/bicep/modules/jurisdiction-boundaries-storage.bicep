// Spec 036 — Jurisdiction boundaries storage (T-A12)
//
// Provisions a versioned blob container `jurisdiction-boundaries` to hold the
// polygon GeoJSON used by the STRtree jurisdiction lookup (FR-021 step 4).
// Soft delete enabled; private endpoint only.

@description('Existing storage account.')
param storageAccountName string

@description('Container name.')
param containerName string = 'jurisdiction-boundaries'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    isVersioningEnabled: true
    deleteRetentionPolicy: {
      enabled: true
      days: 30
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 30
    }
  }
}

resource jurisdictionBoundariesContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: containerName
  properties: {
    publicAccess: 'None'
    metadata: {
      spec: '036'
      contentType: 'jurisdiction-polygon-geojson'
    }
  }
}

output containerName string = jurisdictionBoundariesContainer.name
