using '../main.bicep'

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
