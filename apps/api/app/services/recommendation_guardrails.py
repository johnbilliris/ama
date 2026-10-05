from app.services.degraded_mode_service import DegradedModeState


def apply_recommendation_guardrails(
    recommendation: dict[str, object],
    degraded_mode: DegradedModeState,
    signal_source_by_id: dict[str, str] | None = None,
) -> dict[str, object]:
    updated = dict(recommendation)
    raw_supporting_ids = updated.get("supporting_signal_ids", [])
    if not isinstance(raw_supporting_ids, list):
        raise ValueError("Recommendation supporting_signal_ids must be a list")
    supporting_ids = [str(signal_id) for signal_id in raw_supporting_ids]
    degraded_sources = set(degraded_mode.degraded_sources)
    supporting_degraded_sources: list[str] = []
    if signal_source_by_id is not None:
        supporting_degraded_sources = sorted(
            {
                source_id
                for signal_id in supporting_ids
                if (source_id := signal_source_by_id.get(signal_id)) is not None and source_id in degraded_sources
            }
        )

    if degraded_mode.requires_manual_review:
        updated["requiresManualReview"] = True
        updated["status"] = "under_review"
        if supporting_degraded_sources:
            updated["degradedSupportingSources"] = supporting_degraded_sources

    if supporting_degraded_sources:
        degraded_lookup = {entry.get("sourceId", ""): entry for entry in degraded_mode.degraded_source_details}
        severe_states = {"offline", "unavailable", "open"}
        if any(
            degraded_lookup.get(source_id, {}).get("status") in severe_states
            for source_id in supporting_degraded_sources
        ):
            updated["status"] = "suppressed"
            updated["suppressed"] = True
        else:
            raw_rank_penalty = updated.get("rankPenalty", 0)
            if not isinstance(raw_rank_penalty, (int, float, str)):
                raise ValueError("Recommendation rankPenalty must be numeric")
            updated["rankPenalty"] = int(raw_rank_penalty) + 100

    return updated
