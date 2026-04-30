// ────────────────────────────────────────────────────────────────────────────────
// Cosmos DB CMK encryption (spec-032 T402, FR-S05).
//
// Builds on the existing pattern in log-analytics-key.bicep. Provisions:
//  - HSM-backed key in Key Vault Premium
//  - Access policy / RBAC for the Cosmos managed identity
//  - 90-day rotation policy via Azure Policy (out-of-band assignment)
//
// Output: keyVaultKeyUri (passed to the Cosmos account creation as
// `keyVaultKeyUri` parameter to enable CMK).
// ────────────────────────────────────────────────────────────────────────────────

@description('Key Vault Premium name (CMK requires HSM-backed)')
param keyVaultName string

@description('Location')
param location string

@description('Tags')
param tags object = {}

@description('Cosmos DB system-assigned principalId (for access)')
param cosmosPrincipalId string

@description('Key name for Cosmos CMK')
param keyName string = 'cosmos-cmk'

resource keyVault 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing = {
  name: keyVaultName
}

// HSM-backed key with rotation policy; rotation enforced by Azure Policy externally.
resource cosmosKey 'Microsoft.KeyVault/vaults/keys@2024-04-01-preview' = {
  parent: keyVault
  name: keyName
  tags: tags
  properties: {
    keySize: 4096
    kty: 'RSA-HSM'
    keyOps: [
      'wrapKey'
      'unwrapKey'
    ]
    rotationPolicy: {
      lifetimeActions: [
        {
          action: { type: 'Rotate' }
          trigger: { timeAfterCreate: 'P90D' }
        }
        {
          action: { type: 'Notify' }
          trigger: { timeBeforeExpiry: 'P30D' }
        }
      ]
      attributes: {
        expiryTime: 'P2Y'
      }
    }
  }
}

// Grant Cosmos managed identity wrap/unwrap on this key
@description('Built-in Key Vault Crypto Service Encryption User role')
var keyVaultCryptoServiceEncryptionUserRoleId = 'e147488a-f6f5-4113-8e2d-b22465e65bf6'

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, cosmosPrincipalId, keyVaultCryptoServiceEncryptionUserRoleId)
  scope: keyVault
  properties: {
    principalId: cosmosPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultCryptoServiceEncryptionUserRoleId)
  }
}

output keyVaultKeyUri string = cosmosKey.properties.keyUriWithVersion
output keyName string = cosmosKey.name
