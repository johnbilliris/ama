"""Template-based fallback text generators for evacuation plans.

These templates are used when the LLM is unavailable. They produce structured
plan summaries using AIIMS (Australasian Inter-service Incident Management System)
terminology. Templates are pre-approved (no runtime content safety check needed).
"""

from __future__ import annotations

from typing import Any


def generate_plan_summary_template(
    plan_data: dict[str, Any],
    hazard_type: str = "bushfire",
    max_length: int = 1000,
) -> str:
    """Generate a structured plain-language plan summary using AIIMS format.

    Sections: Situation, Objectives, Strategy, Tactics, Administration/Logistics

    Args:
        plan_data: Dict containing plan fields (population_estimate, zones, routes,
            assembly_areas, transport_requirements, confidence_score, etc.).
        hazard_type: One of bushfire, cyclone, flood, earthquake, tsunami.
        max_length: Maximum character length of the returned summary.

    Returns:
        AIIMS-formatted plan summary string.
    """
    pop_est = plan_data.get("population_estimate", 0)
    zone_count = len(plan_data.get("zones", []))
    route_count = len(plan_data.get("routes", []))
    assembly_count = len(plan_data.get("assembly_areas", []))
    transport_count = len(plan_data.get("transport_requirements", []))
    confidence = plan_data.get("confidence_score", 0.0)
    confidence_level = plan_data.get("confidence_level", "medium")
    hazard_severity = plan_data.get("hazard_severity", "high")
    time_horizon = plan_data.get("time_horizon", "unknown")

    hazard_descriptions: dict[str, str] = {
        "bushfire": "bushfire emergency",
        "cyclone": "tropical cyclone event",
        "flood": "flood emergency",
        "earthquake": "earthquake event",
        "tsunami": "tsunami warning",
    }
    hazard_desc = hazard_descriptions.get(hazard_type, "natural disaster event")

    summary = (
        f"SITUATION: A {hazard_severity}-severity {hazard_desc} has been identified "
        f"affecting an estimated {pop_est:,} persons across {zone_count} evacuation zones. "
        f"Time horizon: {time_horizon}.\n\n"
        f"OBJECTIVES: Evacuate all persons from mandatory and recommended zones "
        f"in priority order, ensuring vulnerable populations receive transport assistance.\n\n"
        f"STRATEGY: {route_count} evacuation route(s) computed to {assembly_count} "
        f"assembly area(s). Routes selected to avoid hazard impact zones and maintain "
        f"safe passage with capacity management.\n\n"
        f"TACTICS: Five-phase evacuation sequence — Zone 1 vulnerable populations "
        f"first, followed by Zone 1 general population, then Zone 2 vulnerable, "
        f"Zone 2 general, and Zone 3 advisory.\n\n"
    )

    if transport_count > 0:
        summary += (
            f"ADMINISTRATION/LOGISTICS: {transport_count} transport requirement(s) "
            f"identified for vulnerable populations requiring specialised vehicles.\n\n"
        )
    else:
        summary += (
            "ADMINISTRATION/LOGISTICS: No specialised transport requirements identified. "
            "Standard evacuation vehicles apply.\n\n"
        )

    summary += f"CONFIDENCE: {confidence_level} ({confidence:.0%}). Plan generated using template-based analysis."

    return summary[:max_length]


def generate_route_rationale_template(
    route: dict[str, Any],
    hazard_type: str = "bushfire",
) -> str:
    """Generate per-route selection rationale explaining selection criteria.

    Args:
        route: Dict with route fields (distance_km, capacity_vehicles_per_hour,
            congestion_risk_pct, assembly_area_id).
        hazard_type: One of bushfire, cyclone, flood, earthquake, tsunami.

    Returns:
        Plain-text rationale string for the route.
    """
    distance = route.get("distance_km", 0)
    capacity = route.get("capacity_vehicles_per_hour", 0)
    congestion_risk_pct = route.get("congestion_risk_pct", 0)
    destination = route.get("assembly_area_id", "assembly area")

    hazard_strategies: dict[str, str] = {
        "bushfire": "away from fire front and predicted downwind direction",
        "cyclone": "inland toward designated cyclone shelters",
        "flood": "toward higher ground and away from waterways",
        "earthquake": "away from damaged infrastructure and unstable structures",
        "tsunami": "toward elevated ground inland from coastal areas",
    }
    strategy = hazard_strategies.get(hazard_type, "away from hazard impact zone")

    rationale = (
        f"Route selected directing evacuees {strategy} to {destination}. "
        f"Total distance: {distance:.1f}km. "
        f"Bottleneck capacity: {capacity} vehicles/hour. "
        f"Estimated congestion risk: {congestion_risk_pct}%."
    )

    if congestion_risk_pct > 80:
        rationale += (
            " WARNING: This corridor has high congestion risk. "
            "Consider staging departures or activating alternative routes."
        )

    return rationale


def generate_change_summary_template(
    old_plan: dict[str, Any] | None,
    new_plan: dict[str, Any],
    triggers: list[str] | None = None,
) -> str:
    """Generate change summary for replan diffs.

    Compares old and new plan dicts, highlighting material changes in routes,
    population estimates, transport requirements, and confidence.

    Args:
        old_plan: Previous plan dict, or None for initial plans.
        new_plan: Updated plan dict.
        triggers: List of trigger descriptions that caused the replan.

    Returns:
        Plain-text change summary string.
    """
    if old_plan is None:
        return "Initial evacuation plan — no previous version."

    changes: list[str] = []
    trigger_desc = ", ".join(triggers) if triggers else "condition change"

    old_routes = len(old_plan.get("routes", []))
    new_routes = len(new_plan.get("routes", []))
    if old_routes != new_routes:
        changes.append(f"Routes: {old_routes} → {new_routes}")

    old_pop = old_plan.get("population_estimate", 0)
    new_pop = new_plan.get("population_estimate", 0)
    if old_pop != new_pop:
        changes.append(f"Population estimate: {old_pop:,} → {new_pop:,}")

    old_transport = len(old_plan.get("transport_requirements", []))
    new_transport = len(new_plan.get("transport_requirements", []))
    if old_transport != new_transport:
        changes.append(f"Transport requirements: {old_transport} → {new_transport}")

    old_confidence = old_plan.get("confidence_score", 0)
    new_confidence = new_plan.get("confidence_score", 0)
    if abs(old_confidence - new_confidence) > 0.01:
        changes.append(f"Confidence: {old_confidence:.0%} → {new_confidence:.0%}")

    if not changes:
        return f"Plan updated due to {trigger_desc}. No material changes to routes or population estimates."

    change_list = "; ".join(changes)
    return f"Plan updated due to {trigger_desc}. Changes: {change_list}."
