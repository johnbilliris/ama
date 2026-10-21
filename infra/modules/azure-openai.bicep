// ────────────────────────────────────────────────────────────────────────────────
// Foundry (Microsoft AIServices) Model Deployments, RBAC, and Diagnostics
//
// Spec 036 / ADR-20 (hard-cutover migration) — this module deploys
// `Microsoft.CognitiveServices/accounts/deployments` resources on the parent
// `Microsoft.CognitiveServices/accounts` of kind 'AIServices' (Foundry). The
// deployment shape is unchanged from the legacy Azure-OpenAI pattern because
// the deployments resource type is identical across both kinds. The endpoint
// URL the parent emits is the Foundry endpoint, consumed by callers via the
// `AZURE_AI_PROJECT_ENDPOINT` env var. The transitional `AZURE_OPENAI_ENDPOINT`
// compatibility seam was dropped in the post-cutover cleanup PR per
// ADR-20 §Q-P6-03.
// ────────────────────────────────────────────────────────────────────────────────

import { deploymentOperatingState } from './cognitive-services-deployment-preservation.bicep'

@export()
@description('Explicit approved operating states for all existing deployments, including embedding.')
type deploymentOperatingStatesType = {
  reasoning: deploymentOperatingState
  drafting: deploymentOperatingState
  simulation: deploymentOperatingState
  embedding: deploymentOperatingState
}

@description('Required observed capacities and Running/Paused states; no inferred defaults.')
param deploymentOperatingStates deploymentOperatingStatesType

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
@minLength(1)
param reasoningModelName string

@description('Reasoning-tier model version')
@minLength(1)
param reasoningModelVersion string

@description('Drafting-tier model name')
@minLength(1)
param draftingModelName string

@description('Drafting-tier model version')
@minLength(1)
param draftingModelVersion string

@description('Simulation Controller model name (used by the Simulation chat endpoint).')
@minLength(1)
param simulationModelName string

@description('Simulation Controller model version.')
@minLength(1)
param simulationModelVersion string

@description('Existing reasoning deployment name. Purpose/environment default is for new resources only.')
param reasoningDeploymentName string = 'reasoning-${envPrefix}'

@description('Existing drafting deployment name. Purpose/environment default is for new resources only.')
param draftingDeploymentName string = 'drafting-${envPrefix}'

@description('Existing simulation deployment name. Purpose/environment default is for new resources only.')
param simulationDeploymentName string = 'simulation-${envPrefix}'

@description('Explicit approved reasoning version upgrade behavior.')
param reasoningVersionUpgradeOption string

@description('Explicit approved drafting version upgrade behavior.')
param draftingVersionUpgradeOption string

@description('Explicit approved simulation version upgrade behavior.')
param simulationVersionUpgradeOption string

@description('Explicit approved embedding version upgrade behavior.')
param embeddingVersionUpgradeOption string

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

@description('Embedding model name (Spec 036 FR-RAG-IDX-02 — corpus chunks → 3072-dim vectors).')
param embeddingModelName string = 'text-embedding-3-large'

@description('Embedding model version.')
param embeddingModelVersion string = '1'

@description('Embedding deployment TPM quota (K). Sized for full corpus rebuild headroom.')
@minValue(1)
param embeddingTpmQuota int = 60

@description('Model deployment SKU — GlobalStandard for dev/staging (draws from global capacity pool), Standard for production (regional capacity)')
@allowed(['Standard', 'GlobalStandard'])
param modelDeploymentSku string = 'GlobalStandard'

@description('Approved reasoning SKU; defaults to the explicitly selected shared SKU.')
param reasoningDeploymentSku string = modelDeploymentSku

@description('Approved drafting SKU; defaults to the explicitly selected shared SKU.')
param draftingDeploymentSku string = modelDeploymentSku

@description('Approved simulation SKU; defaults to the explicitly selected shared SKU.')
param simulationDeploymentSku string = modelDeploymentSku

// RBAC
@description('Principal IDs to grant Cognitive Services OpenAI User role')
param agentPrincipalIds array = []

// Diagnostics
@description('Log Analytics workspace ID for diagnostic settings')
param logAnalyticsWorkspaceId string

@description('Approved diagnostic log and metric snapshots; omitted fields retain the existing module defaults.')
param diagnosticSettings object = {}

// ────────────────────────────────────────────────────────────────────────────────
// Reference the existing Azure OpenAI account
// ────────────────────────────────────────────────────────────────────────────────

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: openAiAccountName
}

// ────────────────────────────────────────────────────────────────────────────────
// Responsible AI policy (emergency-management domain)
//
// All three model deployments — reasoning, drafting, and simulation — routinely
// process emergency-management vocabulary (bushfire behaviour, escalation,
// casualty projections) that the DefaultV2 content filter scores as
// high-severity violence on the prompt side and blocks before the model can
// respond. We attach a custom policy that raises the Violence threshold from
// the default Medium → High on both Prompt and Completion, while leaving
// Hate / Sexual / SelfHarm / Jailbreak / IndirectAttack at base defaults.
//
// Each deployment gets its own copy of the policy (identical contentFilters)
// so that future per-tier tuning — e.g. relaxing the simulation tier further
// without touching live-incident tiers — is a localised change.
//
// Reference: Microsoft.CognitiveServices/accounts/raiPolicies API 2026-05-01.
// ────────────────────────────────────────────────────────────────────────────────

var emDomainContentFilters = [
  {
    name: 'Violence'
    source: 'Prompt'
    enabled: true
    blocking: true
    severityThreshold: 'High'
    action: 'NONE'
  }
  {
    name: 'Violence'
    source: 'Completion'
    enabled: true
    blocking: true
    severityThreshold: 'High'
    action: 'NONE'
  }
]

var reasoningRaiPolicyName = 'reasoning-em-domain-${envPrefix}'
var draftingRaiPolicyName = 'drafting-em-domain-${envPrefix}'
var simulationRaiPolicyName = 'sim-em-domain-${envPrefix}'

// NOTE: Cognitive Services accounts only allow ONE child operation (deployment
// or RAI policy) at a time. Deploying RAI policies in parallel with
// deployments causes ARM to return "RequestConflict: Another operation is
// being performed on the parent resource". We serialise the full chain:
//   reasoningRaiPolicy → reasoningDeployment
//     → draftingRaiPolicy → draftingDeployment
//     → simulationRaiPolicy → simulationDeployment
//     → embeddingDeployment (existing Microsoft.DefaultV2; serialised on simulationDeployment)

// Preserve the observed wire action exactly; do not assume NONE/None or omission equivalence.
#disable-next-line BCP081
resource reasoningRaiPolicy 'Microsoft.CognitiveServices/accounts/raiPolicies@2026-05-01' = {
  parent: openAiAccount
  name: reasoningRaiPolicyName
  properties: {
    basePolicyName: 'Microsoft.DefaultV2'
    mode: 'Blocking'
    contentFilters: emDomainContentFilters
  }
}

#disable-next-line BCP081
resource draftingRaiPolicy 'Microsoft.CognitiveServices/accounts/raiPolicies@2026-05-01' = {
  parent: openAiAccount
  name: draftingRaiPolicyName
  properties: {
    basePolicyName: 'Microsoft.DefaultV2'
    mode: 'Blocking'
    contentFilters: emDomainContentFilters
  }
  dependsOn: [reasoningDeployment]
}

#disable-next-line BCP081
resource simulationRaiPolicy 'Microsoft.CognitiveServices/accounts/raiPolicies@2026-05-01' = {
  parent: openAiAccount
  name: simulationRaiPolicyName
  properties: {
    basePolicyName: 'Microsoft.DefaultV2'
    mode: 'Blocking'
    contentFilters: emDomainContentFilters
  }
  dependsOn: [draftingDeployment]
}

// ────────────────────────────────────────────────────────────────────────────────
// Model Deployments
// ────────────────────────────────────────────────────────────────────────────────

module reasoningDeployment './cognitive-services-deployment-preservation.bicep' = {
  name: 'reasoning-model-deployment'
  params: {
    accountName: openAiAccountName
    name: reasoningDeploymentName
    sku: {
      name: reasoningDeploymentSku
      capacity: reasoningTpmQuota
    }
    model: {
      format: 'OpenAI'
      name: reasoningModelName
      version: reasoningModelVersion
    }
    raiPolicyName: reasoningRaiPolicy.name
    versionUpgradeOption: reasoningVersionUpgradeOption
    operatingState: deploymentOperatingStates.reasoning
  }
}

module draftingDeployment './cognitive-services-deployment-preservation.bicep' = {
  name: 'drafting-model-deployment'
  params: {
    accountName: openAiAccountName
    name: draftingDeploymentName
    sku: {
      name: draftingDeploymentSku
      capacity: draftingTpmQuota
    }
    model: {
      format: 'OpenAI'
      name: draftingModelName
      version: draftingModelVersion
    }
    raiPolicyName: draftingRaiPolicy.name
    versionUpgradeOption: draftingVersionUpgradeOption
    operatingState: deploymentOperatingStates.drafting
  }
}

// Dedicated deployment for the Simulation Controller (spec 024).
// Preserve its separate existing quota so an exercise cannot starve live agents.
module simulationDeployment './cognitive-services-deployment-preservation.bicep' = {
  name: 'simulation-model-deployment'
  params: {
    accountName: openAiAccountName
    name: simulationDeploymentName
    sku: {
      name: simulationDeploymentSku
      capacity: simulationTpmQuota
    }
    model: {
      format: 'OpenAI'
      name: simulationModelName
      version: simulationModelVersion
    }
    raiPolicyName: simulationRaiPolicy.name
    versionUpgradeOption: simulationVersionUpgradeOption
    operatingState: deploymentOperatingStates.simulation
  }
}

// Spec 036 FR-RAG-IDX-02 — embedding deployment for the corpus ingest pipeline
// (apps/ingest-runner) and runtime hybrid retrieval (apps/agents/common/retrieval_client.py).
// Embedding retains Microsoft.DefaultV2. Serialised behind the simulation
// deployment so all four child operations on the parent Cognitive Services account
// run sequentially (ARM rejects concurrent child ops with RequestConflict).
module embeddingDeployment './cognitive-services-deployment-preservation.bicep' = {
  name: 'embedding-model-deployment'
  params: {
    accountName: openAiAccountName
    name: '${embeddingModelName}-${envPrefix}'
    sku: {
      name: 'Standard'
      capacity: embeddingTpmQuota
    }
    model: {
      format: 'OpenAI'
      name: embeddingModelName
      version: embeddingModelVersion
    }
    raiPolicyName: 'Microsoft.DefaultV2'
    versionUpgradeOption: embeddingVersionUpgradeOption
    operatingState: deploymentOperatingStates.embedding
  }
  dependsOn: [simulationDeployment]
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
    logs: diagnosticSettings.?logs ?? [
      { category: 'RequestResponse', enabled: true }
      { category: 'Audit', enabled: true }
    ]
    metrics: diagnosticSettings.?metrics ?? [
      { category: 'AllMetrics', enabled: true }
    ]
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Outputs
// ────────────────────────────────────────────────────────────────────────────────

output reasoningDeploymentName string = reasoningDeployment.outputs.name
output draftingDeploymentName string = draftingDeployment.outputs.name
output simulationDeploymentName string = simulationDeployment.outputs.name
output embeddingDeploymentName string = embeddingDeployment.outputs.name
output reasoningRaiPolicyName string = reasoningRaiPolicy.name
output draftingRaiPolicyName string = draftingRaiPolicy.name
output simulationRaiPolicyName string = simulationRaiPolicy.name
output openAiEndpoint string = openAiAccount.properties.endpoint

@description('Model-coordinate candidates, including unchanged embedding compatibility.')
var selections = [
  { model: reasoningModelName, version: reasoningModelVersion, deployment: reasoningDeploymentName }
  { model: draftingModelName, version: draftingModelVersion, deployment: draftingDeploymentName }
  { model: simulationModelName, version: simulationModelVersion, deployment: simulationDeploymentName }
  { model: embeddingModelName, version: embeddingModelVersion, deployment: '${embeddingModelName}-${envPrefix}' }
]

@description('Stable tier aliases; preflight rejects collisions with unrelated model coordinates.')
var tierAliases = [
  'reasoning=${reasoningDeploymentName}'
  'drafting=${draftingDeploymentName}'
  'simulation=${simulationDeploymentName}'
]

@description('Only coordinates with exactly one distinct destination remain in the legacy map.')
var legacyCoordinates = flatten(map(selections, selection => [
  { key: '${selection.model}@${selection.version}', deployment: selection.deployment }
  { key: selection.model, deployment: selection.deployment }
]))

@description('Group aliases before rendering, so a shared chat model never silently selects the first tier.')
var coordinateGroups = groupBy(legacyCoordinates, coordinate => coordinate.key)

@description('Unambiguous legacy entries, deduplicated by key and destination.')
var uniqueCoordinates = filter(items(coordinateGroups), entry => length(union(
  map(entry.value, coordinate => coordinate.deployment),
  []
)) == 1)

@description('Reuse identical tier aliases; leave unrelated collisions visible to mandatory preflight validation.')
var distinctCoordinates = filter(uniqueCoordinates, entry => !contains(
  tierAliases,
  '${entry.key}=${first(entry.value)!.deployment}'
))

@description('One compatibility CSV for every application consumer.')
output azureAiProjectDeployments string = join(concat(
  tierAliases,
  map(distinctCoordinates, entry => '${entry.key}=${first(entry.value)!.deployment}')
), ',')

// Spec 036 — embedding model key (`<modelId>@<version>`) consumed by the
// ingest-runner CLI. The carve-out preflight splits on `@` and looks up
// `embeddingModelName` in `infra/parameters/foundry-carveout.yaml`.
output embeddingModelKey string = '${embeddingModelName}@${embeddingModelVersion}'

@description('Reasoning model identity, not a destination alias.')
output reasoningDeploymentModelKey string = '${reasoningModelName}@${reasoningModelVersion}'
@description('Drafting model identity, not a destination alias.')
output draftingDeploymentModelKey string = '${draftingModelName}@${draftingModelVersion}'
@description('Simulation model identity, not a destination alias.')
output simulationDeploymentModelKey string = '${simulationModelName}@${simulationModelVersion}'
