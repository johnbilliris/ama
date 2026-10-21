using '../main.bicep'

// Spec 029 Topology B: single subscription for all environments.
param subscriptionTopology = 'B'
param environmentName = 'dev'
param location = 'australiaeast'
param subscriptionId = '74a25c57-d6e4-446e-8c99-7f5ace60011b'
// Approved existing Dev aliases are not inferred from model names.
param reasoningDeploymentName = 'gpt-5.4-dev'
param reasoningModelName = 'gpt-5.4'
param reasoningModelVersion = '2026-03-05'
param draftingDeploymentName = 'gpt-5.4-mini-dev'
param draftingModelName = 'gpt-5.4'
param draftingModelVersion = '2026-03-05'
param simulationDeploymentName = 'gpt-5.4-sim-dev'
param simulationModelName = 'gpt-5.4'
param simulationModelVersion = '2026-03-05'
param openAiDeploymentSku = 'GlobalStandard'
param reasoningTpmQuota = 30
param draftingTpmQuota = 60
param simulationTpmQuota = 20
param reasoningVersionUpgradeOption = 'OnceNewDefaultVersionAvailable'
param draftingVersionUpgradeOption = 'OnceNewDefaultVersionAvailable'
param simulationVersionUpgradeOption = 'OnceNewDefaultVersionAvailable'
param embeddingVersionUpgradeOption = 'OnceNewDefaultVersionAvailable'
param deploymentOperatingStates = {
  reasoning: { currentCapacity: 30, deploymentState: 'Running' }
  drafting: { currentCapacity: 60, deploymentState: 'Running' }
  simulation: { currentCapacity: 20, deploymentState: 'Running' }
  embedding: { currentCapacity: 60, deploymentState: 'Running' }
}
param openAiDiagnosticSettings = {
  logs: [
    { category: 'RequestResponse', enabled: true, retentionPolicy: { days: 0, enabled: false } }
    { category: 'Audit', enabled: true, retentionPolicy: { days: 0, enabled: false } }
    { category: 'AzureOpenAIRequestUsage', enabled: false, retentionPolicy: { days: 0, enabled: false } }
    { category: 'Trace', enabled: false, retentionPolicy: { days: 0, enabled: false } }
    { category: 'ManagedNetworkEvent', enabled: false, retentionPolicy: { days: 0, enabled: false } }
  ]
  metrics: [
    { category: 'AllMetrics', enabled: true, retentionPolicy: { days: 0, enabled: false } }
  ]
}
// Merged onto the baseline tags (azd-env-name, project) inside main.bicep.
param additionalTags = {
  environment: 'dev'
  workload: 'ama'
  costCenter: 'platform'
  dataClassification: 'sensitive'
  spec: '029'
}
