// ────────────────────────────────────────────────────────────────────────────────
// Microsoft Sentinel onto an existing Log Analytics workspace
// (spec-032 T408, FR-S04). Includes 2 priority analytics rules per the
// Top-5 must-land split (KeyVaultAnomalousAccess, CosmosFirewallChange).
// ────────────────────────────────────────────────────────────────────────────────

@description('Log Analytics workspace name (Sentinel attaches here)')
param workspaceName string

@description('Workspace location')
param location string

@description('Tags')
param tags object = {}

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: workspaceName
}

// Enable Sentinel via the SecurityInsights solution
resource sentinelSolution 'Microsoft.OperationsManagement/solutions@2015-11-01-preview' = {
  name: 'SecurityInsights(${workspaceName})'
  location: location
  tags: tags
  plan: {
    name: 'SecurityInsights(${workspaceName})'
    publisher: 'Microsoft'
    product: 'OMSGallery/SecurityInsights'
    promotionCode: ''
  }
  properties: {
    workspaceResourceId: workspace.id
  }
}

// Analytics rule 1: anomalous Key Vault access patterns
resource ruleKeyVaultAnomalous 'Microsoft.SecurityInsights/alertRules@2024-09-01' = {
  scope: workspace
  name: 'KeyVaultAnomalousAccess'
  kind: 'Scheduled'
  dependsOn: [
    sentinelSolution
  ]
  properties: {
    displayName: 'Key Vault — anomalous access pattern'
    description: 'Detects unusual access patterns to Key Vault (high request rate, denied requests, or unusual identities). Spec-032 FR-S04 must-land.'
    severity: 'High'
    enabled: true
    query: '''
AzureDiagnostics
| where ResourceType == "VAULTS"
| where OperationName in ("VaultGet", "SecretGet", "KeyGet", "KeyWrap", "KeyUnwrap")
| summarize requests = count(), denied = countif(ResultType != "Success") by identity_claim_oid_g, bin(TimeGenerated, 5m)
| where requests > 50 or denied > 5
'''
    queryFrequency: 'PT15M'
    queryPeriod: 'PT1H'
    triggerOperator: 'GreaterThan'
    triggerThreshold: 0
    suppressionDuration: 'PT1H'
    suppressionEnabled: false
    tactics: [
      'CredentialAccess'
      'PrivilegeEscalation'
    ]
  }
}

// Analytics rule 2: Cosmos firewall configuration change
resource ruleCosmosFirewall 'Microsoft.SecurityInsights/alertRules@2024-09-01' = {
  scope: workspace
  name: 'CosmosFirewallChange'
  kind: 'Scheduled'
  dependsOn: [
    sentinelSolution
  ]
  properties: {
    displayName: 'Cosmos DB — firewall or PE configuration change'
    description: 'Detects updates to Cosmos networkAcl, firewall, or Private Endpoint configuration. Spec-032 FR-S04 must-land + FR-S01.'
    severity: 'High'
    enabled: true
    query: '''
AzureActivity
| where ResourceProvider == "Microsoft.DocumentDB"
| where OperationNameValue has_any ("UPDATE", "WRITE")
| where Properties has_any ("ipRules", "virtualNetworkRules", "publicNetworkAccess", "privateEndpoint")
| project TimeGenerated, Caller, ResourceId, OperationNameValue, ActivityStatusValue
'''
    queryFrequency: 'PT5M'
    queryPeriod: 'PT15M'
    triggerOperator: 'GreaterThan'
    triggerThreshold: 0
    suppressionDuration: 'PT30M'
    suppressionEnabled: false
    tactics: [
      'DefenseEvasion'
      'Persistence'
    ]
  }
}

output workspaceId string = workspace.id
output sentinelEnabled bool = true
