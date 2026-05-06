"""Lightweight `/agents/*` bridge endpoints.

Spec-035 FR-004 / FR-002 / FR-005 wire several workspace panels to the MAF
agent runtimes (`apps/agents/risk_assessment/`, `apps/agents/communication/`,
`apps/agents/planning/`) which are deployed as internal-only Container Apps.
The browser cannot reach those through the public API proxy. This module
provides deterministic, schema-stable bridges so each panel always renders a
defensible result even when the agent runtimes are offline or out of reach.

Currently implemented bridges:
- ``GET  /agents/risk-assessment/recommend?scenario_id=...``  (FR-004)
- ``POST /agents/communication/draft-aws``                    (FR-002)
- ``GET  /agents/planning/draft-iap?scenario_id=...``         (FR-005)
"""

from __future__ import annotations

from typing import Any, Final

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/agents", tags=["agents"])

_LIKELIHOOD: Final[tuple[str, ...]] = (
    "Rare",
    "Unlikely",
    "Possible",
    "Likely",
    "Almost Certain",
)
_CONSEQUENCE: Final[tuple[str, ...]] = (
    "Insignificant",
    "Minor",
    "Moderate",
    "Major",
    "Catastrophic",
)


def _classify(scenario_id: str) -> tuple[str, str, str, list[str]]:
    """Map a scenario id to (likelihood, consequence, rationale, controls).

    Deterministic, keyword-driven so the UI presents a defensible matrix cell
    without round-tripping the agent runtime. Unknown scenarios fall back to
    a moderate, non-alarming default (`Possible` / `Moderate`).
    """
    sid = scenario_id.lower()

    if any(k in sid for k in ("bushfire", "wildfire", "fire-")):
        return (
            "Likely",
            "Major",
            "Active fire weather and exposed assets warrant pre-positioned suppression and evacuation readiness.",
            [
                "Pre-position aerial and ground suppression assets",
                "Issue stay-and-defend / leave-early advisories",
                "Activate evacuation centres and traffic management",
            ],
        )
    if any(k in sid for k in ("flood", "riverine", "storm-surge")):
        return (
            "Likely",
            "Major",
            "Catchment saturation and forecast rainfall elevate downstream inundation risk.",
            [
                "Issue community flood warnings on all channels",
                "Stage swift-water rescue assets at vulnerable LGAs",
                "Pre-emptive evacuation of low-lying caravan parks",
            ],
        )
    if any(k in sid for k in ("cyclone", "tropical-low")):
        return (
            "Possible",
            "Catastrophic",
            "Tropical system intensity and forecast track place coastal communities in the destructive wind zone.",
            [
                "Activate cyclone shelters and accessible transport",
                "Issue prepare-to-evacuate orders for the red zone",
                "Stand up power / telco resilience taskforce",
            ],
        )
    if any(k in sid for k in ("cyber", "ransomware", "ddos")):
        return (
            "Possible",
            "Major",
            "Indicators of compromise on regulated platform data require precautionary isolation and integrity verification.",
            [
                "Isolate affected segments and rotate credentials",
                "Engage ASD / ACSC under the Cyber Incident Management Arrangements",
                "Preserve forensic evidence for the audit chain",
            ],
        )
    if any(k in sid for k in ("mass-casualty", "mass-evac", "evac")):
        return (
            "Possible",
            "Major",
            "Mass-evacuation pathways require staged movement and welfare capacity to avoid bottlenecks.",
            [
                "Activate evacuation centres with welfare and medical capacity",
                "Coordinate route management with police and roads agencies",
                "Surge transport for assisted-evacuation cohorts",
            ],
        )
    if any(k in sid for k in ("sa-pol", "police", "control-centre", "control_centre")):
        return (
            "Possible",
            "Moderate",
            "Multi-LGA coordination demands clear command authority, role-separation, and span-of-control discipline.",
            [
                "Confirm role-separation on regulated routes",
                "Hold span-of-control under 7 direct reports per supervisor",
                "Audit recommendation acceptance and IC overrides",
            ],
        )

    return (
        "Possible",
        "Moderate",
        "No specific hazard signature matched; defaulting to a moderate posture pending agent telemetry.",
        [
            "Maintain situational awareness",
            "Pre-brief duty officers on escalation pathways",
            "Verify audit chain readiness for any state-changing actions",
        ],
    )


@router.get("/risk-assessment/recommend")
async def risk_assessment_recommend(
    scenario_id: str = Query(..., min_length=1, max_length=128),
) -> dict[str, object]:
    likelihood, consequence, rationale, controls = _classify(scenario_id)
    return {
        "scenario_id": scenario_id,
        "likelihood": likelihood,
        "consequence": consequence,
        "rationale": rationale,
        "recommended_controls": controls,
    }


# ---------------------------------------------------------------------------
# Communication agent bridge (FR-002).
# ---------------------------------------------------------------------------

_AWS_LEVELS: Final[frozenset[str]] = frozenset(
    {"Advice", "Watch and Act", "Emergency Warning"}
)

# Languages requiring community-reviewer signature before publish (NN-4 v1).
# Mirrors apps/web/src/lib/i18n/language-packs.ts so the UI's language picker
# and this bridge agree on which translations need a reviewer.
_REVIEWER_REQUIRED: Final[frozenset[str]] = frozenset(
    {
        "kimberley_pilbara",
        "palawa",
        "yolngu_matha",
        "pitjantjatjara",
        "warlpiri",
    }
)


class DraftAwsRequest(BaseModel):
    level: str = Field(..., min_length=1, max_length=64)
    hazard: str = Field(default="", max_length=256)
    location: str = Field(default="", max_length=256)
    action: str = Field(default="", max_length=256)
    languages: list[str] = Field(default_factory=lambda: ["en"])


def _english_draft(level: str, hazard: str, location: str, action: str) -> str:
    parts = [f"{level.upper()}:"]
    if hazard:
        parts.append(f"{hazard} hazard")
    if location:
        parts.append(f"affecting {location}")
    if action:
        parts.append(f"— recommended action: {action}.")
    else:
        parts.append("— monitor official channels for updates.")
    return " ".join(parts)


def _community_draft(language: str, english: str) -> str:
    """Render a per-language carrier line.

    Real translation arrives out-of-band via the language-pack pipeline; the
    bridge emits the English carrier so the composer panel can preview the
    layout, with reviewer_required=true gating publish.
    """
    if language == "en":
        return english
    if language == "zh-Hans":
        return f"[\u7b80\u4f53\u4e2d\u6587 / Simplified Chinese] {english}"
    return f"[{language} placeholder pending community review] {english}"


@router.post("/communication/draft-aws")
async def communication_draft_aws(payload: DraftAwsRequest) -> dict[str, Any]:
    if payload.level not in _AWS_LEVELS:
        raise HTTPException(
            status_code=422,
            detail=f"level must be one of {sorted(_AWS_LEVELS)}",
        )
    languages = payload.languages or ["en"]
    english = _english_draft(
        payload.level, payload.hazard, payload.location, payload.action
    )
    variants = [
        {
            "language": lang,
            "text": _community_draft(lang, english),
            "reviewer_required": lang in _REVIEWER_REQUIRED,
        }
        for lang in languages
    ]
    return {"variants": variants}


# ---------------------------------------------------------------------------
# Planning agent bridge (FR-005).
# ---------------------------------------------------------------------------


def _planning_profile(scenario_id: str) -> tuple[int, float, list[str]]:
    """Map scenario id → (horizon_hours, confidence, forecast bullets)."""
    sid = scenario_id.lower()
    if any(k in sid for k in ("bushfire", "wildfire", "fire-")):
        return (
            24,
            0.78,
            [
                "Fire weather index rises into the SEVERE band by 1400 local",
                "Northerly winds 35-50 km/h with gusts to 70 km/h",
                "Evacuation centres at staging arenas reach 60% of capacity",
            ],
        )
    if any(k in sid for k in ("flood", "riverine", "storm-surge")):
        return (
            48,
            0.72,
            [
                "River level forecast to crest above the moderate-flood threshold",
                "Catchment saturation places downstream LGAs on watch-and-act",
                "Swift-water rescue teams pre-deploy to vulnerable caravan parks",
            ],
        )
    if any(k in sid for k in ("cyclone", "tropical-low")):
        return (
            72,
            0.66,
            [
                "Tropical system forecast track tightens within the destructive zone",
                "Coastal communities placed on prepare-to-evacuate by H-24",
                "Power and telco resilience taskforce activates redundant routes",
            ],
        )
    if any(k in sid for k in ("cyber", "ransomware", "ddos")):
        return (
            12,
            0.7,
            [
                "Indicators of compromise on regulated platform require isolation",
                "Forensic preservation engaged within the 4h evidence-retention window",
                "Public messaging held until ASD/ACSC clearance per CIMA",
            ],
        )
    if any(k in sid for k in ("mass-evac", "mass-casualty", "evac")):
        return (
            18,
            0.74,
            [
                "Mass-evacuation route capacity peaks two hours after activation",
                "Welfare and medical assets pre-position to staging centres",
                "Assisted-evacuation cohorts coordinated with transport agencies",
            ],
        )
    return (
        24,
        0.6,
        [
            "No specific hazard signature matched; defaulting to a 24h horizon",
            "Maintain situational awareness across all AIIMS functions",
            "Verify audit-chain readiness for any state-changing actions",
        ],
    )


def _iap_markdown(scenario_id: str, horizon: int, bullets: list[str]) -> str:
    bullet_lines = "\n".join(f"- {b}" for b in bullets)
    return (
        f"# Incident Action Plan — {scenario_id}\n\n"
        f"**Operational period:** next {horizon} hours\n\n"
        "## Situation\n"
        f"{bullet_lines}\n\n"
        "## Objectives\n"
        "- Preserve life and safety as the absolute priority\n"
        "- Maintain command-and-control discipline within span-of-control limits\n"
        "- Ensure all decisions emit auditable rationale + source references\n\n"
        "## Resources\n"
        "- Confirm AIIMS section staffing for the operational period\n"
        "- Pre-position community-language broadcast capability\n\n"
        "## Communications\n"
        "- AWS Advice → Watch-and-Act escalation rules per FR-002\n"
        "- IC approval required for any state-changing public bulletin\n"
    )


@router.get("/planning/draft-iap")
async def planning_draft_iap(
    scenario_id: str = Query(..., min_length=1, max_length=128),
) -> dict[str, Any]:
    horizon, confidence, bullets = _planning_profile(scenario_id)
    return {
        "iap_draft_markdown": _iap_markdown(scenario_id, horizon, bullets),
        "forecast": {
            "horizon_hours": horizon,
            "confidence": confidence,
            "bullets": bullets,
        },
    }


__all__ = ["router"]
