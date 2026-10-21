metadata description = 'First-party existing-parent deployment preservation; approved exception recorded in feature 041 avm-compatibility.md.'

@export()
@description('Observed deployment operating state, independent of requested SKU capacity.')
type deploymentOperatingState = {
  @minValue(0)
  currentCapacity: int
  deploymentState: 'Running' | 'Paused'
}

@description('Existing parent Cognitive Services account ARM name.')
@minLength(2)
param accountName string

@description('Existing model deployment name.')
@minLength(1)
param name string

@description('Explicit model identity, including the approved version.')
param model {
  format: string
  name: string
  version: string
}

@description('Explicit approved deployment SKU and requested capacity.')
param sku resourceInput<'Microsoft.CognitiveServices/accounts/deployments@2025-06-01'>.sku

@description('Explicit approved RAI policy attachment.')
@minLength(1)
param raiPolicyName string

@description('Explicit approved model version-upgrade behavior.')
@allowed(['OnceNewDefaultVersionAvailable', 'OnceCurrentVersionExpired', 'NoAutoUpgrade'])
param versionUpgradeOption string

@description('Required observed operating state; never derived from SKU or defaulted to Running.')
param operatingState deploymentOperatingState

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: accountName
}

// The exact API exposes both preservation inputs but is not in the installed Bicep type bundle.
#disable-next-line BCP081
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2026-05-01' = {
  parent: account
  name: name
  sku: sku
  properties: {
    model: model
    raiPolicyName: raiPolicyName
    versionUpgradeOption: versionUpgradeOption
    currentCapacity: operatingState.currentCapacity
    deploymentState: operatingState.deploymentState
  }
}

@description('Preserved deployment name.')
output name string = deployment.name

@description('Preserved deployment resource ID.')
output resourceId string = deployment.id
