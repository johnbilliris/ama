"""Pillar A — KPI ladder repository (T-A05, FR-005, CHK030).

Cosmos read/write + version monotonicity + transactional supersede.
Backed by the in-memory registry for tests / local dev.
"""

from __future__ import annotations

from .._clients import get_registry
from ..models.kpi import IndicatorDefinition

CONTAINER = "kpi_ladder"


class VersionMonotonicityError(ValueError):
    pass


def latest_version_for(kpi_id: str) -> int:
    container = get_registry().get(CONTAINER)
    rows = [r for r in container.all() if r.get("kpi_id") == kpi_id]
    return max((int(r.get("version", 0)) for r in rows), default=0)


def list_published() -> list[IndicatorDefinition]:
    """Return only the latest, non-superseded published rows."""
    container = get_registry().get(CONTAINER)
    rows = container.all()
    by_kpi: dict[str, dict] = {}
    for r in rows:
        if r.get("superseded_by"):
            continue
        kpi = r.get("kpi_id")
        prev = by_kpi.get(kpi)
        if prev is None or int(r.get("version", 0)) > int(prev.get("version", 0)):
            by_kpi[kpi] = r
    return [IndicatorDefinition.model_validate(r) for r in by_kpi.values()]


def get_by_id(doc_id: str) -> IndicatorDefinition | None:
    container = get_registry().get(CONTAINER)
    try:
        r = container.read_item(doc_id)
    except KeyError:
        return None
    return IndicatorDefinition.model_validate(r)


def publish(indicator: IndicatorDefinition) -> IndicatorDefinition:
    """Persist a new version. FR-005 — version is monotonically increasing."""
    container = get_registry().get(CONTAINER)
    current_max = latest_version_for(indicator.kpi_id)
    if indicator.version <= current_max:
        raise VersionMonotonicityError(f"version {indicator.version} not greater than current max {current_max}")
    # Mark prior latest as superseded — transactional batch (best-effort here).
    prior = [r for r in container.all() if r.get("kpi_id") == indicator.kpi_id and not r.get("superseded_by")]
    for p in prior:
        p["superseded_by"] = indicator.id
        container.replace_item(p["id"], p)
    container.upsert_item(indicator.model_dump(mode="json"))
    return indicator
