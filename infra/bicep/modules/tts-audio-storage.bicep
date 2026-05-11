// Spec 036 — TTS audio storage (T-A13)
//
// Container `tts-audio-artefacts` for pre-rendered Azure AI Speech bilingual
// watermark audio (FR-058). Private signed-URL access only; CMK encryption.
// Lifecycle policy moves blobs > 90 days to Cool tier.

@description('Existing storage account.')
param storageAccountName string

@description('Container name.')
param containerName string = 'tts-audio-artefacts'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  parent: storageAccount
  name: 'default'
}

resource ttsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: containerName
  properties: {
    publicAccess: 'None'
    metadata: {
      spec: '036'
      contentType: 'simulation-tts-watermark'
    }
  }
}

resource lifecyclePolicy 'Microsoft.Storage/storageAccounts/managementPolicies@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    policy: {
      rules: [
        {
          name: 'ttsToCoolAfter90d'
          enabled: true
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: [ 'blockBlob' ]
              prefixMatch: [ '${containerName}/' ]
            }
            actions: {
              baseBlob: {
                tierToCool: { daysAfterModificationGreaterThan: 90 }
              }
            }
          }
        }
      ]
    }
  }
}

output containerName string = ttsContainer.name
