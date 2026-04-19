"""Governance dashboard API router.

All 13 dashboard endpoints for the governance dashboard feature (021).
Read-only endpoints except audit export (creates files, not state changes).
"""

import logging
import time
from datetime import datetime

from app.models.audit_export import AuditExportJobResponse, AuditExportRequest
from app.models.governance_health import (
    AuditDecisionChainResponse,
    AuditTrailResponse,
    ComplianceDetailResponse,
    ComplianceMatrixResponse,
    DashboardConfigResponse,
    ExecutiveSummaryResponse,
    OperationalReadinessResponse,
    RecoveryDomainDetail,
    RecoveryProgressResponse,
    RiskDetailResponse,
    RiskWarningResponse,
)
from app.services.audit_export_service import AuditExportService
from app.services.dashboard_aggregation_service import DashboardAggregationService
from app.services.governance_data_service import GovernanceDataService
from app.services.seed_service import SeedService
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from packages.domain.src.domain.models.dashboard_widget_config import (
    AIIMS_AUTHORITY_RANKS,
    WidgetDefinition,
)

logger = logging.getLogger("governance_dashboard")
perf_logger = logging.getLogger("governance_dashboard.perf")

router = APIRouter(
    prefix="/governance/dashboard",
    tags=["governance-dashboard"],
)


# --- Performance logging middleware for dashboard endpoints (T097) ---


def _log_perf(endpoint: str, start: float, tenant_id: str = "live") -> None:
    """Log endpoint response time for performance monitoring."""
    elapsed_ms = round((time.monotonic() - start) * 1000, 1)
    perf_logger.info(
        "dashboard.perf endpoint=%s tenant=%s elapsed_ms=%.1f",
        endpoint,
        tenant_id,
        elapsed_ms,
    )
    if elapsed_ms > 2000:
        perf_logger.warning(
            "dashboard.perf.slow endpoint=%s elapsed_ms=%.1f exceeds_target=2000ms",
            endpoint,
            elapsed_ms,
        )


_data_service: GovernanceDataService | None = None
_aggregation: DashboardAggregationService | None = None
_export_service = AuditExportService()


def _get_aggregation() -> DashboardAggregationService:
    """Lazy-initialise DashboardAggregationService with seed data."""
    global _data_service, _aggregation
    if _aggregation is None:
        from pathlib import Path

        from packages.domain.src.domain.seed import bootstrap as _seed_mod

        _seed_root = Path(_seed_mod.__file__).resolve().parent
        _seed_data = SeedService().load(_seed_root)
        _data_service = GovernanceDataService(seed_data=_seed_data)
        _aggregation = DashboardAggregationService(data_service=_data_service)
    return _aggregation


# --- Role-to-widget mapping configuration (US7) ---

ROLE_WIDGET_CONFIGS: dict[str, dict] = {
    "incident_controller": {
        "default_view": "executive_summary",
        "widgets": [
            {
                "widget_id": "health_score_gauge",
                "widget_type": "gauge",
                "display_name": "Health Score",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "constitutional_gates",
                "widget_type": "grid",
                "display_name": "Constitutional Gates",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "active_incidents",
                "widget_type": "counter",
                "display_name": "Active Incidents",
                "priority": 3,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "resource_utilisation",
                "widget_type": "gauge",
                "display_name": "Resource Utilisation",
                "priority": 4,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "risk_summary",
                "widget_type": "chart",
                "display_name": "Strategic Risk Summary",
                "priority": 5,
                "data_endpoint": "/governance/dashboard/risk",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "pprr_indicator",
                "widget_type": "indicator",
                "display_name": "PPRR Phase",
                "priority": 6,
                "data_endpoint": "/governance/dashboard/readiness",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "warning_compliance",
                "widget_type": "grid",
                "display_name": "Alert Approval Status",
                "priority": 7,
                "data_endpoint": "/governance/dashboard/risk",
                "refresh_group": "active_incident",
            },
        ],
    },
    "operations_officer": {
        "default_view": "executive_summary",
        "widgets": [
            {
                "widget_id": "active_incidents",
                "widget_type": "counter",
                "display_name": "Active Incidents",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "resource_utilisation",
                "widget_type": "gauge",
                "display_name": "Resource Utilisation",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "pprr_indicator",
                "widget_type": "indicator",
                "display_name": "PPRR Phase (Response)",
                "priority": 3,
                "data_endpoint": "/governance/dashboard/readiness",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "deployment_status",
                "widget_type": "counter",
                "display_name": "Deployment Status",
                "priority": 4,
                "data_endpoint": "/governance/dashboard/readiness",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "field_safety",
                "widget_type": "indicator",
                "display_name": "Field Safety Status",
                "priority": 5,
                "data_endpoint": "/governance/dashboard/readiness",
                "refresh_group": "active_incident",
            },
        ],
    },
    "planning_officer": {
        "default_view": "operational_readiness",
        "widgets": [
            {
                "widget_id": "emergency_plans",
                "widget_type": "table",
                "display_name": "Emergency Plan Status",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/readiness",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "pprr_indicator",
                "widget_type": "indicator",
                "display_name": "PPRR Phase Indicators",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/readiness",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "recovery_trajectory",
                "widget_type": "chart",
                "display_name": "Recovery Trajectory",
                "priority": 3,
                "data_endpoint": "/governance/dashboard/recovery",
                "refresh_group": "steady_state",
            },
        ],
    },
    "intelligence_officer": {
        "default_view": "compliance",
        "widgets": [
            {
                "widget_id": "compliance_matrix",
                "widget_type": "table",
                "display_name": "Data Source Compliance",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/compliance",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "health_score_gauge",
                "widget_type": "gauge",
                "display_name": "Health Score Trend",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "steady_state",
            },
        ],
    },
    "logistics_officer": {
        "default_view": "operational_readiness",
        "widgets": [
            {
                "widget_id": "resource_utilisation",
                "widget_type": "gauge",
                "display_name": "Resource Utilisation",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "emergency_plans",
                "widget_type": "table",
                "display_name": "Emergency Plan Logistics",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/readiness",
                "refresh_group": "steady_state",
            },
        ],
    },
    "public_information_officer": {
        "default_view": "risk_warning",
        "widgets": [
            {
                "widget_id": "warning_compliance",
                "widget_type": "grid",
                "display_name": "AWS Warning Compliance",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/risk",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "broadcast_reach",
                "widget_type": "gauge",
                "display_name": "Broadcast Reach",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/risk",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "multilingual_coverage",
                "widget_type": "gauge",
                "display_name": "Multilingual Coverage %",
                "priority": 3,
                "data_endpoint": "/governance/dashboard/risk",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "a11y_compliance",
                "widget_type": "indicator",
                "display_name": "Accessibility Compliance",
                "priority": 4,
                "data_endpoint": "/governance/dashboard/risk",
                "refresh_group": "steady_state",
            },
        ],
    },
    "executive_leader": {
        "default_view": "executive_summary",
        "widgets": [
            {
                "widget_id": "health_score_gauge",
                "widget_type": "gauge",
                "display_name": "Health Score",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "constitutional_gates",
                "widget_type": "grid",
                "display_name": "Constitutional Gates",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "risk_summary",
                "widget_type": "chart",
                "display_name": "Strategic Risk Summary",
                "priority": 3,
                "data_endpoint": "/governance/dashboard/risk",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "recovery_domains",
                "widget_type": "progress_bar",
                "display_name": "Recovery Domain Progress",
                "priority": 4,
                "data_endpoint": "/governance/dashboard/recovery",
                "refresh_group": "steady_state",
            },
        ],
    },
    "observer_auditor": {
        "default_view": "audit_trail",
        "widgets": [
            {
                "widget_id": "audit_search",
                "widget_type": "search",
                "display_name": "Audit Trail Search",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/audit",
                "refresh_group": "manual_only",
            },
            {
                "widget_id": "compliance_matrix",
                "widget_type": "table",
                "display_name": "Compliance Matrix",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/compliance",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "constitutional_gates",
                "widget_type": "grid",
                "display_name": "Constitutional Gate Details",
                "priority": 3,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "steady_state",
            },
        ],
    },
    "risk_manager": {
        "default_view": "risk_warning",
        "widgets": [
            {
                "widget_id": "risk_register",
                "widget_type": "table",
                "display_name": "Risk Register",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/risk",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "warning_compliance",
                "widget_type": "grid",
                "display_name": "AWS Compliance",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/risk",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "recovery_domains",
                "widget_type": "progress_bar",
                "display_name": "Recovery Domain Progress",
                "priority": 3,
                "data_endpoint": "/governance/dashboard/recovery",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "health_score_gauge",
                "widget_type": "gauge",
                "display_name": "Governance Health Score",
                "priority": 4,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "steady_state",
            },
        ],
    },
    "resilience_planner": {
        "default_view": "operational_readiness",
        "widgets": [
            {
                "widget_id": "pprr_indicator",
                "widget_type": "indicator",
                "display_name": "PPRR Phase Indicators",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/readiness",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "emergency_plans",
                "widget_type": "table",
                "display_name": "Emergency Plan Lifecycle",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/readiness",
                "refresh_group": "steady_state",
            },
            {
                "widget_id": "recovery_domains",
                "widget_type": "progress_bar",
                "display_name": "Recovery Domain Progress",
                "priority": 3,
                "data_endpoint": "/governance/dashboard/recovery",
                "refresh_group": "steady_state",
            },
        ],
    },
    "field_coordinator": {
        "default_view": "executive_summary",
        "widgets": [
            {
                "widget_id": "active_incidents",
                "widget_type": "counter",
                "display_name": "Active Incidents",
                "priority": 1,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "pprr_indicator",
                "widget_type": "indicator",
                "display_name": "PPRR Phase",
                "priority": 2,
                "data_endpoint": "/governance/dashboard/readiness",
                "refresh_group": "active_incident",
            },
            {
                "widget_id": "resource_utilisation",
                "widget_type": "gauge",
                "display_name": "Resource Utilisation",
                "priority": 3,
                "data_endpoint": "/governance/dashboard/summary",
                "refresh_group": "active_incident",
            },
        ],
    },
}


def _resolve_user_roles(request: Request) -> list[str]:
    """Extract AIIMS roles from request headers/claims."""
    role_header = request.headers.get("X-User-Roles", request.headers.get("X-User-Role", ""))
    if not role_header:
        return []
    return [r.strip() for r in role_header.split(",") if r.strip()]


def _get_tenant_id(request: Request) -> str:
    """Extract tenant_id from request state."""
    ctx = getattr(request.state, "tenant_context", None)
    if ctx:
        return ctx.tenant_id
    return request.headers.get("X-Tenant-Id", "live")


def _resolve_widget_layout(roles: list[str]) -> tuple[list[WidgetDefinition], str]:
    """Resolve widget layout for given roles. Multi-role = union ordered by authority."""
    if not roles:
        return [], "executive_summary"

    # Sort roles by authority (lower rank = higher authority)
    sorted_roles = sorted(
        [r for r in roles if r in AIIMS_AUTHORITY_RANKS],
        key=lambda r: AIIMS_AUTHORITY_RANKS.get(r, 99),
    )

    if not sorted_roles:
        return [], "executive_summary"

    primary_role = sorted_roles[0]
    primary_config = ROLE_WIDGET_CONFIGS.get(primary_role, {})
    default_view = primary_config.get("default_view", "executive_summary")

    # Merge widgets from all roles (union, ordered by primary first)
    seen_ids: set[str] = set()
    merged: list[WidgetDefinition] = []

    for role in sorted_roles:
        config = ROLE_WIDGET_CONFIGS.get(role, {})
        for w in config.get("widgets", []):
            if w["widget_id"] not in seen_ids:
                seen_ids.add(w["widget_id"])
                merged.append(WidgetDefinition(**{**w, "priority": len(merged) + 1}))

    return merged, default_view


# --- Endpoint 1: Dashboard Config ---


@router.get("/config", response_model=DashboardConfigResponse)
async def get_dashboard_config(request: Request) -> DashboardConfigResponse:
    """GET /governance/dashboard/config — user role config and polling settings."""
    roles = _resolve_user_roles(request)
    tenant_id = _get_tenant_id(request)
    is_sim = tenant_id.startswith("sim-")

    if not roles:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "restricted_access",
                "message": "No AIIMS role assigned. Please request a role assignment.",
            },
        )

    widgets, default_view = _resolve_widget_layout(roles)
    sorted_roles = sorted(
        [r for r in roles if r in AIIMS_AUTHORITY_RANKS],
        key=lambda r: AIIMS_AUTHORITY_RANKS.get(r, 99),
    )
    primary = sorted_roles[0] if sorted_roles else None

    # Check for active incident to set polling interval
    try:
        summary = _get_aggregation().get_executive_summary(tenant_id=tenant_id)
        has_incident = summary.active_incident_count > 0
    except Exception:
        has_incident = False

    poll_ms = 30000 if has_incident else 300000

    return DashboardConfigResponse(
        user_roles=roles,
        primary_role=primary,
        widget_layout=widgets,
        default_view=default_view,
        poll_interval_ms=poll_ms,
        has_active_incident=has_incident,
        cache_ttl_s=300,
        tenant_id=tenant_id,
        tenant_display_name=f"SIMULATION — {tenant_id}" if is_sim else "Live",
        is_simulation=is_sim,
    )


# --- Endpoint 2: Executive Summary ---


@router.get("/summary", response_model=ExecutiveSummaryResponse)
async def get_executive_summary(
    request: Request,
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
) -> JSONResponse:
    """GET /governance/dashboard/summary — health score, gates, incidents, risks."""
    start = time.monotonic()
    tenant_id = _get_tenant_id(request)
    bypass_cache = request.headers.get("Cache-Control") == "no-cache"

    try:
        summary = _get_aggregation().get_executive_summary(
            tenant_id=tenant_id,
            jurisdiction_id=jurisdiction_id,
        )
        data = summary.model_dump(mode="json")

        headers = {
            "X-Data-Freshness": summary.data_freshness.isoformat(),
            "X-Cache-Status": "BYPASS" if bypass_cache else "MISS",
        }

        _log_perf("executive_summary", start, tenant_id)
        return JSONResponse(content=data, headers=headers)

    except Exception as e:
        logger.exception("Failed to get executive summary")
        return JSONResponse(
            status_code=503,
            content={"error": "degraded_mode", "degraded_sources": [str(e)]},
            headers={"X-Cache-Status": "ERROR"},
        )


# --- Endpoint 3: Compliance Matrix ---


@router.get("/compliance", response_model=ComplianceMatrixResponse)
async def get_compliance_matrix(
    request: Request,
    compliance_status: str | None = Query(None),
    category: str | None = Query(None),
    sort_by: str | None = Query(None),
    sort_dir: str = Query("asc"),
    page_size: int = Query(50, ge=1, le=100),
    continuation_token: str | None = Query(None),
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
) -> ComplianceMatrixResponse:
    """GET /governance/dashboard/compliance — data source compliance matrix."""
    start = time.monotonic()
    tenant_id = _get_tenant_id(request)
    result = _get_aggregation().get_compliance_matrix(
        tenant_id=tenant_id,
        compliance_status=compliance_status,
        category=category,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page_size=page_size,
        continuation_token=continuation_token,
        jurisdiction_id=jurisdiction_id,
    )
    _log_perf("compliance_matrix", start, tenant_id)
    return result


# --- Endpoint 4: Compliance Detail ---


@router.get("/compliance/{data_source_id}", response_model=ComplianceDetailResponse)
async def get_compliance_detail(
    data_source_id: str,
    request: Request,
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
) -> ComplianceDetailResponse:
    """GET /governance/dashboard/compliance/{dataSourceId} — detail view."""
    tenant_id = _get_tenant_id(request)
    detail = _get_aggregation().get_compliance_detail(
        data_source_id,
        tenant_id=tenant_id,
        jurisdiction_id=jurisdiction_id,
    )
    if not detail:
        raise HTTPException(status_code=404, detail=f"Data source '{data_source_id}' not found.")
    return detail


# --- Endpoint 5: Audit Trail ---


@router.get("/audit", response_model=AuditTrailResponse)
async def get_audit_trail(
    request: Request,
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    actor: str | None = Query(None),
    action_type: str | None = Query(None),
    affected_entity: str | None = Query(None),
    keyword: str | None = Query(None),
    page_size: int = Query(50, ge=1, le=100),
    continuation_token: str | None = Query(None),
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
) -> AuditTrailResponse:
    """GET /governance/dashboard/audit — searchable audit trail."""
    start = time.monotonic()
    tenant_id = _get_tenant_id(request)

    from_dt = datetime.fromisoformat(date_from) if date_from else None
    to_dt = datetime.fromisoformat(date_to) if date_to else None

    result = _get_aggregation().search_audit_events(
        tenant_id=tenant_id,
        date_from=from_dt,
        date_to=to_dt,
        actor=actor,
        action_type=action_type,
        affected_entity=affected_entity,
        keyword=keyword,
        page_size=page_size,
        continuation_token=continuation_token,
        jurisdiction_id=jurisdiction_id,
    )
    _log_perf("audit_trail_search", start, tenant_id)
    return result


# --- Endpoint 6: Decision Chain ---


@router.get("/audit/{event_id}/chain", response_model=AuditDecisionChainResponse)
async def get_decision_chain(
    event_id: str,
    request: Request,
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
) -> AuditDecisionChainResponse:
    """GET /governance/dashboard/audit/{eventId}/chain — decision chain."""
    tenant_id = _get_tenant_id(request)
    chain = _get_aggregation().get_decision_chain(
        event_id,
        tenant_id=tenant_id,
        jurisdiction_id=jurisdiction_id,
    )
    if not chain:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
    return chain


# --- Endpoint 7: Audit Export (create) ---


@router.post("/audit/export", status_code=202, response_model=AuditExportJobResponse)
async def create_audit_export(
    body: AuditExportRequest,
    request: Request,
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
) -> AuditExportJobResponse:
    """POST /governance/dashboard/audit/export — start async export."""
    tenant_id = _get_tenant_id(request)
    user_id = request.headers.get("X-User-Id", "anonymous")

    try:
        job = _export_service.create_export_job(
            format=body.format,
            filter_params=body.filter_params,
            record_ids=body.record_ids,
            requested_by=user_id,
            tenant_id=tenant_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))

    # Simulate async processing
    _export_service.process_export(job.id, [])

    return AuditExportJobResponse(
        id=job.id,
        status=job.status,
        download_url=job.download_url,
        progress=100.0 if job.status == "complete" else 0.0,
    )


# --- Endpoint 8: Audit Export Status ---


@router.get("/audit/export/{job_id}", response_model=AuditExportJobResponse)
async def get_export_status(job_id: str) -> AuditExportJobResponse:
    """GET /governance/dashboard/audit/export/{jobId} — export job status."""
    job = _export_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Export job '{job_id}' not found.")

    return AuditExportJobResponse(
        id=job.id,
        status=job.status,
        download_url=job.download_url,
        progress=100.0 if job.status == "complete" else 50.0 if job.status == "processing" else 0.0,
        error_message=job.error_message,
    )


# --- Endpoint 9: Operational Readiness ---


@router.get("/readiness", response_model=OperationalReadinessResponse)
async def get_operational_readiness(
    request: Request,
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
    hazard_type: str | None = Query(
        None, description="Filter by hazard type (bushfire, flood, storm, cyclone, earthquake, tsunami, etc.)"
    ),
) -> OperationalReadinessResponse:
    """GET /governance/dashboard/readiness — PPRR, plans, exercises, roles."""
    start = time.monotonic()
    tenant_id = _get_tenant_id(request)
    result = _get_aggregation().get_operational_readiness(
        tenant_id=tenant_id,
        jurisdiction_id=jurisdiction_id,
        hazard_type=hazard_type,
    )
    _log_perf("operational_readiness", start, tenant_id)
    return result


# --- Endpoint 10: Recovery Progress ---


@router.get("/recovery", response_model=RecoveryProgressResponse)
async def get_recovery_progress(
    request: Request,
    incident_id: str | None = Query(None),
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
) -> RecoveryProgressResponse:
    """GET /governance/dashboard/recovery — 5-domain recovery progress."""
    start = time.monotonic()
    tenant_id = _get_tenant_id(request)
    result = _get_aggregation().get_recovery_progress(
        tenant_id=tenant_id,
        incident_id=incident_id,
        jurisdiction_id=jurisdiction_id,
    )
    _log_perf("recovery_progress", start, tenant_id)
    return result


# --- Endpoint 11: Recovery Domain Detail ---


@router.get("/recovery/{domain}")
async def get_recovery_domain_detail(
    domain: str,
    request: Request,
    incident_id: str | None = Query(None),
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
) -> RecoveryDomainDetail:
    """GET /governance/dashboard/recovery/{domain} — domain detail."""
    tenant_id = _get_tenant_id(request)
    valid_domains = {"overarching", "social", "economic", "built", "natural"}

    if domain not in valid_domains:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid domain '{domain}'. Valid: {sorted(valid_domains)}",
        )

    detail = _get_aggregation().get_recovery_domain_detail(
        domain,
        tenant_id=tenant_id,
        incident_id=incident_id,
        jurisdiction_id=jurisdiction_id,
    )
    if not detail:
        raise HTTPException(status_code=404, detail=f"No recovery data for domain '{domain}'.")
    return detail


# --- Endpoint 12: Risk & Warning ---


@router.get("/risk", response_model=RiskWarningResponse)
async def get_risk_and_warning(
    request: Request,
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
    issuing_authority: str | None = Query(None, description="Filter warnings by statutory issuing authority"),
    hazard_type: str | None = Query(
        None, description="Filter by hazard type (bushfire, flood, storm, cyclone, earthquake, tsunami, etc.)"
    ),
) -> RiskWarningResponse:
    """GET /governance/dashboard/risk — risk register + warning compliance."""
    start = time.monotonic()
    tenant_id = _get_tenant_id(request)
    result = _get_aggregation().get_risk_and_warning(
        tenant_id=tenant_id,
        jurisdiction_id=jurisdiction_id,
        issuing_authority=issuing_authority,
        hazard_type=hazard_type,
    )
    _log_perf("risk_warning", start, tenant_id)
    return result


# --- Endpoint 13: Risk Detail ---


@router.get("/risk/{risk_id}")
async def get_risk_detail(
    risk_id: str,
    request: Request,
    jurisdiction_id: str | None = Query(None, description="Filter by jurisdiction ID"),
) -> RiskDetailResponse:
    """GET /governance/dashboard/risk/{riskId} — risk detail."""
    tenant_id = _get_tenant_id(request)
    detail = _get_aggregation().get_risk_detail(
        risk_id,
        tenant_id=tenant_id,
        jurisdiction_id=jurisdiction_id,
    )
    if not detail:
        raise HTTPException(status_code=404, detail=f"Risk '{risk_id}' not found.")
    return detail
