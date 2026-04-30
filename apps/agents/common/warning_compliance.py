"""AWS three-tier warning compliance validator and ten-principle checker.

Validates warning tier/colour/icon consistency, action statement presence,
and all 10 Australian Warning System principles.

FRs: FR-006 | SCs: SC-006 | Research: R-004
"""

from packages.domain.src.domain.models.public_alert import (
    TIER_COLOUR_MAP,
    WARNING_PRINCIPLE_KEYS,
    PublicAlert,
)

# Ten Warning Principles (FR-006, SC-006)
# Each principle is a named check with a validation function
PRINCIPLE_DESCRIPTIONS: dict[str, str] = {
    "life_saving": "Warning content prioritises life safety",
    "empowering": "Warning empowers recipients to take action",
    "trusted": "Warning comes from a trusted, authoritative source",
    "risk_scaled": "Warning severity matches assessed risk level",
    "timely_targeted": "Warning is timely and targeted to affected areas",
    "impact_conveying": "Warning clearly conveys expected impact",
    "action_calling": "Warning includes clear call to action",
    "clearly_communicated": "Warning uses clear, plain language",
    "accessible": "Warning is accessible to diverse audiences",
    "bigger_picture": "Warning places event in broader context",
}


class WarningComplianceResult:
    """Result of a warning compliance validation check."""

    def __init__(self) -> None:
        self.is_compliant: bool = True
        self.tier_valid: bool = True
        self.colour_valid: bool = True
        self.icon_valid: bool = True
        self.action_statement_valid: bool = True
        self.principles_checklist: dict[str, bool] = {}
        self.errors: list[str] = []

    @property
    def principle_compliance_rate(self) -> float:
        """Percentage of principles that passed (0.0–1.0)."""
        if not self.principles_checklist:
            return 0.0
        passed = sum(1 for v in self.principles_checklist.values() if v)
        return passed / len(self.principles_checklist)


def validate_tier_colour_consistency(alert: PublicAlert) -> list[str]:
    """Validate that warning_tier and colour_code are consistent."""
    errors: list[str] = []
    if alert.warning_tier is not None:
        expected_colour = TIER_COLOUR_MAP.get(alert.warning_tier)
        if alert.colour_code != expected_colour:
            errors.append(
                f"Colour mismatch: tier '{alert.warning_tier}' requires '{expected_colour}', got '{alert.colour_code}'"
            )
        if not alert.action_statement:
            errors.append("action_statement is required for tiered warnings")
        if alert.hazard_icon is None:
            errors.append("hazard_icon is recommended for tiered warnings")
    if alert.is_all_clear and alert.warning_tier is not None:
        errors.append("All-clear notifications must not have a warning_tier")
    return errors


def validate_warning_principles(
    alert: PublicAlert,
    *,
    content_analysis: dict[str, bool] | None = None,
) -> dict[str, bool]:
    """Evaluate the 10 AWS warning principles against an alert.

    If content_analysis is provided, use it directly. Otherwise, perform
    basic structural checks based on alert fields.

    Returns:
        Dict mapping principle name to pass/fail status.
    """
    if content_analysis and set(content_analysis.keys()) == set(WARNING_PRINCIPLE_KEYS):
        return content_analysis

    # Structural checks when no LLM-based analysis is available
    checklist: dict[str, bool] = {}
    has_content = bool(alert.content_blocks)
    has_action = bool(alert.action_statement)
    has_audiences = bool(alert.audience_segments)
    has_accessibility = bool(alert.accessibility_attributes)
    has_languages = bool(alert.languages)
    has_tier = alert.warning_tier is not None

    checklist["life_saving"] = has_tier or alert.is_all_clear
    checklist["empowering"] = has_action
    checklist["trusted"] = alert.approval_mode in ("human_approved", "escalated")
    checklist["risk_scaled"] = has_tier
    checklist["timely_targeted"] = has_audiences
    checklist["impact_conveying"] = has_content
    checklist["action_calling"] = has_action
    checklist["clearly_communicated"] = has_content
    checklist["accessible"] = has_accessibility or has_languages
    checklist["bigger_picture"] = has_content and len(alert.content_blocks) > 1

    return checklist


def validate_warning_compliance(
    alert: PublicAlert,
    *,
    content_analysis: dict[str, bool] | None = None,
) -> WarningComplianceResult:
    """Full compliance validation for an AWS warning alert.

    Checks tier/colour/icon consistency and all 10 warning principles.
    Returns a WarningComplianceResult with detailed findings.
    """
    result = WarningComplianceResult()

    # Tier/colour/icon checks
    tier_errors = validate_tier_colour_consistency(alert)
    if tier_errors:
        result.is_compliant = False
        result.tier_valid = False
        result.errors.extend(tier_errors)

    # Principles check
    result.principles_checklist = validate_warning_principles(alert, content_analysis=content_analysis)

    # SC-006: 100% compliance required
    if not all(result.principles_checklist.values()):
        result.is_compliant = False
        failed = [k for k, v in result.principles_checklist.items() if not v]
        result.errors.append(f"Failed warning principles: {failed}")

    return result
