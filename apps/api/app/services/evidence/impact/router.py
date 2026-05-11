"""Pillar D — Causal Chain router (T-D05, contracts: getCausalChain)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path

from .._correlation import correlation_id_dep
from .._problem_details import ProblemDetails
from ..models.chain import CausalChain
from .repository import latest_for, publish
from .seed import seed_chains

router = APIRouter(tags=["evidence-impact"])

_SEEDED = False


def _ensure_seed() -> None:
    global _SEEDED
    if _SEEDED:
        return
    for c in seed_chains():
        if latest_for(c.capability_id) is None:
            publish(c)
    _SEEDED = True


@router.get(
    "/causal-chains/{capability_id}",
    response_model=CausalChain,
    operation_id="getCausalChain",
)
def get_causal_chain(
    capability_id: str = Path(...),
    correlation_id: str = Depends(correlation_id_dep),
) -> CausalChain:
    _ensure_seed()
    chain = latest_for(capability_id)
    if chain is None:
        raise HTTPException(
            status_code=404,
            detail=ProblemDetails.of(
                title="causal chain not found",
                status=404,
                detail=f"no published chain for capability_id={capability_id}",
            ).model_dump(),
        )
    return chain
