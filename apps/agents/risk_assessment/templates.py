"""Template-based fallback text generators for hazard assessments and recommendations.

These templates are used when the LLM is unavailable. They include signal-ID
placeholders and are pre-approved (no runtime content safety check needed).
"""

from __future__ import annotations

from risk_assessment.correlation import RiskSignal


def generate_assessment_summary(
    assessment_type: str,
    signals: list[RiskSignal],
    severity: str,
    confidence: float,
    contradiction_detected: bool = False,
    stale_signal_ids: list[str] | None = None,
) -> str:
    """Generate a template-based assessment summary.

    Returns a signal-ID-inclusive summary text.
    """
    signal_ids = [s.get("signal_id", "unknown") for s in signals]
    cited = ", ".join(signal_ids) if signal_ids else "no signals available"
    stale_note = ""
    if stale_signal_ids:
        stale_note = f" Note: signals {', '.join(stale_signal_ids)} are stale and may be unreliable."

    contradiction_note = ""
    if contradiction_detected:
        contradiction_note = (
            " WARNING: Contradictory signals detected among sources. "
            "Both risk-increasing and risk-decreasing indicators are present. "
            "Human review recommended."
        )

    templates: dict[str, str] = {
        "spread_prediction": (
            f"SPREAD PREDICTION ({severity.upper()} severity, confidence {confidence:.2f}): "
            f"Based on {len(signals)} signal(s) ({cited}), fire spread modelling indicates "
            f"potential expansion of the hazard zone. Assessment generated from template due to "
            f"LLM unavailability.{stale_note}{contradiction_note}"
        ),
        "impact_projection": (
            f"IMPACT PROJECTION ({severity.upper()} severity, confidence {confidence:.2f}): "
            f"Based on {len(signals)} signal(s) ({cited}), impact modelling projects "
            f"significant effects on the affected area. Assessment generated from template due to "
            f"LLM unavailability.{stale_note}{contradiction_note}"
        ),
        "route_risk": (
            f"ROUTE RISK ({severity.upper()} severity, confidence {confidence:.2f}): "
            f"Based on {len(signals)} signal(s) ({cited}), evacuation route risk assessment "
            f"indicates potential threats to safe passage. Assessment generated from template due to "
            f"LLM unavailability.{stale_note}{contradiction_note}"
        ),
        "infrastructure_risk": (
            f"INFRASTRUCTURE RISK ({severity.upper()} severity, confidence {confidence:.2f}): "
            f"Based on {len(signals)} signal(s) ({cited}), critical infrastructure may be "
            f"at risk. Assessment generated from template due to "
            f"LLM unavailability.{stale_note}{contradiction_note}"
        ),
        "community_impact": (
            f"COMMUNITY IMPACT ({severity.upper()} severity, confidence {confidence:.2f}): "
            f"Based on {len(signals)} signal(s) ({cited}), community-level impacts are "
            f"projected. Assessment generated from template due to "
            f"LLM unavailability.{stale_note}{contradiction_note}"
        ),
    }

    return templates.get(assessment_type, templates["impact_projection"])


def generate_recommendation_explanation(
    rec_type: str,
    signals: list[RiskSignal],
    assessment_summary: str,
) -> str:
    """Generate a template-based recommendation explanation.

    Returns a signal-ID-inclusive explanation text.
    """
    signal_ids = [s.get("signal_id", "unknown") for s in signals]
    cited = ", ".join(signal_ids) if signal_ids else "no signals available"

    templates: dict[str, str] = {
        "public_alert": (
            f"Authoritative and community signals indicate escalating community risk. "
            f"A public alert is recommended to inform affected populations. "
            f"Signal references: {cited}."
        ),
        "evacuation": (
            f"Hazard assessment indicates threat to evacuation routes or populated areas. "
            f"Evacuation planning and execution is recommended. "
            f"Signal references: {cited}."
        ),
        "resource_allocation": (
            f"Assessment indicates need for resource coordination and allocation "
            f"to support emergency response operations. "
            f"Signal references: {cited}."
        ),
        "coordination": (
            f"Multi-agency coordination is required to address the identified hazard. "
            f"Cross-agency task coordination is recommended. "
            f"Signal references: {cited}."
        ),
        "infrastructure_action": (
            f"Critical infrastructure protection or restoration actions are required "
            f"based on the current risk assessment. "
            f"Signal references: {cited}."
        ),
    }

    return templates.get(rec_type, templates["public_alert"])
