// =============================================================================
// recovery-signing-keyvault.bicep — spec-035 T012
// =============================================================================
// Provisions a Key Vault dedicated to the recovery-handover PDF signing
// certificate (FR-007). The Key Vault hosts:
//   - a system-assigned-MI-readable RSA 3072-bit signing key
//   - the certificate (provisioned out-of-band via az keyvault certificate
//     import or a deployment script — left as placeholder for this module)
//
// AVM dep: br/public:avm/res/key-vault/vault
// =============================================================================

targetScope = 'resourceGroup'

@description('Azure region.')
param location string

@description('Environment-specific resource naming prefix (CAF).')
param envPrefix string

@description('Tags applied to every deployed resource.')
param tags object = {}

@description('Name of the signing key (used by recovery-handover service).')
param signingKeyName string = 'recovery-handover-signing-key'

@description('System-assigned managed-identity principal id of the API container app (read access).')
param apiPrincipalId string = ''

var keyVaultName = take('kv-rec-${envPrefix}-${uniqueString(resourceGroup().id, envPrefix)}', 24)

module keyVault 'br/public:avm/res/key-vault/vault:0.13.3' = {
  name: take('kv-rec-${envPrefix}', 64)
  params: {
    name: keyVaultName
    location: location
    tags: tags
    sku: 'standard'
    enableRbacAuthorization: true
    enablePurgeProtection: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    publicNetworkAccess: 'Disabled'
    enableTelemetry: false
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
    keys: [
      {
        name: signingKeyName
        kty: 'RSA'
        keySize: 3072
        rotationPolicy: {
          attributes: {
            expiryTime: 'P730D'
          }
          lifetimeActions: [
            {
              action: { type: 'rotate' }
              trigger: { timeBeforeExpiry: 'P30D' }
            }
          ]
        }
      }
    ]
    roleAssignments: empty(apiPrincipalId) ? [] : [
      {
        principalId: apiPrincipalId
        roleDefinitionIdOrName: '21090545-7ca7-4776-b22c-e363652d74d2'
        principalType: 'ServicePrincipal'
      }
    ]
  }
}

@description('Resource id of the Key Vault.')
output keyVaultId string = keyVault.outputs.resourceId

@description('Vault URI for the Key Vault.')
output keyVaultUri string = keyVault.outputs.uri

@description('Name of the signing key.')
output signingKeyName string = signingKeyName
