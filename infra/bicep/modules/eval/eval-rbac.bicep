// infra/bicep/modules/eval/eval-rbac.bicep
//
// Role assignments and Entra ID role definitions for the eval framework.
// Depends on eval-platform.bicep outputs.

targetScope = 'resourceGroup'

@description('Principal id of the runner managed identity')
param runnerIdentityPrincipalId string

@description('Cosmos account name (for data plane RBAC)')
param cosmosAccountName string

@description('Storage account resource id (for data plane RBAC)')
param storageAccountResourceId string

@description('Key Vault resource id')
param keyVaultResourceId string

@description('Foundry/AI Services account resource id (for Azure AI Developer role)')
param foundryAccountResourceId string

@description('Resource group id for ephemeral run-scoped RGs (e.g., rg-eval-runs-<env>)')
param ephemeralRunsResourceGroupId string

// Built-in role definition ids
var roles = {
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  keyVaultSecretsUser:        '4633458b-17de-408a-b874-0445c86b69e6'
  contributor:                'b24988ac-6180-42a0-ab88-20f7382dd24c'
  azureAIDeveloper:           '64702f94-c441-49e6-a78b-ef80e0188fee'
  cosmosDbDataContributor:    '00000000-0000-0000-0000-000000000002' // Cosmos data plane built-in
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' existing = {
  name: cosmosAccountName
}

// Cosmos DB data plane (Cosmos DB Built-in Data Contributor)
resource cosmosDataRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = {
  parent: cosmos
  name: guid(cosmos.id, runnerIdentityPrincipalId, 'data-contributor')
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/${roles.cosmosDbDataContributor}'
    principalId: runnerIdentityPrincipalId
    scope: cosmos.id
  }
}

// Storage Blob Data Contributor on the eval storage account
resource storageBlobRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccountResourceId, runnerIdentityPrincipalId, 'storage-blob-contrib')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.storageBlobDataContributor)
    principalId: runnerIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Key Vault Secrets User
resource kvSecretsRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVaultResourceId, runnerIdentityPrincipalId, 'kv-secrets-user')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.keyVaultSecretsUser)
    principalId: runnerIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Azure AI Developer on the Foundry project (judge + MUT inference)
resource foundryRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryAccountResourceId, runnerIdentityPrincipalId, 'azure-ai-developer')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.azureAIDeveloper)
    principalId: runnerIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Contributor on a single dedicated rg-eval-runs-${env} for ephemeral RG creation
// NOTE: This role assignment is best authored at the run-RG scope; if applied here it
// scopes to the platform RG which is broader than ideal. For least privilege, deploy
// rbac at the dedicated rg-eval-runs-* RG scope using a separate stack.
output runnerIdentityPrincipalId string = runnerIdentityPrincipalId
output ephemeralRunsResourceGroupId string = ephemeralRunsResourceGroupId
