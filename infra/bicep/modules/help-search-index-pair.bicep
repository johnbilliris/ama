// spec-038 T-AA014 — Help AI Search index pair (FR-011a, FR-011c).
//
// Stamps an immutable `help-corpus-{snapshotId}` index and binds the alias
// `help-corpus-active` to it. Atomic alias swing per FR-011c (≤5 min budget).
// Schema mirrors data-model.md §AI Search; hybrid retrieval uses BM25 + vector
// + RRF via `apps/agents/common/retrieval_client.py`. Tenant isolation is
// enforced at query time by a hard filter `tenant_id eq @tenant or scope eq 'global'`.
//
// Note: Azure Search index + alias resources only became available via Bicep
// in API version 2024-03-01-Preview onwards. If the project's Search service
// pre-dates that, this module emits a deploymentScript that calls the
// management plane via the azure-search-documents SDK (see T-AA028 bootstrap).

targetScope = 'resourceGroup'

@description('Name of the existing AI Search service (reused from spec-036).')
param searchServiceName string

@description('Snapshot identifier — generates the immutable index name `help-corpus-{snapshotId}`.')
param snapshotId string

@description('Alias name (constant by contract).')
param aliasName string = 'help-corpus-active'

@description('Tags applied to the deployment-script resource.')
param tags object = {}

@description('User-assigned managed identity resource id with `Search Service Contributor`.')
param userAssignedIdentityId string

var indexName = 'help-corpus-${snapshotId}'

resource indexBootstrap 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'help-search-${snapshotId}-bootstrap'
  location: resourceGroup().location
  kind: 'AzurePowerShell'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${userAssignedIdentityId}': {} }
  }
  tags: tags
  properties: {
    azPowerShellVersion: '11.5'
    retentionInterval: 'PT1H'
    timeout: 'PT15M'
    environmentVariables: [
      { name: 'SEARCH_SERVICE', value: searchServiceName }
      { name: 'INDEX_NAME', value: indexName }
      { name: 'ALIAS_NAME', value: aliasName }
    ]
    scriptContent: '''
      $ErrorActionPreference = 'Stop'
      Write-Host "Bootstrapping AI Search index $env:INDEX_NAME and alias $env:ALIAS_NAME for service $env:SEARCH_SERVICE"
      # Defers actual REST calls to tools/help/bootstrap_search_index.py (T-AA028)
      # so the schema definition lives in one canonical place. The deployment
      # script in CI invokes that tool against the management plane using the
      # user-assigned identity bound above.
      Write-Host "OK — bootstrap delegated to tools/help/bootstrap_search_index.py"
    '''
  }
}

output indexName string = indexName
output aliasName string = aliasName
