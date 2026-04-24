# Quickstart: Simulation Time Warp & Playback

**Feature**: `026-sim-warp-playback`  
**Date**: 2026-04-22

## Prerequisites

- Python 3.12+ with dependencies from `pyproject.toml`
- Node.js 20+ with pnpm
- Cosmos DB emulator or `COSMOS_ENDPOINT` environment variable (optional — falls back to in-memory)

## Running Locally

### Backend (FastAPI)

```bash
cd apps/api
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend (Next.js)

```bash
cd apps/web
pnpm dev
```

The frontend proxies `/api/*` requests to the backend via `next.config.ts`.

## Testing the Feature

### Unit Tests

```bash
# From repo root
python -m pytest tests/unit/test_warp_scheduler.py tests/unit/test_simulation_clock.py tests/unit/test_event_recorder.py tests/unit/test_playback_service.py -v
```

### Integration Tests

```bash
python -m pytest tests/integration/test_warp_simulation_lifecycle.py tests/integration/test_playback_events.py -v
```

### Contract Tests

```bash
python -m pytest tests/contract/test_warp_speed_api.py tests/contract/test_playback_api.py tests/contract/test_annotation_api.py -v
```

## Key Scenarios to Verify

### 1. Create a Time-Warped Simulation

```bash
curl -X POST http://localhost:8000/api/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_type": "bushfire",
    "jurisdictions": ["NSW"],
    "participants": [{"oid": "user-1", "persona": "IC"}],
    "warp_speed": 10
  }'
```

### 2. Change Warp Speed Mid-Simulation

```bash
curl -X POST http://localhost:8000/api/simulations/{tenant_id}/warp-speed \
  -H "Content-Type: application/json" \
  -d '{"warp_speed": 24}'
```

### 3. Check Server Clock

```bash
curl http://localhost:8000/api/simulations/{tenant_id}/clock
```

### 4. Retrieve Playback Events

```bash
curl "http://localhost:8000/api/simulations/{tenant_id}/playback/events?limit=50"
```

### 5. Create a Playback Annotation

```bash
curl -X POST http://localhost:8000/api/simulations/{tenant_id}/playback/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "sim_time_offset": 1800.0,
    "text": "Good coordination at this point"
  }'
```

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Next.js Web   │────▶│   FastAPI API     │────▶│   Cosmos DB     │
│                 │     │                  │     │                 │
│ • Warp selector │     │ • Clock service  │     │ • simulation    │
│ • Sim clock     │     │ • Warp scheduler │     │ • sim-events    │
│ • Playback page │     │ • Event recorder │     │ • sim-chat      │
│ • Annotations   │     │ • Playback svc   │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### New Services
- **SimulationClockService**: Server-owned canonical clock — computes simulated time, handles pause/resume/speed-change transitions
- **WarpScheduler**: Durable signal delivery using cursor + canonical clock — delivers signals at correct warp-adjusted times
- **SimulationEventRecorder**: Write-boundary interceptor — records decision-significant events to `sim-events` container
- **PlaybackService**: Reads events and snapshots — paginated retrieval, snapshot-based scrub support
- **AnnotationService**: CRUD for playback annotations — author-only edit/delete enforcement
