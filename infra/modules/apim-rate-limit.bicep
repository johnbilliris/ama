// =============================================================================
// apim-rate-limit.bicep — spec-035 T009
// =============================================================================
// Composes Azure API Management with the Q3 rate-limit policy from
// specs/035-webapp-capstone-closure/contracts/rate-limit.policy.md.
//
// Rate-limit budgets (App Configuration-driven; defaults per contract):
//   Per-(persona_id, route): 10 req / 60 s + 600 req / 1 h
//   Global ceiling:           600 req / 60 s
//
// AVM dep: br/public:avm/res/api-management/service (host) + a global
// policy fragment composing the Q3 inbound <rate-limit-by-key> /
// <quota-by-key> / <rate-limit> trio. Counter keys derive from the
// X-Persona-Id request header and the APIM operation name.
// =============================================================================

targetScope = 'resourceGroup'

@description('Location for the APIM service.')
param location string

@description('Environment-specific resource naming prefix (CAF: e.g. dev, prd).')
param envPrefix string

@description('Tags applied to every deployed resource.')
param tags object = {}

@description('APIM publisher email (placeholder; override per environment).')
param publisherEmail string = 'ops@example.com'

@description('APIM publisher organisation name.')
param publisherName string = 'AMA Disaster Response Hub'

@description('Per-(persona_id, route) per-minute rate-limit (App Config: rate-limit:perPersonaRoute:perMinute).')
@minValue(1)
@maxValue(10000)
param perPersonaRoutePerMinute int = 10

@description('Per-(persona_id, route) per-hour quota (App Config: rate-limit:perPersonaRoute:perHour).')
@minValue(1)
@maxValue(100000)
param perPersonaRoutePerHour int = 600

@description('Global API ceiling per minute (CI-protective; App Config: rate-limit:global:perMinute).')
@minValue(1)
@maxValue(100000)
param globalPerMinute int = 600

@description('SKU for APIM. StandardV2 recommended for production parity; Developer for dev.')
@allowed([
  'Developer'
  'Basic'
  'Standard'
  'StandardV2'
  'Premium'
])
param skuName string = 'StandardV2'

@minValue(1)
@maxValue(10)
@description('SKU capacity units.')
param skuCapacity int = 1

var apimName = take('apim-${envPrefix}', 50)

// AVM composition: API Management service host. The AVM module enforces
// system-assigned managed identity, TLS 1.2 minimum, public-network-access
// disabled where supported, and emits diagnostic settings to Log Analytics
// when workspaceResourceId is supplied.
module apimHost 'br/public:avm/res/api-management/service:0.14.1' = {
  name: take('apim-host-${envPrefix}', 64)
  params: {
    name: apimName
    location: location
    publisherEmail: publisherEmail
    publisherName: publisherName
    sku: skuName
    skuCapacity: skuCapacity
    tags: tags
    managedIdentities: {
      systemAssigned: true
    }
    minApiVersion: '2021-08-01'
    enableTelemetry: false
  }
}

// =============================================================================
// Global inbound policy implementing the Q3 rate-limit trio.
// =============================================================================
//
// The XML must be inlined as a string parameter consumed by the
// Microsoft.ApiManagement/service/policies child resource. Counter keys are
// composed from the X-Persona-Id request header and operation name.
// =============================================================================
var globalPolicyXml = '''<policies>
  <inbound>
    <base />
    <set-variable name="perPersonaRoutePerMinute" value="@PER_MINUTE@" />
    <set-variable name="perPersonaRoutePerHour" value="@PER_HOUR@" />
    <set-variable name="globalPerMinute" value="@GLOBAL_PER_MINUTE@" />
    <rate-limit-by-key
        calls="@PER_MINUTE@"
        renewal-period="60"
        counter-key="@(context.Subscription.Id + ':' + context.Request.Headers.GetValueOrDefault('X-Persona-Id', '') + ':' + context.Operation.Name)" />
    <quota-by-key
        calls="@PER_HOUR@"
        renewal-period="3600"
        counter-key="@(context.Subscription.Id + ':' + context.Request.Headers.GetValueOrDefault('X-Persona-Id', '') + ':' + context.Operation.Name + ':hour')" />
    <rate-limit calls="@GLOBAL_PER_MINUTE@" renewal-period="60" />
    <on-error>
      <set-header name="X-Rate-Limit-Triggered" exists-action="override">
        <value>true</value>
      </set-header>
    </on-error>
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>'''

var globalPolicyHydrated = replace(replace(replace(globalPolicyXml, '@PER_MINUTE@', string(perPersonaRoutePerMinute)), '@PER_HOUR@', string(perPersonaRoutePerHour)), '@GLOBAL_PER_MINUTE@', string(globalPerMinute))

resource apimRef 'Microsoft.ApiManagement/service@2023-09-01-preview' existing = {
  name: apimName
  dependsOn: [apimHost]
}

resource ratelimitPolicy 'Microsoft.ApiManagement/service/policies@2023-09-01-preview' = {
  parent: apimRef
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: globalPolicyHydrated
  }
}

@description('Resource id of the APIM service.')
output apimResourceId string = apimHost.outputs.resourceId

@description('Name of the APIM service.')
output apimName string = apimName

@description('Hydrated policy XML, exported for unit-test verification.')
output policyXml string = globalPolicyHydrated
