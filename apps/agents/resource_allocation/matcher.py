"""Resource-demand matching engine.

Implements:
- Greedy assignment (highest-scoring resource to highest-priority demand)
- Partial allocation with shortfall details
- Tie-breaking (highest capability count, then alphabetical resource ID)
- Cross-incident contention detection
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from resource_allocation.config import ResourceAllocationConfig
from resource_allocation.models import (
    ResourceAssignment,
    ResourceDemand,
    ResourceInventoryItem,
    ResourceStatus,
    ScoringRationale,
    ShortfallDetail,
    TradeOffAnalysis,
)
from resource_allocation.scoring import (
    check_capability_match,
    check_type_compatibility,
    compute_score,
    estimate_travel_time,
    haversine_distance,
)

logger = logging.getLogger(__name__)


class ResourceMatcher:
    """Greedy resource-demand matching with scoring and shortfall reporting."""

    def __init__(self, config: ResourceAllocationConfig | None = None) -> None:
        self._config = config or ResourceAllocationConfig()

    def match_demands(
        self,
        demands: list[ResourceDemand],
        eligible_resources: list[ResourceInventoryItem],
        config: ResourceAllocationConfig | None = None,
    ) -> tuple[list[ResourceAssignment], list[ShortfallDetail]]:
        """Match demands to resources using greedy algorithm.

        Iterates demands in priority order (caller must pre-sort),
        scores all eligible resources, assigns highest-scoring.

        Returns (assignments, shortfalls).
        """
        cfg = config or self._config
        assignments: list[ResourceAssignment] = []
        shortfalls: list[ShortfallDetail] = []

        # Track which resources are already assigned in this round
        assigned_resource_ids: set[str] = set()

        for demand in demands:
            # Get unassigned eligible resources
            available = [
                r for r in eligible_resources
                if r.resource_id not in assigned_resource_ids
            ]

            # Score all candidates
            candidates = self._score_candidates(demand, available, cfg)

            # Assign up to demand.quantity
            assigned_count = 0
            for resource, score, rationale in candidates:
                if assigned_count >= demand.quantity:
                    break

                assignment = self._build_assignment(
                    resource=resource,
                    demand=demand,
                    score=score,
                    rationale=rationale,
                    alternatives_count=len(candidates),
                    config=cfg,
                )
                assignments.append(assignment)
                assigned_resource_ids.add(resource.resource_id)
                assigned_count += 1

            # Build shortfall if not fully met
            if assigned_count < demand.quantity:
                shortfall = self._build_shortfall(
                    demand=demand,
                    assigned_count=assigned_count,
                )
                shortfalls.append(shortfall)

                # Update demand fulfilment status
                if assigned_count == 0:
                    demand.fulfilment_status = "unmet"
                else:
                    demand.fulfilment_status = "partially_met"
            else:
                demand.fulfilment_status = "fully_met"

        return assignments, shortfalls

    def _score_candidates(
        self,
        demand: ResourceDemand,
        eligible_resources: list[ResourceInventoryItem],
        config: ResourceAllocationConfig,
    ) -> list[tuple[ResourceInventoryItem, float, ScoringRationale]]:
        """Score all eligible resources for a demand.

        Returns list sorted by score descending, with tie-breaking applied.
        """
        scored: list[tuple[ResourceInventoryItem, float, ScoringRationale]] = []

        for resource in eligible_resources:
            score, rationale_dict = compute_score(resource, demand, config)

            if score <= 0.0:
                continue

            rationale = ScoringRationale(
                capability_match=rationale_dict["capability_match"],
                distance_km=rationale_dict["distance_km"],
                distance_factor=rationale_dict["distance_factor"],
                availability_factor=rationale_dict["availability_factor"],
                priority_weight=rationale_dict["priority_weight"],
                final_score=rationale_dict["final_score"],
                selection_reason="Highest-scoring eligible resource",
                alternatives_considered=len(eligible_resources),
            )
            scored.append((resource, score, rationale))

        # Sort by score descending, then apply tie-breaking
        scored.sort(key=lambda x: (
            -x[1],  # score descending
            -len(x[0].capabilities),  # more capabilities preferred
            x[0].resource_id,  # alphabetical as final tiebreak
        ))

        # Mark tie-break if applied
        if len(scored) >= 2 and abs(scored[0][1] - scored[1][1]) < 1e-9:
            if len(scored[0][0].capabilities) != len(scored[1][0].capabilities):
                scored[0][2].tie_break_applied = "capability_count"
            else:
                scored[0][2].tie_break_applied = "alphabetical_id"

        return scored

    def _apply_tie_breaking(
        self,
        candidates: list[tuple[ResourceInventoryItem, float, ScoringRationale]],
    ) -> ResourceInventoryItem | None:
        """Resolve ties: highest capability count, then alphabetical resource ID."""
        if not candidates:
            return None
        return candidates[0][0]

    def _build_assignment(
        self,
        resource: ResourceInventoryItem,
        demand: ResourceDemand,
        score: float,
        rationale: ScoringRationale,
        alternatives_count: int,
        config: ResourceAllocationConfig,
    ) -> ResourceAssignment:
        """Construct a ResourceAssignment with travel time estimation."""
        # Compute distance and travel time
        res_loc = resource.location
        dem_loc = demand.location
        distance_km = haversine_distance(
            res_loc.get("lat", 0.0), res_loc.get("lon", 0.0),
            dem_loc.get("lat", 0.0), dem_loc.get("lon", 0.0),
        )

        res_type = resource.resource_type.value if hasattr(resource.resource_type, "value") else str(resource.resource_type)
        travel_time = estimate_travel_time(
            distance_km=distance_km,
            resource_type=res_type,
            config=config,
            resource_sub_type=resource.resource_sub_type,
        )

        mob_minutes = config.mobilisation_minutes_for(res_type, resource.resource_sub_type)

        now = datetime.now(UTC)
        from datetime import timedelta
        estimated_arrival = now + timedelta(minutes=travel_time)

        # Update rationale with selection reason
        rationale.selection_reason = (
            f"Highest-scoring resource (score: {score:.4f}) "
            f"from {alternatives_count} candidate(s)"
        )
        rationale.alternatives_considered = alternatives_count

        return ResourceAssignment(
            assignment_id=f"asgn-{uuid4().hex[:12]}",
            demand_id=demand.demand_id,
            resource_id=resource.resource_id,
            assignment_status="proposed",
            score=score,
            scoring_rationale=rationale,
            estimated_travel_minutes=travel_time,
            estimated_arrival_time=estimated_arrival,
            mobilisation_minutes=mob_minutes,
            distance_km=distance_km,
            created_at=now,
        )

    def _build_shortfall(
        self,
        demand: ResourceDemand,
        assigned_count: int,
    ) -> ShortfallDetail:
        """Build shortfall detail for unmet/partially-met demands."""
        unmet = demand.quantity - assigned_count

        if assigned_count == 0:
            reason = (
                f"No available {demand.resource_sub_type or demand.resource_type.value} "
                f"resources with required capabilities in inventory"
            )
        else:
            reason = (
                f"Only {assigned_count} of {demand.quantity} requested "
                f"{demand.resource_sub_type or demand.resource_type.value} resources available"
            )

        recommendation = (
            f"Request mutual aid for {unmet} additional "
            f"{demand.resource_sub_type or demand.resource_type.value} "
            f"from neighbouring region"
        )

        return ShortfallDetail(
            demand_id=demand.demand_id,
            resource_type=demand.resource_type,
            resource_sub_type=demand.resource_sub_type,
            quantity_requested=demand.quantity,
            quantity_assigned=assigned_count,
            quantity_unmet=unmet,
            reason=reason,
            recommendation=recommendation,
        )

    def detect_cross_incident_contention(
        self,
        demands: list[ResourceDemand],
        eligible_resources: list[ResourceInventoryItem],
    ) -> list[dict]:
        """Identify resources demanded by multiple incidents.

        Returns list of contention records: {resource_id, competing_incidents, resource_type}.
        """
        # Map resource to demanding incidents
        resource_incidents: dict[str, set[str]] = {}

        for demand in demands:
            for resource in eligible_resources:
                # Check basic type compatibility
                if resource.resource_type == demand.resource_type:
                    key = resource.resource_id
                    if key not in resource_incidents:
                        resource_incidents[key] = set()
                    resource_incidents[key].add(demand.incident_id)

        # Find resources demanded by multiple incidents
        contentions = []
        for resource_id, incidents in resource_incidents.items():
            if len(incidents) > 1:
                resource = next(
                    (r for r in eligible_resources if r.resource_id == resource_id),
                    None,
                )
                contentions.append({
                    "resource_id": resource_id,
                    "competing_incidents": sorted(incidents),
                    "resource_type": resource.resource_type.value if resource else "unknown",
                })

        return contentions
