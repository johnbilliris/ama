"""Public Information render service (T-AMD-14, FR-039)."""

from __future__ import annotations

from typing import Literal

MANDATORY_AUSLAN_SCENARIOS = {"cyclone", "bushfire", "flood"}
DEFERRED_AUSLAN_SCENARIOS = {"urban-fire", "mass-casualty", "hazmat", "marine-sar"}

AuslanStatus = Literal["available", "auslan-asset-missing"]

LANGUAGE_CHANNELS = [
    "en-plain-grade-8",
    "zh-Hant",
    "ar",
    "vi",
    "yue",
    "pa",
    "auslan",
    "kriol",
]


def render_public_information(scenario_id: str) -> dict:
    """Render public information channels for a scenario (T-AMD-14, FR-039)."""
    auslan_status: AuslanStatus = "available" if scenario_id in MANDATORY_AUSLAN_SCENARIOS else "auslan-asset-missing"
    channels = []
    for lang in LANGUAGE_CHANNELS:
        channels.append(
            {
                "language_code": lang,
                "content": f"[{lang}] Public information for scenario {scenario_id}",
                "auslan_asset_status": auslan_status if lang == "auslan" else None,
            }
        )
    return {
        "scenario_id": scenario_id,
        "channels": channels,
        "auslan_asset_status": auslan_status,
        "language_fallback_used": None,
    }
