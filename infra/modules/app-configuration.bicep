// =============================================================================
// app-configuration.bicep — spec-035 T011
// =============================================================================
// Provisions an Azure App Configuration store seeded with the spec-035 keys
// from contracts/cultural-safety.contract.md and contracts/rate-limit.policy.md.
//
// Keys provisioned (defaults match the contracts):
//   cultural-safety:default-timeout-seconds            = 90
//   cultural-safety:timeout-override-aws-levels        = ["emergency_warning"]
//   rate-limit:perPersonaRoute:perMinute               = 10
//   rate-limit:perPersonaRoute:perHour                 = 600
//   rate-limit:global:perMinute                        = 600
//   offline:queueCap                                   = 500
//   offline:lifeSafetyBatchSize                        = 50
//   recovery:signing-key-rotation-days                 = 90
//
// AVM dep: br/public:avm/res/app-configuration/configuration-store
// =============================================================================

targetScope = 'resourceGroup'

@description('Azure region for the App Configuration store.')
param location string

@description('Environment-specific resource naming prefix (CAF).')
param envPrefix string

@description('Tags applied to every deployed resource.')
param tags object = {}

@description('Per-(persona_id, route) per-minute rate-limit ceiling.')
@minValue(1)
param perPersonaRoutePerMinute int = 10

@description('Per-(persona_id, route) per-hour quota ceiling.')
@minValue(1)
param perPersonaRoutePerHour int = 600

@description('Global API per-minute ceiling.')
@minValue(1)
param globalPerMinute int = 600

@description('Cultural-safety default timeout (seconds).')
@minValue(1)
param culturalSafetyDefaultTimeoutSeconds int = 90

@description('Service-Worker offline queue cap per persona.')
@minValue(1)
param offlineQueueCap int = 500

@description('Service-Worker life-safety batch size during replay.')
@minValue(1)
param offlineLifeSafetyBatchSize int = 50

@description('Recovery signing-key rotation interval (days).')
@minValue(1)
param recoverySigningKeyRotationDays int = 90

var storeName = take('appcs-${envPrefix}-${uniqueString(resourceGroup().id, envPrefix)}', 50)

module appConfig 'br/public:avm/res/app-configuration/configuration-store:0.9.3' = {
  name: take('appcs-${envPrefix}', 64)
  params: {
    name: storeName
    location: location
    sku: 'Standard'
    tags: tags
    enablePurgeProtection: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Disabled'
    disableLocalAuth: true
    enableTelemetry: false
    managedIdentities: {
      systemAssigned: true
    }
    keyValues: [
      {
        name: 'cultural-safety:default-timeout-seconds'
        value: string(culturalSafetyDefaultTimeoutSeconds)
        contentType: 'application/json'
      }
      {
        name: 'cultural-safety:timeout-override-aws-levels'
        value: '["emergency_warning"]'
        contentType: 'application/json'
      }
      {
        name: 'rate-limit:perPersonaRoute:perMinute'
        value: string(perPersonaRoutePerMinute)
        contentType: 'application/json'
      }
      {
        name: 'rate-limit:perPersonaRoute:perHour'
        value: string(perPersonaRoutePerHour)
        contentType: 'application/json'
      }
      {
        name: 'rate-limit:global:perMinute'
        value: string(globalPerMinute)
        contentType: 'application/json'
      }
      {
        name: 'offline:queueCap'
        value: string(offlineQueueCap)
        contentType: 'application/json'
      }
      {
        name: 'offline:lifeSafetyBatchSize'
        value: string(offlineLifeSafetyBatchSize)
        contentType: 'application/json'
      }
      {
        name: 'recovery:signing-key-rotation-days'
        value: string(recoverySigningKeyRotationDays)
        contentType: 'application/json'
      }
    ]
  }
}

@description('Resource id of the App Configuration store.')
output appConfigStoreId string = appConfig.outputs.resourceId

@description('Endpoint of the App Configuration store.')
output appConfigStoreEndpoint string = appConfig.outputs.endpoint

@description('Name of the App Configuration store.')
output appConfigStoreName string = storeName
