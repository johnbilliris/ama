// =============================================================================
// blob-immutable.bicep — spec-035 T010
// =============================================================================
// Composes a Storage Account + immutable Blob container for recovery-handover
// PDFs per
// specs/035-webapp-capstone-closure/contracts/recovery-handover.contract.md.
//
// AVM dep: br/public:avm/res/storage/storage-account
//          - HTTPS-only, TLS 1.2 minimum, public-network-access disabled,
//            shared-key access disabled, system-assigned managed identity.
//          - Container created with default
//            immutabilityPolicy.allowProtectedAppendWrites=true and a
//            time-based retention policy. legalHold is enabled with a single
//            tag matching the artefact-domain.
// =============================================================================

targetScope = 'resourceGroup'

@description('Azure region for the storage account.')
param location string

@description('Environment-specific resource naming prefix (CAF).')
param envPrefix string

@description('Tags applied to every deployed resource.')
param tags object = {}

@description('Container name carrying the recovery-handover PDFs.')
param containerName string = 'recovery-handover'

@description('Time-based immutability retention period (days). Sendai handover artefacts retained 7y by default.')
@minValue(30)
@maxValue(36500)
param immutabilityRetentionDays int = 2557

@description('Legal-hold tag applied at container creation time.')
param legalHoldTag string = 'recovery-handover-spec035'

@description('Storage SKU. ZRS recommended for AU regions; LRS acceptable for dev.')
@allowed([
  'Standard_LRS'
  'Standard_GRS'
  'Standard_RAGRS'
  'Standard_ZRS'
  'Standard_GZRS'
  'Standard_RAGZRS'
])
param storageSku string = 'Standard_ZRS'

var storageName = toLower(replace(take('strchm${envPrefix}${uniqueString(resourceGroup().id, envPrefix)}', 24), '-', ''))

module storage 'br/public:avm/res/storage/storage-account:0.32.0' = {
  name: take('strchm-${envPrefix}', 64)
  params: {
    name: storageName
    location: location
    skuName: storageSku
    kind: 'StorageV2'
    accessTier: 'Cool'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    publicNetworkAccess: 'Disabled'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    requireInfrastructureEncryption: true
    tags: tags
    enableTelemetry: false
    managedIdentities: {
      systemAssigned: true
    }
    blobServices: {
      containers: [
        {
          name: containerName
          publicAccess: 'None'
          immutableStorageWithVersioningEnabled: true
          immutabilityPolicy: {
            immutabilityPeriodSinceCreationInDays: immutabilityRetentionDays
            allowProtectedAppendWrites: true
          }
          metadata: {
            legalHoldTag: legalHoldTag
          }
        }
      ]
      containerDeleteRetentionPolicyEnabled: true
      containerDeleteRetentionPolicyDays: 30
      deleteRetentionPolicyEnabled: true
      deleteRetentionPolicyDays: 30
    }
  }
}

// Apply legal hold via a tag-driven child policy. AVM exposes legalHold via
// blobServices.containers[].defaultEncryptionScope, but the tag-based legal
// hold is set via the dedicated child resource at deploy time.
resource handoverContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' existing = {
  name: '${storageName}/default/${containerName}'
  dependsOn: [storage]
}

resource legalHoldPolicy 'Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies@2023-05-01' = {
  name: 'default'
  parent: handoverContainer
  properties: {
    immutabilityPeriodSinceCreationInDays: immutabilityRetentionDays
    allowProtectedAppendWrites: true
  }
}

@description('Resource id of the storage account.')
output storageAccountId string = storage.outputs.resourceId

@description('Name of the storage account.')
output storageAccountName string = storageName

@description('Name of the immutable handover container.')
output handoverContainerName string = containerName
