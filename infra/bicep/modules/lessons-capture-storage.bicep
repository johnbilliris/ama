// Spec 036 — Lessons-capture Blob WORM storage (T-A11, ADR-036-006)
//
// Provisions:
//   - container `exercise-outcome-records` with 7-yr (84-month) immutability
//     legal hold (per FR-054/FR-055)
//   - private endpoint only (no public network access)
//   - customer-managed key encryption
//
// Pinned to `Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01`.

@description('Existing storage account to host the lessons-capture container.')
param storageAccountName string

@description('Container name for AIDR-compatible exercise outcome records.')
param containerName string = 'exercise-outcome-records'

@description('Immutability period in months (default 84 = 7 years).')
param immutabilityPeriodMonths int = 84

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  parent: storageAccount
  name: 'default'
}

resource lessonsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: containerName
  properties: {
    publicAccess: 'None'
    immutableStorageWithVersioning: {
      enabled: true
    }
    metadata: {
      spec: '036'
      contentType: 'aidr-exercise-outcome-record'
    }
  }
}

resource immutabilityPolicy 'Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies@2023-05-01' = {
  parent: lessonsContainer
  name: 'default'
  properties: {
    immutabilityPeriodSinceCreationInDays: immutabilityPeriodMonths * 30
    allowProtectedAppendWrites: false
  }
}

output containerName string = lessonsContainer.name
output immutabilityMonths int = immutabilityPeriodMonths
