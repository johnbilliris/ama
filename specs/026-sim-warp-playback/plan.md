# Implementation Plan: Simulation Time Warp & Playback

**Branch**: `026-sim-warp-playback` | **Date**: 2026-04-22 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/026-sim-warp-playback/spec.md`

## Summary

Add accelerated/time-warped simulation execution at 1×–60× speed with a server-owned canonical clock and durable cursor-based signal scheduler. After completion, simulations can be replayed in a read-only playback mode with scrub, snapshots, and reviewer annotations. Three runtimes are affected: the **Next.js 16 web dashboard** (clock display, warp selector, playback UI), the **FastAPI coordination API** (clock service, scheduler, event recording, playback/annotation endpoints), and **Python-based autonomous agents** (chat controller timing, event recording hooks).

## Technical Context

**Language/Version**: Python 3.12 (backend + agents), TypeScript/React 19 (frontend)  
**Primary Dependencies**: FastAPI, Pydantic, azure-cosmos, azure-identity (API); Next.js 16.2, React 19 (web); asyncio, azure-cosmos (agents)  
**Storage**: Azure Cosmos DB — containers: `simulation` (tenants, scheduler state), `sim-events` (events, snapshots, annotations), `sim-chat` (chat history)  
**Testing**: pytest (unit, integration, contract, simulation, e2e); pnpm test (frontend)  
**Target Platform**: Microsoft Azure (Australia East / Australia Southeast) — Azure Container Apps, Cosmos DB, Azure OpenAI  
**Project Type**: Monorepo — web-service (3 runtimes: Next.js dashboard, FastAPI API, Python agents)  
**Performance Goals**: Signal burst rate ≤100 signals/sec; playback scrub <3s (SC-004); 24hr scenario at 60× in <25min (SC-001); speed change takes effect <5s (SC-002)  
**Constraints**: Data sovereignty (AU regions only); delivery lag warning at 10s wall-clock; playback access restricted to participants + controller  
**Scale/Scope**: Hundreds to low-thousands of coarse events per simulation; concurrent playback sessions per simulation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| **I. Primacy of Life** | ✅ PASS | Simulation is a training tool; no real-world actions. Time-warp and playback improve training quality (Principle 11: continual improvement). |
| **II. AIIMS Alignment** | ✅ PASS | No change to AIIMS functional structure. Simulations already model AIIMS roles. |
| **III. Multi-Hazard** | ✅ PASS | Time-warp is hazard-agnostic; works across all scenario types. |
| **IV. Transparency & Auditability** | ✅ PASS | Event recording with monotonic `event_seq` provides full provenance. Annotations add human review layer. Existing audit writer unchanged. |
| **V. Warnings** | ✅ PASS | Feature does not change warning generation. Simulated warnings are replayed, not regenerated. |
| **VIII. Azure Platform** | ✅ PASS | All storage in Cosmos DB (Azure-native). No new non-Azure dependencies. |
| **NON-NEG 1: Human-in-the-loop** | ✅ PASS | Controller initiates all speed changes. Playback is read-only review. |
| **NON-NEG 2: Data sovereignty** | ✅ PASS | All data remains in AU Cosmos DB regions. |
| **NON-NEG 3: Privacy** | ✅ PASS | No new PII collection. Annotation `author_id` uses existing OID. |
| **NON-NEG 4: Interoperability** | ✅ PASS | New endpoints follow existing OpenAPI pattern. No external API changes. |
| **NON-NEG 5: Graceful degradation** | ✅ PASS | FR-010a: recording failure → simulation continues with partial playback. Throttle preserves order under backpressure. |
| **Quality Gates** | ✅ PASS | Feature adds unit, integration, contract tests. No infra changes without What-If review. |

**Post-Phase 1 re-check**: All gates remain PASS. New `sim-events` Cosmos container is Azure-native (VIII). Event recording graceful degradation satisfies NON-NEG 5. Annotation author-only edit/delete uses existing auth middleware.

## Project Structure

### Documentation (this feature)

```text
specs/026-sim-warp-playback/
├── plan.md              # This file
├── spec.md              # Feature specification (19 FRs, 12 clarifications)
├── research.md          # 7 research decisions (R1–R7)
├── data-model.md        # 6 entities with full schemas
├── quickstart.md        # Dev setup, test commands, curl examples
├── contracts/
│   └── api-contracts.md # 5 modified + 7 new API endpoints
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # 57 tasks across 7 phases
```

### Source Code (repository root)

```text
# Runtime 1: FastAPI Coordination API
apps/api/app/
├── api/routes/
│   ├── simulations.py              # Modified: warp_speed param, server-owned clock responses
│   └── simulation_playback.py      # NEW: playback events, snapshots, annotation CRUD
├── models/
│   ├── simulation_event.py         # NEW: SimulationEvent Pydantic response model
│   └── playback_models.py          # NEW: PlaybackEvent, AnnotationCreate/Update schemas
├── repositories/
│   ├── simulation_repository.py    # Modified: clock state persistence, scheduler state
│   └── simulation_event_repository.py  # NEW: sim-events Cosmos container access
├── services/
│   ├── simulation_service.py       # Modified: clock transitions on pause/resume/archive
│   ├── simulation_clock_service.py # NEW: server-owned canonical clock computation
│   ├── warp_scheduler.py           # NEW: durable cursor signal delivery, throttle + lag
│   ├── simulation_event_recorder.py # NEW: write-boundary event recording
│   ├── playback_service.py         # NEW: paginated events, snapshot retrieval
│   └── annotation_service.py       # NEW: annotation CRUD with author enforcement
├── services/simulation/
│   └── controller_service.py       # Modified: event recording hooks for chat turns
└── validators/
    └── simulation_validators.py    # Modified: warp speed validation

# Runtime 2: Next.js Web Dashboard
apps/web/src/
├── app/simulations/
│   ├── create/page.tsx             # Modified: warp speed selector
│   ├── [tenantId]/page.tsx         # Modified: server-owned clock display, speed change
│   └── [tenantId]/playback/page.tsx # NEW: playback page
├── components/
│   ├── simulation-banner.tsx       # Modified: warp speed indicator + lag warning
│   ├── simulation-clock.tsx        # NEW: server-polled simulated time display
│   ├── warp-speed-selector.tsx     # NEW: speed picker with allowed values
│   ├── playback-timeline.tsx       # NEW: event timeline with scrub + play/pause
│   └── playback-annotations.tsx    # NEW: annotation overlay + CRUD
└── lib/api/
    ├── simulations.ts              # Modified: clock polling, warp speed change
    └── playback.ts                 # NEW: playback events, snapshots, annotations client

# Runtime 3: Python Autonomous Agents
apps/agents/
└── common/
    └── event_recording_hook.py     # NEW: hook for agent event recording to sim-events

# Shared Domain Models
packages/domain/src/domain/models/
├── simulation_tenant.py            # Modified: clock state fields, playback_status
├── simulation_event.py             # NEW: SimulationEvent entity
├── warp_speed_change.py            # NEW: WarpSpeedChange embedded value object
├── playback_snapshot.py            # NEW: PlaybackSnapshot entity
├── signal_scheduler_state.py       # NEW: SignalSchedulerState entity
└── warp_constants.py               # NEW: ALLOWED_WARP_SPEEDS, ALLOWED_PLAYBACK_SPEEDS, defaults

# Tests (repo root)
tests/
├── unit/
│   ├── test_simulation_clock.py    # NEW: clock computation, transitions
│   ├── test_warp_scheduler.py      # NEW: signal delivery timing, cursor, throttle
│   ├── test_event_recorder.py      # NEW: event recording, seq generation
│   ├── test_playback_service.py    # NEW: event retrieval, snapshot scrub
│   └── test_annotation_service.py  # NEW: annotation CRUD, author enforcement
├── integration/
│   ├── test_warp_simulation_lifecycle.py  # NEW: full warp lifecycle
│   └── test_playback_events.py     # NEW: recording → playback round-trip
├── contract/
│   ├── test_warp_speed_api.py      # NEW: warp speed endpoint contracts
│   ├── test_playback_api.py        # NEW: playback events/snapshots contracts
│   └── test_annotation_api.py      # NEW: annotation CRUD contracts
└── simulation/
    └── test_warp_scenario.py       # NEW: 60× scenario timing validation (SC-001)

# Infrastructure
infra/
└── modules/
    └── simulation-cosmos.bicep     # Modified: add sim-events container definition
```

**Structure Decision**: Existing monorepo with three runtimes. All new files follow established patterns — services in `apps/api/app/services/`, domain models in `packages/domain/`, routes in `apps/api/app/api/routes/`, frontend pages in `apps/web/src/app/simulations/`. New Cosmos container `sim-events` provisioned via Bicep module.

## Complexity Tracking

> No constitution violations requiring justification. All gates PASS.
