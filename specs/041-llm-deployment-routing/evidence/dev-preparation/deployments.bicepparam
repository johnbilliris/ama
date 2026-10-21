using '../../../../infra/modules/azure-openai.bicep'

param openAiAccountName = 'cog-dev-w3uq6w'
param location = 'australiaeast'
param envPrefix = 'dev'
param tags = {}
param logAnalyticsWorkspaceId = '/subscriptions/74a25c57-d6e4-446e-8c99-7f5ace60011b/resourceGroups/ama/providers/Microsoft.OperationalInsights/workspaces/log-dev'
param reasoningDeploymentName = 'gpt-5.4-dev'
param reasoningModelName = 'gpt-5.4'
param reasoningModelVersion = '2026-03-05'
param draftingDeploymentName = 'gpt-5.4-mini-dev'
param draftingModelName = 'gpt-5.4'
param draftingModelVersion = '2026-03-05'
param simulationDeploymentName = 'gpt-5.4-sim-dev'
param simulationModelName = 'gpt-5.4'
param simulationModelVersion = '2026-03-05'
param modelDeploymentSku = 'GlobalStandard'
param reasoningTpmQuota = 30
param draftingTpmQuota = 60
param simulationTpmQuota = 20
param embeddingModelName = 'text-embedding-3-large'
param embeddingModelVersion = '1'
param embeddingTpmQuota = 60
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
param diagnosticSettings = {
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
