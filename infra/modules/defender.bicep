// ────────────────────────────────────────────────────────────────────────────────
// Defender for Cloud — enable Standard tier on key resource types
// (spec-032 T407, FR-S04).
// ────────────────────────────────────────────────────────────────────────────────

targetScope = 'subscription'

@description('Resource types to enable Defender Standard for')
param pricingPlans array = [
  'CloudPosture'
  'KeyVaults'
  'StorageAccounts'
  'CosmosDbs'
  'ContainerRegistry'
  'Containers'
  'AppServices'
  'OpenSourceRelationalDatabases'
  'AI'
]

resource pricings 'Microsoft.Security/pricings@2024-01-01' = [for plan in pricingPlans: {
  name: plan
  properties: {
    pricingTier: 'Standard'
  }
}]

output enabled array = [for (plan, i) in pricingPlans: {
  name: plan
  id: pricings[i].id
}]
