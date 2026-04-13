# Quickstart: AIDR Guidance Integration

**Feature**: 018-aidr-guidance-integration  
**Branch**: `018-aidr-guidance-integration`  
**Audience**: Developers implementing the AIDR integration tasks

---

## Prerequisites

- Python 3.10+ installed
- pnpm installed (monorepo package manager)
- Azure CLI authenticated with Australia East subscription
- Repository cloned and on the `018-aidr-guidance-integration` branch

```bash
git checkout 018-aidr-guidance-integration
pnpm install
```

## Project Layout

```
packages/domain/src/domain/models/   # Domain models (Pydantic BaseModel)
apps/agents/                          # Agent applications (FastAPI + create_app factory)
apps/agents/common/                   # Shared agent utilities
apps/api/app/                         # Platform API (FastAPI)
apps/api/app/api/routes/              # API route handlers
apps/api/app/services/                # Business logic services
infra/                                # Azure Bicep IaC
tests/                                # All test tiers
docs/aidr/                            # AIDR handbook reference materials (6 handbooks)
```

## Key References

| Document | Path | Purpose |
|----------|------|---------|
| Feature spec | `specs/018-aidr-guidance-integration/spec.md` | 54 FRs, 15 NFRs, 10 SCs |
| Implementation plan | `specs/018-aidr-guidance-integration/plan.md` | Architecture and structure |
| Research decisions | `specs/018-aidr-guidance-integration/research.md` | 13 design decisions |
| Data model | `specs/018-aidr-guidance-integration/data-model.md` | 4 new + 3 extended models |
| API contracts | `specs/018-aidr-guidance-integration/contracts/` | 6 API contract files |
| Constitution | `.specify/memory/constitution.md` | Supreme authority (v1.1.0) |
| AIDR Handbooks | `docs/aidr/` | 6 handbooks (reference material) |

## Domain Model Conventions

All domain models in this project follow these patterns:

```python
# File: packages/domain/src/domain/models/example.py
from datetime import UTC, datetime
from typing import Literal
from pydantic import BaseModel, Field

class Example(BaseModel):
    example_id: str                                    # String IDs, not UUIDs
    status: Literal["active", "closed"] = "active"     # Literal unions, not Enum
    items: list[str] = Field(default_factory=list)      # Mutable defaults via Field
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

**Rules**:
- Use `Literal[...]` for constrained types, never `enum.Enum`
- Use `str` for all IDs with descriptive prefixes (e.g., `aiims-`, `les-`, `rt-`, `es-`, `pprr-`)
- Use `Field(default_factory=...)` for all mutable defaults
- No ORM — relationships via `*_id` string references
- Validators via `@model_validator` when needed (see `HazardAssessment` for examples)

## Agent Development Conventions

### create_app() Factory Pattern

Every agent uses a factory function that returns a FastAPI app:

```python
# File: apps/agents/{agent_name}/agent.py
from fastapi import FastAPI

def create_app(config=None) -> FastAPI:
    app = FastAPI()
    # Store dependencies on app.state
    app.state.config = config or load_config()
    app.state.agent = AgentClass(app.state.config)

    @app.get("/health")
    async def health():
        # Return agent health status
        return {"status": "healthy", "agent": "agent_name"}

    return app
```

### Agent Communication via Handoffs

Agents communicate via `AgentHandoffEvent` (defined in `apps/agents/common/handoffs.py`):

```python
from apps.agents.common.handoffs import build_handoff

handoff = build_handoff(
    incident_id="inc-2025-001",
    source_agent="risk_assessment",
    target_agent="communication",
    scope_key="inc-2025-001",
    payload={"hazard_assessment_id": "ha-001", "recommendation": "escalate_warning"},
    confidence=0.85,
)
```

### Testing with TestClient

```python
from fastapi.testclient import TestClient
from apps.agents.{agent_name}.agent import create_app

def test_health():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
```

## New Capabilities — Implementation Guide

### 1. AWS Warning Generation (FR-001–007)

**Files to modify**: `apps/agents/communication/agent.py`, `apps/agents/communication/models.py`  
**Files to create**: `apps/agents/common/warning_compliance.py`, `apps/agents/communication/warning_builder.py`  
**Domain model**: Extend `PublicAlert` in `packages/domain/src/domain/models/public_alert.py`

The Communication Agent generates warnings. Add:
- AWS nested model builder (tier + hazard/location + action statement)
- Hazard icon selection logic
- Warning chain management (supersession via `superseded_warning_id`)
- Ten warning principles compliance checker (NFR-001: ≤5s)
- De-escalation and all-clear generation

### 2. AIIMS Role Assignment (FR-013–017)

**Files to create**: `packages/domain/src/domain/models/aiims_role_assignment.py`, `apps/api/app/services/aiims_service.py`, `apps/api/app/api/routes/aiims.py`, `apps/agents/common/aiims_mapping.py`

Platform service assigns agents to AIIMS functions per incident. Reference the existing `OperatingFramework` seed data (`frameworks_australia.json`) for AIIMS framework definitions.

Default AIIMS function mapping:
| Agent | Default AIIMS Function |
|-------|----------------------|
| Incident Controller (future) | Control |
| Monitoring Agent | Intelligence |
| Resource Allocation Agent | Planning + Logistics |
| Evacuation Agent | Operations |
| Communication Agent | Public Information |

### 3. Five-Stage Evacuation (FR-018–025)

**Files to modify**: `apps/agents/evacuation/agent.py`, `apps/agents/evacuation/models.py`  
**Files to create**: `packages/domain/src/domain/models/evacuation_stage.py`, `apps/agents/evacuation/stages.py`

The Evacuation Agent already has zone-based planning. Add the five-stage lifecycle **on top of** existing functionality — do not replace zone routing, transport coordination, or replanning capabilities.

### 4. PPRR Lifecycle (FR-026–031)

**Files to create**: `packages/domain/src/domain/models/pprr_phase_context.py`, `apps/api/app/services/pprr_service.py`, `apps/api/app/api/routes/pprr.py`, `apps/agents/common/pprr_lifecycle.py`  
**Files to modify**: `packages/domain/src/domain/models/incident.py`

Key design decision: `Incident.pprr_phase` for incident-bound phases; `PprrPhaseContext` for region/scenario-bound Prevention/Preparedness phases (see research.md R-001).

### 5. Community Recovery (FR-032–037)

**Files to create**: `packages/domain/src/domain/models/recovery_environment_tracker.py`, `apps/api/app/services/recovery_service.py`, `apps/api/app/api/routes/recovery.py`

Recovery tracking is a platform service, not an agent. Existing agents gain recovery-mode behaviour by checking `Incident.pprr_phase == "recovery"`.

### 6. Lessons Management (FR-038–042)

**Files to create**: `packages/domain/src/domain/models/lesson.py`, `apps/api/app/services/lessons_service.py`, `apps/api/app/api/routes/lessons.py`

Cross-cutting platform capability. Auto-triggered on Level 2+ incident closure and exercise completion.

## Running Tests

```bash
# Unit tests only (fast, no external dependencies)
python -m pytest tests/unit/ -v

# Contract tests (validates schemas and handoffs)
python -m pytest tests/contract/ -v

# Integration tests (requires Azure services)
python -m pytest tests/integration/ -v

# Specific AIDR tests (once implemented)
python -m pytest tests/unit/test_warning_compliance.py -v
python -m pytest tests/unit/test_aiims_role_assignment.py -v
python -m pytest tests/unit/test_evacuation_stages.py -v
python -m pytest tests/unit/test_pprr_lifecycle.py -v
python -m pytest tests/unit/test_recovery_tracker.py -v
python -m pytest tests/unit/test_lessons_management.py -v
```

## Running Agents Locally

```bash
# Start individual agents (each is a standalone FastAPI app)
cd apps/agents
uvicorn monitoring.agent:create_app --factory --port 8001
uvicorn risk_assessment.agent:create_app --factory --port 8002
uvicorn evacuation.agent:create_app --factory --port 8003
uvicorn resource_allocation.agent:create_app --factory --port 8004
uvicorn communication.agent:create_app --factory --port 8005

# Start platform API
cd apps/api
uvicorn app.main:create_app --factory --port 8000
```

## Infrastructure Changes

New Cosmos DB containers needed (all in existing `disaster-hub` account, Australia East):
- `recovery` (partition key: `/incident_id`)
- `lessons` (partition key: `/incident_id`)
- `aiims-assignments` (partition key: `/incident_id`)
- `evacuation-stages` (partition key: `/incident_id`)
- `pprr-contexts` (partition key: `/context_reference_id`)

Deploy via Bicep:
```bash
az deployment group create \
  --resource-group rg-disaster-hub \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json
```

## Checklist Before PR

- [ ] All new domain models exported from `packages/domain/src/domain/models/__init__.py`
- [ ] All new API routes registered in `apps/api/app/api/router.py`
- [ ] Health endpoints respond within 1s (NFR-009)
- [ ] All new Cosmos containers in Australia East/Southeast only (NFR-015)
- [ ] Social recovery indicators enforce k-anonymity ≥ 10 (NFR-014)
- [ ] Warning compliance validator runs within 5s (NFR-001)
- [ ] Unit tests pass: `python -m pytest tests/unit/ -v`
- [ ] Contract tests pass: `python -m pytest tests/contract/ -v`
- [ ] No secrets in source code
- [ ] Constitution alignment verified (see plan.md Constitution Check table)
