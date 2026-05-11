// ────────────────────────────────────────────────────────────────────────────────
// Ingest-runner Container Apps Job (Spec 036 T050; FR-RAG-IDX-01..05)
//
// Provisions the corpus ingest-runner as a manual-trigger Container Apps Job
// inside the existing Container Apps environment. The job runs:
//
//   docker run apps/ingest-runner: python -m ama_ingest [--full|--incremental|--dry-run]
//
// **Identity model**: User-assigned managed identity (workload identity) with
// data-plane access to:
//   - AI Search (Search Service Contributor + Index Data Contributor) for
//     blue-green index writes (FR-RAG-IDX-04).
//   - Foundry account (Cognitive Services User) for embedding calls
//     (FR-RAG-IDX-02; R-02; FR-RAG-CV-01).
//   - Service Bus topic ``topic.corpus-build-complete`` for downstream
//     orchestration (FR-RAG-IDX-05).
//
// **Carve-out invariants** (Principle I; FR-RAG-CV-01):
//   - All resources are AU East.
//   - No public ingress on AI Search (PE-only enforced by ai-search.bicep).
//   - No data leaves Australia (Foundry account region pinned by carve-out registry).
//
// **Image source**: ACR repository ``ama/ingest-runner`` built by the cd.yml
// pipeline; tag pinned to the ``corpus_build_sha`` for traceability.
// ────────────────────────────────────────────────────────────────────────────────

@description('Job name (e.g. caj-ingest-runner-prod)')
param name string

@description('Azure region — Australia East (constitution NN-2)')
@allowed([
  'australiaeast'
])
param location string = 'australiaeast'

@description('Tags applied to the job + identity')
param tags object = {}

@description('Existing Container Apps managed environment id')
param environmentId string

@description('Container image (e.g. <acrLoginServer>/ama/ingest-runner:<corpusBuildSha>)')
param image string

@description('User-assigned managed identity resource id used by the job')
param userAssignedIdentityId string

@description('User-assigned managed identity client id (for AZURE_CLIENT_ID env)')
param userAssignedClientId string

@description('Container registry login server (for the registries[] config)')
param containerRegistryLoginServer string

@description('AI Search service endpoint (https://<svc>.search.windows.net)')
param searchServiceEndpoint string

@description('Index alias name the runner writes through (e.g. corpus)')
param indexAlias string = 'corpus'

@description('Embedding deployment name surfaced via Foundry (FR-RAG-IDX-02; R-02)')
param embeddingDeploymentName string

@description('Embedding model coordinate in `<modelId>@<version>` form (FR-RAG-CV-01 — carveout preflight splits on `@` to look up the registry row). Not a credential; named `Coordinate` to avoid PSRule AZR-000408 false positives.')
param embeddingModelCoordinate string

@description('CSV map of `<modelId>@<version>=<deploymentName>` entries for every Foundry deployment used (consumed by the embedder via AZURE_AI_PROJECT_DEPLOYMENTS — see apps/ingest-runner/src/ama_ingest/embedder.py:_resolve)')
param azureAiProjectDeployments string = ''

@description('Foundry / Azure AI project endpoint (e.g. https://<proj>.services.ai.azure.com)')
param azureAiProjectEndpoint string

@description('Carve-out registry path (relative to repo) — fail-closed gate (FR-RAG-CV-01)')
param carveoutRegistryPath string = 'infra/parameters/foundry-carveout.yaml'

@description('Service Bus namespace endpoint (e.g. sb://<ns>.servicebus.windows.net)')
param serviceBusFullyQualifiedNamespace string

@description('Service Bus topic name where the runner publishes the build-complete event (FR-RAG-IDX-05)')
param serviceBusBuildCompleteTopic string = 'topic.corpus-build-complete'

@description('CPU allocation per replica (default 1.0)')
param cpu string = '1.0'

@description('Memory allocation per replica (default 2.0Gi)')
param memory string = '2.0Gi'

@description('Replica timeout in seconds (default 28800 = 8h — full corpus rebuild headroom)')
param replicaTimeoutSeconds int = 28800

@description('Initial corpus_build_sha (overridable per run; runner recomputes from git ls-tree)')
param initialCorpusBuildSha string = ''

@description('Workload profile name. Empty string = Consumption-only environment (default for legacy CA envs); set to "Consumption" or a custom profile when running in a workload-profiles env.')
param workloadProfileName string = ''

@description('Application Insights connection string for runner telemetry')
@secure()
param appInsightsConnectionString string = ''

resource job 'Microsoft.App/jobs@2024-03-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: union(
    {
      environmentId: environmentId
      configuration: {
        replicaTimeout: replicaTimeoutSeconds
        replicaRetryLimit: 1
        triggerType: 'Manual'
        registries: [
          {
            server: containerRegistryLoginServer
            identity: userAssignedIdentityId
          }
        ]
        manualTriggerConfig: {
          parallelism: 1
          replicaCompletionCount: 1
        }
      }
    template: {
      containers: [
        {
          name: 'ingest-runner'
          image: image
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          // ``python -m ama_ingest`` reads its config purely from env vars + CLI
          // flags. The CLI defaults to ``--mode incremental`` and writes a
          // manifest under ``/workspace/artifacts/`` which the postprovision
          // hook (T052) reads via ``az containerapp job execution show``.
          command: [
            'python'
          ]
          args: [
            '-m'
            'ama_ingest'
            '--corpus-root'
            'docs/corpus'
            '--search-endpoint'
            searchServiceEndpoint
            '--index-alias'
            indexAlias
            '--embedding-model'
            embeddingModelCoordinate
            '--carveout-registry'
            carveoutRegistryPath
            '--mode'
            'incremental'
          ]
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: userAssignedClientId
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: searchServiceEndpoint
            }
            {
              name: 'AZURE_AI_PROJECT_ENDPOINT'
              value: azureAiProjectEndpoint
            }
            {
              name: 'AZURE_AI_PROJECT_DEPLOYMENTS'
              value: azureAiProjectDeployments
            }
            {
              name: 'EMBEDDING_DEPLOYMENT'
              value: embeddingDeploymentName
            }
            {
              name: 'EMBEDDING_MODEL'
              value: embeddingModelCoordinate
            }
            {
              name: 'CARVEOUT_REGISTRY'
              value: carveoutRegistryPath
            }
            {
              name: 'AZURE_AI_PROJECT_REGION'
              value: location
            }
            {
              name: 'CORPUS_BUILD_SHA'
              value: initialCorpusBuildSha
            }
            {
              name: 'SERVICE_BUS_FQDN'
              value: serviceBusFullyQualifiedNamespace
            }
            {
              name: 'SERVICE_BUS_BUILD_COMPLETE_TOPIC'
              value: serviceBusBuildCompleteTopic
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsightsConnectionString
            }
            // Spec 036 R-08 — refuse legacy SDK fallback at runtime.
            {
              name: 'AMA_REQUIRE_AAD'
              value: '1'
            }
          ]
        }
      ]
    }
    },
    empty(workloadProfileName) ? {} : { workloadProfileName: workloadProfileName }
  )
}

// ────────────────────────────────────────────────────────────────────────────────
// Outputs
// ────────────────────────────────────────────────────────────────────────────────

output jobId string = job.id
output jobName string = job.name
output jobIdentityClientId string = userAssignedClientId
output jobIdentityResourceId string = userAssignedIdentityId
