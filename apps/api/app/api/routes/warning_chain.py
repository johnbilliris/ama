"""Warning chain, CAP XML, and compliance validation routes.

Endpoints for traversing AWS warning supersession chains, rendering
CAP 1.2 XML, and validating warning compliance.

FRs: FR-001–005 | Tasks: T023, T024, T025
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.state_store import ALERTS
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from apps.agents.common.warning_compliance import validate_warning_compliance
from apps.agents.communication.edxl_serialiser import serialize_to_edxl
from apps.agents.communication.warning_builder import (
    traverse_chain,
)

router = APIRouter(prefix="/alerts", tags=["warning-chain"])


# ---- GET /api/alerts/{alert_id}/chain ----


@router.get("/{alert_id}/chain")
async def get_warning_chain(alert_id: str) -> list[dict[str, object]]:
    """Traverse the supersession chain for a warning alert, oldest-first."""
    if alert_id not in ALERTS:
        raise HTTPException(status_code=404, detail="Alert not found")
    chain = traverse_chain(alert_id, ALERTS)
    return [
        {
            "alert_id": a.alert_id,
            "warning_tier": a.warning_tier,
            "colour_code": a.colour_code,
            "is_all_clear": a.is_all_clear,
            "superseded_warning_id": a.superseded_warning_id,
            "position": idx + 1,
        }
        for idx, a in enumerate(chain)
    ]


# ---- GET /api/alerts/{alert_id}/cap ----

_CAP_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>{identifier}</identifier>
  <sender>aidr-hub</sender>
  <sent>{sent}</sent>
  <status>{status}</status>
  <msgType>{msg_type}</msgType>
  <scope>Public</scope>
  <info>
    <category>Met</category>
    <event>{event}</event>
    <urgency>{urgency}</urgency>
    <severity>{severity}</severity>
    <certainty>Observed</certainty>
    <headline>{headline}</headline>
    <description>{description}</description>
    <instruction>{instruction}</instruction>{area_block}
  </info>
</alert>"""

_CAP_AREA = """
    <area>
      <areaDesc>{area_desc}</areaDesc>
    </area>"""


def _tier_to_severity(tier: str | None, is_all_clear: bool) -> str:
    if is_all_clear:
        return "Minor"
    mapping = {
        "advice": "Minor",
        "watch_and_act": "Moderate",
        "emergency_warning": "Extreme",
    }
    return mapping.get(tier or "", "Unknown")


def _tier_to_urgency(tier: str | None, is_all_clear: bool) -> str:
    if is_all_clear:
        return "Past"
    mapping = {
        "advice": "Future",
        "watch_and_act": "Expected",
        "emergency_warning": "Immediate",
    }
    return mapping.get(tier or "", "Unknown")


@router.get(
    "/{alert_id}/cap",
    response_class=Response,
    responses={200: {"content": {"application/xml": {}}}},
)
async def get_cap_xml(alert_id: str) -> Response:
    """Render a PublicAlert as minimal CAP 1.2 XML."""
    if alert_id not in ALERTS:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert = ALERTS[alert_id]

    headline = alert.content_blocks.get("headline", alert.alert_id)
    description = alert.content_blocks.get("areas", "")
    event = alert.hazard_icon.replace("_", " ").title() if alert.hazard_icon else "Hazard"
    msg_type = "Cancel" if alert.is_all_clear else "Alert"
    status = "Actual" if alert.status == "published" else "Draft"

    areas = alert.audience_segments or []
    area_block = "".join(_CAP_AREA.format(area_desc=a) for a in areas)

    xml = _CAP_TEMPLATE.format(
        identifier=alert.alert_id,
        sent=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        status=status,
        msg_type=msg_type,
        event=event,
        urgency=_tier_to_urgency(alert.warning_tier, alert.is_all_clear),
        severity=_tier_to_severity(alert.warning_tier, alert.is_all_clear),
        headline=headline,
        description=description,
        instruction=alert.action_statement or "",
        area_block=area_block,
    )
    return Response(content=xml, media_type="application/xml")


# ---- POST /api/alerts/{alert_id}/validate-compliance ----


@router.post("/{alert_id}/validate-compliance")
async def validate_compliance(alert_id: str) -> dict[str, object]:
    """Run AWS warning compliance validation on an alert."""
    if alert_id not in ALERTS:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert = ALERTS[alert_id]
    result = validate_warning_compliance(alert)
    return {
        "alert_id": alert_id,
        "is_compliant": result.is_compliant,
        "tier_valid": result.tier_valid,
        "colour_valid": result.colour_valid,
        "icon_valid": result.icon_valid,
        "action_statement_valid": result.action_statement_valid,
        "principles_checklist": result.principles_checklist,
        "principle_compliance_rate": result.principle_compliance_rate,
        "errors": result.errors,
    }


# ---- GET /api/alerts/{alert_id}/edxl ----


@router.get(
    "/{alert_id}/edxl",
    response_class=Response,
    responses={200: {"content": {"application/xml": {}}}},
)
async def get_edxl_xml(alert_id: str) -> Response:
    """Render a PublicAlert as EDXL-DE XML."""
    if alert_id not in ALERTS:
        raise HTTPException(status_code=404, detail="Alert not found")
    xml = serialize_to_edxl(ALERTS[alert_id])
    return Response(content=xml, media_type="application/xml")
