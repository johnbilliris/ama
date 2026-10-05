"""AIDR-aligned severity computation.

Maps signal categories to severity levels and applies adjustments
based on confidence and population estimates.
"""

from __future__ import annotations

from risk_assessment.models import SeverityLevel

from packages.domain.src.domain.models.hazard_assessment import AssessmentType

# Signal category → default assessment type mapping
CATEGORY_TO_ASSESSMENT_TYPE: dict[str, AssessmentType] = {
    "fire": "spread_prediction",
    "weather": "impact_projection",
    "hydrology": "impact_projection",
    "geohazard": "impact_projection",
    "infrastructure": "infrastructure_risk",
    "community_report": "community_impact",
    "social_report": "community_impact",
}

# Signal category → fallback severity mapping (when LLM unavailable)
CATEGORY_FALLBACK_SEVERITY: dict[str, SeverityLevel] = {
    "fire": SeverityLevel.high,
    "weather": SeverityLevel.moderate,
    "hydrology": SeverityLevel.moderate,
    "geohazard": SeverityLevel.critical,
    "infrastructure": SeverityLevel.moderate,
    "community_report": SeverityLevel.moderate,
    "social_report": SeverityLevel.moderate,
}

# Disaster type → severity mapping (used when signal category maps to a disaster type)
DISASTER_TYPE_SEVERITY: dict[str, SeverityLevel] = {
    "fire": SeverityLevel.high,
    "bushfire": SeverityLevel.high,
    "cyclone": SeverityLevel.critical,
    "flood": SeverityLevel.high,
    "earthquake": SeverityLevel.critical,
    "tsunami": SeverityLevel.critical,
}

# Severity ordering for downgrade logic
_SEVERITY_ORDER = [SeverityLevel.low, SeverityLevel.moderate, SeverityLevel.high, SeverityLevel.critical]


def _severity_index(level: SeverityLevel) -> int:
    return _SEVERITY_ORDER.index(level)


def _downgrade_one_level(level: SeverityLevel) -> SeverityLevel:
    """Downgrade severity by one level, with low as floor."""
    idx = _severity_index(level)
    if idx <= 0:
        return SeverityLevel.low
    return _SEVERITY_ORDER[idx - 1]


class SeverityComputer:
    """Computes AIDR-aligned severity from signal category, confidence, and population."""

    def compute_severity(
        self,
        signal_category: str,
        confidence_adjusted: float,
        population_estimate: int | None = None,
        disaster_type: str | None = None,
    ) -> SeverityLevel:
        """Compute severity level.

        Steps:
        1. Map signal category (or disaster type) to base severity
        2. Adjust for population (≥50000 → upgrade one level if not critical)
        3. Downgrade one level if confidence < 0.4 (low is floor)
        """
        # Determine base severity
        if disaster_type and disaster_type.lower() in DISASTER_TYPE_SEVERITY:
            severity = DISASTER_TYPE_SEVERITY[disaster_type.lower()]
        elif signal_category in CATEGORY_FALLBACK_SEVERITY:
            severity = CATEGORY_FALLBACK_SEVERITY[signal_category]
        else:
            severity = SeverityLevel.moderate

        # Population adjustment: large populations increase severity by one level
        if population_estimate is not None and population_estimate >= 50000:
            idx = _severity_index(severity)
            if idx < len(_SEVERITY_ORDER) - 1:
                severity = _SEVERITY_ORDER[idx + 1]

        # Confidence adjustment: low confidence downgrades severity by one level
        if confidence_adjusted < 0.4:
            severity = _downgrade_one_level(severity)

        return severity

    def derive_assessment_type(self, signal_category: str) -> AssessmentType:
        """Derive the assessment type from signal category (FR-010)."""
        return CATEGORY_TO_ASSESSMENT_TYPE.get(signal_category, "impact_projection")
