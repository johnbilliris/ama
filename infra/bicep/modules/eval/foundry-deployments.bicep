// infra/bicep/modules/eval/foundry-deployments.bicep
//
// Parametrised module that creates a single Foundry model deployment for the lifetime
// of one eval run. Called by the runner's provisioner (apps/eval-runner/.../provisioner.py)
// AFTER `What-If` confirms diff is scoped to the run's RG.
//
// Region selection is NOT restricted to AU here — the Foundry carve-out (constitution
// NN-2) explicitly permits non-AU regions for model-hosting endpoints. Caller is
// responsible for selecting from the carve-out list and enforcing data minimisation
// at the model gateway (FR-018, runner contract).

targetScope = 'resourceGroup'

@description('Foundry account (AI Services / OpenAI) name to host the deployment in')
param foundryAccountName string

@description('Foundry model identifier (e.g., gpt-4o, gpt-4o-mini, Phi-3.5-MoE-instruct)')
param modelId string

@description('Foundry model version (e.g., 2024-11-20)')
param modelVersion string

@description('Deployment name to give this transient deployment')
param deploymentName string

@description('SKU name (e.g., Standard, GlobalStandard)')
param skuName string = 'Standard'

@description('Capacity (Tokens-per-Minute Per 1000 unit). Bounded by ProvisioningPolicy.')
param skuCapacity int = 50

@description('Run id the deployment belongs to — propagates through tags for reconciler')
param runId string

@description('Deployment region — must be on the constitution carve-out list')
param deploymentRegion string

@description('Tags — caller MUST include runId and eval-managed=true')
param tags object = {
  runId: runId
  'eval-managed': 'true'
  'created-by': 'caj-eval-runner'
  feature: '030-llm-eval-framework'
}

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: foundryAccountName
}

resource foundryDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryAccount
  name: deploymentName
  tags: tags
  sku: {
    name: skuName
    capacity: skuCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelId
      version: modelVersion
    }
    raiPolicyName: 'Microsoft.Default'
    versionUpgradeOption: 'NoAutoUpgrade'
  }
}

output deploymentName string = foundryDeployment.name
output deploymentId string = foundryDeployment.id
output endpoint string = foundryAccount.properties.endpoint
output region string = deploymentRegion
