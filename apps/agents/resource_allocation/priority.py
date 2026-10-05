"""Priority normalisation and demand queue for resource allocation.

Implements:
- AIDR 4-level urgency normalisation from Risk Assessment and Evacuation priorities
- Three-tier priority hierarchy (life safety > property > environment)
- Priority-ordered demand queue with four-level tiebreaking
- Proportional distribution for true ties
"""

from __future__ import annotations

import bisect
import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from functools import total_ordering

from resource_allocation.models import (
    PriorityTier,
    ResourceDemand,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Priority normalisation mappings
# ---------------------------------------------------------------------------

# Risk Assessment agent uses AIDR 4-level: critical/high/medium/low
_RISK_ASSESSMENT_MAPPING: dict[str, UrgencyLevel] = {
    "critical": UrgencyLevel.critical,
    "high": UrgencyLevel.high,
    "medium": UrgencyLevel.moderate,
    "moderate": UrgencyLevel.moderate,
    "low": UrgencyLevel.low,
}

# Evacuation agent uses: immediate/critical/high/medium/low
_EVACUATION_MAPPING: dict[str, UrgencyLevel] = {
    "immediate": UrgencyLevel.critical,
    "critical": UrgencyLevel.critical,
    "high": UrgencyLevel.high,
    "medium": UrgencyLevel.moderate,
    "moderate": UrgencyLevel.moderate,
    "low": UrgencyLevel.low,
}


def normalise_urgency(raw_priority: str, source_agent: str) -> UrgencyLevel:
    """Normalise incoming priority to AIDR 4-level taxonomy.

    Maps Risk Assessment and Evacuation priorities per research.md §9 and CHK020.
    """
    raw_lower = raw_priority.lower().strip()
    if source_agent == "evacuation":
        return _EVACUATION_MAPPING.get(raw_lower, UrgencyLevel.moderate)
    # Default to risk_assessment mapping
    return _RISK_ASSESSMENT_MAPPING.get(raw_lower, UrgencyLevel.moderate)


def classify_priority_tier(demand_context: Mapping[str, str]) -> PriorityTier:
    """Assign priority tier based on demand type context.

    Tier 1: evacuation, medical, rescue (life safety)
    Tier 2: structural defence, property protection
    Tier 3: environmental containment
    """
    source_type = demand_context.get("source_type", "")
    resource_sub_type = demand_context.get("resource_sub_type", "").lower()
    demand_type = demand_context.get("demand_type", "").lower()

    # Tier 1 — life safety
    life_safety_keywords = {
        "evacuation",
        "medical",
        "rescue",
        "ambulance",
        "paramedic",
        "hospital",
        "transport_requirement",
        "wheelchair_accessible",
        "patient",
        "life_safety",
    }
    if source_type == "transport_requirement":
        return PriorityTier.tier_1_life_safety
    if any(kw in resource_sub_type for kw in life_safety_keywords):
        return PriorityTier.tier_1_life_safety
    if any(kw in demand_type for kw in life_safety_keywords):
        return PriorityTier.tier_1_life_safety

    # Tier 3 — environment
    env_keywords = {"containment", "environmental", "pollution", "spill"}
    if any(kw in resource_sub_type for kw in env_keywords):
        return PriorityTier.tier_3_environment
    if any(kw in demand_type for kw in env_keywords):
        return PriorityTier.tier_3_environment

    # Default: Tier 2 — property
    return PriorityTier.tier_2_property


# ---------------------------------------------------------------------------
# Priority-ordered demand queue
# ---------------------------------------------------------------------------

# Tier ordering (lower = higher priority)
_TIER_ORDER = {
    PriorityTier.tier_1_life_safety: 0,
    PriorityTier.tier_2_property: 1,
    PriorityTier.tier_3_environment: 2,
}

# Urgency ordering (lower = higher priority)
_URGENCY_ORDER = {
    UrgencyLevel.critical: 0,
    UrgencyLevel.high: 1,
    UrgencyLevel.moderate: 2,
    UrgencyLevel.low: 3,
}


@total_ordering
@dataclass
class _PrioritisedDemand:
    """Wrapper for priority-ordered comparison in the demand queue.

    Four-level comparison: tier → urgency → proximity → timestamp.
    """

    demand: ResourceDemand
    proximity_km: float = 0.0  # lower = closer = higher priority

    def _sort_key(self) -> tuple[int, int, float, float]:
        tier_val = _TIER_ORDER.get(self.demand.priority_tier, 9)
        urgency_val = _URGENCY_ORDER.get(self.demand.urgency, 9)
        ts = self.demand.created_at.timestamp() if self.demand.created_at else 0.0
        return (tier_val, urgency_val, self.proximity_km, ts)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _PrioritisedDemand):
            return NotImplemented
        return self._sort_key() == other._sort_key()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, _PrioritisedDemand):
            return NotImplemented
        return self._sort_key() < other._sort_key()


class DemandQueue:
    """Priority-ordered demand queue with four-level tiebreaking.

    Demands are inserted in priority order (not append), so iteration
    always yields highest-priority first.
    """

    def __init__(self) -> None:
        self._items: list[_PrioritisedDemand] = []

    def insert(self, demand: ResourceDemand, proximity_km: float = 0.0) -> None:
        """Insert a demand in priority order."""
        wrapped = _PrioritisedDemand(demand=demand, proximity_km=proximity_km)
        bisect.insort(self._items, wrapped)

    def __iter__(self) -> Iterator[ResourceDemand]:
        """Iterate demands in priority order (highest first)."""
        return iter(d.demand for d in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def to_list(self) -> list[ResourceDemand]:
        """Return demands as a list in priority order."""
        return [d.demand for d in self._items]


def distribute_proportionally(
    demands: list[ResourceDemand],
    available_count: int,
    incidents: list[str],
) -> dict[str, int]:
    """Distribute resources proportionally for true ties (FR-022).

    When multiple incidents have identical tier, severity, and population,
    split contested resources proportionally by unmet demand ratio.

    Returns {incident_id: allocated_count}.
    """
    if not incidents or available_count <= 0:
        return {inc: 0 for inc in incidents}

    # Count demands per incident
    per_incident: dict[str, int] = {inc: 0 for inc in incidents}
    for d in demands:
        if d.incident_id in per_incident:
            per_incident[d.incident_id] += d.quantity

    total_demand = sum(per_incident.values())
    if total_demand == 0:
        # Equal split
        base = available_count // len(incidents)
        result = {inc: base for inc in incidents}
        # Distribute remainder
        remainder = available_count - base * len(incidents)
        for i, inc in enumerate(incidents):
            if i < remainder:
                result[inc] += 1
        return result

    # Proportional allocation
    result = {}
    allocated = 0
    for inc in incidents:
        ratio = per_incident[inc] / total_demand
        share = int(available_count * ratio)
        result[inc] = share
        allocated += share

    # Distribute remainder by largest fractional part
    remainder = available_count - allocated
    if remainder > 0:
        fracs = []
        for inc in incidents:
            ratio = per_incident[inc] / total_demand
            frac = (available_count * ratio) - result[inc]
            fracs.append((frac, inc))
        fracs.sort(reverse=True)
        for i in range(min(remainder, len(fracs))):
            result[fracs[i][1]] += 1

    return result
