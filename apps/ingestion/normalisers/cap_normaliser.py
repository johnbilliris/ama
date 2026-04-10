import logging
from datetime import UTC, datetime
from typing import Any
from xml.etree import ElementTree

logger = logging.getLogger(__name__)

CAP_NS = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}

URGENCY_CONFIDENCE: dict[str, float] = {
    "Immediate": 0.95,
    "Expected": 0.85,
    "Future": 0.70,
    "Past": 0.50,
    "Unknown": 0.50,
}

SEVERITY_MULTIPLIER: dict[str, float] = {
    "Extreme": 1.0,
    "Severe": 0.95,
    "Moderate": 0.85,
    "Minor": 0.70,
    "Unknown": 0.75,
}

CAP_CATEGORY_MAP: dict[str, str] = {
    "Met": "weather",
    "Geo": "geohazard",
    "Fire": "fire",
    "Health": "community_report",
    "Env": "weather",
    "Transport": "infrastructure",
    "Infra": "infrastructure",
    "CBRNE": "community_report",
    "Other": "weather",
}


def normalise_cap_xml(raw_payload: dict[str, Any]) -> dict[str, Any]:
    """Parse Common Alerting Protocol XML into a SignalEnvelope dict."""
    xml_content = raw_payload.get("xml", raw_payload.get("content", ""))
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8")

    if not xml_content:
        raise ValueError("Empty CAP XML content")

    try:
        root = ElementTree.fromstring(xml_content)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Invalid CAP XML: {exc}") from exc

    def find_text(parent: ElementTree.Element, tag: str) -> str:
        el = parent.find(f"cap:{tag}", CAP_NS) or parent.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    identifier = find_text(root, "identifier")
    sent = find_text(root, "sent")
    if not sent:
        sent = datetime.now(UTC).isoformat()

    info = root.find("cap:info", CAP_NS) or root.find("info")
    urgency = severity = certainty = ""
    category_code = ""
    headline = description = ""
    if info is not None:
        urgency = find_text(info, "urgency")
        severity = find_text(info, "severity")
        certainty = find_text(info, "certainty")
        category_code = find_text(info, "category")
        headline = find_text(info, "headline")
        description = find_text(info, "description")[:500]

    base_confidence = URGENCY_CONFIDENCE.get(urgency, 0.75)
    multiplier = SEVERITY_MULTIPLIER.get(severity, 0.85)
    confidence = min(1.0, base_confidence * multiplier)

    category = CAP_CATEGORY_MAP.get(category_code, "weather")
    if "flood" in headline.lower() or "flood" in description.lower():
        category = "hydrology"
    elif "tsunami" in headline.lower():
        category = "geohazard"

    location = {"type": "Point", "coordinates": [149.13, -35.28], "precisionMeters": 50000}
    if info is not None:
        area = info.find("cap:area", CAP_NS) or info.find("area")
        if area is not None:
            circle = area.find("cap:circle", CAP_NS) or area.find("circle")
            if circle is not None and circle.text:
                parts = circle.text.strip().split()
                if parts:
                    coords = parts[0].split(",")
                    if len(coords) >= 2:
                        try:
                            location = {
                                "type": "Point",
                                "coordinates": [float(coords[1]), float(coords[0])],
                                "precisionMeters": 5000,
                            }
                        except ValueError:
                            pass

            polygon = area.find("cap:polygon", CAP_NS) or area.find("polygon")
            if polygon is not None and polygon.text:
                coord_pairs = polygon.text.strip().split()
                coordinates = []
                for pair in coord_pairs:
                    parts = pair.split(",")
                    if len(parts) >= 2:
                        try:
                            coordinates.append([float(parts[1]), float(parts[0])])
                        except ValueError:
                            pass
                if coordinates:
                    location = {
                        "type": "Polygon",
                        "coordinates": [coordinates],
                        "precisionMeters": 1000,
                    }

    return {
        "source": {
            "dataSourceId": raw_payload.get("data_source_id", "bom-flood-warnings"),
            "name": raw_payload.get("source_name", "Joint Australian Tsunami Warning Centre"),
            "kind": "authoritative",
        },
        "category": category,
        "occurredAt": sent,
        "receivedAt": datetime.now(UTC).isoformat(),
        "jurisdictionId": raw_payload.get("jurisdiction_id"),
        "location": location,
        "payload": {
            "capIdentifier": identifier,
            "headline": headline,
            "description": description,
            "urgency": urgency,
            "severity": severity,
            "certainty": certainty,
        },
        "confidenceScore": confidence,
        "freshnessScore": 0.9,
        "validationStatus": "validated",
        "provenance": {
            "collectionMethod": "api_pull",
            "sourceUri": raw_payload.get("source_uri", ""),
            "sourceTimestamp": sent,
        },
    }
