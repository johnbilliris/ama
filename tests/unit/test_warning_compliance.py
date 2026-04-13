"""Unit tests for AWS warning compliance validator and 10-principle checker."""

import pytest
from apps.agents.common.warning_compliance import (
    WarningComplianceResult,
    validate_tier_colour_consistency,
    validate_warning_compliance,
    validate_warning_principles,
)
from packages.domain.src.domain.models.public_alert import (
    WARNING_PRINCIPLE_KEYS,
    PublicAlert,
)


@pytest.fixture()
def compliant_alert() -> PublicAlert:
    """A fully compliant tiered warning alert."""
    return PublicAlert(
        alert_id="ALR-001",
        incident_id="INC-001",
        warning_tier="emergency_warning",
        action_statement="Leave immediately via main road",
        hazard_icon="fire",
        approval_mode="human_approved",
        audience_segments=["zone-A", "zone-B"],
        languages=["en", "vi"],
        accessibility_attributes=["auslan"],
        content_blocks={"headline": "Emergency", "body": "Fire approaching suburb"},
    )


@pytest.fixture()
def all_clear_alert() -> PublicAlert:
    """An all-clear alert with no tier."""
    return PublicAlert(
        alert_id="ALR-002",
        incident_id="INC-001",
        is_all_clear=True,
    )


# ---------------------------------------------------------------------------
# Tier/colour consistency
# ---------------------------------------------------------------------------


class TestTierColourConsistency:
    def test_compliant_alert_no_errors(self, compliant_alert: PublicAlert) -> None:
        errors = validate_tier_colour_consistency(compliant_alert)
        assert errors == []

    def test_all_clear_without_tier_no_errors(self, all_clear_alert: PublicAlert) -> None:
        errors = validate_tier_colour_consistency(all_clear_alert)
        assert errors == []

    def test_missing_action_statement_detected(self) -> None:
        alert = PublicAlert(
            alert_id="ALR-003",
            incident_id="INC-001",
            warning_tier="advice",
            action_statement="Act now",
        )
        # Override action_statement to empty after construction via model_copy
        patched = alert.model_copy(update={"action_statement": ""})
        errors = validate_tier_colour_consistency(patched)
        assert any("action_statement" in e for e in errors)

    def test_missing_hazard_icon_flagged(self) -> None:
        alert = PublicAlert(
            alert_id="ALR-004",
            incident_id="INC-001",
            warning_tier="advice",
            action_statement="Monitor conditions",
        )
        errors = validate_tier_colour_consistency(alert)
        assert any("hazard_icon" in e for e in errors)

    def test_all_clear_with_tier_detected(self) -> None:
        alert = PublicAlert(
            alert_id="ALR-005",
            incident_id="INC-001",
            is_all_clear=True,
        )
        # Force tier on all-clear via model_copy to bypass model validator
        patched = alert.model_copy(update={"warning_tier": "advice"})
        errors = validate_tier_colour_consistency(patched)
        assert any("All-clear" in e for e in errors)


# ---------------------------------------------------------------------------
# Warning principles
# ---------------------------------------------------------------------------


class TestWarningPrinciples:
    def test_all_10_principles_evaluated(self, compliant_alert: PublicAlert) -> None:
        result = validate_warning_principles(compliant_alert)
        assert len(result) == 10
        assert set(result.keys()) == set(WARNING_PRINCIPLE_KEYS)

    def test_content_analysis_passthrough(self, compliant_alert: PublicAlert) -> None:
        analysis = {k: True for k in WARNING_PRINCIPLE_KEYS}
        result = validate_warning_principles(compliant_alert, content_analysis=analysis)
        assert result == analysis

    def test_structural_checks_without_content(self) -> None:
        alert = PublicAlert(
            alert_id="ALR-006",
            incident_id="INC-001",
            is_all_clear=True,
        )
        result = validate_warning_principles(alert)
        assert len(result) == 10
        # All-clear with no action → empowering and action_calling should be False
        assert result["empowering"] is False
        assert result["action_calling"] is False

    def test_life_saving_true_for_tiered_alert(self, compliant_alert: PublicAlert) -> None:
        result = validate_warning_principles(compliant_alert)
        assert result["life_saving"] is True

    def test_life_saving_true_for_all_clear(self, all_clear_alert: PublicAlert) -> None:
        result = validate_warning_principles(all_clear_alert)
        assert result["life_saving"] is True


# ---------------------------------------------------------------------------
# Full compliance validation
# ---------------------------------------------------------------------------


class TestWarningCompliance:
    def test_compliant_alert_passes(self, compliant_alert: PublicAlert) -> None:
        result = validate_warning_compliance(compliant_alert)
        assert isinstance(result, WarningComplianceResult)
        assert result.tier_valid is True

    def test_principle_compliance_rate_all_pass(self) -> None:
        r = WarningComplianceResult()
        r.principles_checklist = {k: True for k in WARNING_PRINCIPLE_KEYS}
        assert r.principle_compliance_rate == 1.0

    def test_principle_compliance_rate_none_pass(self) -> None:
        r = WarningComplianceResult()
        r.principles_checklist = {k: False for k in WARNING_PRINCIPLE_KEYS}
        assert r.principle_compliance_rate == 0.0

    def test_principle_compliance_rate_half_pass(self) -> None:
        r = WarningComplianceResult()
        keys = list(WARNING_PRINCIPLE_KEYS)
        r.principles_checklist = {k: (i < 5) for i, k in enumerate(keys)}
        assert r.principle_compliance_rate == pytest.approx(0.5)

    def test_principle_compliance_rate_empty(self) -> None:
        r = WarningComplianceResult()
        assert r.principle_compliance_rate == 0.0

    def test_non_compliant_alert_errors(self) -> None:
        alert = PublicAlert(
            alert_id="ALR-007",
            incident_id="INC-001",
            is_all_clear=True,
        )
        result = validate_warning_compliance(alert)
        assert result.is_compliant is False
        assert len(result.errors) > 0

    def test_content_analysis_forwarded(self, compliant_alert: PublicAlert) -> None:
        analysis = {k: True for k in WARNING_PRINCIPLE_KEYS}
        result = validate_warning_compliance(compliant_alert, content_analysis=analysis)
        assert result.principles_checklist == analysis
