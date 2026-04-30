"""Edge case handlers for emergency planning and M&E framework.

Handles: overlapping programs, indicator unavailability, outcome regression,
conflicting standards, and plan hierarchy conflicts.

Spec: Edge cases section
"""

from datetime import UTC, datetime


def handle_overlapping_programs(program_a: dict, program_b: dict) -> dict:
    """Support linking programs to shared indicator data."""
    shared_indicators = set(i.get("indicator_id") for i in program_a.get("standards_of_success", [])) & set(
        i.get("indicator_id") for i in program_b.get("standards_of_success", [])
    )
    return {
        "overlap_detected": len(shared_indicators) > 0,
        "shared_indicator_count": len(shared_indicators),
        "shared_indicator_ids": list(shared_indicators),
        "recommendation": "Coordinate data collection to avoid duplication" if shared_indicators else "No overlap",
    }


def handle_indicator_unavailable(indicator: dict, staleness_days: int = 7) -> dict:
    """Display last-known value with staleness indicator."""
    last_updated = indicator.get("last_updated_at")
    is_stale = False
    if last_updated:
        from datetime import datetime as dt

        try:
            updated = dt.fromisoformat(last_updated) if isinstance(last_updated, str) else last_updated
            days_since = (datetime.now(UTC) - updated).days
            is_stale = days_since > staleness_days
        except (ValueError, TypeError):
            is_stale = True
    return {
        "indicator_id": indicator.get("indicator_id", ""),
        "last_known_value": indicator.get("value"),
        "is_stale": is_stale,
        "staleness_warning": f"Data older than {staleness_days} days" if is_stale else None,
        "data_gap": indicator.get("value") is None,
    }


def handle_outcome_regression(indicator: dict, *, closure_threshold: float = 0.9) -> dict:
    """Flag regression after program closure and assess sustainability."""
    value = indicator.get("value")
    target = indicator.get("target_value")
    if value is None or target is None:
        return {"regression_detected": False, "reason": "Insufficient data"}

    ratio = value / target if target != 0 else 0
    regression = ratio < closure_threshold
    return {
        "regression_detected": regression,
        "current_ratio": round(ratio, 3),
        "threshold": closure_threshold,
        "recommendation": "Consider program reactivation" if regression else "Sustainability maintained",
    }


def handle_conflicting_standards(standards: list[dict]) -> dict:
    """Support multiple standards per indicator with stakeholder labels."""
    grouped: dict[str, list] = {}
    for s in standards:
        iid = s.get("indicator_id", "")
        grouped.setdefault(iid, []).append(s)

    conflicts = {}
    for iid, group in grouped.items():
        if len(group) > 1:
            conflicts[iid] = {
                "indicator_id": iid,
                "standard_count": len(group),
                "stakeholder_labels": [s.get("stakeholder_label", "unknown") for s in group],
                "values": [s.get("threshold_value") for s in group],
            }
    return {
        "has_conflicts": len(conflicts) > 0,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
    }


def handle_plan_hierarchy_conflict(plans: list[dict]) -> dict:
    """Flag inconsistencies between plans at different hierarchy levels."""
    issues = []
    plans_by_level: dict[str, list] = {}
    for p in plans:
        level = p.get("hierarchy_level", "unknown")
        plans_by_level.setdefault(level, []).append(p)

    # Check for local plans without state parent
    for local_plan in plans_by_level.get("local", []):
        if local_plan.get("parent_plan_id") is None:
            issues.append(f"Local plan '{local_plan.get('title', '')}' has no parent state/regional plan")

    return {
        "hierarchy_levels_present": list(plans_by_level.keys()),
        "plans_per_level": {k: len(v) for k, v in plans_by_level.items()},
        "issues": issues,
        "has_conflicts": len(issues) > 0,
    }
