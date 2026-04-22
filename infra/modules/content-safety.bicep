// ────────────────────────────────────────────────────────────────────────────────
// Azure AI Content Safety — FR-007 compliance
// ────────────────────────────────────────────────────────────────────────────────

@description('Name of the Content Safety resource')
param contentSafetyName string

@description('Location — restricted to Australian regions')
@allowed(['australiaeast', 'australiasoutheast'])
param location string

@description('Resource tags')
param tags object

@description('SKU for Content Safety')
@allowed(['S0'])
param skuName string = 'S0'

@description('Principal IDs to grant Cognitive Services User role')
param cognitiveServicesUserPrincipalIds array = []

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

// ── Resource ──────────────────────────────────────────────────────────────────

resource contentSafety 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: contentSafetyName
  location: location
  tags: tags
  kind: 'ContentSafety'
  sku: {
    name: skuName
  }
  properties: {
    customSubDomainName: contentSafetyName
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
    }
    disableLocalAuth: true
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// ── RBAC: Cognitive Services User ─────────────────────────────────────────────

@description('Cognitive Services User role definition ID')
var cognitiveServicesUserRoleId = 'a97b65f3-24c7-4388-baec-2e87135dc908'

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for (principalId, i) in cognitiveServicesUserPrincipalIds: {
    name: guid(contentSafety.id, principalId, cognitiveServicesUserRoleId)
    scope: contentSafety
    properties: {
      roleDefinitionId: subscriptionResourceId(
        'Microsoft.Authorization/roleDefinitions',
        cognitiveServicesUserRoleId
      )
      principalId: principalId
      principalType: 'ServicePrincipal'
    }
  }
]

// ── Diagnostics ───────────────────────────────────────────────────────────────

resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' =
  if (!empty(logAnalyticsWorkspaceId)) {
    name: '${contentSafetyName}-diag'
    scope: contentSafety
    properties: {
      workspaceId: logAnalyticsWorkspaceId
      logs: [
        {
          categoryGroup: 'allLogs'
          enabled: true
        }
      ]
      metrics: [
        {
          category: 'AllMetrics'
          enabled: true
        }
      ]
    }
  }

// ── Outputs ───────────────────────────────────────────────────────────────────

@description('Content Safety resource ID')
output resourceId string = contentSafety.id

@description('Content Safety resource name')
output resourceName string = contentSafety.name

@description('Content Safety endpoint URL')
output endpoint string = contentSafety.properties.endpoint

@description('Content Safety system-assigned principal ID')
output principalId string = contentSafety.identity.principalId
