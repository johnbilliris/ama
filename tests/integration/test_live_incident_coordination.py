from app.services.degraded_mode_service import DegradedModeService
from app.services.provenance_scoring_service import ProvenanceScoringService
from app.services.recommendation_guardrails import apply_recommendation_guardrails

from packages.domain.src.domain.models.recommendation import Recommendation


def test_authoritative_signal_scoring_outranks_social_signal() -> None:
    scorer = ProvenanceScoringService()

    authoritative_score = scorer.score("authoritative", freshness_score=0.9, confidence_score=0.95)
    social_score = scorer.score("social", freshness_score=0.9, confidence_score=0.55)

    assert authoritative_score > social_score


def test_degraded_mode_keeps_public_alert_recommendation_under_review() -> None:
    degraded_mode = DegradedModeService().evaluate({"community": "untrusted"})
    recommendation = Recommendation(
        recommendation_id="rec-002",
        incident_id="incident-001",
        type="public_alert",
        summary="Prepare to evacuate",
        explanation="Observed flood rise exceeds warning threshold.",
        supporting_signal_ids=["sig-001"],
        required_approval_level="incident_commander",
    )

    guarded = apply_recommendation_guardrails(recommendation.model_dump(mode="json"), degraded_mode)

    assert guarded["status"] == "under_review"
    assert guarded["requiresManualReview"] is True
