"""Tests for risk_assessment.severity – SeverityComputer."""

import pytest
from risk_assessment.models import SeverityLevel
from risk_assessment.severity import (
    SeverityComputer,
)


@pytest.fixture
def computer():
    return SeverityComputer()


# ---------------------------------------------------------------------------
# compute_severity – category / disaster_type mapping
# ---------------------------------------------------------------------------


class TestComputeSeverity:
    def test_fire_yields_high(self, computer):
        result = computer.compute_severity("fire", confidence_adjusted=0.8)
        assert result == SeverityLevel.high

    def test_cyclone_yields_critical(self, computer):
        result = computer.compute_severity("weather", confidence_adjusted=0.8, disaster_type="cyclone")
        assert result == SeverityLevel.critical

    def test_flood_yields_high(self, computer):
        result = computer.compute_severity("hydrology", confidence_adjusted=0.8, disaster_type="flood")
        assert result == SeverityLevel.high

    def test_earthquake_yields_critical(self, computer):
        result = computer.compute_severity("geohazard", confidence_adjusted=0.8, disaster_type="earthquake")
        assert result == SeverityLevel.critical

    def test_tsunami_yields_critical(self, computer):
        result = computer.compute_severity("geohazard", confidence_adjusted=0.8, disaster_type="tsunami")
        assert result == SeverityLevel.critical

    def test_unknown_category_yields_moderate(self, computer):
        result = computer.compute_severity("aliens", confidence_adjusted=0.8)
        assert result == SeverityLevel.moderate

    # -------------------------------------------------------------------
    # Population upgrade
    # -------------------------------------------------------------------

    def test_population_upgrades_by_one_level(self, computer):
        base = computer.compute_severity("weather", confidence_adjusted=0.8)
        upgraded = computer.compute_severity("weather", confidence_adjusted=0.8, population_estimate=50_000)
        severity_order = [
            SeverityLevel.low,
            SeverityLevel.moderate,
            SeverityLevel.high,
            SeverityLevel.critical,
        ]
        base_idx = severity_order.index(base)
        upgraded_idx = severity_order.index(upgraded)
        assert upgraded_idx == min(base_idx + 1, 3)

    # -------------------------------------------------------------------
    # Confidence downgrade
    # -------------------------------------------------------------------

    def test_low_confidence_downgrades(self, computer):
        high_conf = computer.compute_severity("fire", confidence_adjusted=0.8)
        low_conf = computer.compute_severity("fire", confidence_adjusted=0.3)
        severity_order = [
            SeverityLevel.low,
            SeverityLevel.moderate,
            SeverityLevel.high,
            SeverityLevel.critical,
        ]
        assert severity_order.index(low_conf) <= severity_order.index(high_conf)

    def test_low_confidence_floor_is_low(self, computer):
        result = computer.compute_severity("community_report", confidence_adjusted=0.1)
        assert result == SeverityLevel.low


# ---------------------------------------------------------------------------
# derive_assessment_type
# ---------------------------------------------------------------------------


class TestDeriveAssessmentType:
    @pytest.mark.parametrize(
        "category, expected",
        [
            ("fire", "spread_prediction"),
            ("weather", "impact_projection"),
            ("hydrology", "impact_projection"),
            ("geohazard", "impact_projection"),
            ("infrastructure", "infrastructure_risk"),
            ("community_report", "community_impact"),
            ("social_report", "community_impact"),
        ],
    )
    def test_known_categories(self, computer, category, expected):
        assert computer.derive_assessment_type(category) == expected

    def test_unknown_category_returns_fallback(self, computer):
        result = computer.derive_assessment_type("unknown_hazard")
        assert isinstance(result, str)
