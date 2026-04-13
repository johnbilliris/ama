"""Unit tests for RecoveryOutcome catalogue models.

Tests: hierarchical ID validation, RecoveryOutcome, CatalogueActivity,
CatalogueIndicator, RecoveryDomain, ObjectiveType.
"""
import pytest

from packages.domain.src.domain.models.recovery_outcome import (
    RecoveryOutcome,
    CatalogueActivity,
    CatalogueIndicator,
    RecoveryDomain,
    ObjectiveType,
    CATALOGUE_OUTCOME_ID_PATTERN,
    CATALOGUE_ACTIVITY_ID_PATTERN,
    CATALOGUE_INDICATOR_ID_PATTERN,
)


class TestRecoveryOutcome:
    def test_valid_outcome_creation(self):
        outcome = RecoveryOutcome(
            outcome_id="aidr:social:community-health-levels",
            domain="social",
            objective_type="resilience",
            title="Community Health Levels",
        )
        assert outcome.outcome_id == "aidr:social:community-health-levels"
        assert outcome.domain == "social"

    def test_outcome_with_description(self):
        outcome = RecoveryOutcome(
            outcome_id="aidr:economic:local-business-recovery",
            domain="economic",
            objective_type="sustainability",
            title="Local Business Recovery",
            description="Businesses in affected area resume operations",
        )
        assert outcome.description == "Businesses in affected area resume operations"

    def test_outcome_with_activity_and_indicator_ids(self):
        outcome = RecoveryOutcome(
            outcome_id="aidr:built:housing-stock",
            domain="built",
            objective_type="resilience",
            title="Housing Stock",
            activity_ids=["aidr:built:housing-stock:act:1"],
            indicator_ids=["aidr:built:housing-stock:ind:1", "aidr:built:housing-stock:ind:2"],
        )
        assert len(outcome.activity_ids) == 1
        assert len(outcome.indicator_ids) == 2

    def test_invalid_outcome_id_format(self):
        with pytest.raises(ValueError, match="outcome_id must match"):
            RecoveryOutcome(
                outcome_id="bad-format",
                domain="social",
                objective_type="resilience",
                title="Test",
            )

    def test_outcome_id_missing_domain(self):
        with pytest.raises(ValueError, match="outcome_id must match"):
            RecoveryOutcome(
                outcome_id="aidr::health",
                domain="social",
                objective_type="resilience",
                title="Test",
            )

    def test_outcome_id_invalid_domain(self):
        with pytest.raises(ValueError, match="outcome_id must match"):
            RecoveryOutcome(
                outcome_id="aidr:invalid_domain:health",
                domain="social",
                objective_type="resilience",
                title="Test",
            )

    def test_outcome_id_uppercase_rejected(self):
        with pytest.raises(ValueError, match="outcome_id must match"):
            RecoveryOutcome(
                outcome_id="aidr:social:CommunityHealth",
                domain="social",
                objective_type="resilience",
                title="Test",
            )

    @pytest.mark.parametrize("domain", ["overarching", "social", "economic", "built", "natural"])
    def test_all_five_recovery_domains(self, domain):
        outcome = RecoveryOutcome(
            outcome_id=f"aidr:{domain}:test-outcome",
            domain=domain,
            objective_type="resilience",
            title="Test",
        )
        assert outcome.domain == domain

    @pytest.mark.parametrize("obj_type", ["sustainability", "resilience"])
    def test_both_objective_types(self, obj_type):
        outcome = RecoveryOutcome(
            outcome_id="aidr:social:test",
            domain="social",
            objective_type=obj_type,
            title="Test",
        )
        assert outcome.objective_type == obj_type

    def test_outcome_default_has_developed_activities(self):
        outcome = RecoveryOutcome(
            outcome_id="aidr:social:test",
            domain="social",
            objective_type="resilience",
            title="Test",
        )
        assert outcome.has_developed_activities is True


class TestCatalogueActivity:
    def test_valid_activity_creation(self):
        activity = CatalogueActivity(
            activity_id="aidr:social:community-health:act:1",
            outcome_id="aidr:social:community-health",
            domain="social",
            title="Health support programs",
        )
        assert activity.activity_id == "aidr:social:community-health:act:1"

    def test_activity_with_description(self):
        activity = CatalogueActivity(
            activity_id="aidr:economic:local-business:act:2",
            outcome_id="aidr:economic:local-business",
            domain="economic",
            title="Business grants",
            description="Financial assistance to local businesses",
        )
        assert activity.description == "Financial assistance to local businesses"

    def test_invalid_activity_id_no_act_segment(self):
        with pytest.raises(ValueError, match="activity_id must match"):
            CatalogueActivity(
                activity_id="aidr:social:community-health:1",
                outcome_id="aidr:social:community-health",
                domain="social",
                title="Test",
            )

    def test_invalid_activity_id_bad_domain(self):
        with pytest.raises(ValueError, match="activity_id must match"):
            CatalogueActivity(
                activity_id="aidr:wrong:community-health:act:1",
                outcome_id="aidr:social:community-health",
                domain="social",
                title="Test",
            )

    def test_invalid_activity_id_no_index(self):
        with pytest.raises(ValueError, match="activity_id must match"):
            CatalogueActivity(
                activity_id="aidr:social:community-health:act:",
                outcome_id="aidr:social:community-health",
                domain="social",
                title="Test",
            )

    def test_invalid_activity_id_ind_instead_of_act(self):
        with pytest.raises(ValueError, match="activity_id must match"):
            CatalogueActivity(
                activity_id="aidr:social:community-health:ind:1",
                outcome_id="aidr:social:community-health",
                domain="social",
                title="Test",
            )

    @pytest.mark.parametrize("domain", ["overarching", "social", "economic", "built", "natural"])
    def test_activity_all_domains(self, domain):
        activity = CatalogueActivity(
            activity_id=f"aidr:{domain}:test-slug:act:1",
            outcome_id=f"aidr:{domain}:test-slug",
            domain=domain,
            title="Test",
        )
        assert activity.domain == domain


class TestCatalogueIndicator:
    def test_valid_indicator_creation(self):
        indicator = CatalogueIndicator(
            indicator_id="aidr:social:community-health:ind:1",
            outcome_id="aidr:social:community-health",
            domain="social",
            title="Community health metric",
        )
        assert indicator.indicator_id == "aidr:social:community-health:ind:1"

    def test_indicator_with_full_details(self):
        indicator = CatalogueIndicator(
            indicator_id="aidr:economic:local-business:ind:3",
            outcome_id="aidr:economic:local-business",
            domain="economic",
            title="Business reopening rate",
            description="Percentage of businesses that have reopened",
            data_collection_methodology="Survey-based quarterly assessment",
            indicator_type="quantitative",
        )
        assert indicator.data_collection_methodology == "Survey-based quarterly assessment"
        assert indicator.indicator_type == "quantitative"

    def test_invalid_indicator_id_no_ind_segment(self):
        with pytest.raises(ValueError, match="indicator_id must match"):
            CatalogueIndicator(
                indicator_id="aidr:social:community-health:1",
                outcome_id="aidr:social:community-health",
                domain="social",
                title="Test",
            )

    def test_invalid_indicator_id_bad_domain(self):
        with pytest.raises(ValueError, match="indicator_id must match"):
            CatalogueIndicator(
                indicator_id="aidr:wrong:community-health:ind:1",
                outcome_id="aidr:social:community-health",
                domain="social",
                title="Test",
            )

    def test_invalid_indicator_id_act_instead_of_ind(self):
        with pytest.raises(ValueError, match="indicator_id must match"):
            CatalogueIndicator(
                indicator_id="aidr:social:community-health:act:1",
                outcome_id="aidr:social:community-health",
                domain="social",
                title="Test",
            )

    @pytest.mark.parametrize("ind_type", ["quantitative", "qualitative", "both"])
    def test_all_indicator_types_valid(self, ind_type):
        indicator = CatalogueIndicator(
            indicator_id="aidr:social:test-slug:ind:1",
            outcome_id="aidr:social:test-slug",
            domain="social",
            title="Test",
            indicator_type=ind_type,
        )
        assert indicator.indicator_type == ind_type

    def test_indicator_default_type_is_quantitative(self):
        indicator = CatalogueIndicator(
            indicator_id="aidr:social:test:ind:1",
            outcome_id="aidr:social:test",
            domain="social",
            title="Test",
        )
        assert indicator.indicator_type == "quantitative"

    @pytest.mark.parametrize("domain", ["overarching", "social", "economic", "built", "natural"])
    def test_indicator_all_domains(self, domain):
        indicator = CatalogueIndicator(
            indicator_id=f"aidr:{domain}:test-slug:ind:1",
            outcome_id=f"aidr:{domain}:test-slug",
            domain=domain,
            title="Test",
        )
        assert indicator.domain == domain


class TestIdPatterns:
    def test_outcome_pattern_matches_valid(self):
        assert CATALOGUE_OUTCOME_ID_PATTERN.match("aidr:social:community-health")

    def test_outcome_pattern_rejects_activity(self):
        assert not CATALOGUE_OUTCOME_ID_PATTERN.match("aidr:social:community-health:act:1")

    def test_activity_pattern_matches_valid(self):
        assert CATALOGUE_ACTIVITY_ID_PATTERN.match("aidr:social:community-health:act:1")

    def test_activity_pattern_rejects_indicator(self):
        assert not CATALOGUE_ACTIVITY_ID_PATTERN.match("aidr:social:community-health:ind:1")

    def test_indicator_pattern_matches_valid(self):
        assert CATALOGUE_INDICATOR_ID_PATTERN.match("aidr:social:community-health:ind:1")

    def test_indicator_pattern_rejects_activity(self):
        assert not CATALOGUE_INDICATOR_ID_PATTERN.match("aidr:social:community-health:act:1")
