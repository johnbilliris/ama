"""Pillar C — Replay router (T-C08, contracts: replayScenario)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from .._correlation import correlation_id_dep
from ..instrumentation import audit_manager
from ..models.scorecard import DeltaScorecard
from .scenarios import SCENARIOS
from .scorecard_builder import build_scorecard

router = APIRouter(tags=["evidence-replay"])


class ReplayRequest(BaseModel):
    seed: str
    run_pair_id: str
    repetitions: int = Field(default=1, ge=1)
    allow_degraded_mode: bool = True


@router.post(
    "/scenarios/{scenario_id}/replay",
    response_model=DeltaScorecard,
    operation_id="replayScenario",
)
def replay_scenario(
    body: ReplayRequest,
    scenario_id: Literal[
        "bushfire",
        "flood",
        "cyclone",
        "urban_fire",
        "mass_casualty",
        "hazmat",
        "marine_sar",
    ] = Path(...),
    correlation_id: str = Depends(correlation_id_dep),
) -> DeltaScorecard:
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="unknown scenario")
    scorecard = build_scorecard(
        scenario_id=scenario_id,
        seed=body.seed,
        run_pair_id=body.run_pair_id,
        repetitions=body.repetitions,
        correlation_id=correlation_id,
    )
    audit_manager.record(
        kind="scorecard_published",
        value_id=scorecard.id,
        actor="system",
        references={"signal": body.seed, "model_output": scenario_id},
        payload={"scenario_id": scenario_id, "seed": body.seed},
        correlation_id=correlation_id,
    )
    if scorecard.determinism is not None and scorecard.determinism.diverged:
        audit_manager.record(
            kind="divergence_flagged",
            value_id=scorecard.id,
            actor="system",
            payload={"reproduction_rate": scorecard.determinism.reproduction_rate},
            correlation_id=correlation_id,
        )
    return scorecard
