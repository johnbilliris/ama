# Contract: Azure OpenAI Bicep Module

**Feature**: 014-azure-openai-integration
**Module**: `infra/modules/azure-openai.bicep` (NEW) + `infra/main.bicep` (MODIFY)
**Date**: 2026-04-16

## Overview

A dedicated Bicep module that provisions Azure OpenAI model deployments, RBAC role assignments, and diagnostic settings. The Azure OpenAI resource itself remains in `main.bicep` (existing, line 379). This module is called from `main.bicep` after the resource is created.

## Module: `infra/modules/azure-openai.bicep`

### Parameters

```bicep
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
param reasoningModelName string = 'gpt-4o'

@description('Reasoning-tier model version')
param reasoningModelVersion string = '2024-08-06'

@description('Drafting-tier model name')
param draftingModelName string = 'gpt-4o-mini'

@description('Drafting-tier model version')
param draftingModelVersion string = '2024-07-18'

// TPM quotas (in thousands)
@description('Reasoning-tier TPM quota (K). Dev=30, Prod=120')
@minValue(1)
param reasoningTpmQuota int = 30

@description('Drafting-tier TPM quota (K). Dev=60, Prod=240')
@minValue(1)
param draftingTpmQuota int = 60

// RBAC
@description('Principal IDs to grant Cognitive Services OpenAI User role')
param agentPrincipalIds array = []

// Diagnostics
@description('Log Analytics workspace ID for diagnostic settings')
param logAnalyticsWorkspaceId string
```

### Resources Created

#### 1. Model Deployments

```bicep
resource reasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiAccount
  name: 'gpt-4o-${envPrefix}'
  sku: { name: 'Standard', capacity: reasoningTpmQuota }
  properties: {
    model: {
      format: 'OpenAI'
      name: reasoningModelName
      version: reasoningModelVersion
    }
  }
}

resource draftingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiAccount
  name: 'gpt-4o-mini-${envPrefix}'
  sku: { name: 'Standard', capacity: draftingTpmQuota }
  properties: {
    model: {
      format: 'OpenAI'
      name: draftingModelName
      version: draftingModelVersion
    }
  }
  dependsOn: [reasoningDeployment]  // Serial deployment to avoid conflicts
}
```

#### 2. RBAC Role Assignments

```bicep
// Role: Cognitive Services OpenAI User
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
```

#### 3. Diagnostic Settings

```bicep
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
```

### Outputs

```bicep
output reasoningDeploymentName string = reasoningDeployment.name
output draftingDeploymentName string = draftingDeployment.name
output openAiEndpoint string = openAiAccount.properties.endpoint
```

## Changes to `infra/main.bicep`

### 1. Disable Local Auth (API Keys)

```bicep
// BEFORE (line 389):
properties: {
  customSubDomainName: '...'
  publicNetworkAccess: 'Enabled'
  disableLocalAuth: false           // ← CHANGE THIS
}

// AFTER:
properties: {
  customSubDomainName: '...'
  publicNetworkAccess: 'Enabled'
  disableLocalAuth: true            // ← Managed identity only (FR-004)
}
```

### 2. Add Module Reference

```bicep
module openAiDeployments './modules/azure-openai.bicep' = {
  name: 'azure-openai-deployments'
  params: {
    openAiAccountName: openAi.name
    location: location
    envPrefix: environmentName
    tags: tags
    reasoningTpmQuota: 30        // Override for prod: 120
    draftingTpmQuota: 60         // Override for prod: 240
    agentPrincipalIds: [
      apiContainerApp.identity.principalId
      agentsContainerApp.identity.principalId
    ]
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsId
  }
}
```

### 3. Add Deployment Name Env Vars to Container Apps

Add to both `apiContainerApp` and `agentsContainerApp` env arrays:

```bicep
{ name: 'AZURE_OPENAI_REASONING_DEPLOYMENT', value: openAiDeployments.outputs.reasoningDeploymentName }
{ name: 'AZURE_OPENAI_DRAFTING_DEPLOYMENT', value: openAiDeployments.outputs.draftingDeploymentName }
```

### 4. Remove API Key Env Var

Remove any `AZURE_OPENAI_API_KEY` entries from Container App env var arrays (if present in future iterations).

## Conventions Followed

| Convention | Source | Applied |
|-----------|--------|---------|
| `param location string` | All existing modules | ✅ |
| `param envPrefix string` | All existing modules | ✅ |
| `param tags object` | All existing modules | ✅ |
| `Microsoft.Authorization/roleAssignments@2022-04-01` | `communication-agent.bicep:266` | ✅ |
| `guid()` for role assignment names | `communication-agent.bicep:267` | ✅ |
| `Microsoft.Insights/diagnosticSettings@2021-05-01-preview` | `main.bicep:695` | ✅ |
| `take()` for name length limits | `monitoring.bicep:22` | ✅ (where applicable) |
