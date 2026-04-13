# Quickstart: AIDR Additional Guidance Integration

**Feature**: 019-aidr-additional-guidances  
**Date**: 2025-07-19

---

## Monorepo Layout

All code for this feature integrates into the existing monorepo structure:

```text
packages/domain/src/domain/models/    # Domain models (Pydantic BaseModel)
packages/domain/src/domain/seed/      # Seed data (JSON → Cosmos DB at deployment)
apps/agents/planning/                 # NEW Planning Agent (AIIMS Planning function)
apps/agents/monitoring/               # EXTENDED with M&E framework capabilities
apps/agents/common/                   # Shared agent infrastructure
apps/api/app/api/routes/              # Platform API routes
apps/api/app/services/                # Platform API business logic
apps/api/app/repositories/            # Cosmos DB repository pattern
infra/modules/                        # Azure Bicep IaC modules
tests/                                # Test tiers: unit, contract, integration, simulation
docs/aidr/                            # AIDR handbook reference materials (Markdown)
```

---

## Domain Model Conventions

All models in `packages/domain/src/domain/models/` follow these conventions:

1. **`Literal[...]` unions** for constrained types — never `Enum` classes:
   ```python
   PlanLifecycleState = Literal[
       "draft", "in_consultation", "under_review", "endorsed",
       "activated", "post_event_review", "superseded",
   ]
   ```

2. **String IDs** — no integer or UUID type fields:
   ```python
   plan_id: str  # e.g., "ep-a1b2c3d4"
   ```

3. **`Field(default_factory=...)` for mutable defaults**:
   ```python
   plan_sections: dict[str, PlanSection] = Field(default_factory=dict)
   activation_records: list[PlanActivationRecord] = Field(default_factory=list)
   ```

4. **`@model_validator(mode="after")`** for cross-field validation:
   ```python
   @model_validator(mode="after")
   def _validate_endorsed(self) -> "EmergencyPlan":
       if self.lifecycle_state in ("endorsed", "activated", "post_event_review"):
           if not self.endorsed_by:
               raise ValueError("endorsed_by required for endorsed+ states")
       return self
   ```

5. **Optional fields default to `None`**, not empty strings:
   ```python
   catalogue_indicator_id: str | None = None
   parent_plan_id: str | None = None
   ```

6. **Docstrings** with FR/research references:
   ```python
   """Emergency Plan — AIDR-compliant emergency planning with 7-state lifecycle.

   27 plan sections per Emergency Planning Handbook Chapter 3.
   Eight planning principles validation (FR-004).

   FRs: FR-001–007 | Research: R-001, R-002, R-008
   """
   ```

---

## Planning Agent Pattern

The new Planning Agent in `apps/agents/planning/` follows the established agent pattern:

### `create_app()` factory (agent.py)

```python
def create_app(
    agent: PlanningAgent | None = None,
    audit_writer=None,
    config: PlanningConfig | None = None,
) -> FastAPI:
    _config = config or PlanningConfig()
    app = FastAPI(title="Planning Agent", version=_config.agent_version)

    # Store dependencies on app.state
    app.state.agent = agent
    app.state.audit_writer = audit_writer
    app.state.config = _config

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        # Standard health endpoint pattern
        ...

    return app
```

### Config pattern (config.py)

```python
@dataclass(frozen=True)
class PlanningConfig:
    plan_generation_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("PLAN_GENERATION_TIMEOUT_SECONDS", "15"))
    )
    plan_review_reminder_days: int = field(
        default_factory=lambda: int(os.getenv("PLAN_REVIEW_REMINDER_DAYS", "365"))
    )
    agent_version: str = field(
        default_factory=lambda: os.getenv("AGENT_VERSION", "0.1.0")
    )
```

### Entrypoint (__main__.py)

```python
if __name__ == "__main__":
    import uvicorn
    _PORT = int(os.environ.get("PORT", "8085"))
    app = create_app(agent=PlanningAgent(config=PlanningConfig()))
    uvicorn.run(app, host="0.0.0.0", port=_PORT)
```

---

## State Machine Pattern

The plan lifecycle state machine follows `common/pprr_lifecycle.py`:

```python
# plan_lifecycle.py
VALID_PLAN_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["in_consultation"],
    "in_consultation": ["under_review", "draft"],
    "under_review": ["endorsed", "draft"],
    "endorsed": ["activated", "superseded"],
    "activated": ["post_event_review"],
    "post_event_review": ["draft"],  # Creates new version; original → superseded
    "superseded": [],  # Terminal state
}

TRANSITION_ROLES: dict[tuple[str, str], str] = {
    ("draft", "in_consultation"): "planning_officer",
    ("in_consultation", "under_review"): "planning_officer",
    ("in_consultation", "draft"): "planning_officer",
    ("under_review", "endorsed"): "designated_authority",
    ("under_review", "draft"): "designated_authority",
    ("endorsed", "activated"): "incident_controller",
    ("activated", "post_event_review"): "incident_controller_or_planning_officer",
    ("post_event_review", "draft"): "planning_officer",
}

def validate_plan_transition(
    current_state: str,
    target_state: str,
    user_role: str,
) -> tuple[bool, str]:
    valid_targets = VALID_PLAN_TRANSITIONS.get(current_state, [])
    if target_state not in valid_targets:
        return False, f"Invalid transition: '{current_state}' → '{target_state}'"
    required_role = TRANSITION_ROLES.get((current_state, target_state))
    if required_role and user_role not in required_role.split("_or_"):
        return False, f"Role '{user_role}' cannot perform '{current_state}' → '{target_state}'"
    return True, ""
```

---

## AIDR Catalogue Seed Data

Catalogue seed data lives in `packages/domain/src/domain/seed/recovery-catalogue/`:

```json
// social.json (example structure)
{
  "domain": "social",
  "outcomes": [
    {
      "outcome_id": "aidr:social:community-health-levels",
      "objective_type": "sustainability",
      "title": "Community health levels are restored",
      "description": "...",
      "activities": [
        {
          "activity_id": "aidr:social:community-health-levels:act:1",
          "title": "Establish community health outreach programs",
          "description": "..."
        }
      ],
      "indicators": [
        {
          "indicator_id": "aidr:social:community-health-levels:ind:1",
          "title": "Mental health service utilisation rate",
          "description": "...",
          "data_collection_methodology": "Health service records; community surveys",
          "indicator_type": "quantitative"
        }
      ]
    }
  ]
}
```

Seeded via `scripts/seed_loader.py` → Cosmos DB `recovery-catalogue` container, partitioned by `domain`.

---

## Agent Handoff Pattern

The Planning Agent uses the established `build_handoff()` pattern:

```python
from common.handoffs import build_handoff

# Plan activation handoff (incident → planning)
def build_plan_activation_handoff(
    *, incident_id: str, plan_id: str, activated_by: str,
) -> AgentHandoffEvent:
    return build_handoff(
        incident_id=incident_id,
        source_agent="incident_management",
        target_agent="planning",
        scope_key=f"plan_activation:{plan_id}",
        payload={"plan_id": plan_id, "activated_by": activated_by},
        confidence=1.0,
    )

# M&E initialisation handoff (planning → monitoring)
def build_me_framework_handoff(
    *, incident_id: str, plan_id: str,
) -> AgentHandoffEvent:
    return build_handoff(
        incident_id=incident_id,
        source_agent="planning",
        target_agent="monitoring",
        scope_key="me_framework_init",
        payload={"plan_id": plan_id, "trigger": "recovery_arrangements_activated"},
        confidence=0.9,
    )
```

---

## Testing Pattern

Use `FastAPI TestClient` for agent endpoint tests:

```python
from fastapi.testclient import TestClient
from planning.agent import create_app, PlanningAgent
from planning.config import PlanningConfig

def test_planning_agent_health():
    config = PlanningConfig()
    agent = PlanningAgent(config=config)
    app = create_app(agent=agent, config=config)
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "agent_version" in data
```

---

## Feature Implementation Guide

| Capability | Files to Create/Modify | Key FRs |
|-----------|----------------------|---------|
| Emergency Plan model + lifecycle | `packages/domain/.../emergency_plan.py`, `apps/agents/planning/plan_lifecycle.py` | FR-001–007 |
| Planning Agent | `apps/agents/planning/agent.py`, `config.py`, `models.py`, `pipeline.py` | FR-001, FR-007 |
| Planning Process Record | `packages/domain/.../planning_process_record.py` | FR-001 |
| M&E Framework model | `packages/domain/.../me_framework.py` | FR-008–014 |
| Program Logic model | `packages/domain/.../program_logic_model.py` | FR-010 |
| Recovery Catalogue models | `packages/domain/.../recovery_outcome.py` | FR-015–024 |
| Catalogue seed data | `packages/domain/src/domain/seed/recovery-catalogue/*.json` | FR-015 |
| Evaluation Report model | `packages/domain/.../evaluation_report.py` | FR-014 |
| AI analysis service | `apps/agents/monitoring/indicator_analysis.py` | FR-025–028 |
| M&E framework service | `apps/agents/monitoring/me_framework_service.py` | FR-008–014 |
| Cosmos DB containers | `infra/modules/emergency-planning.bicep` | NFR-008 |
| RecoveryIndicator extension | `packages/domain/.../recovery_environment_tracker.py` | FR-015, FR-030 |
| Spec 018 integration | `apps/agents/monitoring/catalogue_service.py` | FR-030, FR-031, FR-033 |

---

## Infrastructure

New Bicep module at `infra/modules/emergency-planning.bicep`:

```bicep
// Emergency Plans — partition by region_id (plan hierarchy queries)
resource emergencyPlansContainer '...' = {
  name: 'emergency-plans'
  properties: {
    resource: {
      id: 'emergency-plans'
      partitionKey: { paths: ['/region_id'], kind: 'Hash' }
      // Composite indexes for lifecycle_state + updated_at, hierarchy_level + lifecycle_state
    }
    options: { autoscaleSettings: { maxThroughput: 1000 } }
  }
}

// Recovery Programmes — partition by incident_id (M&E frameworks, program logic, eval reports)
resource recoveryProgrammesContainer '...' = {
  name: 'recovery-programmes'
  // partitionKey: /incident_id
}

// Recovery Catalogue — partition by domain (immutable AIDR reference data)
resource recoveryCatalogueContainer '...' = {
  name: 'recovery-catalogue'
  // partitionKey: /domain
}
```

Referenced in `main.bicep`:
```bicep
module emergencyPlanning './modules/emergency-planning.bicep' = {
  name: 'emergency-planning'
  params: {
    cosmosDbName: cosmosDb.name
    cosmosAccountName: cosmos.name
  }
}
```
