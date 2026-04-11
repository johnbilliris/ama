# Quickstart: Monitoring Agent

**Feature**: 010-monitoring-agent  
**Date**: 2026-04-11

---

## Prerequisites

- Python 3.12+
- UV package manager (`pip install uv`)
- Azure OpenAI deployment (or mock for local dev)
- Azure Cosmos DB account (or emulator for local dev)

## Setup

```bash
# Clone and navigate to the agent workspace
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

# Azure Cosmos DB (required for audit trail)
COSMOS_DB_ENDPOINT=https://<your-instance>.documents.azure.com:443/
COSMOS_DB_KEY=<your-key>
COSMOS_DB_DATABASE=disaster-response
COSMOS_DB_CONTAINER=monitoring-decisions

# Application Insights (optional, enables telemetry)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...

# Agent Configuration (all optional, defaults shown)
ESCALATION_CONFIDENCE_THRESHOLD=0.8
SIGNAL_DEDUP_WINDOW_MINUTES=10
RETROSPECTIVE_LOOKBACK_HOURS=24
STALENESS_THRESHOLD_AUTHORITATIVE_MINUTES=15
STALENESS_THRESHOLD_IOT_MINUTES=5
STALENESS_THRESHOLD_SOCIAL_MINUTES=30
LLM_EVAL_TIMEOUT_SECONDS=3
SUSPICIOUS_CONFIDENCE_PENALTY=0.15
AUDIT_BUFFER_CAPACITY=10000
AGENT_VERSION=0.1.0
PORT=8080
```

## Run Locally

```bash
# Start the health server (keeps container alive)
cd apps/agents
python -m monitoring.agent

# The agent listens on http://localhost:8080/health
curl http://localhost:8080/health
```

## Run Tests

```bash
# From repo root
cd apps/agents
uv run pytest tests/unit/ -v
uv run pytest tests/contract/test_misinformation_detector.py -v
uv run pytest tests/contract/test_incident_association.py -v
uv run pytest tests/integration/test_handoff_retry.py -v
```

## Quick Verification

### 1. Verify signal summarisation

```python
from monitoring.agent import MonitoringAgent
from app.validators.signal_envelope import SignalEnvelope, SignalSourceEnvelope

agent = MonitoringAgent()
envelope = SignalEnvelope(
    source=SignalSourceEnvelope(dataSourceId="bom-1", name="BoM NSW", kind="authoritative"),
    category="weather",
    occurredAt="2026-04-11T10:00:00Z",
    receivedAt="2026-04-11T10:00:05Z",
    location={"type": "Point", "coordinates": [151.2, -33.9]},
    confidenceScore=0.9,
    freshnessScore=0.95,
    validationStatus="validated",
    incidentId="INC-001",
)
summary = agent.summarize_signal(envelope)
assert summary["category"] == "weather"
assert summary["sourceKind"] == "authoritative"
```

### 2. Verify high-risk escalation

```python
handoff = agent.build_high_risk_handoff(envelope)
assert handoff is not None
assert handoff.target_agent == "risk_assessment"
assert handoff.confidence == 0.9  # Will be effectiveConfidence post-implementation
```

### 3. Verify misinformation blocking

```python
# With a mock LLM that returns "misinformation"
from unittest.mock import MagicMock

mock_llm = MagicMock()
mock_llm.generate_response.return_value = {"text": "misinformation"}
agent_with_llm = MonitoringAgent(llm_client=mock_llm)

escalated = SignalEnvelope(
    source=SignalSourceEnvelope(dataSourceId="social-1", name="Twitter", kind="social"),
    category="fire",
    occurredAt="2026-04-11T10:00:00Z",
    receivedAt="2026-04-11T10:00:05Z",
    location={"type": "Point", "coordinates": [151.2, -33.9]},
    confidenceScore=0.9,
    freshnessScore=0.9,
    validationStatus="escalated",
    incidentId="INC-001",
)
result = agent_with_llm.build_high_risk_handoff(escalated)
assert result is None  # Blocked — misinformation
```
