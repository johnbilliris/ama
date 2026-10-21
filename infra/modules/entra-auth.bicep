extension 'br:mcr.microsoft.com/bicep/extensions/microsoftgraph/v1.0:1.0.0'

@description('Deployment environment name used to create tenant-unique application registrations.')
param environmentName string

@description('Stable suffix shared by the workload resources in this environment.')
param uniqueSuffix string

@description('Allowed single-page application redirect URIs.')
param spaRedirectUris array

var applicationSuffix = '${environmentName}-${take(uniqueSuffix, 6)}'
var apiAudience = 'api://ama-api-${applicationSuffix}'
var delegatedPermissionValue = 'access_as_user'
var delegatedPermissionId = guid('ama-api-delegated-permission', delegatedPermissionValue)
var appRoles = [
  { value: 'incident-commander', displayName: 'Incident Commander' }
  { value: 'planning-officer', displayName: 'Planning Officer' }
  { value: 'operations-officer', displayName: 'Operations Officer' }
  { value: 'logistics-officer', displayName: 'Logistics Officer' }
  { value: 'public-information-officer', displayName: 'Public Information Officer' }
  { value: 'field-coordinator', displayName: 'Field Coordinator' }
  { value: 'observer-auditor', displayName: 'Observer Auditor' }
  { value: 'risk-manager', displayName: 'Risk Manager' }
  { value: 'resilience-planner', displayName: 'Resilience Planner' }
  { value: 'executive-leader', displayName: 'Executive Leader' }
  { value: 'system-administrator', displayName: 'System Administrator' }
]

// No AVM exists for Microsoft Graph resources. Raw Graph Bicep was approved on 2026-09-30.
resource apiApplication 'Microsoft.Graph/applications@v1.0' = {
  displayName: 'AMA API (${environmentName})'
  uniqueName: 'ama-api-${applicationSuffix}'
  signInAudience: 'AzureADMyOrg'
  identifierUris: [
    apiAudience
  ]
  api: {
    requestedAccessTokenVersion: 2
    oauth2PermissionScopes: [
      {
        id: delegatedPermissionId
        adminConsentDisplayName: 'Access the AMA API'
        adminConsentDescription: 'Allows the AMA web application to access the AMA API for the signed-in operator.'
        userConsentDisplayName: 'Access the AMA API'
        userConsentDescription: 'Allows this application to access the AMA API on your behalf.'
        value: delegatedPermissionValue
        type: 'User'
        isEnabled: true
      }
    ]
  }
  appRoles: [
    for role in appRoles: {
      id: guid('ama-api-app-role', role.value)
      displayName: role.displayName
      description: 'Grants the ${role.displayName} authorization boundary in AMA.'
      value: role.value
      allowedMemberTypes: [
        'User'
      ]
      isEnabled: true
    }
  ]
  tags: [
    'azd'
    'ama'
    environmentName
  ]
}

resource apiServicePrincipal 'Microsoft.Graph/servicePrincipals@v1.0' = {
  appId: apiApplication.appId
  displayName: apiApplication.displayName
  appRoleAssignmentRequired: false
  tags: [
    'WindowsAzureActiveDirectoryIntegratedApp'
  ]
}

resource spaApplication 'Microsoft.Graph/applications@v1.0' = {
  displayName: 'AMA Web (${environmentName})'
  uniqueName: 'ama-web-${applicationSuffix}'
  signInAudience: 'AzureADMyOrg'
  spa: {
    redirectUris: spaRedirectUris
  }
  requiredResourceAccess: [
    {
      resourceAppId: apiApplication.appId
      resourceAccess: [
        {
          id: delegatedPermissionId
          type: 'Scope'
        }
      ]
    }
  ]
  tags: [
    'azd'
    'ama'
    environmentName
  ]
}

resource spaServicePrincipal 'Microsoft.Graph/servicePrincipals@v1.0' = {
  appId: spaApplication.appId
  displayName: spaApplication.displayName
  appRoleAssignmentRequired: false
  tags: [
    'WindowsAzureActiveDirectoryIntegratedApp'
  ]
}

@description('Application client ID for the AMA API registration.')
output apiApplicationId string = apiApplication.appId

@description('Audience URI accepted by the AMA API token validator.')
output apiAudience string = apiAudience

@description('Object ID for the AMA API enterprise application.')
output apiServicePrincipalId string = apiServicePrincipal.id

@description('Delegated scope requested by the AMA single-page application.')
output delegatedScope string = '${apiAudience}/${delegatedPermissionValue}'

@description('Application client ID for the AMA web SPA registration.')
output spaApplicationId string = spaApplication.appId

@description('Object ID for the AMA web enterprise application.')
output spaServicePrincipalId string = spaServicePrincipal.id
