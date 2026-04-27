// Spec 029 — Pipeline Identity (T022)
// Provisions the per-environment user-assigned managed identities used by
// GitHub Actions OIDC federation. Federated credentials are *not* created here
// (they require Graph API calls); see scripts/spec029-bootstrap/02-create-federated-creds.ps1.
@description('Environment slug — appended to identity name.')
param environmentName string

@description('Azure region.')
param location string = resourceGroup().location

@description('Tag propagation.')
param tags object = {}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'mi-ama-pipeline-${environmentName}'
  location: location
  tags: union(tags, { spec: '029', purpose: 'github-oidc' })
}

output principalId string = identity.properties.principalId
output clientId string = identity.properties.clientId
output identityId string = identity.id
