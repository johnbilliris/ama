from app.services.degraded_mode_service import DegradedModeState


def apply_recommendation_guardrails(
    recommendation: dict[str, object], degraded_mode: DegradedModeState
) -> dict[str, object]:
    updated = dict(recommendation)
    if degraded_mode.requires_manual_review:
        updated["requiresManualReview"] = True
        updated["status"] = "under_review"
    return updated
