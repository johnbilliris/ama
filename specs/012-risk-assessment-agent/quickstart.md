# Quickstart: Risk Assessment Agent

**Feature**: 012-risk-assessment-agent  
**Date**: 2026-04-15

---

## Prerequisites

- Python 3.12+
- UV package manager (`pip install uv`)
- Azure OpenAI deployment (or mock for local dev)
- Azure Cosmos DB account (or emulator for local dev)
- Monitoring Agent running (or synthetic handoff data)

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
SERVICE_BUS_QUEUE_NAME=risk-assessment-handoffs

# Risk Assessment Configuration (all optional — sensible defaults)
SOURCE_WEIGHT_AUTHORITATIVE=2.0
SOURCE_WEIGHT_IOT=1.0
SOURCE_WEIGHT_SOCIAL=0.5
STALE_SIGNAL_THRESHOLD=0.5
HANDOFF_DEDUP_WINDOW_MINUTES=10
CONTRADICTION_REDUCTION_FACTOR=0.7
FALLBACK_REDUCTION_FACTOR=0.8
ESCALATION_THRESHOLD_COMMUNICATION=0.7
ESCALATION_THRESHOLD_EVACUATION=0.6
ASSESSMENT_VALIDITY_HOURS_DEFAULT=4
AGENT_VERSION=0.1.0

# Observability
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<your-key>;...
```

## Run Locally

```bash
# Start the Risk Assessment Agent (health server + queue consumer)
cd apps/agents
uv run python -m risk_assessment.agent

# Agent starts:
# - Health endpoint on http://localhost:8081/health
# - Service Bus consumer listening for handoffs
```

## Verify

### 1. Health Check

```bash
curl http://localhost:8081/health | python -m json.tool
```

Expected output:
```json
{
  "status": "healthy",
  "agent_version": "0.1.0",
  "timestamp": "2026-04-15T10:30:00Z",
  "checks": {
    "llm_connectivity": { "status": "healthy", "latency_ms": 250 },
    "signal_store": { "status": "healthy" },
    "processing_queue": { "depth": 0, "status": "healthy" },
    "audit_store": { "status": "healthy", "buffer_depth": 0 }
  }
}
```

### 2. Send Synthetic Handoff (Integration Test)

```bash
# Run the integration test that sends a synthetic handoff
cd apps/agents
uv run pytest tests/contract/test_risk_assessment_pipeline.py -v
```

### 3. Verify Assessment Output

```bash
# Query Cosmos DB for the generated assessment
# (or check the test output for assessment details)
uv run pytest tests/unit/test_risk_assessment_models.py -v
```

## Run Tests

```bash
# All risk assessment tests
cd apps/agents
uv run pytest tests/ -k "risk_assessment" -v

# Unit tests only
uv run pytest tests/unit/ -k "risk_assessment" -v

# Contract tests
uv run pytest tests/contract/ -k "risk_assessment" -v

# Integration tests (requires Azure services)
uv run pytest tests/integration/ -k "risk_assessment" -v
```

## Docker

```bash
# Build
docker build -t risk-assessment-agent -f apps/agents/Dockerfile .

# Run
docker run -p 8081:8081 --env-file apps/agents/.env risk-assessment-agent
```

## Key Differences from Monitoring Agent

| Aspect | Monitoring Agent | Risk Assessment Agent |
|--------|-----------------|----------------------|
| Input | `SignalEnvelope` from ingestion | `AgentHandoffEvent` from monitoring |
| Output | Single downstream (risk_assessment) | Three downstream agents |
| Processing | 6-stage pipeline | 8-stage pipeline |
| Confidence | `effectiveConfidence = confidence × freshness` | Weighted averaging + contradiction + fallback penalties |
| Storage | `monitoring-decisions` container | `risk-assessments`, `risk-recommendations`, `risk-assessment-decisions` |
| Port | 8080 | 8081 |
