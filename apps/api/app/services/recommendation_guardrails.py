from app.services.degraded_mode_service import DegradedModeState


def apply_recommendation_guardrails(
    recommendation: dict[str, object],
    degraded_mode: DegradedModeState,
    signal_source_by_id: dict[str, str] | None = None,
) -> dict[str, object]:
    updated = dict(recommendation)
    supporting_ids = [str(signal_id) for signal_id in updated.get("supporting_signal_ids", [])]
    degraded_sources = set(degraded_mode.degraded_sources)
    supporting_degraded_sources = sorted(
        {
            signal_source_by_id.get(signal_id)
            for signal_id in supporting_ids
            if signal_source_by_id and signal_source_by_id.get(signal_id) in degraded_sources
        }
    )
    supporting_degraded_sources = [source_id for source_id in supporting_degraded_sources if source_id]

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
            updated["rankPenalty"] = int(updated.get("rankPenalty", 0)) + 100

    return updated
