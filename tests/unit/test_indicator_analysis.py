"""Unit tests for IndicatorAnalysisService.

Tests cross-domain correlation analysis, activity recommendations,
community summary generation, and LLM enrichment paths.
"""

from unittest.mock import MagicMock

import pytest
from monitoring.indicator_analysis import IndicatorAnalysisService


@pytest.fixture
def analysis_service():
    """IndicatorAnalysisService with no LLM or content safety (rule-based only)."""
    return IndicatorAnalysisService()


@pytest.fixture
def mock_catalogue():
    """Mock CatalogueService with a canned suggest_activities response."""
    catalogue = MagicMock()
    catalogue.suggest_activities.return_value = [
        {
            "activity": {"activity_id": "act-1", "title": "Deliver health programs"},
            "for_indicator": "ind-1",
            "outcome": "Community health restored",
            "rationale": "Addresses lagging indicator",
        }
    ]
    return catalogue


@pytest.fixture
def mock_llm():
    """Mock LLM client that returns a valid response."""
    llm = MagicMock()
    llm.generate_response.return_value = {"text": "Cross-domain analysis shows interconnected recovery challenges."}
    return llm


@pytest.fixture
def mock_content_safety():
    """Mock content safety validator that passes all text."""
    cs = MagicMock()
    result = MagicMock()
    result.passed = True
    cs.validate.return_value = result
    return cs


# ---------------------------------------------------------------------------
# Cross-domain correlation analysis
# ---------------------------------------------------------------------------


class TestCrossDomainCorrelations:
    def test_single_domain_no_lagging(self, analysis_service):
        data = [
            {"domain": "social", "indicator_name": "health", "trend": "positive", "value": 0.9, "target_value": 1.0},
        ]
        result = analysis_service.analyse_cross_domain_correlations(data)
        assert result["total_indicators"] == 1
        assert result["correlations"] == []
        assert result["lagging_domains"] == []
        assert "analysis_id" in result
        assert "generated_at" in result

    def test_single_domain_with_lagging(self, analysis_service):
        data = [
            {"domain": "social", "indicator_name": "health", "trend": "negative", "value": 0.3, "target_value": 1.0},
        ]
        result = analysis_service.analyse_cross_domain_correlations(data)
        assert len(result["lagging_domains"]) == 1
        assert result["lagging_domains"][0]["domain"] == "social"
        assert result["correlations"] == []  # Need 2+ domains for correlations

    def test_two_domains_both_lagging(self, analysis_service):
        data = [
            {"domain": "social", "indicator_name": "health", "trend": "negative", "value": 0.3, "target_value": 1.0},
            {
                "domain": "economic",
                "indicator_name": "employment",
                "trend": "negative",
                "value": 0.2,
                "target_value": 1.0,
            },
        ]
        result = analysis_service.analyse_cross_domain_correlations(data)
        assert len(result["lagging_domains"]) == 2
        assert len(result["correlations"]) == 1
        corr = result["correlations"][0]
        assert set(corr["domains"]) == {"social", "economic"}
        assert "description" in corr
        assert "evidence" in corr

    def test_three_domains_lagging_produces_three_correlations(self, analysis_service):
        data = [
            {"domain": "social", "indicator_name": "x", "trend": "negative"},
            {"domain": "economic", "indicator_name": "y", "trend": "negative"},
            {"domain": "built", "indicator_name": "z", "trend": "negative"},
        ]
        result = analysis_service.analyse_cross_domain_correlations(data)
        # 3 choose 2 = 3 correlations
        assert len(result["correlations"]) == 3

    def test_mixed_lagging_and_progressing(self, analysis_service):
        data = [
            {"domain": "social", "indicator_name": "health", "trend": "negative"},
            {"domain": "economic", "indicator_name": "jobs", "trend": "positive", "value": 0.9, "target_value": 1.0},
            {"domain": "built", "indicator_name": "housing", "value": 0.5, "target_value": 1.0},  # <80% → lagging
        ]
        result = analysis_service.analyse_cross_domain_correlations(data)
        assert len(result["lagging_domains"]) == 2  # social + built
        assert len(result["correlations"]) == 1

    def test_value_based_lagging_detection(self, analysis_service):
        """Indicators with value < 80% of target are flagged as lagging."""
        data = [
            {"domain": "social", "indicator_name": "x", "value": 0.79, "target_value": 1.0},  # <0.8 → lagging
            {"domain": "economic", "indicator_name": "y", "value": 0.81, "target_value": 1.0},  # >0.8 → OK
        ]
        result = analysis_service.analyse_cross_domain_correlations(data)
        assert len(result["lagging_domains"]) == 1
        assert result["lagging_domains"][0]["domain"] == "social"

    def test_empty_indicator_data(self, analysis_service):
        result = analysis_service.analyse_cross_domain_correlations([])
        assert result["total_indicators"] == 0
        assert result["correlations"] == []
        assert result["lagging_domains"] == []

    def test_domains_analysed_field(self, analysis_service):
        data = [
            {"domain": "social", "indicator_name": "a"},
            {"domain": "economic", "indicator_name": "b"},
        ]
        result = analysis_service.analyse_cross_domain_correlations(data)
        assert set(result["domains_analysed"]) == {"social", "economic"}


# ---------------------------------------------------------------------------
# LLM enrichment
# ---------------------------------------------------------------------------


class TestLLMEnrichment:
    def test_llm_enrichment_with_content_safety_pass(self, mock_llm, mock_content_safety):
        svc = IndicatorAnalysisService(
            llm_client=mock_llm,
            content_safety=mock_content_safety,
        )
        data = [
            {"domain": "social", "indicator_name": "h", "trend": "negative"},
            {"domain": "economic", "indicator_name": "e", "trend": "negative"},
        ]
        result = svc.analyse_cross_domain_correlations(data)
        assert "ai_summary" in result
        assert result["content_safety_result"] == "passed"
        mock_llm.generate_response.assert_called_once()
        mock_content_safety.validate.assert_called_once()

    def test_llm_enrichment_content_safety_fail(self, mock_llm):
        cs = MagicMock()
        fail_result = MagicMock()
        fail_result.passed = False
        cs.validate.return_value = fail_result

        svc = IndicatorAnalysisService(llm_client=mock_llm, content_safety=cs)
        data = [
            {"domain": "social", "indicator_name": "h", "trend": "negative"},
            {"domain": "economic", "indicator_name": "e", "trend": "negative"},
        ]
        result = svc.analyse_cross_domain_correlations(data)
        assert "ai_summary" not in result
        assert result["content_safety_result"] == "failed"

    def test_llm_unavailable_graceful_fallback(self):
        llm = MagicMock()
        llm.generate_response.side_effect = RuntimeError("LLM down")
        svc = IndicatorAnalysisService(llm_client=llm)
        data = [
            {"domain": "social", "indicator_name": "h", "trend": "negative"},
            {"domain": "economic", "indicator_name": "e", "trend": "negative"},
        ]
        result = svc.analyse_cross_domain_correlations(data)
        assert "ai_summary" not in result
        assert result["content_safety_result"] == "llm_unavailable"

    def test_no_llm_enrichment_when_no_correlations(self, mock_llm, mock_content_safety):
        svc = IndicatorAnalysisService(
            llm_client=mock_llm,
            content_safety=mock_content_safety,
        )
        data = [
            {"domain": "social", "indicator_name": "h", "trend": "positive"},
        ]
        result = svc.analyse_cross_domain_correlations(data)
        assert "ai_summary" not in result
        mock_llm.generate_response.assert_not_called()

    def test_llm_enrichment_without_content_safety(self, mock_llm):
        svc = IndicatorAnalysisService(llm_client=mock_llm)
        data = [
            {"domain": "social", "indicator_name": "h", "trend": "negative"},
            {"domain": "economic", "indicator_name": "e", "trend": "negative"},
        ]
        result = svc.analyse_cross_domain_correlations(data)
        assert "ai_summary" in result
        assert result["content_safety_result"] == "not_validated"


# ---------------------------------------------------------------------------
# Activity recommendations
# ---------------------------------------------------------------------------


class TestRecommendActivities:
    def test_recommend_with_catalogue(self, mock_catalogue):
        svc = IndicatorAnalysisService(catalogue_service=mock_catalogue)
        recs = svc.recommend_activities(["ind-1"])
        assert len(recs) == 1
        assert recs[0]["for_indicator"] == "ind-1"
        mock_catalogue.suggest_activities.assert_called_once_with(["ind-1"])

    def test_recommend_without_catalogue(self, analysis_service):
        recs = analysis_service.recommend_activities(["ind-1"])
        assert recs == []

    def test_recommend_empty_ids(self, mock_catalogue):
        mock_catalogue.suggest_activities.return_value = []
        svc = IndicatorAnalysisService(catalogue_service=mock_catalogue)
        recs = svc.recommend_activities([])
        assert recs == []


# ---------------------------------------------------------------------------
# Community summary
# ---------------------------------------------------------------------------


class TestCommunitySummary:
    def test_basic_community_summary(self, analysis_service):
        data = [
            {"domain": "social", "indicator_name": "h", "trend": "positive"},
            {"domain": "social", "indicator_name": "j", "trend": "negative"},
            {"domain": "economic", "indicator_name": "e", "trend": "positive"},
        ]
        result = analysis_service.generate_community_summary(data)
        assert "summary" in result
        assert "Economic recovery: 1/1 indicators progressing" in result["summary"]
        assert "Social recovery: 1/2 indicators progressing" in result["summary"]
        assert set(result["domains_covered"]) == {"social", "economic"}
        assert "generated_at" in result

    def test_community_summary_with_domain_filter(self, analysis_service):
        data = [
            {"domain": "social", "indicator_name": "h", "trend": "positive"},
            {"domain": "economic", "indicator_name": "e", "trend": "positive"},
        ]
        result = analysis_service.generate_community_summary(data, domain_filter="social")
        assert "Social" in result["summary"]
        assert "Economic" not in result["summary"]
        assert result["domains_covered"] == ["social"]

    def test_community_summary_empty_data(self, analysis_service):
        result = analysis_service.generate_community_summary([])
        assert result["summary"] == "No indicator data available"
        assert result["domains_covered"] == []

    def test_community_summary_all_negative(self, analysis_service):
        data = [
            {"domain": "social", "indicator_name": "a", "trend": "negative"},
            {"domain": "social", "indicator_name": "b", "trend": "negative"},
        ]
        result = analysis_service.generate_community_summary(data)
        assert "0/2 indicators progressing" in result["summary"]

    def test_community_summary_content_safety_field(self, analysis_service):
        result = analysis_service.generate_community_summary([])
        assert result["content_safety_result"] is None
