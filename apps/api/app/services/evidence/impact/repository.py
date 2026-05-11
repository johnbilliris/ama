"""Pillar D — Causal chain repository + manager (T-D04, FR-018, SC-006)."""

from __future__ import annotations

from .._clients import get_registry
from ..models.chain import CausalChain

CONTAINER = "causal_chains"


def latest_for(capability_id: str) -> CausalChain | None:
    rows = [
        r
        for r in get_registry().get(CONTAINER).all()
        if r.get("capability_id") == capability_id and not r.get("superseded_by")
    ]
    if not rows:
        return None
    rows.sort(key=lambda r: r.get("version", 0), reverse=True)
    return CausalChain.model_validate(rows[0])


def publish(chain: CausalChain) -> CausalChain:
    container = get_registry().get(CONTAINER)
    # Mark prior as superseded.
    for r in container.all():
        if r.get("capability_id") == chain.capability_id and not r.get("superseded_by"):
            r["superseded_by"] = chain.id
            container.replace_item(r["id"], r)
    container.upsert_item(chain.model_dump(mode="json"))
    return chain
