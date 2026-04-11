"""Scoring functions for resource-demand matching.

Implements:
- Haversine distance calculation (km)
- Composite scoring: score = capability_match × (1/max(distance, floor)) × availability_factor × priority_weight
- Binary capability matching
- Type/sub-type compatibility checking
- Travel time estimation with mobilisation overhead
"""

from __future__ import annotations

import math

from resource_allocation.config import ResourceAllocationConfig


# Earth radius in km (mean radius)
_EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute Haversine great-circle distance between two points in km.

    Parameters are in decimal degrees.
    """
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return _EARTH_RADIUS_KM * c


def check_capability_match(
    resource_capabilities: list[str],
    required_capabilities: list[str],
) -> float:
    """Binary capability match: 1.0 if resource has ALL required capabilities, else 0.0."""
    if not required_capabilities:
        return 1.0
    resource_set = set(resource_capabilities)
    return 1.0 if all(cap in resource_set for cap in required_capabilities) else 0.0


def check_type_compatibility(
    resource_type: str,
    resource_sub_type: str,
    demand_type: str,
    demand_sub_type: str,
) -> bool:
    """Check if resource type and sub-type are compatible with the demand."""
    if resource_type != demand_type:
        return False
    if demand_sub_type and resource_sub_type != demand_sub_type:
        return False
    return True


def get_availability_factor(status: str, config: ResourceAllocationConfig) -> float:
    """Return the availability factor for a resource status."""
    return config.availability_factor_for(status)


def compute_score(
    resource: object,
    demand: object,
    config: ResourceAllocationConfig,
) -> tuple[float, dict]:
    """Compute the composite matching score for a resource against a demand.

    Returns (score, rationale_dict) where rationale_dict contains all scoring components.

    Formula: score = capability_match × (1/max(distance_km, floor)) × availability_factor × priority_weight
    """
    # Extract locations
    res_loc = getattr(resource, "location", {}) if hasattr(resource, "location") else {}
    dem_loc = getattr(demand, "location", {}) if hasattr(demand, "location") else {}

    res_lat = res_loc.get("lat", 0.0)
    res_lon = res_loc.get("lon", 0.0)
    dem_lat = dem_loc.get("lat", 0.0)
    dem_lon = dem_loc.get("lon", 0.0)

    # Capability match (binary)
    resource_caps = getattr(resource, "capabilities", [])
    required_caps = getattr(demand, "required_capabilities", [])
    cap_match = check_capability_match(resource_caps, required_caps)

    # Distance
    distance_km = haversine_distance(res_lat, res_lon, dem_lat, dem_lon)
    floored_distance = max(distance_km, config.distance_floor_km)
    distance_factor = 1.0 / floored_distance

    # Availability
    status = getattr(resource, "status", "available")
    if isinstance(status, str):
        status_str = status
    else:
        status_str = status.value if hasattr(status, "value") else str(status)
    avail_factor = get_availability_factor(status_str, config)

    # Priority weight
    urgency = getattr(demand, "urgency", "moderate")
    if isinstance(urgency, str):
        urgency_str = urgency
    else:
        urgency_str = urgency.value if hasattr(urgency, "value") else str(urgency)
    priority_weight = config.priority_weight_for(urgency_str)

    # Final score
    score = cap_match * distance_factor * avail_factor * priority_weight

    rationale = {
        "capability_match": cap_match,
        "distance_km": distance_km,
        "distance_factor": distance_factor,
        "availability_factor": avail_factor,
        "priority_weight": priority_weight,
        "final_score": score,
    }

    return score, rationale


def estimate_travel_time(
    distance_km: float,
    resource_type: str,
    config: ResourceAllocationConfig,
    resource_sub_type: str = "",
) -> float:
    """Estimate total travel time in minutes including mobilisation overhead.

    Returns mobilisation_minutes + (distance_km / speed_kmh) * 60
    """
    speed = config.travel_speed_for(resource_type, resource_sub_type)
    mobilisation = config.mobilisation_minutes_for(resource_type, resource_sub_type)
    travel_minutes = (distance_km / max(speed, 1.0)) * 60.0
    return mobilisation + travel_minutes
