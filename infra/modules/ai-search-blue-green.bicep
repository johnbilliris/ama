// ────────────────────────────────────────────────────────────────────────────────
// AI Search blue-green wrapper (Spec 036 T048; FR-RAG-IDX-04; R-15)
//
// Wraps the existing ./ai-search.bicep module to provide blue-green index
// alias semantics:
//
//   * One AI Search service (this wrapper does NOT create a second account)
//   * Two paired index slots — currentIndexName + nextIndexName
//   * One alias name → flipped atomically by the ingest-runner Container Apps
//     Job after the 4-signal parity gate (T046) signs off.
//
// **The wrapper does NOT create the indexes themselves.** Indexes are
// data-plane resources created by ``apps/ingest-runner/src/ama_ingest/indexer.py``
// at runtime via the SearchClient SDK (FR-RAG-IDX-03). The wrapper exists so
// the alias name + paired-index slot identifiers are tracked in the IaC graph
// and surfaced as outputs the ingest job consumes via ARM template params.
//
// REUSE NOTE: ``./ai-search.bicep`` is the canonical single AI Search module
// (spec-032 + spec-036 additive params). This wrapper INVOKES it; it does not
// replace it. Callers that need only the AIDR-only spec-032 surface continue
// to use ``./ai-search.bicep`` directly.
// ────────────────────────────────────────────────────────────────────────────────

@description('AI Search service name')
param name string

@description('Azure region (must match ai-search.bicep location)')
param location string

@description('Tags applied to the search service + alert')
param tags object = {}

@description('SKU — Standard for prod, Basic for dev/staging')
@allowed([
  'basic'
  'standard'
])
param sku string = 'standard'

@description('Replica count (default 1)')
param replicaCount int = 1

@description('Partition count (default 1)')
param partitionCount int = 1

@description('Subnet resource ID for Private Endpoint (PE-only is mandatory in production)')
param privateEndpointSubnetId string = ''

@description('Private DNS zone resource ID for privatelink.search.windows.net')
param privateDnsZoneId string = ''

@description('Disable public network access (MUST be true in production — FR-RAG-IDX-06)')
param disablePublicNetworkAccess bool = true

@description('Embedding vector dimension (R-02 — text-embedding-3-large = 3072)')
param vectorDimensions int = 3072

@description('Allowed jurisdiction filter values (FR-RAG-IDX-08)')
param jurisdictionValues array = [
  'act'
  'nsw'
  'nt'
  'qld'
  'sa'
  'tas'
  'vic'
  'wa'
  'national'
  'aidr'
]

@description('Allowed licence_mode filter values (FR-RAG-IDX-02)')
param licenceModeValues array = [
  'full-text'
  'metadata-only'
]

@description('Capacity alert threshold (percent of SKU quota; default 70 per R-10)')
@minValue(50)
@maxValue(95)
param capacityAlertThresholdPercent int = 70

@description('Optional Action Group resource id used by the capacity alert notification')
param capacityActionGroupId string = ''

@description('Whether to deploy the capacity alert (default true)')
param enableCapacityAlert bool = true

// ────────────────────────────────────────────────────────────────────────────────
// Spec 036 T048 — blue-green-specific params
// ────────────────────────────────────────────────────────────────────────────────

@description('Stable alias name retrieval clients dial (e.g. "corpus")')
param aliasName string = 'corpus'

@description('Currently-active index slot the alias points at (e.g. "corpus-v1")')
param currentIndexName string = 'corpus-v1'

@description('Next index slot the ingest-runner writes to during a model swap (e.g. "corpus-v2")')
param nextIndexName string = 'corpus-v2'

@description('How long to retain the previous index after a flip (days; R-15 = 7)')
@minValue(1)
@maxValue(30)
param previousIndexRetentionDays int = 7

@description('Embedding model id stamped on every chunk (R-02; R-05 signal 4 invariant)')
param embeddingModelId string = 'text-embedding-3-large@1'

// ────────────────────────────────────────────────────────────────────────────────
// Underlying AI Search service (delegates to ./ai-search.bicep)
// ────────────────────────────────────────────────────────────────────────────────

module search './ai-search.bicep' = {
  name: 'aiSearch-${name}'
  params: {
    name: name
    location: location
    tags: tags
    sku: sku
    replicaCount: replicaCount
    partitionCount: partitionCount
    privateEndpointSubnetId: privateEndpointSubnetId
    privateDnsZoneId: privateDnsZoneId
    disablePublicNetworkAccess: disablePublicNetworkAccess
    vectorDimensions: vectorDimensions
    jurisdictionValues: jurisdictionValues
    licenceModeValues: licenceModeValues
    capacityAlertThresholdPercent: capacityAlertThresholdPercent
    capacityActionGroupId: capacityActionGroupId
    enableCapacityAlert: enableCapacityAlert
  }
}

// ────────────────────────────────────────────────────────────────────────────────
// Outputs — fed to the ingest-runner Container Apps Job (T050) via env vars.
// The job uses these to:
//   1. Pick the next index slot for blue-green writes.
//   2. Issue the alias flip via SearchIndexClient.create_or_update_alias.
//   3. Schedule the previous-index retention (cleared after R-15 days).
// ────────────────────────────────────────────────────────────────────────────────

output searchServiceId string = search.outputs.searchServiceId
output searchServiceName string = search.outputs.searchServiceName
output searchPrincipalId string = search.outputs.principalId
output aliasName string = aliasName
output currentIndexName string = currentIndexName
output nextIndexName string = nextIndexName
output previousIndexRetentionDays int = previousIndexRetentionDays
output embeddingModelId string = embeddingModelId
output vectorDimensions int = vectorDimensions
output jurisdictionValues array = jurisdictionValues
output licenceModeValues array = licenceModeValues
output capacityAlertThresholdPercent int = capacityAlertThresholdPercent

// Composite "ready to flip" hint — set to true when both slots have a name.
// Real readiness is enforced data-plane-side after the parity gate signs off.
output aliasFlipReady bool = !empty(currentIndexName) && !empty(nextIndexName) && currentIndexName != nextIndexName
