"""Resource inventory manager with state machine and operational flags.

Implements:
- Static inventory loading from JSON
- Formal state machine for resource status transitions
- Operational limit flagging (rotation, replenishment, mechanical)
- Eligible resource filtering for demand matching
- Bulk resource release on incident closure
- Utilisation metrics computation
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from resource_allocation.config import ResourceAllocationConfig
from resource_allocation.models import (
    ResourceInventoryItem,
    ResourceStatus,
    ResourceType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Valid state machine transitions
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[ResourceStatus, set[ResourceStatus]] = {
    ResourceStatus.available: {ResourceStatus.reserved, ResourceStatus.assigned},
    ResourceStatus.reserved: {ResourceStatus.assigned, ResourceStatus.available, ResourceStatus.unavailable},
    ResourceStatus.assigned: {ResourceStatus.en_route, ResourceStatus.unavailable},
    ResourceStatus.en_route: {ResourceStatus.deployed, ResourceStatus.unavailable},
    ResourceStatus.deployed: {ResourceStatus.returning, ResourceStatus.unavailable},
    ResourceStatus.returning: {ResourceStatus.available, ResourceStatus.unavailable},
    ResourceStatus.unavailable: {ResourceStatus.available},  # commander override only
}


class ResourceInventoryManager:
    """Manages resource inventory state with formal state machine transitions."""

    def __init__(self, config: ResourceAllocationConfig | None = None) -> None:
        self._config = config or ResourceAllocationConfig()
        self._resources: dict[str, ResourceInventoryItem] = {}
        self._last_loaded_at: datetime | None = None

    def load_from_json(self, path: str) -> list[ResourceInventoryItem]:
        """Load baseline inventory from a JSON file.

        Returns the list of loaded resources.
        """
        file_path = Path(path)
        if not file_path.exists():
            logger.warning("Inventory file not found: %s", path)
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        items = data if isinstance(data, list) else data.get("resources", [])
        loaded = []
        for item_data in items:
            try:
                item = ResourceInventoryItem.model_validate(item_data)
                self._resources[item.resource_id] = item
                loaded.append(item)
            except Exception as exc:
                logger.warning("Failed to load resource item: %s", exc)

        self._last_loaded_at = datetime.now(UTC)
        logger.info("Loaded %d resources from %s", len(loaded), path)
        return loaded

    def add_resource(self, resource: ResourceInventoryItem) -> None:
        """Add or update a resource in the inventory."""
        self._resources[resource.resource_id] = resource

    def get_resource(self, resource_id: str) -> ResourceInventoryItem | None:
        """Get a resource by ID."""
        return self._resources.get(resource_id)

    def get_all_resources(self) -> list[ResourceInventoryItem]:
        """Return all resources in the inventory."""
        return list(self._resources.values())

    def transition_status(
        self,
        resource_id: str,
        new_status: ResourceStatus,
        incident_id: str | None = None,
    ) -> bool:
        """Validate and apply a status transition.

        Returns True if transition was applied, False if rejected.
        """
        resource = self._resources.get(resource_id)
        if resource is None:
            logger.warning("Resource not found for transition: %s", resource_id)
            return False

        current = resource.status
        valid_targets = VALID_TRANSITIONS.get(current, set())

        if new_status not in valid_targets:
            logger.warning(
                "Invalid transition for %s: %s → %s (valid: %s)",
                resource_id, current.value, new_status.value,
                {s.value for s in valid_targets},
            )
            return False

        # Apply transition
        resource.status = new_status
        resource.last_status_update = datetime.now(UTC)

        if incident_id is not None:
            if new_status in (ResourceStatus.assigned, ResourceStatus.reserved):
                resource.assigned_incident_id = incident_id
            elif new_status == ResourceStatus.available:
                resource.assigned_incident_id = None

        logger.info(
            "Resource %s transitioned: %s → %s",
            resource_id, current.value, new_status.value,
        )
        return True

    def flag_operational_limits(self, resources: list[ResourceInventoryItem] | None = None) -> list[ResourceInventoryItem]:
        """Flag resources that have hit operational limits.

        Checks:
        - Rotation needed: >rotation_threshold_hours continuous deployment
        - Replenishment needed: capacity < replenishment_threshold_percent of initial
        - Degraded: any existing mechanical/degraded flags

        Returns list of flagged resources.
        """
        target = resources or list(self._resources.values())
        flagged = []

        for resource in target:
            resource_flags: list[str] = list(resource.flags)  # copy

            # Rotation check (personnel/vehicle deployed > threshold hours)
            if resource.status == ResourceStatus.deployed:
                if resource.continuous_deployment_hours > self._config.rotation_threshold_hours:
                    if "rotation_needed" not in resource_flags:
                        resource_flags.append("rotation_needed")

            # Replenishment check (consumables below threshold)
            if resource.capacity is not None and resource.initial_capacity:
                ratio = resource.capacity / resource.initial_capacity
                if ratio < self._config.replenishment_threshold_percent:
                    if "replenishment_needed" not in resource_flags:
                        resource_flags.append("replenishment_needed")

            if resource_flags != list(resource.flags):
                resource.flags = resource_flags
                flagged.append(resource)

        return flagged

    def get_eligible_resources(
        self,
        demand: Any,
    ) -> list[ResourceInventoryItem]:
        """Filter resources eligible for a specific demand.

        Eligible = type/sub-type match + capability match + availability status
        (only 'available' and 'returning' are eligible).
        Reserved resources for other incidents are excluded (CHK021).
        """
        demand_type = getattr(demand, "resource_type", None)
        demand_sub_type = getattr(demand, "resource_sub_type", "")
        demand_caps = set(getattr(demand, "required_capabilities", []))
        demand_incident = getattr(demand, "incident_id", None)

        eligible = []
        for resource in self._resources.values():
            # Type match
            res_type = resource.resource_type
            if isinstance(demand_type, str):
                if res_type.value != demand_type and res_type != demand_type:
                    continue
            elif demand_type is not None and res_type != demand_type:
                continue

            # Sub-type match (if specified)
            if demand_sub_type and resource.resource_sub_type != demand_sub_type:
                continue

            # Status check: only available and returning
            if resource.status not in (ResourceStatus.available, ResourceStatus.returning):
                # Exception: reserved resources for the SAME incident are eligible
                if resource.status == ResourceStatus.reserved:
                    if resource.assigned_incident_id == demand_incident:
                        pass  # eligible for this incident
                    else:
                        continue
                else:
                    continue

            # Capability match
            if demand_caps and not demand_caps.issubset(set(resource.capabilities)):
                continue

            # Location check: must have valid location for distance scoring
            loc = resource.location
            if not loc or ("lat" not in loc and "lon" not in loc):
                continue

            eligible.append(resource)

        return eligible

    def release_incident_resources(self, incident_id: str) -> int:
        """Bulk release all resources assigned to an incident (CHK032).

        Transitions assigned/reserved resources back to available.
        Returns count of released resources.
        """
        released = 0
        for resource in self._resources.values():
            if resource.assigned_incident_id == incident_id:
                if resource.status in (
                    ResourceStatus.assigned,
                    ResourceStatus.reserved,
                    ResourceStatus.en_route,
                ):
                    resource.status = ResourceStatus.available
                    resource.assigned_incident_id = None
                    resource.last_status_update = datetime.now(UTC)
                    released += 1
        logger.info("Released %d resources for incident %s", released, incident_id)
        return released

    def update_capacity(self, resource_id: str, remaining_capacity: int) -> bool:
        """Update remaining capacity for consumable resources."""
        resource = self._resources.get(resource_id)
        if resource is None:
            return False
        resource.capacity = remaining_capacity
        resource.last_status_update = datetime.now(UTC)
        return True

    def compute_utilisation(self) -> dict:
        """Compute utilisation metrics.

        Returns totals, assigned/available counts, utilisation %, and flagged counts.
        """
        total = len(self._resources)
        if total == 0:
            return {
                "total": 0,
                "available": 0,
                "assigned": 0,
                "deployed": 0,
                "returning": 0,
                "unavailable": 0,
                "reserved": 0,
                "utilisation_percent": 0.0,
                "flagged_rotation": 0,
                "flagged_replenishment": 0,
                "flagged_degraded": 0,
            }

        counts: dict[str, int] = {}
        flagged_rotation = 0
        flagged_replenishment = 0
        flagged_degraded = 0

        for resource in self._resources.values():
            status_key = resource.status.value
            counts[status_key] = counts.get(status_key, 0) + 1
            if "rotation_needed" in resource.flags:
                flagged_rotation += 1
            if "replenishment_needed" in resource.flags:
                flagged_replenishment += 1
            if "degraded" in resource.flags:
                flagged_degraded += 1

        active = counts.get("assigned", 0) + counts.get("en_route", 0) + counts.get("deployed", 0)
        utilisation = (active / total * 100.0) if total > 0 else 0.0

        return {
            "total": total,
            "available": counts.get("available", 0),
            "assigned": counts.get("assigned", 0),
            "deployed": counts.get("deployed", 0),
            "returning": counts.get("returning", 0),
            "unavailable": counts.get("unavailable", 0),
            "reserved": counts.get("reserved", 0),
            "utilisation_percent": round(utilisation, 1),
            "flagged_rotation": flagged_rotation,
            "flagged_replenishment": flagged_replenishment,
            "flagged_degraded": flagged_degraded,
        }

    def compute_inventory_hash(self) -> str:
        """Compute a hash of the current inventory state for reproducibility."""
        items = sorted(
            (r.resource_id, r.status.value, r.resource_type.value)
            for r in self._resources.values()
        )
        return hashlib.sha256(str(items).encode()).hexdigest()

    @property
    def last_loaded_at(self) -> datetime | None:
        """When the inventory was last loaded."""
        return self._last_loaded_at

    @property
    def resource_count(self) -> int:
        """Total number of resources in inventory."""
        return len(self._resources)
