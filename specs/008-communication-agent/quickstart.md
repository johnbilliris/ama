# Quickstart: Communication Agent

**Phase 1 output** | **Date**: 2026-04-18 | **Spec**: [spec.md](spec.md)

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Python package manager — used by this repo)
- Azure CLI (`az`) for local Azure service authentication
- Docker (optional, for container testing)

### Azure Services (required for integration tests, optional for unit tests)

- Azure Cosmos DB (NoSQL API)
- Azure OpenAI (with chat completion and embedding deployments)
- Azure Service Bus (namespace with queues)
- Azure Communication Services (SMS)
- Azure Notification Hubs (push notifications)

---

## 1. Clone and Setup

```bash
# From repository root
cd apps/agents

# Install dependencies (uv reads pyproject.toml)
uv sync

# Verify Python version
uv run python --version
# Expected: Python 3.12.x
```

---

## 2. Configure Environment

Copy the example environment file and fill in values:

```bash
cp .env.example .env
```

### Minimum Configuration for Local Development

```env
# Agent metadata
AGENT_VERSION=0.1.0
PORT=8084

# Azure OpenAI (required for LLM-based drafting)
AZURE_OPENAI_ENDPOINT=https://<your-openai>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2024-02-01

# Azure Cosmos DB (required for persistence)
AZURE_COSMOS_ENDPOINT=https://<your-cosmos>.documents.azure.com:443/
AZURE_COSMOS_DATABASE=disaster-response

# Azure Service Bus (required for handoff intake)
AZURE_SERVICEBUS_CONNECTION=Endpoint=sb://<your-sb>.servicebus.windows.net/;...

# Azure Communication Services (required for SMS delivery)
AZURE_COMMUNICATION_ENDPOINT=https://<your-acs>.communication.azure.com

# Azure Notification Hubs (required for push delivery)
AZURE_NOTIFICATION_HUB_CONNECTION=Endpoint=sb://<your-nh>.servicebus.windows.net/;...
AZURE_NOTIFICATION_HUB_NAME=disaster-alerts

# Emergency broadcast webhook
EAS_ENDPOINT_URL=https://<your-eas>/api/broadcast

# Translation and quality
SUPPORTED_LANGUAGES=en-AU,zh-Hans,ar,vi,el,it
BACK_TRANSLATION_THRESHOLD=0.85
ALERT_MAX_TOKENS=180

# Deduplication
HANDOFF_DEDUP_WINDOW_MINUTES=30

# Approval
APPROVAL_ESCALATION_TIMEOUT_MINUTES=15
MAX_ESCALATION_LEVELS=3

# Delivery
DELIVERY_CHANNELS=sms,push,emergency_broadcast
DELIVERY_MAX_RETRIES=3
SMS_MAX_LENGTH=612

# Alert lifecycle
ALERT_EXPIRY_HOURS=24

# Audit
AUDIT_BUFFER_CAPACITY=10000
AUDIT_BUFFER_FILE_PATH=communication_audit.jsonl
```

### Authentication

The agent uses `DefaultAzureCredential` from `azure-identity`. For local development:

```bash
# Login to Azure CLI
az login

# Set the subscription
az account set --subscription <your-subscription-id>
```

---

## 3. Run Unit Tests

Unit tests run without any Azure services (all external dependencies are mocked).

```bash
# From repository root
uv run pytest tests/unit/test_communication_*.py -v

# Run with coverage
uv run pytest tests/unit/test_communication_*.py -v --cov=apps/agents/communication
```

### Expected Test Categories

| Test File | What It Tests |
|-----------|--------------|
| `test_communication_models.py` | Pydantic v2 model validation, enum values, state transitions |
| `test_communication_config.py` | Config loading from env vars, defaults, hash computation |
| `test_communication_translator.py` | LLM translation, back-translation, template fallback |
| `test_communication_segmentation.py` | Zone segmentation, vulnerability detection, language assignment |
| `test_communication_delivery.py` | Multi-channel dispatch, retry logic, multi-part SMS |
| `test_communication_approval.py` | Approval workflow, escalation chain, concurrent conflict |
| `test_communication_versioning.py` | OCC version counter, etag handling |
| `test_communication_dedup.py` | TTL-based dedup, LRU eviction, dual dedup key |
| `test_communication_audit.py` | Three-tier degradation, flush, tier transitions |
| `test_communication_pipeline.py` | 11-stage pipeline, stage isolation |
| `test_communication_endpoints.py` | FastAPI endpoint responses, auth validation |

---

## 4. Start the Agent Locally

```bash
# From repository root
cd apps/agents
uv run python -m communication

# Expected output:
# INFO:     Communication Agent v0.1.0 starting on port 8084
# INFO:     Template files loaded: 6 languages
# INFO:     Dedup cache initialised (window=30min)
# INFO:     Health endpoint ready: http://0.0.0.0:8084/health
```

---

## 5. Verify Health

```bash
curl -s http://localhost:8084/health | python -m json.tool
```

Expected response (without Azure services, shows degraded):

```json
{
  "status": "degraded",
  "agent": "communication",
  "version": "0.1.0",
  "checks": {
    "llm_connectivity": { "status": "unhealthy" },
    "cosmos_connectivity": { "status": "unhealthy" },
    "sms_service_status": { "status": "unhealthy" },
    "push_service_status": { "status": "unhealthy" },
    "broadcast_endpoint_status": { "status": "unhealthy" }
  },
  "operational": {
    "pending_approvals_count": 0,
    "active_deliveries_count": 0,
    "processing_queue_depth": 0,
    "audit_store": "file",
    "dedup_cache_size": 0
  }
}
```

---

## 6. Verify Alert Drafting (Manual Test)

With Azure OpenAI configured, test alert drafting via the existing stub:

```python
# test_draft.py — quick manual verification
import asyncio
from communication.agent import CommunicationAgent

async def main():
    agent = CommunicationAgent()
    alert = agent.draft_alert(
        incident_id="inc-test-001",
        recommendation_id="rec-test-001"
    )
    print(f"Alert ID: {alert.alert_id}")
    print(f"Status: {alert.status}")
    print(f"Languages: {list(alert.content_blocks.keys())}")
    for lang, text in alert.content_blocks.items():
        print(f"  [{lang}]: {text[:80]}...")

asyncio.run(main())
```

```bash
uv run python test_draft.py
```

---

## 7. Run Integration Tests

Requires Azure services configured in `.env`:

```bash
# Cosmos DB integration
uv run pytest tests/integration/test_communication_cosmos.py -v

# Service Bus integration
uv run pytest tests/integration/test_communication_service_bus.py -v
```

---

## 8. Run Simulation Scenarios

```bash
# All disaster scenarios
uv run pytest tests/simulation/ -v -k communication

# Specific scenarios
uv run pytest tests/simulation/test_cyclone_alert_scenario.py -v
uv run pytest tests/simulation/test_bushfire_alert_scenario.py -v
uv run pytest tests/simulation/test_flood_alert_scenario.py -v
```

---

## 9. Docker Build (Optional)

```bash
# From repository root
docker build -t communication-agent -f apps/agents/Dockerfile --target communication .

# Run
docker run -p 8084:8084 --env-file apps/agents/.env communication-agent

# Verify
curl http://localhost:8084/health
```

---

## Key Verification Checks

| Check | Command | Expected |
|-------|---------|----------|
| Health endpoint | `curl localhost:8084/health` | 200 with status object |
| Unit tests pass | `uv run pytest tests/unit/test_communication_*.py` | All green |
| Template loading | Agent startup logs | "Template files loaded: 6 languages" |
| Config hash | Health response `config_hash` | Non-empty SHA-256 hash |
| Port correct | Agent startup | Listening on 8084 |

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: communication` | Not running from `apps/agents/` | `cd apps/agents && uv run python -m communication` |
| `LLM connectivity: unhealthy` | Azure OpenAI not configured | Set `AZURE_OPENAI_ENDPOINT` and authenticate via `az login` |
| `Template file not found` | Missing `data/alert-templates/` | Create template files per data-model.md schema |
| `Port 8084 already in use` | Another process on 8084 | Change `PORT` env var or stop conflicting process |
| All tests skip | Missing test markers | Ensure pytest markers are configured in `pyproject.toml` |
