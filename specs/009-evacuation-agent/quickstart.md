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

# Azure Cosmos DB (required for persistence)
COSMOS_DB_ENDPOINT=https://<your-instance>.documents.azure.com:443/
COSMOS_DB_KEY=<your-key>
COSMOS_DB_DATABASE=disaster-response

# Azure Service Bus (required for handoff intake)
SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://<your-namespace>.servicebus.windows.net/;...
SERVICE_BUS_QUEUE_NAME=evacuation-handoffs

# Road Network Configuration
ROAD_NETWORK_FILE_PATH=data/road-network.json

# Evacuation Agent Configuration (all optional — sensible defaults)
ROAD_DATA_STALENESS_HOURS=6
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
AUDIT_BUFFER_FILE_PATH=/var/log/evacuation-agent/audit-buffer.jsonl

# Observability
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<your-key>;...
```

## Run Locally

```bash
# Start the Evacuation Agent (health server + queue consumer)
cd apps/agents
uv run python -m evacuation.agent

# Agent starts:
# - Health endpoint on http://localhost:8082/health
# - Service Bus consumer listening for handoffs
# - Road network loaded from ROAD_NETWORK_FILE_PATH
```

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
      "last_loaded_at": "2026-04-16T08:00:00Z"
    },
    "llm_connectivity": { "status": "healthy", "latency_ms": 350 },
    "cosmos_connectivity": { "status": "healthy" },
    "active_plan_count": { "count": 0, "status": "healthy" },
    "processing_queue_depth": { "depth": 0, "status": "healthy" },
    "audit_store": { "status": "healthy", "buffer_depth": 0 }
  }
}
```

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
docker run -p 8082:8082 --env-file apps/agents/.env evacuation-agent
```

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
