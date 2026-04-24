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
param reasoningModelName string = 'gpt-5.4'

@description('Reasoning-tier model version')
param reasoningModelVersion string = '2026-03-05'

@description('Drafting-tier model name')
param draftingModelName string = 'gpt-5.4'

@description('Drafting-tier model version')
param draftingModelVersion string = '2026-03-05'

@description('Simulation Controller model name (used by the Simulation chat endpoint).')
param simulationModelName string = 'gpt-5.4'

@description('Simulation Controller model version.')
param simulationModelVersion string = '2026-03-05'

// TPM quotas (in thousands)
@description('Reasoning-tier TPM quota (K). Dev=30, Prod=120')
@minValue(1)
param reasoningTpmQuota int = 30

@description('Drafting-tier TPM quota (K). Dev=60, Prod=240')
@minValue(1)
param draftingTpmQuota int = 60

@description('Simulation Controller TPM quota (K). Dev=20, Prod=80. Isolated quota so an exercise cannot starve live agents.')
@minValue(1)
param simulationTpmQuota int = 20

@description('Model deployment SKU — GlobalStandard for dev/staging (draws from global capacity pool), Standard for production (regional capacity)')
@allowed(['Standard', 'GlobalStandard'])
param modelDeploymentSku string = 'GlobalStandard'

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
// Responsible AI policy (simulation-only)
//
// The Simulation Controller routinely processes emergency-management vocabulary
// (bushfire behaviour, escalation, casualty projections) that the DefaultV2
// content filter scores as high-severity violence on the prompt side and blocks
// before the model can respond. We attach a custom policy that raises the
// Violence threshold from the default Medium → High on both Prompt and
// Completion, while leaving Hate / Sexual / SelfHarm / Jailbreak / IndirectAttack
// at base defaults. This policy is applied ONLY to the simulation deployment —
// the live-incident reasoning and drafting deployments keep the stock filter.
//
// Reference: Microsoft.CognitiveServices/accounts/raiPolicies API 2024-10-01.
// ────────────────────────────────────────────────────────────────────────────────

var simulationRaiPolicyName = 'sim-em-domain-${envPrefix}'

// NOTE: Cognitive Services accounts only allow ONE child operation (deployment
// or RAI policy) at a time. Deploying this policy in parallel with
// reasoningDeployment causes ARM to return "RequestConflict: Another operation
// is being performed on the parent resource". We serialise it into the chain
// AFTER draftingDeployment, so the end-to-end order is:
//   reasoningDeployment → draftingDeployment → simulationRaiPolicy → simulationDeployment
resource simulationRaiPolicy 'Microsoft.CognitiveServices/accounts/raiPolicies@2024-10-01' = {
  parent: openAiAccount
  name: simulationRaiPolicyName
  properties: {
    basePolicyName: 'Microsoft.DefaultV2'
    mode: 'Blocking'
    contentFilters: [
      {
        name: 'Violence'
        source: 'Prompt'
        enabled: true
        blocking: true
        severityThreshold: 'High'
      }
      {
        name: 'Violence'
        source: 'Completion'
        enabled: true
        blocking: true
        severityThreshold: 'High'
      }
    ]
  }
  dependsOn: [draftingDeployment]
}

// ────────────────────────────────────────────────────────────────────────────────
// Model Deployments
// ────────────────────────────────────────────────────────────────────────────────

resource reasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiAccount
  name: 'gpt-5.4-${envPrefix}'
  sku: {
    name: modelDeploymentSku
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
  name: 'gpt-5.4-mini-${envPrefix}'
  sku: {
    name: modelDeploymentSku
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

// Dedicated deployment for the Simulation Controller (spec 024).
// GlobalStandard SKU isolates exercise traffic from live-incident reasoning/drafting
// quota so a runaway simulation cannot starve real-incident agents.
// Uses the custom RAI policy (see simulationRaiPolicy above) so emergency-management
// vocabulary — fire escalation, casualty projections — doesn't trip the default
// violence filter during an exercise.
resource simulationDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiAccount
  name: 'gpt-5.4-sim-${envPrefix}'
  sku: {
    name: modelDeploymentSku
    capacity: simulationTpmQuota
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: simulationModelName
      version: simulationModelVersion
    }
    raiPolicyName: simulationRaiPolicy.name
  }
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
output simulationDeploymentName string = simulationDeployment.name
output simulationRaiPolicyName string = simulationRaiPolicy.name
output openAiEndpoint string = openAiAccount.properties.endpoint
