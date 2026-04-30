from fastapi import HTTPException

from packages.domain.src.domain.models.handoff_chain import HandoffChainDefinition

RECOGNIZED_AGENTS = frozenset(
    {
        "monitoring",
        "risk_assessment",
        "evacuation",
        "resource_allocation",
        "communication",
    }
)

# Valid audit action types for dashboard search (021-governance-dashboard)
DASHBOARD_ACTION_TYPES = frozenset(
    {
        "dashboard_view",
        "dashboard_filter",
        "dashboard_search",
        "dashboard_export",
        "dashboard_drill_down",
        "dashboard_navigate_to_crud",
    }
)

VALID_EXPORT_FORMATS: frozenset[str] = frozenset({"pdf", "csv", "json"})
MAX_EXPORT_RECORD_COUNT = 10000


def validate_agent_name(agent_name: str) -> None:
    if agent_name not in RECOGNIZED_AGENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Agent '{agent_name}' is not in the recognised agent catalogue. "
            f"Valid agents: {sorted(RECOGNIZED_AGENTS)}",
        )


def validate_handoff_chain(chain: HandoffChainDefinition, primary_agent: str | None = None) -> None:
    if not chain.steps:
        raise HTTPException(status_code=400, detail="Handoff chain must contain at least one step.")

    for step in chain.steps:
        validate_agent_name(step.source_agent)
        validate_agent_name(step.target_agent)
        if step.confidence_threshold is not None and not (0 <= step.confidence_threshold <= 1):
            raise HTTPException(
                status_code=400,
                detail=f"Step {step.step_order}: confidence_threshold must be between 0 and 1.",
            )

    for i in range(len(chain.steps) - 1):
        if chain.steps[i].target_agent != chain.steps[i + 1].source_agent:
            raise HTTPException(
                status_code=400,
                detail=f"Chain continuity broken: step {chain.steps[i].step_order} target "
                f"'{chain.steps[i].target_agent}' != step {chain.steps[i + 1].step_order} "
                f"source '{chain.steps[i + 1].source_agent}'.",
            )

    if primary_agent and chain.steps[0].source_agent != primary_agent:
        raise HTTPException(
            status_code=400,
            detail=f"First step source_agent '{chain.steps[0].source_agent}' must match "
            f"primary agent assignment '{primary_agent}'.",
        )


# --- Dashboard validators (021-governance-dashboard) ---


def validate_export_format(format_str: str) -> None:
    """Validate export format is one of pdf, csv, json."""
    if format_str not in VALID_EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid export format '{format_str}'. Valid: {sorted(VALID_EXPORT_FORMATS)}",
        )


def validate_export_record_count(count: int) -> None:
    """Validate export record count is within limits."""
    if count > MAX_EXPORT_RECORD_COUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Export limited to {MAX_EXPORT_RECORD_COUNT} records. Requested: {count}",
        )


def validate_audit_search_params(
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    action_type: str | None = None,
) -> None:
    """Validate audit search parameters."""
    from datetime import datetime

    if date_from:
        try:
            datetime.fromisoformat(date_from)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_from format: '{date_from}'. Use ISO 8601.",
            )

    if date_to:
        try:
            datetime.fromisoformat(date_to)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_to format: '{date_to}'. Use ISO 8601.",
            )

    if date_from and date_to:
        from_dt = datetime.fromisoformat(date_from)
        to_dt = datetime.fromisoformat(date_to)
        if from_dt > to_dt:
            raise HTTPException(
                status_code=400,
                detail="date_from must be before date_to.",
            )
