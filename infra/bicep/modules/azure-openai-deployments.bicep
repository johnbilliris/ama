// Spec 036 — Azure OpenAI deployments for sim realm (T-A14)
//
// Provisions the **gpt-4o-mini** (150K TPM) and **gpt-4o** (100K TPM)
// deployments for the AU East Foundry account, per plan-decision #11/12.
//
// Constitution v1.2.0 §Non-Negotiable #2 — AU residency. Any non-AU
// placement requires a corresponding entry in the Foundry carve-out registry
// validated by T-A18 + T-K07 (6-month review-date enforcement).

@description('Existing Azure OpenAI account name.')
param openAiAccountName string

@description('Region — must be exactly `australiaeast` to honour Constitution NN-2.')
@allowed([ 'australiaeast' ])
param location string = 'australiaeast'

@description('TPM budget for gpt-4o-mini (per plan-decision #11).')
param miniTpm int = 150

@description('TPM budget for gpt-4o (per plan-decision #11).')
param fullTpm int = 100

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: openAiAccountName
}

resource gpt4oMini 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: account
  name: 'gpt-4o-mini-${location}'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-mini'
      version: '2024-07-18'
    }
    raiPolicyName: 'Microsoft.DefaultV2'
  }
  sku: {
    name: 'Standard'
    capacity: miniTpm
  }
}

resource gpt4o 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: account
  name: 'gpt-4o-${location}'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'
    }
    raiPolicyName: 'Microsoft.DefaultV2'
  }
  sku: {
    name: 'Standard'
    capacity: fullTpm
  }
}

output gpt4oMiniDeploymentName string = gpt4oMini.name
output gpt4oDeploymentName string = gpt4o.name
output assertedLocation string = location
