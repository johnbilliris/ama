using '../main.bicep'

// Production needs its own approved profile; Dev observations are not deployment authority here.
var models = json(readEnvironmentVariable('AMA_PRODUCTION_MODEL_PARAMETERS'))
param reasoningModelName = models.reasoningModelName
param reasoningModelVersion = models.reasoningModelVersion
param draftingModelName = models.draftingModelName
param draftingModelVersion = models.draftingModelVersion
param simulationModelName = models.simulationModelName
param simulationModelVersion = models.simulationModelVersion
param reasoningVersionUpgradeOption = models.reasoningVersionUpgradeOption
param draftingVersionUpgradeOption = models.draftingVersionUpgradeOption
param simulationVersionUpgradeOption = models.simulationVersionUpgradeOption
param embeddingVersionUpgradeOption = models.embeddingVersionUpgradeOption
param deploymentOperatingStates = models.deploymentOperatingStates

param subscriptionTopology = 'B'
param environmentName = 'production'
param location = 'australiaeast'
param subscriptionId = 'c8703ebc-bc5d-488d-9489-5883c9fde6c2'
// Merged onto the baseline tags (azd-env-name, project) inside main.bicep.
param additionalTags = {
  environment: 'production'
  workload: 'ama'
  costCenter: 'platform'
  dataClassification: 'sensitive'
  spec: '029'
}
