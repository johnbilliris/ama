// ────────────────────────────────────────────────────────────────────────────────
// Azure OpenAI Model Deployments, RBAC, and Diagnostics
// ────────────────────────────────────────────────────────────────────────────────

@description('Name of the existing Azure OpenAI resource')
param openAiAccountName string

@description('Location — restricted to Australian regions')
@allowed(['australiaeast', 'australiasoutheast'])
param location string

@description('Environment prefix for deployment naming')
param envPrefix string

@description('Resource tags')
param tags object

// Model configuration
@description('Reasoning-tier model name')
param reasoningModelName string = 'gpt-4o'

@description('Reasoning-tier model version')
param reasoningModelVersion string = '2024-08-06'

@description('Drafting-tier model name')
param draftingModelName string = 'gpt-4o-mini'

@description('Drafting-tier model version')
param draftingModelVersion string = '2024-07-18'

// TPM quotas (in thousands)
@description('Reasoning-tier TPM quota (K). Dev=30, Prod=120')
@minValue(1)
param reasoningTpmQuota int = 30

@description('Drafting-tier TPM quota (K). Dev=60, Prod=240')
@minValue(1)
param draftingTpmQuota int = 60

// RBAC
@description('Principal IDs to grant Cognitive Services OpenAI User role')
param agentPrincipalIds array = []

// Diagnostics
@description('Log Analytics workspace ID for diagnostic settings')
param logAnalyticsWorkspaceId string

// ────────────────────────────────────────────────────────────────────────────────
// Reference the existing Azure OpenAI account
// ────────────────────────────────────────────────────────────────────────────────

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: openAiAccountName
}

// ────────────────────────────────────────────────────────────────────────────────
// Model Deployments
// ────────────────────────────────────────────────────────────────────────────────

resource reasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiAccount
  name: 'gpt-4o-${envPrefix}'
  sku: {
    name: 'Standard'
    capacity: reasoningTpmQuota
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: reasoningModelName
      version: reasoningModelVersion
    }
  }
}

resource draftingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiAccount
  name: 'gpt-4o-mini-${envPrefix}'
  sku: {
    name: 'Standard'
    capacity: draftingTpmQuota
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: draftingModelName
      version: draftingModelVersion
    }
  }
  dependsOn: [reasoningDeployment]
}

// ────────────────────────────────────────────────────────────────────────────────
// RBAC: Cognitive Services OpenAI User
// ────────────────────────────────────────────────────────────────────────────────

var cognitiveServicesOpenAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource openAiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for (principalId, i) in agentPrincipalIds: {
    name: guid(openAiAccount.id, principalId, cognitiveServicesOpenAiUserRoleId)
    scope: openAiAccount
    properties: {
      roleDefinitionId: subscriptionResourceId(
        'Microsoft.Authorization/roleDefinitions',
        cognitiveServicesOpenAiUserRoleId
      )
      principalId: principalId
      principalType: 'ServicePrincipal'
    }
  }
]

// ────────────────────────────────────────────────────────────────────────────────
// Diagnostic Settings
// ────────────────────────────────────────────────────────────────────────────────

resource openAiDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'openai-diagnostics'
  scope: openAiAccount
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      { category: 'RequestResponse', enabled: true }
      { category: 'Audit', enabled: true }
    ]
    metrics: [
      { category: 'AllMetrics', enabled: true }
    ]
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Outputs
// ────────────────────────────────────────────────────────────────────────────────

output reasoningDeploymentName string = reasoningDeployment.name
output draftingDeploymentName string = draftingDeployment.name
output openAiEndpoint string = openAiAccount.properties.endpoint
