from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.services.governance_cache import GovernanceCacheService
from app.services.governance_registry import GovernanceRegistryService
from packages.domain.src.domain.models.agent_governance import AgentName, AssignmentRole
from packages.domain.src.domain.models.constitutional_assessment import (
    AssessmentComplianceStatus,
    AssessmentTrigger,
    ConstitutionalAssessment,
    ConstitutionalPrinciple,
)
from packages.domain.src.domain.models.agent_governance import AgentGovernanceAssignment
from packages.domain.src.domain.models.functional_domain_precedence import FunctionalDomainPrecedence
from packages.domain.src.domain.models.handoff_chain import HandoffChainDefinition, HandoffStep, SignalCategory

GOVERNANCE_WRITE_ROLES = frozenset({"governance_lead", "safety_lead", "system_architect"})
GOVERNANCE_READ_ROLES = frozenset({"governance_lead", "safety_lead", "system_architect", "incident_commander", "executive", "auditor"})


def _get_user_role(request: Request) -> str:
    return request.headers.get("X-User-Role", "reader")


def require_governance_write(request: Request) -> None:
    role = _get_user_role(request)
    if role not in GOVERNANCE_WRITE_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions for governance write operations.")


def require_governance_read(request: Request) -> None:
    role = _get_user_role(request)
    if role not in GOVERNANCE_READ_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions for governance read operations.")


router = APIRouter(tags=["Governance"])

_service = GovernanceRegistryService()
_cache = GovernanceCacheService()


# --- Compliance endpoints (US2) ---

class AssessmentCreate(BaseModel):
    principle: ConstitutionalPrinciple
    compliance_status: AssessmentComplianceStatus
    explanation: str
    conditions: list[str] = []
    gaps: list[str] = []
    assessor_id: str
    triggered_by: AssessmentTrigger = "initial_review"


@router.get("/data-sources/{data_source_id}/compliance")
async def get_compliance_profile(data_source_id: str) -> dict:
    profile = _service.get_compliance_profile(data_source_id)
    return {
        "data_source_id": profile["data_source_id"],
        "current_assessments": [a.model_dump(mode="json") for a in profile["current_assessments"]],
        "historical_assessments": [a.model_dump(mode="json") for a in profile["historical_assessments"]],
    }


@router.post("/data-sources/{data_source_id}/compliance", status_code=201)
async def create_assessment(data_source_id: str, body: AssessmentCreate) -> dict:
    assessment = ConstitutionalAssessment(
        assessment_id=f"assess-{uuid4().hex[:12]}",
        data_source_id=data_source_id,
        assessed_at=datetime.now(UTC),
        **body.model_dump(),
    )
    saved = _service.create_assessment(assessment, actor_id=body.assessor_id)
    return saved.model_dump(mode="json")


# --- Grace period (US2) ---

class GracePeriodAction(BaseModel):
    action: str  # "extend" or "block"
    extend_hours: int | None = None
    rationale: str = ""


@router.post("/data-sources/{data_source_id}/governance/grace-period")
async def manage_grace_period(data_source_id: str, body: GracePeriodAction) -> dict:
    if body.action == "extend":
        if not body.extend_hours or body.extend_hours < 1:
            raise HTTPException(status_code=400, detail="extend_hours must be >= 1 for extend action.")
        result = _service.extend_grace_period(data_source_id, body.extend_hours, actor_id="api-user", rationale=body.rationale)
    elif body.action == "block":
        result = _service.block_source_immediately(data_source_id, actor_id="api-user")
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


@router.get("/data-sources/{data_source_id}/governance")
async def get_governance_profile(data_source_id: str) -> dict:
    profile = _service.get_governance_profile(data_source_id)
    return {
        "data_source_id": profile["data_source_id"],
        "assignments": [a.model_dump(mode="json") for a in profile["assignments"]],
        "handoff_chain": profile["handoff_chain"].model_dump(mode="json") if profile["handoff_chain"] else None,
    }


@router.post("/data-sources/{data_source_id}/governance/assignments", status_code=201)
async def assign_agent(data_source_id: str, body: AgentAssignmentCreate) -> dict:
    assignment = AgentGovernanceAssignment(
        assignment_id=f"assign-{uuid4().hex[:12]}",
        data_source_id=data_source_id,
        assigned_at=datetime.now(UTC),
        **body.model_dump(),
    )
    saved = _service.assign_agent(assignment, actor_id=body.assigned_by)
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


@router.put("/data-sources/{data_source_id}/governance/handoff-chain")
async def define_handoff_chain(data_source_id: str, body: HandoffChainCreate) -> dict:
    chain = HandoffChainDefinition(
        chain_id=f"chain-{uuid4().hex[:12]}",
        data_source_id=data_source_id,
        steps=[HandoffStep(**s.model_dump()) for s in body.steps],
        created_by=body.created_by,
        created_at=datetime.now(UTC),
    )
    saved = _service.define_handoff_chain(chain, actor_id=body.created_by)
    _cache.invalidate(data_source_id)
    return saved.model_dump(mode="json")


# --- Functional-domain precedence (US3) ---

class PrecedenceCreate(BaseModel):
    hazard_type: SignalCategory
    jurisdiction_id: str | None = None
    primary_data_source_id: str
    rationale: str
    created_by: str


@router.get("/governance/precedence")
async def list_precedence(hazard_type: str | None = None, jurisdiction_id: str | None = None) -> list[dict]:
    results = _service.list_precedence(hazard_type, jurisdiction_id)
    return [p.model_dump(mode="json") for p in results]


@router.post("/governance/precedence", status_code=201)
async def set_precedence(body: PrecedenceCreate) -> dict:
    precedence = FunctionalDomainPrecedence(
        precedence_id=f"prec-{uuid4().hex[:12]}",
        created_at=datetime.now(UTC),
        **body.model_dump(),
    )
    saved = _service.set_precedence(precedence, actor_id=body.created_by)
    return saved.model_dump(mode="json")


# --- Handoff lookup (US3, NFR-001) ---

@router.get("/governance/handoff-lookup")
async def lookup_handoff_chain(data_source_id: str) -> dict:
    cached = _cache.get(data_source_id)
    if cached:
        return {**cached.model_dump(mode="json"), "_cache_status": "HIT"}

    chain = _service.lookup_handoff_chain(data_source_id)
    if not chain:
        raise HTTPException(status_code=404, detail=f"No active handoff chain for source '{data_source_id}'.")
    _cache.put(data_source_id, chain)
    return {**chain.model_dump(mode="json"), "_cache_status": "MISS"}


# --- Governance dashboard (US4) ---

@router.get("/governance/dashboard")
async def get_governance_dashboard(
    compliance_status: str | None = None,
    governance_status: str | None = None,
    kind: str | None = None,
    agent_name: str | None = None,
    geographic_coverage: str | None = None,
) -> dict:
    summary = _service.get_dashboard_summary()
    filters: dict[str, str | None] = {
        k: v for k, v in {
            "compliance_status": compliance_status,
            "governance_status": governance_status,
            "kind": kind,
            "geographic_coverage": geographic_coverage,
        }.items() if v is not None
    }
    sources = _service.list_sources(**filters)
    active_sources = [s for s in sources if s.status != "deactivated"]
    return {
        "summary": summary,
        "sources": [s.model_dump(mode="json") for s in active_sources],
    }


# --- Audit trail (US4) ---

@router.get("/data-sources/{data_source_id}/audit")
async def get_audit_trail(
    data_source_id: str,
    action: str | None = None,
    from_dt: str | None = None,
    to_dt: str | None = None,
) -> list[dict]:
    from_datetime = datetime.fromisoformat(from_dt) if from_dt else None
    to_datetime = datetime.fromisoformat(to_dt) if to_dt else None
    entries = _service.get_audit_trail(data_source_id, action, from_datetime, to_datetime)
    return [e.model_dump(mode="json") for e in entries]
