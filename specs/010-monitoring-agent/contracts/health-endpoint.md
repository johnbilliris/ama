# Contract: Health Endpoint

**Feature**: 010-monitoring-agent  
**Date**: 2026-04-11  
**Type**: HTTP API (Azure Container Apps health probe)

---

## Endpoint

```
GET /health
```

**Response time SLA**: ≤ 1 second (FR-025, SC-007)  
**Authentication**: None (internal container health probe)

---

## Response Schema

```json
{
  "status": "healthy | degraded | unhealthy",
  "agent_version": "0.1.0",
  "timestamp": "2026-04-11T10:30:00Z",
  "checks": {
    "llm_connectivity": {
      "status": "healthy | degraded | offline",
      "last_checked_at": "2026-04-11T10:29:55Z",
      "latency_ms": 120
    },
    "data_source_freshness": {
      "summary": "healthy | degraded",
      "sources": [
        {
          "data_source_id": "bom-weather-nsw",
          "source_type": "authoritative",
          "status": "healthy | degraded | offline",
          "last_signal_received_at": "2026-04-11T10:29:50Z",
          "staleness_threshold_minutes": 15
        }
      ]
    },
    "processing_queue": {
      "depth": 42,
      "status": "healthy | warning | critical"
    },
    "audit_store": {
      "status": "healthy | buffering | degraded",
      "buffer_depth": 0
    }
  }
}
```

---

## Status Determination

| Overall Status | Condition |
|----------------|-----------|
| `healthy` | All checks pass |
| `degraded` | One or more non-critical checks are degraded; agent can still process signals |
| `unhealthy` | Critical component failure; agent cannot process signals safely |

| Component | Healthy | Degraded | Unhealthy |
|-----------|---------|----------|-----------|
| LLM connectivity | Responds within 5s | Responds but slow (>5s) | Unreachable |
| Data source freshness | All sources healthy | One or more sources degraded | N/A (never unhealthy) |
| Processing queue | depth < 1000 | depth 1000–5000 | depth > 5000 |
| Audit store | Cosmos DB writable | Buffering in-memory | Buffer full + file spill |

---

## Endpoint: Retrospective Association

```
POST /associate
```

**Authentication**: Internal service-to-service (Azure Managed Identity)  
**Content-Type**: `application/json`

### Request

```json
{
  "incident_id": "INC-042",
  "jurisdiction_id": "NSW-SYDNEY",
  "lookback_hours": 24,
  "tenant_id": "live"
}
```

### Response

```json
{
  "incident_id": "INC-042",
  "jurisdiction_id": "NSW-SYDNEY",
  "signals_associated": 5,
  "lookback_hours": 24,
  "timestamp": "2026-04-11T10:30:00Z"
}
```

### Error Response

```json
{
  "error": "repository_unavailable",
  "signals_associated": 0,
  "message": "Signal repository is currently unavailable"
}
```

**Status codes**: 200 (success), 503 (repository unavailable), 400 (invalid request)
