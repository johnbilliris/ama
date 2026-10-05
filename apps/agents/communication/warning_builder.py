"""AWS three-tier warning builder.

Constructs PublicAlert instances with correct tier-colour mapping,
hazard icons, action statements, supersession chains, de-escalation,
all-clear notifications, and tier-skip for sudden-onset hazards.

FRs: FR-001–005, FR-048 | SCs: SC-001–005
"""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from packages.domain.src.domain.models.public_alert import (
    WARNING_PRINCIPLE_KEYS,
    HazardIcon,
    PublicAlert,
    WarningTier,
)

INCIDENT_TO_HAZARD_ICON: dict[str, HazardIcon] = {
    "cyclone": "cyclone",
    "bushfire": "fire",
    "flood": "flood",
    "extreme_heat": "heat",
    "storm": "storm",
}

ACTION_TEMPLATES: dict[str, str] = {
    "advice": "Stay informed. Monitor conditions and follow official advice.",
    "watch_and_act": ("Be ready to act. Conditions are changing and you need to take action now."),
    "emergency_warning": ("Take action now. Your life is at risk. Do not wait."),
}

TIER_ORDER: list[WarningTier] = ["advice", "watch_and_act", "emergency_warning"]


def _resolve_hazard_icon(
    incident_type: str,
    override: HazardIcon | None = None,
) -> HazardIcon:
    if override is not None:
        return override
    return INCIDENT_TO_HAZARD_ICON.get(incident_type, "other")


def _resolve_action_statement(
    tier: WarningTier,
    override: str | None = None,
) -> str:
    if override:
        return override
    return ACTION_TEMPLATES[tier]


def _default_principles_checklist(value: bool = True) -> dict[str, bool]:
    return {k: value for k in WARNING_PRINCIPLE_KEYS}


def build_aws_warning(
    incident_id: str,
    warning_tier: WarningTier,
    incident_type: str,
    *,
    affected_areas: list[str] | None = None,
    audience_segments: list[str] | None = None,
    action_statement_override: str | None = None,
    hazard_icon_override: HazardIcon | None = None,
    supersedes_alert_id: str | None = None,
    tier_skip_justification: str | None = None,
    content_blocks: dict[str, str] | None = None,
    approval_mode: Literal["human_approved", "autonomous", "escalated"] = "human_approved",
    generation_method: Literal["llm", "template", "template_fallback", "safety_fallback"] = "template",
) -> PublicAlert:
    """Build a PublicAlert conforming to the AWS three-tier warning model."""
    if tier_skip_justification:
        _validate_tier_skip(warning_tier, tier_skip_justification)

    alert_id = f"alert-{uuid4().hex[:12]}"
    hazard_icon = _resolve_hazard_icon(incident_type, hazard_icon_override)
    action_statement = _resolve_action_statement(warning_tier, action_statement_override)

    blocks = content_blocks or {
        "headline": f"{warning_tier.replace('_', ' ').title()} — {incident_type.replace('_', ' ').title()}",
        "areas": ", ".join(affected_areas) if affected_areas else "See advisory",
    }

    alert = PublicAlert(
        alert_id=alert_id,
        incident_id=incident_id,
        warning_tier=warning_tier,
        hazard_icon=hazard_icon,
        action_statement=action_statement,
        superseded_warning_id=supersedes_alert_id,
        tier_skip_justification=tier_skip_justification,
        content_blocks=blocks,
        audience_segments=audience_segments or (affected_areas or []),
        approval_mode=approval_mode,
        generation_method=generation_method,
        warning_principles_checklist=_default_principles_checklist(),
        accessibility_attributes=["plain_language"],
        languages=["en"],
    )
    return alert


def _validate_tier_skip(tier: WarningTier, justification: str) -> None:
    """Tier-skip is only valid when jumping straight to emergency_warning."""
    if tier != "emergency_warning":
        msg = "Tier-skip justification is only valid for emergency_warning tier"
        raise ValueError(msg)
    if len(justification.strip()) < 10:
        msg = "Tier-skip justification must provide meaningful reasoning (≥10 chars)"
        raise ValueError(msg)


def build_deescalation_warning(
    incident_id: str,
    new_tier: WarningTier,
    incident_type: str,
    supersedes_alert_id: str,
    *,
    affected_areas: list[str] | None = None,
    action_statement_override: str | None = None,
) -> PublicAlert:
    """Create a lower-tier warning that supersedes a higher-tier one."""
    return build_aws_warning(
        incident_id,
        new_tier,
        incident_type,
        affected_areas=affected_areas,
        action_statement_override=action_statement_override,
        supersedes_alert_id=supersedes_alert_id,
    )


def build_all_clear(
    incident_id: str,
    incident_type: str,
    supersedes_alert_id: str,
    *,
    affected_areas: list[str] | None = None,
) -> PublicAlert:
    """Generate an all-clear notification that supersedes the final warning."""
    alert_id = f"alert-{uuid4().hex[:12]}"
    return PublicAlert(
        alert_id=alert_id,
        incident_id=incident_id,
        is_all_clear=True,
        superseded_warning_id=supersedes_alert_id,
        action_statement="All clear. The threat has passed. Resume normal activities.",
        content_blocks={
            "headline": f"All Clear — {incident_type.replace('_', ' ').title()}",
            "areas": ", ".join(affected_areas) if affected_areas else "See advisory",
        },
        audience_segments=affected_areas or [],
        approval_mode="human_approved",
        generation_method="template",
        accessibility_attributes=["plain_language"],
        languages=["en"],
    )


def get_chain_position(
    alert: PublicAlert,
    alerts_store: dict[str, PublicAlert],
) -> int:
    """Return 1-based position of this alert in its supersession chain.

    Position 1 = first warning in the chain (no superseded_warning_id).
    """
    position = 1
    current = alert
    while current.superseded_warning_id:
        previous = alerts_store.get(current.superseded_warning_id)
        if previous is None:
            break
        position += 1
        current = previous
    return position


def traverse_chain(
    alert_id: str,
    alerts_store: dict[str, PublicAlert],
) -> list[PublicAlert]:
    """Walk the supersession chain backwards from alert_id, return oldest-first."""
    chain: list[PublicAlert] = []
    current_id: str | None = alert_id
    visited: set[str] = set()
    while current_id and current_id not in visited:
        visited.add(current_id)
        alert = alerts_store.get(current_id)
        if alert is None:
            break
        chain.append(alert)
        current_id = alert.superseded_warning_id
    chain.reverse()
    return chain
