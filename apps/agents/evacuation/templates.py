"""Template-based fallback text generators for evacuation plans.

These templates are used when the LLM is unavailable. They produce structured
plan summaries using AIIMS (Australasian Inter-service Incident Management System)
terminology. Templates are pre-approved (no runtime content safety check needed).
"""

from __future__ import annotations

from collections import Counter
from typing import Any

_GENERIC_HAZARD_GUIDANCE = {
    "bushfire": (
        "If directed to evacuate and it remains safe to leave, move away from "
        "the known fire threat using roads verified locally at the time. "
        "Otherwise follow official bushfire shelter advice."
    ),
    "cyclone": (
        "Follow cyclone and storm-tide warnings. Do not travel during "
        "destructive winds or through floodwater; use only officially "
        "nominated evacuation locations."
    ),
    "flood": (
        "Move toward higher ground only when officially directed or locally "
        "verified safe. Never enter floodwater; treat roads and bridges as "
        "unverified."
    ),
    "earthquake": (
        "During shaking, Drop, Cover and Hold On. Afterwards avoid damaged "
        "structures, roads, bridges and utilities pending verified directions."
    ),
    "tsunami": (
        "On natural warning signs or an official warning, move quickly inland "
        "and to higher ground using locally verified access. Follow official "
        "vertical-evacuation advice if movement is impossible."
    ),
}


def generate_generic_evacuation_guidance(hazard_type: str) -> str:
    """Return conservative guidance when route computation is unavailable."""
    hazard_guidance = _GENERIC_HAZARD_GUIDANCE.get(
        hazard_type,
        "No hazard-specific movement direction is available. Do not infer a "
        "safe direction or route; await official incident-controller guidance.",
    )
    return (
        "IMMEDIATE HUMAN REVIEW REQUIRED. Road data is stale or unavailable. "
        "No route, destination, road passability, or capacity was computed or "
        "verified. Follow current official warnings and incident-controller "
        f"directions. {hazard_guidance}"
    )


def _bounded_summary(
    mandatory: str,
    body: str,
    confidence: str,
    max_length: int,
) -> str:
    required = "\n\n".join(section for section in (mandatory.strip(), confidence.strip()) if section)
    if len(required) >= max_length:
        confidence_space = len(confidence) + 2
        warning = mandatory[: max(0, max_length - confidence_space)].rstrip()
        return f"{warning}\n\n{confidence}"[-max_length:]
    available_body = max_length - len(required) - (2 if body else 0)
    bounded_body = body[: max(0, available_body)].rstrip()
    return "\n\n".join(section for section in (mandatory.strip(), bounded_body, confidence.strip()) if section)


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
    routing_mode = plan_data.get(
        "routing_mode",
        "hazard_constrained_degraded",
    )
    routing_gaps = plan_data.get("hazard_routing_data_gaps", [])
    excluded_roads = plan_data.get("excluded_roads", [])
    excluded_destinations = plan_data.get("excluded_destinations", [])
    zero_route_zones = plan_data.get("zero_route_zones", [])
    unresolved_destinations = plan_data.get(
        "unresolved_destination_demands",
        [],
    )
    overloaded_routes = [
        route.get("route_id", "unknown") for route in plan_data.get("routes", []) if route.get("capacity_overloaded")
    ]
    road_data_status = plan_data.get("road_data_status", "unavailable")
    facility_data_status = plan_data.get(
        "facility_data_status",
        "unavailable",
    )
    population_data_status = plan_data.get(
        "population_data_status",
        "unavailable",
    )
    generation_method = plan_data.get(
        "generation_method",
        "template_fallback",
    )
    dispositions = plan_data.get("zone_dispositions", [])
    phases = plan_data.get("phases", [])
    disposition_counts = Counter(item.get("disposition", "unknown") for item in dispositions)
    urgent_dispositions = []
    for item in dispositions:
        disposition = item.get("disposition")
        zone = item.get("zone_number", item.get("zone_id", "unknown"))
        if disposition == "emergency_escalation":
            urgent_dispositions.append(f"EMERGENCY ESCALATION: Zone {zone} requires immediate operator action.")
        elif disposition == "shelter_in_place":
            urgent_dispositions.append(f"SHELTER IN PLACE: Zone {zone} has no verified evacuation movement.")
        elif disposition == "partial_evacuation":
            urgent_dispositions.append(
                f"PARTIAL EVACUATION: Zone {zone} retains {item.get('remaining_population', 0)} people."
            )
    confidence_text = f"CONFIDENCE: {confidence_level} ({confidence:.0%}). Generation: {generation_method}."
    if road_data_status in {"stale", "unavailable"} or route_count == 0:
        guidance = (
            generate_generic_evacuation_guidance(hazard_type)
            if road_data_status in {"stale", "unavailable"}
            else (
                "IMMEDIATE HUMAN REVIEW REQUIRED. The current road snapshot "
                "produced no viable route or destination. Do not infer a safe "
                "movement path; follow official incident-controller directions. "
                + _GENERIC_HAZARD_GUIDANCE.get(
                    hazard_type,
                    "Await verified hazard-specific movement directions.",
                )
            )
        )
        vulnerable_warning = (
            " VULNERABLE NEEDS INCOMPLETE. Do not interpret zero transport "
            "requests as zero vulnerable people; verify needs through local "
            "contacts before approval."
            if facility_data_status != "fresh" or population_data_status != "fresh"
            else ""
        )
        urgent_text = " ".join(plan_data.get("urgent_assumptions", []))
        return _bounded_summary(
            " ".join(section for section in (guidance, urgent_text) if section),
            vulnerable_warning.strip(),
            confidence_text,
            max_length,
        )

    hazard_descriptions: dict[str, str] = {
        "bushfire": "bushfire emergency",
        "cyclone": "tropical cyclone event",
        "flood": "flood emergency",
        "earthquake": "earthquake event",
        "tsunami": "tsunami warning",
    }
    hazard_desc = hazard_descriptions.get(hazard_type, "natural disaster event")

    if routing_mode == "hazard_aware":
        strategy = "Hazard-specific road exclusions, destination screening, and deterministic preferences were applied"
    else:
        gap_text = ", ".join(routing_gaps) or "required hazard reference data"
        strategy = (
            "Available hard hazard constraints were applied, but routes require "
            f"commander review because data is incomplete: {gap_text}"
        )
    exclusion_counts = Counter(
        road.get("source_hazard_type") or road.get("closure_reason") or "unspecified" for road in excluded_roads
    )
    exclusion_text = ", ".join(f"{count} {reason}" for reason, count in sorted(exclusion_counts.items())) or "none"
    destination_text = (
        ", ".join(f"{item.get('assembly_area_id')}: {item.get('reason')}" for item in excluded_destinations) or "none"
    )
    overload_text = ", ".join(overloaded_routes) or "none"
    zero_route_text = ", ".join(f"Zone {zone_number}" for zone_number in zero_route_zones) or "none"
    unresolved_destination_text = (
        ", ".join(
            f"Zone {item.get('zone_number')}: {item.get('population')} ({item.get('reason')})"
            for item in unresolved_destinations
        )
        or "none"
    )

    mandatory_warnings = []
    route_identifiers = [route.get("route_id", "unknown") for route in plan_data.get("routes", [])]
    selected_route_ids = ", ".join(route_identifiers[:5]) or "none"
    if len(route_identifiers) > 5:
        selected_route_ids += f" (+{len(route_identifiers) - 5} more)"
    cache_warning = (
        "IMMEDIATE HUMAN REVIEW REQUIRED. A fresh last-known-good road "
        "snapshot was used after refresh failure; routes are not verified "
        "against a successful current refresh."
        if road_data_status == "fresh_cache_refresh_failed"
        else ""
    )
    if cache_warning:
        mandatory_warnings.append(cache_warning)
    elif plan_data.get("immediate_human_review_required"):
        mandatory_warnings.append(
            "IMMEDIATE HUMAN REVIEW REQUIRED before this plan is approved; "
            "commander review must retain the structured safety decisions."
        )
    mandatory_warnings.extend(plan_data.get("urgent_assumptions", []))
    mandatory_warnings.append(
        f"ROUTING EVIDENCE: Unavailable roads: {exclusion_text}. "
        f"Zones without routes: {zero_route_text}. "
        f"Selected routes: {selected_route_ids}. "
        "Unresolved destination demand: "
        f"{unresolved_destination_text[:180]}. "
        "Use the structured routes, "
        "exclusions, destinations, and dispositions as the authoritative record."
    )
    mandatory_warnings.extend(urgent_dispositions)
    objective = (
        "Apply the structured zone dispositions: "
        + ", ".join(f"{count} {name.replace('_', ' ')}" for name, count in sorted(disposition_counts.items()))
        if disposition_counts
        else "Apply the validated route and shelter decisions shown below"
    )
    route_details = (
        "; ".join(
            f"{route.get('route_id', 'unknown')} from Zone "
            f"{route.get('zone_id', 'unknown')} to "
            f"{route.get('assembly_area_id', 'unresolved')} via "
            f"{len(route.get('path', route.get('waypoints', [])))} edge(s), "
            f"{route.get('allocated_population', 0)} people, "
            f"{route.get('estimated_travel_time_loaded_min', route.get('estimated_travel_minutes', 0))} loaded minutes"
            for route in plan_data.get("routes", [])
        )
        or "none"
    )
    phase_details = (
        "; ".join(
            f"Phase {phase.get('phase_number', 'unknown')} zones "
            f"{','.join(phase.get('zone_ids', [])) or 'none'} starts "
            f"{phase.get('start_offset_minutes', 0)}m, completes "
            f"{phase.get('completion_offset_minutes', 'blocked')}m, trigger "
            f"{phase.get('selected_transition_trigger', 'unknown')}"
            for phase in phases
        )
        or "none"
    )
    transport_details = (
        "; ".join(
            f"{item.get('requirement_id', 'unknown')} for "
            f"{item.get('facility_id', 'unknown')}: "
            f"{item.get('quantity_required', 0)} {item.get('vehicle_type', 'vehicle')} to "
            f"{item.get('destination_assembly_area_id', 'unresolved')}"
            for item in plan_data.get("transport_requirements", [])
        )
        or "none"
    )
    summary = (
        f"SITUATION: A {hazard_severity}-severity {hazard_desc} has been identified "
        f"affecting an estimated {pop_est:,} persons across {zone_count} evacuation zones. "
        f"Time horizon: {time_horizon}.\n\n"
        f"OBJECTIVES: {objective}.\n\n"
        f"STRATEGY: {route_count} evacuation route(s) computed to {assembly_count} "
        f"assembly area(s). {strategy}. Capacity management remains applied.\n\n"
        f"ROUTING EVIDENCE: Unavailable roads: {exclusion_text}. "
        f"Rejected destinations: {destination_text}. "
        f"Overloaded routes: {overload_text}. "
        f"Zones without routes: {zero_route_text}. "
        f"Unresolved destination demand: {unresolved_destination_text}. "
        f"Selected routes: {route_details}.\n\n"
        f"TACTICS: {len(phases)} modeled phase(s); "
        f"{sum(1 for phase in phases if phase.get('clearance_blocked'))} "
        f"phase(s) have blocked clearance. Timeline: {phase_details}.\n\n"
    )

    if transport_count > 0:
        summary += (
            f"ADMINISTRATION/LOGISTICS: {transport_count} transport requirement(s) "
            "identified for vulnerable populations requiring specialised vehicles. "
            f"Requests: {transport_details}.\n\n"
        )
    elif facility_data_status == "fresh":
        summary += (
            "ADMINISTRATION/LOGISTICS: No specialised transport requirements identified. "
            "Standard evacuation vehicles apply.\n\n"
        )
    else:
        summary += (
            "ADMINISTRATION/LOGISTICS: VULNERABLE NEEDS INCOMPLETE. Zero "
            "transport requests must not be interpreted as zero vulnerable "
            "people. Verify needs through local contacts before approval.\n\n"
        )

    return _bounded_summary(
        " ".join(mandatory_warnings),
        summary,
        confidence_text,
        max_length,
    )


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
    distance = route.get("total_distance_km", route.get("distance_km", 0))
    capacity = route.get("capacity_vehicles_per_hour", 0)
    utilisation = route.get(
        "estimated_utilisation_pct",
        route.get("uncapped_utilisation_pct", 0),
    )
    destination = route.get(
        "destination_assembly_area",
        route.get("assembly_area_id", "assembly area"),
    )
    normal_minutes = route.get("estimated_travel_time_normal_min", 0)
    loaded_minutes = route.get("estimated_travel_time_loaded_min", 0)
    allocated = route.get("allocated_population", 0)
    mode = route.get("routing_mode", "hazard_constrained_degraded")
    suitability = route.get("vehicle_suitability", {})
    suitable_types = sorted(vehicle_type for vehicle_type, suitable in suitability.items() if suitable)
    evidence = route.get("hazard_preference_evidence", [])
    evidence_text = "; ".join(
        f"{item.get('edge_id')}: {item.get('reason')} ({item.get('multiplier', 1):.2f}x)" for item in evidence
    )
    gaps = route.get("hazard_data_gaps", [])

    rationale = (
        f"{mode} deterministic route for {hazard_type} from "
        f"{route.get('origin_node_id', 'origin')} to {destination}; "
        f"{len(route.get('path', route.get('waypoints', [])))} connected edge(s), "
        f"{distance:.2f} km, {normal_minutes:.2f} min normal and "
        f"{loaded_minutes:.2f} min loaded. Assigned {allocated} people; "
        f"bottleneck capacity {capacity} vehicles/hour; "
        f"uncapped utilization {utilisation:.2f}%. "
        f"Suitable vehicles: {', '.join(suitable_types) or 'none verified'}."
    )
    if evidence_text:
        rationale += f" Applied preferences: {evidence_text}."
    if gaps:
        rationale += f" Data gaps: {', '.join(gaps)}."
    excluded_roads = route.get("excluded_roads", [])
    if excluded_roads:
        reason_counts = Counter(
            road.get("source_hazard_type") or road.get("closure_reason") or "unspecified" for road in excluded_roads
        )
        rationale += (
            " Excluded road inventory: "
            + ", ".join(f"{count} {reason}" for reason, count in sorted(reason_counts.items()))
            + "."
        )
    if route.get("capacity_overloaded"):
        rationale += " Capacity is overloaded."
    elif route.get("congestion_risk"):
        rationale += " Congestion threshold is exceeded."

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
