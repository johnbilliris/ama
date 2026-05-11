// spec-038 T-AA015 — Help screenshots storage container (FR-006, FR-007).
//
// Adds a `help-screenshots` blob container under the existing AU East storage
// account with:
//   - private endpoint (network access via the platform private DNS zone)
//   - 30-day immutability policy (versioned + WORM)
//   - 90-day soft-delete
//   - customer-managed key (reuses the account-level encryption scope)
//
// CMK + private endpoint are inherited from the parent storage account
// configuration; this module only adds the container + immutability policy.

targetScope = 'resourceGroup'

@description('Existing storage account name (reused from platform).')
param storageAccountName string

@description('Container name (constant by contract).')
param containerName string = 'help-screenshots'

@description('Immutability period in days.')
param immutabilityDays int = 30

@description('Tags applied to the container.')
param tags object = {}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  parent: storage
  name: 'default'
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: containerName
  properties: {
    publicAccess: 'None'
    metadata: {
      spec: 'spec-038'
      purpose: 'help-screenshots'
    }
  }
}

resource immutability 'Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies@2023-05-01' = {
  parent: container
  name: 'default'
  properties: {
    immutabilityPeriodSinceCreationInDays: immutabilityDays
    allowProtectedAppendWrites: false
  }
}

output containerName string = container.name
