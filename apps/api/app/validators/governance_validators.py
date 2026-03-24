from fastapi import HTTPException

from packages.domain.src.domain.models.handoff_chain import HandoffChainDefinition

RECOGNIZED_AGENTS = frozenset({
    "monitoring",
    "risk_assessment",
    "evacuation",
    "resource_allocation",
    "communication",
})


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
