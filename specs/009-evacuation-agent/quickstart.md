# Quickstart: Evacuation Agent

**Feature**: 009-evacuation-agent  
**Date**: 2026-04-16

---

## Prerequisites

- Python 3.12+
- UV package manager (`pip install uv`)
- Azure OpenAI deployment (or mock for local dev)
- Azure Cosmos DB account (or emulator for local dev)
- Risk Assessment Agent running (or synthetic handoff data)
- Shapely library (installed via UV dependencies)

## Setup

```bash
# Navigate to the agent workspace
cd apps/agents

# Install dependencies with UV
uv sync

# Copy environment template
cp .env.example .env
```

## Environment Variables

```bash
# Azure OpenAI (required for LLM features, optional for template-based fallback)
AZURE_OPENAI_ENDPOINT=https://<your-instance>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_REASONING_DEPLOYMENT=gpt-4o
AZURE_OPENAI_DRAFTING_DEPLOYMENT=gpt-4o-mini

# Azure Cosmos DB (managed identity; required outside development/test)
COSMOS_ENDPOINT=https://<your-instance>.documents.azure.com:443/
COSMOS_DATABASE_NAME=disaster-response
EVACUATION_PLANS_CONTAINER_NAME=evacuation-plans
EVACUATION_DECISIONS_CONTAINER_NAME=evacuation-decisions
ASSESSMENTS_CONTAINER_NAME=hazard-assessments
RECOMMENDATIONS_CONTAINER_NAME=risk-recommendations

# Azure Service Bus (managed identity; required outside development/test)
AZURE_SERVICEBUS_NAMESPACE=<your-namespace>.servicebus.windows.net
EVACUATION_HANDOFFS_QUEUE=evacuation-handoffs

# Reference data
ROAD_NETWORK_FILE_PATH=data/road-networks/far-north-qld-sample.json
POPULATION_DATA_FILE_PATH=data/population/sample-population.json
AMA_ENVIRONMENT=development

# Evacuation Agent Configuration (all optional — sensible defaults)
ROAD_DATA_STALENESS_HOURS=6
POPULATION_DATA_STALENESS_HOURS=24
HANDOFF_DEDUP_WINDOW_MINUTES=10
CONGESTION_RISK_THRESHOLD_PCT=80
VULNERABLE_POPULATION_BUFFER=1.5
PHASE_TRANSITION_TIME_FACTOR=1.2
PHASE_TRANSITION_POPULATION_PCT=50
HAZARD_EXPANSION_REPLAN_PCT=10
PROGRESS_DELAY_REPLAN_PCT=30
FALLBACK_CONFIDENCE_REDUCTION=0.8
REPLAN_RATE_LIMIT_SECONDS=30
AGENT_VERSION=0.1.0

# Mobilisation times per hazard type (minutes)
MOBILISATION_TIME_TSUNAMI_MIN=30
MOBILISATION_TIME_FLOOD_MIN=120
MOBILISATION_TIME_BUSHFIRE_MIN=60
MOBILISATION_TIME_CYCLONE_MIN=120
MOBILISATION_TIME_EARTHQUAKE_MIN=30

# Audit Configuration
AUDIT_BUFFER_CAPACITY=10000
AUDIT_BUFFER_FILE_PATH=/app/var/evacuation-agent/audit-buffer.jsonl

# Observability
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<your-key>;...
```

Both reference files require a timezone-aware `metadata.last_updated`. Freshness is measured from that source timestamp, not file load time. Stale roads produce a persisted review-required plan with no computed routes and conservative hazard-specific guidance; stale population/facility data remains best-available but is age-labelled and confidence-reduced.

## Run Locally

```bash
# Start the Evacuation Agent (health server + queue consumer)
cd apps/agents
uv run python -m evacuation

# Agent starts:
# - Health endpoint on http://localhost:8082/health
# - Liveness endpoint on http://localhost:8082/live
# - Readiness endpoint on http://localhost:8082/ready
# - Service Bus consumer listening for handoffs
# - Road network loaded from ROAD_NETWORK_FILE_PATH
```

When `APPLICATIONINSIGHTS_CONNECTION_STRING` is configured, startup binds the Azure Monitor OpenTelemetry distro using
`DefaultAzureCredential`; set `AZURE_CLIENT_ID` for the user-assigned managed identity. The infrastructure-provided
connection string points to the Australia-hosted Application Insights component. Local runs without it retain no-op
telemetry instruments.

## Verify

### 1. Health Check

```bash
curl http://localhost:8082/health | python -m json.tool
```

Expected output:

```json
{
  "status": "healthy",
  "agent_version": "0.1.0",
  "timestamp": "2026-04-16T10:30:00Z",
  "checks": {
    "road_network_loaded": {
      "status": "healthy",
      "node_count": 500,
      "edge_count": 2100,
      "stale": false,
      "last_loaded_at": "2026-04-16T08:00:00Z",
      "source_updated_at": "2026-04-16T07:55:00Z"
    },
    "llm_connectivity": {
      "status": "healthy",
      "last_checked_at": "2026-04-16T10:30:00Z",
      "last_successful_at": "2026-04-16T10:30:00Z",
      "latency_ms": 350
    },
    "cosmos_connectivity": {
      "status": "healthy",
      "last_checked_at": "2026-04-16T10:30:00Z",
      "last_successful_at": "2026-04-16T10:30:00Z",
      "latency_ms": null
    },
    "active_plan_count": { "count": 0, "status": "healthy" },
    "processing_queue_depth": {
      "depth": 0,
      "status": "healthy",
      "connected": true,
      "last_checked_at": "2026-04-16T10:30:00Z",
      "last_successful_at": "2026-04-16T10:30:00Z"
    },
    "audit_store": { "status": "healthy", "buffer_depth": 0 }
  }
}
```

`/health` always returns HTTP `200` with cached state. Use `/live` for process liveness and `/ready` for platform
readiness; `/ready` returns HTTP `503` when the road graph or Service Bus intake is offline.

### 2. Send Synthetic Handoff (Contract Test)

```bash
# Run the contract test that sends a synthetic handoff
cd apps/agents
uv run pytest tests/contract/test_evacuation_handoff.py -v
```

### 3. Verify Plan Output

```bash
# Run unit tests for model validation
uv run pytest tests/unit/test_evacuation_models.py -v
```

## Run Tests

```bash
# All evacuation agent tests
cd apps/agents
uv run pytest tests/ -k "evacuation" -v

# Unit tests only
uv run pytest tests/unit/ -k "evacuation" -v

# Contract tests
uv run pytest tests/contract/ -k "evacuation" -v

# Integration tests (requires Azure services)
uv run pytest tests/integration/ -k "evacuation" -v
```

## Docker

```bash
# Build
docker build -t evacuation-agent -f apps/agents/Dockerfile .

# Run
docker run -p 8082:8082 -e AMA_AGENTS_RUNTIME=evacuation --env-file apps/agents/.env evacuation-agent
```

## Azure Deployment Topology

`azure.yaml` packages `evacuation` as a distinct azd service from the conversational `agents` dispatcher. Both use the
same reviewed agents Dockerfile, but the evacuation service deploys to its own internal-ingress Container App on port
8082 with `AMA_AGENTS_RUNTIME=evacuation`. Liveness uses `/live`; startup uses `/live`; readiness uses `/ready`.

The deployment shares the existing Australia East Container Apps environment, Container Registry, Cosmos account and
`disaster-hub` database, storage account, Log Analytics workspace, Application Insights component, and Microsoft
Foundry endpoint. It does not treat the dispatcher as an evacuation runtime. Dedicated resources are:

- a regional user-assigned managed identity;
- `evacuation-plans`, `evacuation-decisions`, `hazard-assessments`, and `risk-recommendations` Cosmos containers,
  partitioned by `/incident_scope_key`;
- a Standard Service Bus namespace with the `evacuation-handoffs` queue, three-delivery dead-letter behavior, and
  queue-scoped receiver/sender roles;
- a 5 GiB `evacuation-audit-wal` Azure Files share mounted read/write at `/app/var/evacuation-agent`;
- a managed-identity `azure-servicebus` KEDA rule with `messageCount=20`, one minimum replica, and four maximum
  replicas.

The runtime, identity, Service Bus, Cosmos containers/role, file share, and resource-group roles use pinned Azure
Verified Modules. `Microsoft.App/managedEnvironments/storages` has no AVM; the one raw child resource was explicitly
approved on 2026-09-18 because Container Apps requires it to mount the restart-durable audit WAL. The storage key is a
secure module parameter used only by the environment storage binding and is not exposed as an output.

```bash
# Provision/build contracts
python -m pytest tests/devops/test_evacuation_runtime_bicep.py -q

# Static Docker validation
docker buildx build --check -f apps/agents/Dockerfile .

# Compile source configuration
az bicep build --file infra/bicep/modules/evacuation-runtime.bicep
az bicep build --file infra/main.bicep
```

## Supported Runtime Paths

- `python -m evacuation` and `AMA_AGENTS_RUNTIME=evacuation` use `evacuation.runtime.build_application`, which loads reference data, binds the scoped Cosmos containers, starts the Service Bus intake lifecycle, and calls `EvacuationAgent.process_handoff`.
- The MAF `legacy` and `maf` evacuation modes both adapt a validated `AgentHandoffEvent` to that same deterministic planner. The model may enrich validated narrative inside the pipeline; it does not create routes or plan records.
- The dispatcher remains a conversational compatibility surface. Its text response is not an evacuation plan and must not be treated as evidence of route computation or persistence.
- The previous MAF-generated empty-plan path and the optional routing-tool result that was logged then discarded are retired. Malformed or rejected handoffs now produce an explicit failure instead of an empty `v1` plan.

## Service Bus Settlement

- Validated receipt latency is measured separately from plan-generation latency and checked against the five-second intake acknowledgement target.
- Messages remain under PeekLock while planning; the runtime registers automatic lock renewal for up to five minutes.
- A message is completed only after the deterministic pipeline returns a durable plan, a duplicate is identified, or a permanent semantic rejection has been written to the audit trail.
- Transient dependency, lock-renewal, timeout, throttle, and connection failures abandon the message for broker redelivery. The third delivery is dead-lettered as `TransientRetriesExhausted`.
- Malformed raw JSON/schema payloads are audited as `handoff_rejected` and dead-lettered as `InvalidHandoffPayload`.
- Receiver connection failures use a bounded three-attempt reconnect loop. Shutdown cancellation interrupts reconnect backoff.
- If broker completion loses its response after plan persistence, the runtime does not attempt a contradictory settlement; Service Bus redelivery and idempotency remain authoritative.
- Configured runtimes persist an owner-bound `HandoffProcessingClaim` in the plan's tenant/incident partition. Independent replicas race on atomic claim creation; only one plans, while completed redelivery resolves to the original `plan_id` and writes a duplicate-discard audit.
- A plan ID is linked to the claim before plan creation. This lets a fresh replica recover an accepted write whose response or claim-completion update was lost, without allocating `v2`.
- Retryable processing marks the owned claim abandoned. A losing replica cannot release the winner's claim; stale processing leases are taken over only with an ETag condition.

## Deterministic Replanning

- Replanning starts from a persisted tenant/incident-scoped source plan with an ETag. A missing scope or concurrency token is rejected.
- Reported closures are applied to an isolated graph snapshot and carried into later versions. Routes using a newly closed edge are recomputed with Dijkstra; unaffected route documents remain unchanged.
- Updated zone snapshots recompute hazard-adjusted capacities, routes, population, transport, phases, and zone dispositions. Severity and progress changes rebuild the timeline from structured data.
- Material comparison includes complete route paths, zones, transport, phases, dispositions, shelter state, and hazard summary. A trigger without a material plan change creates no version.
- A material update atomically condition-checks the source ETag, advances the incident counter, and creates linked proposed `vN+1` in one partition batch. The source record remains unchanged apart from its Cosmos-managed ETag. Approved-source supersession is resolved separately by the lifecycle policy.
- Change summaries name triggers, changed routes, excluded road IDs, zone/transport/timeline changes, and severity changes. `plan_updated` audit and telemetry reference the committed new ID/version; shelter recovery events include an actual nonempty route ID.
- Initial plan versions use the installed Cosmos SDK's typed ETag/match-condition write. Concurrent 404/409 bootstrap and 412 replacement races retry with a bounded budget; exhaustion and timeouts remain retryable work and never fabricate `v1` or `current+1`. Hermetic strict-store tests cover these paths; service/emulator contention evidence is a future V-STORE run requiring isolated infrastructure approval.
- Plan `create_item` is followed by an exact scoped read-back of the complete validated model. Active counts, final `plan_generated` audit, telemetry, claim completion, and broker completion occur only after that receipt. A lost write response may still succeed when read-back confirms the intended document.
- A confirmed missing read-back records an orphaned reserved version; timeout or indeterminate read-back records an uncertain version. Redelivery uses the claim's linked plan ID to recover an existing valid `v1` without allocating `v2`; a malformed or wrong-scope document never completes the claim.

## Key Differences from Other Agents

| Aspect | Monitoring Agent | Risk Assessment Agent | Evacuation Agent |
|--------|-----------------|----------------------|-----------------|
| Input | `SignalEnvelope` from ingestion | `AgentHandoffEvent` from monitoring | `AgentHandoffEvent` from risk assessment |
| Output | Single downstream (risk_assessment) | Three downstream agents | Plans for commander review (no downstream agent handoff) |
| Processing | 6-stage pipeline | 8-stage pipeline | 10-stage pipeline |
| Core Algorithm | Signal evaluation | Weighted averaging + contradiction detection | Dijkstra's pathfinding + Shapely geospatial |
| Unique Dependencies | — | — | Shapely (geospatial), static road network JSON |
| Storage | `monitoring-decisions` | `risk-assessments`, `risk-recommendations`, `risk-assessment-decisions` | `evacuation-plans`, `evacuation-decisions` |
| Port | 8080 | 8081 | 8082 |
| SLA (initial) | 5 seconds | 10 seconds | 30 seconds |
| SLA (update) | — | — | 15 seconds (replanning) |

## Sample Road Network

A sample road network file is provided at `data/road-networks/far-north-qld-sample.json` for local development and testing. It covers a simplified Far North Queensland coastal region (Cairns to Cooktown) with:
- ~50 nodes (intersections)
- ~120 edges (road segments)
- 5 assembly areas
- Mix of sealed and unsealed roads
- Accessibility features on major corridors
