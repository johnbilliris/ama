using '../main.bicep'

// Spec 029 Topology B: single subscription for all environments.
param subscriptionTopology = 'B'
param environmentName = 'dev'
param location = 'australiaeast'
param subscriptionId = 'c8703ebc-bc5d-488d-9489-5883c9fde6c2'
// Merged onto the baseline tags (azd-env-name, project) inside main.bicep.
param additionalTags = {
  environment: 'dev'
  workload: 'ama'
  costCenter: 'platform'
  dataClassification: 'sensitive'
  spec: '029'
}
