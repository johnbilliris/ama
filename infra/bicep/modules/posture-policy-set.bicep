// Spec 029 — Posture Policy Set (T019)
// Generates an Azure Policy Initiative whose member assignments enforce the
// posture-matrix.yaml contract at the subscription / management-group scope.
//
// NOTE: This module deliberately keeps the policy *definitions* declarative so
// that the same source-of-truth (posture-matrix.yaml) drives both the OPA
// pre-merge gate and the runtime initiative.
targetScope = 'subscription'

@description('Environment slug — used as policy assignment display-name suffix.')
param environmentName string

@description('Subscription topology (A: per-env subs, B: shared sub).')
@allowed([ 'A', 'B' ])
param subscriptionTopology string = 'B'

@description('Tags propagated onto the assignment metadata.')
param tags object = {}

var initiativeName = 'ama-spec029-posture-${environmentName}'

resource initiative 'Microsoft.Authorization/policySetDefinitions@2023-04-01' = {
  name: initiativeName
  properties: {
    displayName: 'AMA Spec 029 — Posture matrix (${environmentName})'
    description: 'Locked-down storage / Cosmos / Key Vault / app baseline derived from infra/policy/posture-matrix.yaml.'
    policyType: 'Custom'
    metadata: {
      category: 'AMA Platform Hardening'
      version: '1.0.0'
      spec: '029'
      topology: subscriptionTopology
    }
    policyDefinitions: [
      {
        policyDefinitionId: '/providers/Microsoft.Authorization/policyDefinitions/34c877ad-507e-4c82-993e-3452a6e0ad3c'
        parameters: {
          effect: { value: environmentName == 'dev' ? 'Audit' : 'Deny' }
        }
      }
      {
        policyDefinitionId: '/providers/Microsoft.Authorization/policyDefinitions/0a9795e7-2ed9-49e9-ade8-49a1d2ad8c69'
        parameters: {
          effect: { value: environmentName == 'dev' ? 'Audit' : 'Deny' }
        }
      }
      {
        policyDefinitionId: '/providers/Microsoft.Authorization/policyDefinitions/8c6e48be-a08b-4a3a-9a55-de5fb5e4ff93'
        parameters: {
          effect: { value: 'Audit' }
        }
      }
    ]
  }
}

resource assignment 'Microsoft.Authorization/policyAssignments@2023-04-01' = {
  name: 'assn-${initiativeName}'
  location: 'australiaeast'
  identity: { type: 'SystemAssigned' }
  properties: {
    displayName: 'AMA Spec 029 — Posture (${environmentName})'
    policyDefinitionId: initiative.id
    enforcementMode: environmentName == 'dev' ? 'DoNotEnforce' : 'Default'
    metadata: union(tags, { spec: '029', topology: subscriptionTopology })
  }
}

output initiativeId string = initiative.id
output assignmentId string = assignment.id
