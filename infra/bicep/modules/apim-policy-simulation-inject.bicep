// Spec 036 — APIM rate-limit policy for `inject-telemetry` (T-A15)
//
// Sets a token-bucket rate limit on the `/api/simulations/*/inject-telemetry`
// route per plan-decision #4:
//   - 60 requests / minute per user
//   - burst tolerance 10 requests / second
//
// In-process FR-009 success-only counting + parse-attempt circuit-breaker
// implements the second-layer enforcement (`apps/api/app/services/simulation`).
//
// References the inline XML policy `apim-policy-simulation-inject.xml`
// embedded below; raw policy text is the canonical artefact.

@description('Existing APIM service name.')
param apimServiceName string

@description('Existing API name (e.g. simulation-api).')
param apiName string = 'simulation-api'

@description('Existing operation name (matches the OpenAPI operationId `injectTelemetry`).')
param operationName string = 'injectTelemetry'

resource apim 'Microsoft.ApiManagement/service@2023-09-01-preview' existing = {
  name: apimServiceName
}

resource simulationApi 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' existing = {
  parent: apim
  name: apiName
}

resource injectOperation 'Microsoft.ApiManagement/service/apis/operations@2023-09-01-preview' existing = {
  parent: simulationApi
  name: operationName
}

resource injectRateLimitPolicy 'Microsoft.ApiManagement/service/apis/operations/policies@2023-09-01-preview' = {
  parent: injectOperation
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: '''
<policies>
  <inbound>
    <base />
    <!-- 60/min/user — FR-009 token budget per plan-decision #4. -->
    <rate-limit-by-key calls="60" renewal-period="60"
                      counter-key="@((string)context.User?.Id ?? context.Request.IpAddress)" />
    <!-- 10 req/sec burst floor (Redis token-bucket). -->
    <rate-limit-by-key calls="10" renewal-period="1"
                      counter-key="@((string)context.User?.Id ?? context.Request.IpAddress)" />
    <set-header name="X-Sim-Inject-Limit" exists-action="override">
      <value>fr-009/inject-telemetry</value>
    </set-header>
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
'''
  }
}
