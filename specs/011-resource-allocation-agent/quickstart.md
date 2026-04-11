# Quickstart: Resource Allocation Agent

**Feature**: 011-resource-allocation-agent  
**Date**: 2026-04-17

---

## Prerequisites

- Python 3.12+
- UV package manager (`pip install uv`)
- Azure OpenAI deployment (or mock for local dev)
- Azure Cosmos DB account (or emulator for local dev)
- Risk Assessment Agent running (or synthetic handoff data)
- Evacuation Agent running (or synthetic transport dispatch data)

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
# Azure OpenAI (required for LLM features, optional for rule-based fallback)
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
SERVICE_BUS_QUEUE_NAME=resource-allocation-handoffs

# Resource Allocation Configuration (all optional — sensible defaults)
PRIORITY_WEIGHT_CRITICAL=4.0
PRIORITY_WEIGHT_HIGH=3.0
PRIORITY_WEIGHT_MODERATE=2.0
PRIORITY_WEIGHT_LOW=1.0
DISTANCE_FLOOR_KM=0.1
AVAILABILITY_RETURNING=0.5
TRAVEL_SPEED_PERSONNEL_KMH=40
TRAVEL_SPEED_VEHICLE_KMH=60
TRAVEL_SPEED_HELICOPTER_KMH=200
MOBILISATION_PERSONNEL_MINUTES=15
MOBILISATION_VEHICLE_MINUTES=10
MOBILISATION_HELICOPTER_MINUTES=5
PLAN_EXPIRY_HOURS=4
HANDOFF_DEDUP_WINDOW_MINUTES=10
INVENTORY_STALENESS_WINDOW_MINUTES=30
ROTATION_THRESHOLD_HOURS=12
REPLENISHMENT_THRESHOLD_PERCENT=20
CONFIDENCE_BASE=0.9
FALLBACK_REDUCTION_FACTOR=0.8
STALE_DATA_REDUCTION_FACTOR=0.8
PARTIAL_DATA_REDUCTION_FACTOR=0.7
VERSION_CONFLICT_MAX_RETRIES=3
AGENT_VERSION=0.1.0
REQUIRE_AUTH=false  # Set to true in production

# Observability
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<your-key>;...
```

## Run Locally

```bash
# Start the Resource Allocation Agent (health server + queue consumer)
cd apps/agents
uv run python -m resource_allocation.agent

# Agent starts:
# - Health endpoint on http://localhost:8083/health
# - Service Bus consumer listening for handoffs from risk_assessment and evacuation
# - Static resource inventory loaded from config
```

## Verify

### 1. Health Check

```bash
curl http://localhost:8083/health | python -m json.tool
```

Expected output:
```json
{
  "status": "healthy",
  "agent_version": "0.1.0",
  "timestamp": "2026-04-17T10:30:00Z",
  "checks": {
    "inventory_loaded": {
      "status": "healthy",
      "resource_count": 150,
      "last_updated_at": "2026-04-17T10:29:00Z",
      "staleness_minutes": 1.0
    },
    "llm_connectivity": { "status": "healthy", "latency_ms": 250 },
    "cosmos_connectivity": { "status": "healthy" },
    "active_plan_count": 0,
    "pending_demands": 0,
    "processing_queue": { "depth": 0, "status": "healthy" },
    "audit_store": { "status": "healthy", "buffer_depth": 0, "current_tier": 1 }
  }
}
```

### 2. Send Synthetic Handoff (Integration Test)

```bash
# Run the contract test that sends a synthetic handoff from risk assessment
cd apps/agents
uv run pytest tests/contract/test_resource_allocation_handoff.py -v
```

### 3. Verify Plan Output

```bash
# Run unit tests for model validation and scoring
uv run pytest tests/unit/test_resource_allocation_models.py -v
uv run pytest tests/unit/test_resource_allocation_scoring.py -v
```

## Run Tests

```bash
# All resource allocation tests
cd apps/agents
uv run pytest tests/ -k "resource_allocation" -v

# Unit tests only
uv run pytest tests/unit/ -k "resource_allocation" -v

# Contract tests only
uv run pytest tests/contract/ -k "resource_allocation" -v

# Integration tests (requires Cosmos DB and Service Bus)
uv run pytest tests/integration/ -k "resource_allocation" -v

# Simulation tests
uv run pytest tests/simulation/ -k "allocation" -v
```

## Port Assignments

| Agent | Port |
|-------|------|
| Monitoring | 8080 |
| Risk Assessment | 8081 |
| Evacuation | 8082 |
| **Resource Allocation** | **8083** |

## Sample Resource Inventory

A sample resource inventory file is provided at `data/resource-inventories/sample-inventory.json` with the following resource types for testing:

- **Vehicles**: 2 ambulances, 2 fire trucks, 3 buses, 1 helicopter
- **Personnel**: 4 paramedic teams, 3 firefighter crews, 2 SES volunteer teams, 2 police units
- **Supplies**: Water (5000L), food (1000 meals), medical kits (50), generators (10), fuel (2000L)
- **Facilities**: 2 evacuation centres, 1 hospital, 2 staging areas

Each resource has defined capabilities, locations (south-east Queensland coordinates), and initial availability status.
