"""Pillar D — Causal chain repository + manager (T-D04, FR-018, SC-006)."""

from __future__ import annotations

from pathlib import Path

from .._clients import get_registry
from ..models.chain import CausalChain

CONTAINER = "causal_chains"
REPO_ROOT = Path(__file__).resolve().parents[6]


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
    _validate_source_reference(chain)
    container = get_registry().get(CONTAINER)
    # Mark prior as superseded.
    for r in container.all():
        if r.get("capability_id") == chain.capability_id and not r.get("superseded_by"):
            r["superseded_by"] = chain.id
            container.replace_item(r["id"], r)
    container.upsert_item(chain.model_dump(mode="json"))
    return chain


def _validate_source_reference(chain: CausalChain) -> None:
    source_path = (REPO_ROOT / chain.originating_spec_path).resolve()
    if not source_path.is_relative_to(REPO_ROOT) or not source_path.is_file():
        raise ValueError(f"originating spec does not exist: {chain.originating_spec_path}")

    marker = f"**{chain.originating_requirement}**"
    if marker not in source_path.read_text(encoding="utf-8"):
        raise ValueError(f"{chain.originating_requirement} not found in {chain.originating_spec_path}")
