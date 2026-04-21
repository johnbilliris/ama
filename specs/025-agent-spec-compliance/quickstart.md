# Quickstart: Agent Specification Compliance Audit

**Feature**: 025-agent-spec-compliance  
**Branch**: `025-agent-spec-compliance`

## Prerequisites

- Python 3.11+
- Node.js 18+ (for Next.js dashboard)
- Azure subscription with Australia East region access
- Azure CLI (`az`) authenticated
- `pnpm` package manager
- Poetry or pip for Python dependencies

## New Dependencies

### Python (add to `apps/agents/pyproject.toml`)

```toml
azure-ai-contentsafety = ">=1.0.0"  # F08: Content safety
azure-iot-device = ">=2.12.0"        # F01: IoT adapter
```

### Infrastructure

```bash
# Deploy new Azure resources (Content Safety + IoT Hub)
az deployment group create \
  --resource-group <rg-name> \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.development.json
```

## Local Development

### Run Tests for This Feature

```bash
# From repo root
python -m pytest tests/unit/test_async_handoff_retry.py -v        # F10
python -m pytest tests/unit/test_hazard_map_generation.py -v       # F03
python -m pytest tests/unit/test_content_safety_azure.py -v        # F08
python -m pytest tests/unit/test_content_safety_factual.py -v      # F08 factual
python -m pytest tests/unit/test_content_safety_tone.py -v         # F08 tone
python -m pytest tests/unit/test_circuit_breaker.py -v             # FR-009
python -m pytest tests/unit/test_evacuation_transport_handoff.py -v # F05
python -m pytest tests/unit/test_resource_dispatch_handoff.py -v   # F06
python -m pytest tests/unit/test_road_network_dynamic.py -v        # F04
python -m pytest tests/unit/test_iot_adapter.py -v                 # F01
python -m pytest tests/unit/test_translation_embedding.py -v       # F09
python -m pytest tests/unit/test_dead_letter_redelivery.py -v      # FR-003a
python -m pytest tests/unit/test_named_location_lookup.py -v       # FR-004a

# All compliance tests at once
python -m pytest tests/unit/ -k "async_handoff or hazard_map or content_safety or circuit_breaker or transport_handoff or dispatch_handoff or road_network_dynamic or iot_adapter or translation_embedding or dead_letter or named_location" -v

# Contract tests
python -m pytest tests/contract/test_evacuation_resource_handoff.py -v
python -m pytest tests/contract/test_resource_communication_handoff.py -v
```

### Verify Async Conversion Doesn't Break Existing Tests

```bash
# Run full unit + contract test suite
python -m pytest tests/unit/ tests/contract/ -v --tb=short
```

## Environment Variables

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `AZURE_CONTENT_SAFETY_ENDPOINT` | Azure AI Content Safety endpoint URL | F08 |
| `AZURE_CONTENT_SAFETY_KEY` | API key (local dev only; production uses managed identity) | F08 |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint (existing) | F09 |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding model deployment name | F09 |
| `IOT_HUB_CONNECTION_STRING` | IoT Hub connection string | F01 |
| `IOT_HUB_EVENT_GRID_ENDPOINT` | Event Grid webhook URL | F01 |
| `COSMOS_DB_ENDPOINT` | Cosmos DB endpoint (existing, used for new collections) | FR-003a, FR-006, FR-004a |
| `MANAGEMENT_API_KEY` | API key for local dev management API auth | FR-021 |
| `DEAD_LETTER_POLL_INTERVAL_SECONDS` | Background poller interval (default 30) | FR-003a |

## Implementation Order

Recommended sequence based on dependency chain:

1. **F10** — Async delivery + dead-letter persistence + redelivery poller (foundation for all handoff changes)
2. **FR-021** — Management API auth middleware (required by radius table and dead-letter endpoints)
3. **F03** — Hazard map generation + Cosmos DB radius lookup table + named-location lookup (independent, risk_assessment)
4. **F08** — Content safety integration + circuit breaker + factual + tone checks (independent, communication)
5. **F09** — Embedding similarity (independent, communication only)
6. **F04** — Dynamic road network (requires F10 for async handoff)
7. **F05** — Evacuation→Resource handoff with priority (requires F10)
8. **F06** — Resource→Communication dispatch (requires F05, F10)
9. **F01** — IoT adapter with dedup (requires infrastructure deployment)
