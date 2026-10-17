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
param reasoningModelName string = 'gpt-5.6'

@description('Reasoning-tier model version')
param reasoningModelVersion string = '2026-03-05'

@description('Drafting-tier model name')
param draftingModelName string = 'gpt-5.6'

@description('Drafting-tier model version')
param draftingModelVersion string = '2026-03-05'

@description('Simulation Controller model name (used by the Simulation chat endpoint).')
param simulationModelName string = 'gpt-5.6'

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
// Reference: Microsoft.CognitiveServices/accounts/raiPolicies API 2024-10-01.
// ────────────────────────────────────────────────────────────────────────────────

var emDomainContentFilters = [
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
//     → embeddingDeployment (no RAI policy; serialised on simulationDeployment)

resource reasoningRaiPolicy 'Microsoft.CognitiveServices/accounts/raiPolicies@2024-10-01' = {
  parent: openAiAccount
  name: reasoningRaiPolicyName
  properties: {
    basePolicyName: 'Microsoft.DefaultV2'
    mode: 'Blocking'
    contentFilters: emDomainContentFilters
  }
}

resource draftingRaiPolicy 'Microsoft.CognitiveServices/accounts/raiPolicies@2024-10-01' = {
  parent: openAiAccount
  name: draftingRaiPolicyName
  properties: {
    basePolicyName: 'Microsoft.DefaultV2'
    mode: 'Blocking'
    contentFilters: emDomainContentFilters
  }
  dependsOn: [reasoningDeployment]
}

resource simulationRaiPolicy 'Microsoft.CognitiveServices/accounts/raiPolicies@2024-10-01' = {
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

resource reasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiAccount
  name: 'gpt-5.6-${envPrefix}'
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
    raiPolicyName: reasoningRaiPolicy.name
  }
}

resource draftingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiAccount
  name: 'gpt-5.6-mini-${envPrefix}'
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
    raiPolicyName: draftingRaiPolicy.name
  }
}

// Dedicated deployment for the Simulation Controller (spec 024).
// GlobalStandard SKU isolates exercise traffic from live-incident reasoning/drafting
// quota so a runaway simulation cannot starve real-incident agents.
resource simulationDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiAccount
  name: 'gpt-5.6-sim-${envPrefix}'
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

// Spec 036 FR-RAG-IDX-02 — embedding deployment for the corpus ingest pipeline
// (apps/ingest-runner) and runtime hybrid retrieval (apps/agents/common/retrieval_client.py).
// Embedding deployments do not require an RAI policy. Serialised behind the simulation
// deployment so all four child operations on the parent Cognitive Services account
// run sequentially (ARM rejects concurrent child ops with RequestConflict).
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiAccount
  name: '${embeddingModelName}-${envPrefix}'
  sku: {
    name: 'Standard'
    capacity: embeddingTpmQuota
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: embeddingModelName
      version: embeddingModelVersion
    }
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
output embeddingDeploymentName string = embeddingDeployment.name
output reasoningRaiPolicyName string = reasoningRaiPolicy.name
output draftingRaiPolicyName string = draftingRaiPolicy.name
output simulationRaiPolicyName string = simulationRaiPolicy.name
output openAiEndpoint string = openAiAccount.properties.endpoint

// Spec 036 / ADR-20 — Foundry deployments CSV consumed by `azure-ai-inference`
// SDK (apps/agents/maf_runtime/chat_client.py + apps/agents/common/llm_client.py +
// apps/api/app/services/simulation/controller_service.py). Format: per-deployment
// `<modelId>@<version>=<deploymentName>`, comma-separated.
//
// Spec 036 FR-RAG-IDX-02 — embedding deployment is included so the ingest-runner
// (apps/ingest-runner) and any future retrieval consumer can resolve
// `<embeddingModelName>@<version>` → live deployment name through the same env
// var (``AZURE_AI_PROJECT_DEPLOYMENTS``) used by the chat seam.
output azureAiProjectDeployments string = '${reasoningModelName}@${reasoningModelVersion}=${reasoningDeployment.name},${draftingModelName}@${draftingModelVersion}=${draftingDeployment.name},${simulationModelName}@${simulationModelVersion}=${simulationDeployment.name},${embeddingModelName}@${embeddingModelVersion}=${embeddingDeployment.name}'

// Spec 036 — embedding model key (`<modelId>@<version>`) consumed by the
// ingest-runner CLI. The carve-out preflight splits on `@` and looks up
// `embeddingModelName` in `infra/parameters/foundry-carveout.yaml`.
output embeddingModelKey string = '${embeddingModelName}@${embeddingModelVersion}'

// Per-tier deployment model-key outputs — the simulation Controller and
// agent llm clients pick the deployment by `<modelName>@<version>` from
// the AZURE_AI_PROJECT_DEPLOYMENTS CSV. Until tiers diverge, all three
// resolve to the same key (gpt-5.6@2026-03-05) — the CSV lookup picks
// the first matching entry, which is the reasoning deployment.
output reasoningDeploymentModelKey string = '${reasoningModelName}@${reasoningModelVersion}'
output draftingDeploymentModelKey string = '${draftingModelName}@${draftingModelVersion}'
output simulationDeploymentModelKey string = '${simulationModelName}@${simulationModelVersion}'
