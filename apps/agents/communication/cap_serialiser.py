from __future__ import annotations

from datetime import UTC, datetime
from xml.etree.ElementTree import Element, ParseError, SubElement, fromstring, register_namespace, tostring

from fastapi import HTTPException

from packages.domain.src.domain.models.public_alert import PublicAlert

CAP_NAMESPACE = "urn:oasis:names:tc:emergency:cap:1.2"
_CATEGORY_BY_HAZARD: dict[str, str] = {
    "fire": "Fire",
    "flood": "Met",
    "storm": "Met",
    "cyclone": "Met",
    "heat": "Health",
}
_CERTAINTY_BY_TIER: dict[str, str] = {
    "advice": "Possible",
    "watch_and_act": "Likely",
    "emergency_warning": "Observed",
}

register_namespace("", CAP_NAMESPACE)


def _iso_utc(value: datetime) -> str:
    normalized = value.astimezone(UTC).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


def _sent_at(alert: PublicAlert) -> datetime:
    if alert.published_at is not None:
        return alert.published_at
    approved_at = alert.content_blocks.get("approvedAt")
    if approved_at:
        try:
            parsed = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                return parsed
        except ValueError:
            pass
    return datetime.now(UTC)


def _message_type(alert: PublicAlert) -> str:
    if alert.is_all_clear:
        return "Cancel"
    if alert.superseded_warning_id:
        return "Update"
    return "Alert"


def _status(alert: PublicAlert) -> str:
    return "Actual" if alert.status == "published" else "Draft"


def _urgency(alert: PublicAlert) -> str:
    if alert.is_all_clear:
        return "Past"
    return {
        "advice": "Future",
        "watch_and_act": "Expected",
        "emergency_warning": "Immediate",
    }.get(alert.warning_tier or "", "Unknown")


def _severity(alert: PublicAlert) -> str:
    if alert.is_all_clear:
        return "Minor"
    return {
        "advice": "Minor",
        "watch_and_act": "Moderate",
        "emergency_warning": "Extreme",
    }.get(alert.warning_tier or "", "Unknown")


def _category(alert: PublicAlert) -> str:
    return _CATEGORY_BY_HAZARD.get(alert.hazard_icon or "", "Safety")


def _certainty(alert: PublicAlert) -> str:
    if alert.is_all_clear:
        return "Observed"
    return _CERTAINTY_BY_TIER.get(alert.warning_tier or "", "Likely")


def serialize_cap(alert: PublicAlert) -> bytes:
    msg_type = _message_type(alert)
    sent_at = _iso_utc(_sent_at(alert))
    event_name = (alert.hazard_icon or "hazard").replace("_", " ").title()
    area_desc = alert.content_blocks.get("geography") or alert.content_blocks.get("areas") or "Unspecified area"
    body_text = alert.content_blocks.get("body") or alert.content_blocks.get("headline") or alert.alert_id
    headline = alert.content_blocks.get("headline") or alert.alert_id
    sender = alert.content_blocks.get("sender") or "aidr-hub"

    root = Element(f"{{{CAP_NAMESPACE}}}alert")
    SubElement(root, f"{{{CAP_NAMESPACE}}}identifier").text = alert.alert_id
    SubElement(root, f"{{{CAP_NAMESPACE}}}sender").text = sender
    SubElement(root, f"{{{CAP_NAMESPACE}}}sent").text = sent_at
    SubElement(root, f"{{{CAP_NAMESPACE}}}status").text = _status(alert)
    SubElement(root, f"{{{CAP_NAMESPACE}}}msgType").text = msg_type
    SubElement(root, f"{{{CAP_NAMESPACE}}}scope").text = "Public"

    if msg_type in {"Cancel", "Update"}:
        if not alert.superseded_warning_id:
            raise HTTPException(status_code=422, detail="Cancel/Update alerts require superseded_warning_id")
        refs = f"{sender},{alert.superseded_warning_id},{sent_at}"
        SubElement(root, f"{{{CAP_NAMESPACE}}}references").text = refs

    for language in list(dict.fromkeys(alert.languages or ["en-AU"])):
        info = SubElement(root, f"{{{CAP_NAMESPACE}}}info")
        SubElement(info, f"{{{CAP_NAMESPACE}}}language").text = language
        SubElement(info, f"{{{CAP_NAMESPACE}}}category").text = _category(alert)
        SubElement(info, f"{{{CAP_NAMESPACE}}}event").text = event_name
        SubElement(info, f"{{{CAP_NAMESPACE}}}urgency").text = _urgency(alert)
        SubElement(info, f"{{{CAP_NAMESPACE}}}severity").text = _severity(alert)
        SubElement(info, f"{{{CAP_NAMESPACE}}}certainty").text = _certainty(alert)
        SubElement(info, f"{{{CAP_NAMESPACE}}}headline").text = alert.content_blocks.get(
            f"headline:{language}", headline
        )
        SubElement(info, f"{{{CAP_NAMESPACE}}}description").text = alert.content_blocks.get(
            f"body:{language}", body_text
        )
        SubElement(info, f"{{{CAP_NAMESPACE}}}instruction").text = alert.action_statement or ""

        area = SubElement(info, f"{{{CAP_NAMESPACE}}}area")
        SubElement(area, f"{{{CAP_NAMESPACE}}}areaDesc").text = area_desc

    return tostring(root, encoding="utf-8", xml_declaration=True)


def validate_cap_xml(cap_xml: bytes) -> None:
    try:
        root = fromstring(cap_xml)
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=f"CAP XML is malformed: {exc}") from exc

    if root.tag != f"{{{CAP_NAMESPACE}}}alert":
        raise HTTPException(status_code=422, detail="CAP payload does not use CAP 1.2 namespace")
