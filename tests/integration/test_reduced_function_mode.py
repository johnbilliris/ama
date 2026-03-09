from app.services.degraded_mode_service import DegradedModeService
from app.services.recommendation_guardrails import apply_recommendation_guardrails


def test_degraded_inputs_force_manual_review() -> None:
    degraded_mode = DegradedModeService().evaluate(
        {
            "bom": "available",
            "community-feed": "untrusted",
        }
    )

    guarded = apply_recommendation_guardrails({"status": "proposed"}, degraded_mode)

    assert degraded_mode.requires_manual_review is True
    assert guarded["status"] == "under_review"
    assert guarded["requiresManualReview"] is True
