"""Template-based fallback text generators for resource deployment plans.

These templates are used when the LLM is unavailable. They include resource
assignment details and are pre-approved (no runtime content safety check needed).
Confidence is reduced by 20% (multiplicative) when using template fallback.
"""

from __future__ import annotations

from typing import Any


def generate_plan_summary(
    plan: Any,
    assignments: list[Any],
    shortfalls: list[Any],
    trade_offs: Any | None = None,
) -> str:
    """Generate a template-based plan summary with AIIMS-consistent terminology.

    Includes resource assignments, priorities, shortfalls, and trade-offs.
    """
    incident_id = getattr(plan, "incident_id", "unknown") if plan else "unknown"
    version = getattr(plan, "version", 1) if plan else 1

    parts = [
        f"RESOURCE DEPLOYMENT PLAN (Incident: {incident_id}, Version: {version})",
        "Generated via template due to LLM unavailability.",
        "",
    ]

    # Assignments summary
    if assignments:
        parts.append(f"ASSIGNMENTS ({len(assignments)} resource(s) allocated):")
        for i, assignment in enumerate(assignments, 1):
            res_id = getattr(assignment, "resource_id", "unknown")
            demand_id = getattr(assignment, "demand_id", "unknown")
            score = getattr(assignment, "score", 0.0)
            travel = getattr(assignment, "estimated_travel_minutes", 0.0)
            parts.append(f"  {i}. Resource {res_id} → Demand {demand_id} (score: {score:.2f}, ETA: {travel:.0f} min)")
    else:
        parts.append("ASSIGNMENTS: No resources assigned.")

    # Shortfalls
    if shortfalls:
        parts.append("")
        parts.append(f"SHORTFALLS ({len(shortfalls)} unmet/partially-met demand(s)):")
        for shortfall in shortfalls:
            demand_id = getattr(shortfall, "demand_id", "unknown")
            unmet = getattr(shortfall, "quantity_unmet", 0)
            reason = getattr(shortfall, "reason", "Insufficient inventory")
            recommendation = getattr(shortfall, "recommendation", "")
            parts.append(f"  - Demand {demand_id}: {unmet} unmet. Reason: {reason}")
            if recommendation:
                parts.append(f"    Recommendation: {recommendation}")

    # Trade-offs
    if trade_offs:
        parts.append("")
        impact = getattr(trade_offs, "impact_summary", "")
        if impact:
            parts.append(f"TRADE-OFF ANALYSIS: {impact}")
        requires_approval = getattr(trade_offs, "requires_commander_approval", False)
        if requires_approval:
            parts.append("⚠ COMMANDER APPROVAL REQUIRED for cross-incident reallocation.")

    return "\n".join(parts)


def generate_assignment_rationale(
    assignment: Any,
    scoring_rationale: Any,
) -> str:
    """Generate per-assignment explanation of why a resource was selected."""
    res_id = getattr(assignment, "resource_id", "unknown")
    demand_id = getattr(assignment, "demand_id", "unknown")

    cap_match = getattr(scoring_rationale, "capability_match", 0.0)
    distance = getattr(scoring_rationale, "distance_km", 0.0)
    avail = getattr(scoring_rationale, "availability_factor", 0.0)
    priority = getattr(scoring_rationale, "priority_weight", 0.0)
    score = getattr(scoring_rationale, "final_score", 0.0)
    alternatives = getattr(scoring_rationale, "alternatives_considered", 0)
    tie_break = getattr(scoring_rationale, "tie_break_applied", None)

    parts = [
        f"Resource {res_id} selected for demand {demand_id}.",
        f"Capability match: {'full' if cap_match == 1.0 else 'none'} ({cap_match:.1f}).",
        f"Distance: {distance:.1f} km (factor: {1.0 / max(distance, 0.1):.2f}).",
        f"Availability: {avail:.1f}. Priority weight: {priority:.1f}.",
        f"Final score: {score:.4f}.",
        f"Evaluated against {alternatives} alternative(s).",
    ]

    if tie_break:
        parts.append(f"Tie-break applied: {tie_break}.")

    return " ".join(parts)


def generate_trade_off_summary(trade_off_analysis: Any) -> str:
    """Generate cross-incident trade-off text."""
    competing = getattr(trade_off_analysis, "competing_incidents", [])
    contested = getattr(trade_off_analysis, "contested_resources", [])
    impact = getattr(trade_off_analysis, "impact_summary", "")

    parts = [
        "CROSS-INCIDENT TRADE-OFF ANALYSIS:",
        f"Competing incidents: {', '.join(competing) if competing else 'none'}.",
        f"Contested resources: {len(contested)} resource(s).",
    ]

    if impact:
        parts.append(f"Impact: {impact}")

    recommendations = getattr(trade_off_analysis, "reallocation_recommendations", [])
    if recommendations:
        parts.append(f"Reallocation recommendations: {len(recommendations)} pending.")
        parts.append("Commander approval is required for all cross-incident reallocations.")

    return " ".join(parts)


def generate_transport_dispatch_summary(
    assignments: list[Any],
    evacuation_plan_id: str | None = None,
) -> str:
    """Generate evacuation transport dispatch rationale."""
    parts = [
        "TRANSPORT DISPATCH PLAN",
    ]

    if evacuation_plan_id:
        parts.append(f"Linked to evacuation plan: {evacuation_plan_id}.")

    if assignments:
        parts.append(f"{len(assignments)} transport resource(s) dispatched:")
        for i, assignment in enumerate(assignments, 1):
            res_id = getattr(assignment, "resource_id", "unknown")
            travel = getattr(assignment, "estimated_travel_minutes", 0.0)
            parts.append(f"  {i}. Vehicle {res_id} (ETA: {travel:.0f} min)")
    else:
        parts.append("No transport resources assigned. Shortfall flagged for commander review.")

    return "\n".join(parts)
