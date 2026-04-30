// ────────────────────────────────────────────────────────────────────────────────
// Azure IoT Hub + Event Grid subscription — FR-016/017/018
// ────────────────────────────────────────────────────────────────────────────────

@description('IoT Hub name')
param iotHubName string

@description('Location — restricted to Australian regions')
@allowed(['australiaeast', 'australiasoutheast'])
param location string

@description('Resource tags')
param tags object

@description('IoT Hub SKU')
@allowed(['S1', 'S2', 'S3'])
param skuName string = 'S1'

@description('IoT Hub SKU capacity (units)')
@minValue(1)
param skuCapacity int = 1

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

@description('Event Grid webhook endpoint for telemetry events')
param eventGridWebhookEndpoint string = ''

// ── IoT Hub ───────────────────────────────────────────────────────────────────

resource iotHub 'Microsoft.Devices/IotHubs@2023-06-30' = {
  name: iotHubName
  location: location
  tags: tags
  sku: {
    name: skuName
    capacity: skuCapacity
  }
  properties: {
    minTlsVersion: '1.2'
    publicNetworkAccess: 'Disabled'
    disableLocalAuth: true
    features: 'None'
    routing: {
      routes: [
        {
          name: 'telemetry-to-events'
          source: 'DeviceMessages'
          condition: 'true'
          endpointNames: [
            'events'
          ]
          isEnabled: true
        }
      ]
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// ── Event Grid System Topic ───────────────────────────────────────────────────

resource eventGridTopic 'Microsoft.EventGrid/systemTopics@2024-06-01-preview' = {
  name: '${iotHubName}-events'
  location: location
  tags: tags
  // PSRule: Azure.EventGrid.ManagedIdentity — system-assigned MI for outbound auth.
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    source: iotHub.id
    topicType: 'Microsoft.Devices.IoTHubs'
  }
}

// ── Event Grid Subscription (webhook to monitoring agent) ─────────────────────

resource eventGridSubscription 'Microsoft.EventGrid/systemTopics/eventSubscriptions@2024-06-01-preview' =
  if (!empty(eventGridWebhookEndpoint)) {
    name: 'telemetry-to-monitoring'
    parent: eventGridTopic
    properties: {
      destination: {
        endpointType: 'WebHook'
        properties: {
          endpointUrl: eventGridWebhookEndpoint
        }
      }
      filter: {
        includedEventTypes: [
          'Microsoft.Devices.DeviceTelemetry'
        ]
      }
      retryPolicy: {
        maxDeliveryAttempts: 10
        eventTimeToLiveInMinutes: 1440
      }
    }
  }

// ── Diagnostics ───────────────────────────────────────────────────────────────

resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' =
  if (!empty(logAnalyticsWorkspaceId)) {
    name: '${iotHubName}-diag'
    scope: iotHub
    properties: {
      workspaceId: logAnalyticsWorkspaceId
      logs: [
        {
          categoryGroup: 'allLogs'
          enabled: true
        }
      ]
      metrics: [
        {
          category: 'AllMetrics'
          enabled: true
        }
      ]
    }
  }

// ── Outputs ───────────────────────────────────────────────────────────────────

@description('IoT Hub resource ID')
output resourceId string = iotHub.id

@description('IoT Hub resource name')
output resourceName string = iotHub.name

@description('IoT Hub hostname')
output hostname string = iotHub.properties.hostName

@description('IoT Hub system-assigned principal ID')
output principalId string = iotHub.identity.principalId

@description('Event Grid system topic ID')
output eventGridTopicId string = eventGridTopic.id
