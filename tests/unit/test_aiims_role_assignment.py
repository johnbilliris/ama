"""Unit tests for AIIMS role mapping and coverage validation."""

import pytest

from apps.agents.common.aiims_mapping import (
    DEFAULT_AGENT_AIIMS_MAP,
    FULL_COVERAGE_REQUIRED_LEVEL,
    get_default_function,
    is_full_coverage_required,
    validate_coverage,
)
from packages.domain.src.domain.models.aiims_role_assignment import ALL_AIIMS_FUNCTIONS

# ---------------------------------------------------------------------------
# Default mapping
# ---------------------------------------------------------------------------


class TestDefaultAgentAiimsMap:
    def test_monitoring_maps_to_intelligence(self) -> None:
        assert DEFAULT_AGENT_AIIMS_MAP["monitoring"] == "intelligence"

    def test_risk_assessment_maps_to_planning(self) -> None:
        assert DEFAULT_AGENT_AIIMS_MAP["risk_assessment"] == "planning"

    def test_evacuation_maps_to_operations(self) -> None:
        assert DEFAULT_AGENT_AIIMS_MAP["evacuation"] == "operations"

    def test_resource_allocation_maps_to_logistics(self) -> None:
        assert DEFAULT_AGENT_AIIMS_MAP["resource_allocation"] == "logistics"

    def test_communication_maps_to_public_information(self) -> None:
        assert DEFAULT_AGENT_AIIMS_MAP["communication"] == "public_information"

    def test_map_has_five_entries(self) -> None:
        assert len(DEFAULT_AGENT_AIIMS_MAP) == 5


# ---------------------------------------------------------------------------
# get_default_function
# ---------------------------------------------------------------------------


class TestGetDefaultFunction:
    @pytest.mark.parametrize(
        ("agent", "expected"),
        [
            ("monitoring", "intelligence"),
            ("risk_assessment", "planning"),
            ("evacuation", "operations"),
            ("resource_allocation", "logistics"),
            ("communication", "public_information"),
        ],
    )
    def test_known_agents_return_correct_function(self, agent: str, expected: str) -> None:
        assert get_default_function(agent) == expected

    def test_unknown_agent_returns_none(self) -> None:
        assert get_default_function("unknown_agent") is None

    def test_empty_string_returns_none(self) -> None:
        assert get_default_function("") is None


# ---------------------------------------------------------------------------
# validate_coverage
# ---------------------------------------------------------------------------


class TestValidateCoverage:
    def test_full_coverage(self) -> None:
        ratio, missing = validate_coverage(list(ALL_AIIMS_FUNCTIONS), incident_level=3)
        assert ratio == pytest.approx(1.0)
        assert missing == []

    def test_partial_coverage(self) -> None:
        assigned = ["control", "intelligence", "planning"]
        ratio, missing = validate_coverage(assigned, incident_level=2)
        assert ratio == pytest.approx(3 / 6)
        assert "operations" in missing
        assert "logistics" in missing
        assert "public_information" in missing

    def test_empty_coverage(self) -> None:
        ratio, missing = validate_coverage([], incident_level=1)
        assert ratio == pytest.approx(0.0)
        assert len(missing) == 6

    def test_single_function_coverage(self) -> None:
        ratio, missing = validate_coverage(["control"], incident_level=1)
        assert ratio == pytest.approx(1 / 6)
        assert "control" not in missing
        assert len(missing) == 5

    def test_missing_sorted_alphabetically(self) -> None:
        ratio, missing = validate_coverage(["planning"], incident_level=1)
        assert missing == sorted(missing)


# ---------------------------------------------------------------------------
# is_full_coverage_required
# ---------------------------------------------------------------------------


class TestIsFullCoverageRequired:
    def test_level_3_requires_full_coverage(self) -> None:
        assert is_full_coverage_required(3) is True

    def test_level_2_does_not_require_full_coverage(self) -> None:
        assert is_full_coverage_required(2) is False

    def test_level_1_does_not_require_full_coverage(self) -> None:
        assert is_full_coverage_required(1) is False

    def test_threshold_constant(self) -> None:
        assert FULL_COVERAGE_REQUIRED_LEVEL == 3
