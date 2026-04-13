"""Unit tests for the CatalogueService in the monitoring agent.

The service loads from seed JSON files, so these tests use the real catalogue data
to verify correct loading, filtering, lookup, and suggestion behaviour.
"""
import pytest

from monitoring.catalogue_service import CatalogueService, DOMAIN_FILES, SEED_ROOT


@pytest.fixture(scope="module")
def catalogue():
    """Shared CatalogueService instance loaded once for all tests."""
    return CatalogueService()


class TestCatalogueLoading:
    """Verify that the catalogue loads correctly from seed files."""

    def test_seed_root_exists(self):
        assert SEED_ROOT.exists(), f"Seed root not found: {SEED_ROOT}"

    def test_all_domain_files_exist(self):
        for domain in DOMAIN_FILES:
            path = SEED_ROOT / f"{domain}.json"
            assert path.exists(), f"Missing seed file: {path}"

    def test_outcomes_loaded(self, catalogue):
        outcomes = catalogue.list_outcomes()
        assert len(outcomes) > 0, "No outcomes loaded from seed data"

    def test_evaluation_questions_loaded(self, catalogue):
        eq = catalogue.get_evaluation_questions("governance")
        assert eq is not None
        assert "questions" in eq
        assert len(eq["questions"]) > 0


class TestListOutcomes:
    """Test outcome listing and filtering."""

    def test_list_all_outcomes(self, catalogue):
        outcomes = catalogue.list_outcomes()
        assert isinstance(outcomes, list)
        assert len(outcomes) > 0

    def test_filter_by_domain_social(self, catalogue):
        outcomes = catalogue.list_outcomes(domain="social")
        assert all(o["domain"] == "social" for o in outcomes)
        assert len(outcomes) > 0

    def test_filter_by_domain_economic(self, catalogue):
        outcomes = catalogue.list_outcomes(domain="economic")
        assert all(o["domain"] == "economic" for o in outcomes)

    def test_filter_by_domain_built(self, catalogue):
        outcomes = catalogue.list_outcomes(domain="built")
        assert all(o["domain"] == "built" for o in outcomes)

    def test_filter_by_domain_natural(self, catalogue):
        outcomes = catalogue.list_outcomes(domain="natural")
        assert all(o["domain"] == "natural" for o in outcomes)

    def test_filter_by_nonexistent_domain(self, catalogue):
        outcomes = catalogue.list_outcomes(domain="nonexistent")
        assert outcomes == []

    def test_filter_by_objective_type(self, catalogue):
        outcomes = catalogue.list_outcomes(objective_type="sustainability")
        assert len(outcomes) > 0
        assert all(o["objective_type"] == "sustainability" for o in outcomes)

    def test_combined_filter(self, catalogue):
        outcomes = catalogue.list_outcomes(domain="social", objective_type="sustainability")
        assert all(o["domain"] == "social" and o["objective_type"] == "sustainability" for o in outcomes)


class TestGetOutcome:
    """Test single outcome retrieval."""

    def test_get_existing_outcome(self, catalogue):
        outcome = catalogue.get_outcome("aidr:social:community-health-levels")
        assert outcome is not None
        assert outcome["outcome_id"] == "aidr:social:community-health-levels"
        assert outcome["domain"] == "social"
        assert "title" in outcome

    def test_get_nonexistent_outcome(self, catalogue):
        outcome = catalogue.get_outcome("nonexistent-outcome-id")
        assert outcome is None

    def test_outcome_has_required_fields(self, catalogue):
        outcomes = catalogue.list_outcomes()
        for o in outcomes:
            assert "outcome_id" in o
            assert "domain" in o
            assert "objective_type" in o
            assert "title" in o
            assert "activity_ids" in o
            assert "indicator_ids" in o


class TestActivitiesAndIndicators:
    """Test activity and indicator retrieval for outcomes."""

    def test_get_activities_for_existing_outcome(self, catalogue):
        activities = catalogue.get_activities_for_outcome("aidr:social:community-health-levels")
        assert isinstance(activities, list)
        assert len(activities) > 0
        for act in activities:
            assert "activity_id" in act
            assert "title" in act

    def test_get_activities_for_nonexistent_outcome(self, catalogue):
        activities = catalogue.get_activities_for_outcome("nonexistent")
        assert activities == []

    def test_get_indicators_for_existing_outcome(self, catalogue):
        indicators = catalogue.get_indicators_for_outcome("aidr:social:community-health-levels")
        assert isinstance(indicators, list)
        assert len(indicators) > 0
        for ind in indicators:
            assert "indicator_id" in ind
            assert "title" in ind

    def test_get_indicators_for_nonexistent_outcome(self, catalogue):
        indicators = catalogue.get_indicators_for_outcome("nonexistent")
        assert indicators == []


class TestDomainSummary:
    """Test domain summary statistics."""

    def test_social_domain_summary(self, catalogue):
        summary = catalogue.get_domain_summary("social")
        assert summary["domain"] == "social"
        assert summary["outcome_count"] > 0
        assert summary["activity_count"] > 0
        assert summary["indicator_count"] > 0

    def test_nonexistent_domain_summary(self, catalogue):
        summary = catalogue.get_domain_summary("nonexistent")
        assert summary["domain"] == "nonexistent"
        assert summary["outcome_count"] == 0
        assert summary["activity_count"] == 0
        assert summary["indicator_count"] == 0


class TestSuggestActivities:
    """Test activity suggestion for lagging indicators."""

    def test_suggest_for_known_indicator(self, catalogue):
        suggestions = catalogue.suggest_activities(
            ["aidr:social:community-health-levels:ind:1"]
        )
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        for s in suggestions:
            assert "activity" in s
            assert "for_indicator" in s
            assert "outcome" in s
            assert "rationale" in s

    def test_suggest_for_unknown_indicator(self, catalogue):
        suggestions = catalogue.suggest_activities(["nonexistent:ind:999"])
        assert suggestions == []

    def test_suggest_for_multiple_indicators(self, catalogue):
        suggestions = catalogue.suggest_activities([
            "aidr:social:community-health-levels:ind:1",
            "nonexistent:ind:999",
        ])
        # Only known indicators should produce suggestions
        assert len(suggestions) > 0
        for s in suggestions:
            assert s["for_indicator"] == "aidr:social:community-health-levels:ind:1"

    def test_suggest_for_empty_list(self, catalogue):
        suggestions = catalogue.suggest_activities([])
        assert suggestions == []


class TestEvaluationQuestions:
    """Test evaluation question retrieval."""

    def test_get_governance_questions(self, catalogue):
        eq = catalogue.get_evaluation_questions("governance")
        assert eq is not None
        assert eq["domain"] == "governance"
        assert "questions" in eq
        assert len(eq["questions"]) > 0

    def test_get_community_engagement_questions(self, catalogue):
        eq = catalogue.get_evaluation_questions("community_engagement")
        assert eq is not None

    def test_get_effectiveness_questions(self, catalogue):
        eq = catalogue.get_evaluation_questions("effectiveness")
        assert eq is not None

    def test_get_nonexistent_domain_questions(self, catalogue):
        eq = catalogue.get_evaluation_questions("nonexistent")
        assert eq is None
