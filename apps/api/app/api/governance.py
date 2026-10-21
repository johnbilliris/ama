from datetime import UTC, datetime
from uuid import uuid4

from app.api.dependencies.governance_auth import (
    GovernancePrincipal,
    require_governance_read,
    require_governance_write,
)
from app.api.dependencies.governance_composition import get_governance_cache, get_governance_registry
from app.services.governance_cache import GovernanceCacheService
from app.services.governance_registry import GovernanceRegistryService
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from packages.domain.src.domain.models.agent_governance import (
    AgentGovernanceAssignment,
    AgentName,
    AssignmentRole,
)
from packages.domain.src.domain.models.constitutional_assessment import (
    AssessmentComplianceStatus,
    AssessmentTrigger,
    ConstitutionalAssessment,
    ConstitutionalPrinciple,
)
from packages.domain.src.domain.models.functional_domain_precedence import (
    FunctionalDomainPrecedence,
)
from packages.domain.src.domain.models.handoff_chain import (
    HandoffChainDefinition,
    HandoffStep,
    SignalCategory,
)

router = APIRouter(tags=["Governance"])


# --- Compliance endpoints (US2) ---


class AssessmentCreate(BaseModel):
    principle: ConstitutionalPrinciple
    compliance_status: AssessmentComplianceStatus
    explanation: str
    conditions: list[str] = []
    gaps: list[str] = []
    assessor_id: str
    triggered_by: AssessmentTrigger = "initial_review"


@router.get("/data-sources/{data_source_id}/compliance", dependencies=[Depends(require_governance_read)])
async def get_compliance_profile(
    data_source_id: str,
    registry: GovernanceRegistryService = Depends(get_governance_registry),
) -> dict[str, object]:
    profile = registry.get_compliance_profile(data_source_id)
    return {
        "data_source_id": profile["data_source_id"],
        "current_assessments": [a.model_dump(mode="json") for a in profile["current_assessments"]],
        "historical_assessments": [a.model_dump(mode="json") for a in profile["historical_assessments"]],
    }


@router.post(
    "/data-sources/{data_source_id}/compliance",
    status_code=201,
)
async def create_assessment(
    data_source_id: str,
    body: AssessmentCreate,
    principal: GovernancePrincipal = Depends(require_governance_write),
    registry: GovernanceRegistryService = Depends(get_governance_registry),
) -> dict[str, object]:
    assessment = ConstitutionalAssessment(
        assessment_id=f"assess-{uuid4().hex[:12]}",
        data_source_id=data_source_id,
        assessed_at=datetime.now(UTC),
        assessor_id=principal.subject,
        **body.model_dump(exclude={"assessor_id"}),
    )
    saved = registry.create_assessment(assessment, actor_id=principal.subject)
    return saved.model_dump(mode="json")


# --- Grace period (US2) ---


class GracePeriodAction(BaseModel):
    action: str  # "extend" or "block"
    extend_hours: int | None = None
    rationale: str = ""


@router.post(
    "/data-sources/{data_source_id}/governance/grace-period",
)
async def manage_grace_period(
    data_source_id: str,
    body: GracePeriodAction,
    principal: GovernancePrincipal = Depends(require_governance_write),
    registry: GovernanceRegistryService = Depends(get_governance_registry),
) -> dict[str, object]:
    if body.action == "extend":
        if not body.extend_hours or body.extend_hours < 1:
            raise HTTPException(status_code=400, detail="extend_hours must be >= 1 for extend action.")
        result = registry.extend_grace_period(
            data_source_id,
            body.extend_hours,
            actor_id=principal.subject,
            rationale=body.rationale,
        )
    elif body.action == "block":
        result = registry.block_source_immediately(data_source_id, actor_id=principal.subject)
    else:
        raise HTTPException(status_code=400, detail="action must be 'extend' or 'block'.")
    return result.model_dump(mode="json")


# --- Agent governance endpoints (US3) ---


class AgentAssignmentCreate(BaseModel):
    agent_name: AgentName
    role: AssignmentRole
    scope_of_responsibility: str
    operational_conditions: list[str] = []
    assigned_by: str


@router.get("/data-sources/{data_source_id}/governance", dependencies=[Depends(require_governance_read)])
async def get_governance_profile(
    data_source_id: str,
    registry: GovernanceRegistryService = Depends(get_governance_registry),
) -> dict[str, object]:
    profile = registry.get_governance_profile(data_source_id)
    return {
        "data_source_id": profile["data_source_id"],
        "assignments": [a.model_dump(mode="json") for a in profile["assignments"]],
        "handoff_chain": profile["handoff_chain"].model_dump(mode="json") if profile["handoff_chain"] else None,
    }


@router.post(
    "/data-sources/{data_source_id}/governance/assignments",
    status_code=201,
)
async def assign_agent(
    data_source_id: str,
    body: AgentAssignmentCreate,
    principal: GovernancePrincipal = Depends(require_governance_write),
    registry: GovernanceRegistryService = Depends(get_governance_registry),
) -> dict[str, object]:
    assignment = AgentGovernanceAssignment(
        assignment_id=f"assign-{uuid4().hex[:12]}",
        data_source_id=data_source_id,
        assigned_at=datetime.now(UTC),
        **body.model_dump(exclude={"assigned_by"}),
        assigned_by=principal.subject,
    )
    saved = registry.assign_agent(assignment, actor_id=principal.subject)
    return saved.model_dump(mode="json")


# --- Handoff chain (US3) ---


class HandoffStepCreate(BaseModel):
    step_order: int
    source_agent: str
    target_agent: str
    confidence_threshold: float | None = None
    category_filter: list[SignalCategory] = []
    payload_contract_ref: str | None = None


class HandoffChainCreate(BaseModel):
    steps: list[HandoffStepCreate]
    created_by: str


@router.put(
    "/data-sources/{data_source_id}/governance/handoff-chain",
)
async def define_handoff_chain(
    data_source_id: str,
    body: HandoffChainCreate,
    principal: GovernancePrincipal = Depends(require_governance_write),
    registry: GovernanceRegistryService = Depends(get_governance_registry),
    cache: GovernanceCacheService = Depends(get_governance_cache),
) -> dict[str, object]:
    chain = HandoffChainDefinition(
        chain_id=f"chain-{uuid4().hex[:12]}",
        data_source_id=data_source_id,
        steps=[HandoffStep(**s.model_dump()) for s in body.steps],
        created_by=principal.subject,
        created_at=datetime.now(UTC),
    )
    saved = registry.define_handoff_chain(chain, actor_id=principal.subject)
    cache.invalidate(data_source_id)
    return saved.model_dump(mode="json")


# --- Functional-domain precedence (US3) ---


class PrecedenceCreate(BaseModel):
    hazard_type: SignalCategory
    jurisdiction_id: str | None = None
    primary_data_source_id: str
    rationale: str
    created_by: str


@router.get("/governance/precedence", dependencies=[Depends(require_governance_read)])
async def list_precedence(
    hazard_type: str | None = None,
    jurisdiction_id: str | None = None,
    registry: GovernanceRegistryService = Depends(get_governance_registry),
) -> list[dict[str, object]]:
    results = registry.list_precedence(hazard_type, jurisdiction_id)
    return [p.model_dump(mode="json") for p in results]


@router.post(
    "/governance/precedence",
    status_code=201,
)
async def set_precedence(
    body: PrecedenceCreate,
    principal: GovernancePrincipal = Depends(require_governance_write),
    registry: GovernanceRegistryService = Depends(get_governance_registry),
) -> dict[str, object]:
    precedence = FunctionalDomainPrecedence(
        precedence_id=f"prec-{uuid4().hex[:12]}",
        created_at=datetime.now(UTC),
        **body.model_dump(exclude={"created_by"}),
        created_by=principal.subject,
    )
    saved = registry.set_precedence(precedence, actor_id=principal.subject)
    return saved.model_dump(mode="json")


# --- Handoff lookup (US3, NFR-001) ---


@router.get("/governance/handoff-lookup", dependencies=[Depends(require_governance_read)])
async def lookup_handoff_chain(
    data_source_id: str,
    registry: GovernanceRegistryService = Depends(get_governance_registry),
    cache: GovernanceCacheService = Depends(get_governance_cache),
) -> dict[str, object]:
    cached = cache.get(data_source_id)
    if cached:
        return {**cached.model_dump(mode="json"), "_cache_status": "HIT"}

    chain = registry.lookup_handoff_chain(data_source_id)
    if not chain:
        raise HTTPException(status_code=404, detail=f"No active handoff chain for source '{data_source_id}'.")
    cache.put(data_source_id, chain)
    return {**chain.model_dump(mode="json"), "_cache_status": "MISS"}


# --- Governance dashboard (US4) ---


@router.get("/governance/dashboard", dependencies=[Depends(require_governance_read)])
async def get_governance_dashboard(
    compliance_status: str | None = None,
    governance_status: str | None = None,
    kind: str | None = None,
    agent_name: str | None = None,
    geographic_coverage: str | None = None,
    registry: GovernanceRegistryService = Depends(get_governance_registry),
) -> dict[str, object]:
    summary = registry.get_dashboard_summary()
    filters: dict[str, str | None] = {
        k: v
        for k, v in {
            "compliance_status": compliance_status,
            "governance_status": governance_status,
            "kind": kind,
            "geographic_coverage": geographic_coverage,
        }.items()
        if v is not None
    }
    sources = registry.list_sources(**filters)
    active_sources = [s for s in sources if s.status != "deactivated"]
    return {
        "summary": summary,
        "sources": [s.model_dump(mode="json") for s in active_sources],
    }


# --- Audit trail (US4) ---


@router.get("/data-sources/{data_source_id}/audit", dependencies=[Depends(require_governance_read)])
async def get_audit_trail(
    data_source_id: str,
    action: str | None = None,
    from_dt: str | None = None,
    to_dt: str | None = None,
    registry: GovernanceRegistryService = Depends(get_governance_registry),
) -> list[dict[str, object]]:
    from_datetime = datetime.fromisoformat(from_dt) if from_dt else None
    to_datetime = datetime.fromisoformat(to_dt) if to_dt else None
    entries = registry.get_audit_trail(data_source_id, action, from_datetime, to_datetime)
    return [e.model_dump(mode="json") for e in entries]


# --- Foundry carveout registry (spec-035 T070) ---


@router.get("/governance/carveout-registry", dependencies=[Depends(require_governance_read)])
async def get_carveout_registry() -> dict[str, object]:
    """List Foundry carve-out models with their review cadence (FR-029)."""

    from app.repositories.carveout_registry_repository import (
        get_carveout_registry_repository,
    )

    repository = get_carveout_registry_repository()
    return {"entries": repository.list_entries()}
