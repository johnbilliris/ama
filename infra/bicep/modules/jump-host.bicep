// Spec 029 — Hardened Jump Host (T071)
// Bastion-fronted Windows VM for break-glass production access.
@description('Environment slug.')
param environmentName string
param location string = resourceGroup().location
param tags object = {}

@description('Existing VNet ID for AzureBastionSubnet + management subnet placement.')
param vnetId string

@secure()
@description('Local admin password (rotated each run by the issuance workflow).')
param adminPassword string

var vmName = take('vm-amabh-${environmentName}-${uniqueString(resourceGroup().id)}', 15)

resource bastionPip 'Microsoft.Network/publicIPAddresses@2024-01-01' = {
  name: 'pip-bastion-${environmentName}'
  location: location
  sku: { name: 'Standard' }
  properties: { publicIPAllocationMethod: 'Static' }
  tags: tags
}

resource bastion 'Microsoft.Network/bastionHosts@2024-01-01' = {
  name: 'bastion-${environmentName}'
  location: location
  sku: { name: 'Standard' }
  properties: {
    ipConfigurations: [
      {
        name: 'config'
        properties: {
          subnet: { id: '${vnetId}/subnets/AzureBastionSubnet' }
          publicIPAddress: { id: bastionPip.id }
        }
      }
    ]
  }
  tags: tags
}

resource nic 'Microsoft.Network/networkInterfaces@2024-01-01' = {
  name: 'nic-${vmName}'
  location: location
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig'
        properties: {
          subnet: { id: '${vnetId}/subnets/snet-mgmt' }
          privateIPAllocationMethod: 'Dynamic'
        }
      }
    ]
  }
  tags: tags
}

resource vm 'Microsoft.Compute/virtualMachines@2024-03-01' = {
  name: vmName
  location: location
  tags: union(tags, { spec: '029', purpose: 'jump-host' })
  identity: { type: 'SystemAssigned' }
  properties: {
    hardwareProfile: { vmSize: 'Standard_D2s_v5' }
    storageProfile: {
      imageReference: {
        publisher: 'MicrosoftWindowsServer'
        offer: 'WindowsServer'
        sku: '2022-datacenter-azure-edition-hotpatch'
        version: 'latest'
      }
      osDisk: { createOption: 'FromImage', managedDisk: { storageAccountType: 'Premium_LRS' } }
    }
    osProfile: {
      computerName: vmName
      adminUsername: 'amaadmin'
      adminPassword: adminPassword
      windowsConfiguration: { enableAutomaticUpdates: true, provisionVMAgent: true }
    }
    networkProfile: { networkInterfaces: [ { id: nic.id } ] }
    securityProfile: {
      securityType: 'TrustedLaunch'
      uefiSettings: { secureBootEnabled: true, vTpmEnabled: true }
    }
    diagnosticsProfile: { bootDiagnostics: { enabled: true } }
  }
}

output vmId string = vm.id
output bastionId string = bastion.id
