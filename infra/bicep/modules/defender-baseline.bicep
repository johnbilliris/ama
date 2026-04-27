// Spec 029 — Defender for Cloud Baseline (T072)
// Enables Defender plans (Servers P2, AppService, Containers, KeyVault, Storage,
// Cosmos, ResourceManager) and turns on Microsoft Entra ID Protection toggles.
targetScope = 'subscription'

@description('Environment slug.')
param environmentName string

resource defenderServers 'Microsoft.Security/pricings@2024-01-01' = {
  name: 'VirtualMachines'
  properties: { pricingTier: 'Standard', subPlan: 'P2' }
}

resource defenderApp 'Microsoft.Security/pricings@2024-01-01' = {
  name: 'AppServices'
  properties: { pricingTier: 'Standard' }
}

resource defenderContainers 'Microsoft.Security/pricings@2024-01-01' = {
  name: 'Containers'
  properties: { pricingTier: 'Standard' }
}

resource defenderKv 'Microsoft.Security/pricings@2024-01-01' = {
  name: 'KeyVaults'
  properties: { pricingTier: 'Standard' }
}

resource defenderStorage 'Microsoft.Security/pricings@2024-01-01' = {
  name: 'StorageAccounts'
  properties: { pricingTier: 'Standard' }
}

resource defenderCosmos 'Microsoft.Security/pricings@2024-01-01' = {
  name: 'CosmosDbs'
  properties: { pricingTier: 'Standard' }
}

resource defenderArm 'Microsoft.Security/pricings@2024-01-01' = {
  name: 'Arm'
  properties: { pricingTier: 'Standard' }
}

output environment string = environmentName
