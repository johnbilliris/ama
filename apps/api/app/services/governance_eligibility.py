from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from packages.domain.src.domain.models.data_source import DataSource


@dataclass(frozen=True)
class EligibilityDecision:
    allowed: bool
    reason: str


def is_source_eligible(
    source: DataSource | None,
    *,
    now: datetime,
    require_governed_chain: bool = False,
    has_active_chain: bool | None = None,
) -> EligibilityDecision:
    if source is None:
        return EligibilityDecision(allowed=False, reason="unknown_source")

    if source.status == "deactivated":
        return EligibilityDecision(allowed=False, reason="source_deactivated")

    if source.compliance_status == "non_compliant":
        return EligibilityDecision(allowed=False, reason="source_non_compliant")

    if source.compliance_status == "compliance_lapsed":
        if source.grace_period_end is None:
            return EligibilityDecision(allowed=False, reason="grace_period_missing_end")
        if source.grace_period_end <= now:
            return EligibilityDecision(allowed=False, reason="grace_period_expired")

    if require_governed_chain:
        if source.governance_status not in {"assigned", "fully_governed"}:
            return EligibilityDecision(allowed=False, reason="source_unassigned")
        if has_active_chain is False:
            return EligibilityDecision(allowed=False, reason="handoff_chain_unavailable")

    return EligibilityDecision(allowed=True, reason="eligible")
