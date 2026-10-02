import logging
from datetime import UTC, datetime
from typing import Any
from xml.etree import ElementTree

from apps.ingestion.normalisers.timestamps import parse_iso_timestamp, to_utc_iso_z

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

CERTAINTY_MULTIPLIER: dict[str, float] = {
    "Observed": 1.0,
    "Likely": 0.95,
    "Possible": 0.8,
    "Unlikely": 0.6,
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


def _find_child(parent: ElementTree.Element, tag: str) -> ElementTree.Element | None:
    namespaced = parent.find(f"cap:{tag}", CAP_NS)
    if namespaced is not None:
        return namespaced
    return parent.find(tag)


def _find_text(parent: ElementTree.Element, tag: str) -> str:
    element = _find_child(parent, tag)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _findall(parent: ElementTree.Element, tag: str) -> list[ElementTree.Element]:
    namespaced = parent.findall(f"cap:{tag}", CAP_NS)
    if namespaced:
        return namespaced
    return parent.findall(tag)


def extract_cap_identity(raw_payload: dict[str, Any]) -> dict[str, str]:
    xml_content = raw_payload.get("xml", raw_payload.get("content", ""))
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8")
    if not xml_content:
        raise ValueError("Empty CAP XML content")

    try:
        root = ElementTree.fromstring(xml_content)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Invalid CAP XML: {exc}") from exc

    cap_identifier = _find_text(root, "identifier")
    if not cap_identifier:
        raise ValueError("CAP XML missing required identifier")
    sent_raw = _find_text(root, "sent")
    if not sent_raw:
        raise ValueError("CAP XML missing required sent timestamp")

    return {
        "identifier": cap_identifier,
        "sent": to_utc_iso_z(parse_iso_timestamp(sent_raw, provider="cap_xml", field="sent")),
        "status": _find_text(root, "status"),
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

    source_uri = str(raw_payload.get("source_uri", "")).strip()
    if not source_uri:
        raise ValueError("CAP XML missing required source_uri")

    metadata = extract_cap_identity(raw_payload)
    identifier = metadata["identifier"]
    sent = metadata["sent"]
    status = metadata["status"]

    infos = _findall(root, "info")
    if not infos:
        raise ValueError("CAP XML missing required info block")

    info_blocks: list[dict[str, Any]] = []
    all_areas: list[dict[str, Any]] = []
    for info in infos:
        urgency = _find_text(info, "urgency")
        severity = _find_text(info, "severity")
        certainty = _find_text(info, "certainty")
        category_code = _find_text(info, "category")
        headline = _find_text(info, "headline")
        description = _find_text(info, "description")[:500]
        language = _find_text(info, "language")

        if not urgency or not severity or not certainty:
            raise ValueError("CAP XML missing required urgency/severity/certainty in info block")

        area_entries: list[dict[str, Any]] = []
        for area in _findall(info, "area"):
            area_desc = _find_text(area, "areaDesc")
            circle = _find_text(area, "circle")
            polygon = _find_text(area, "polygon")
            area_entries.append(
                {
                    "areaDesc": area_desc,
                    "circle": circle,
                    "polygon": polygon,
                }
            )
            all_areas.append(area_entries[-1])

        info_blocks.append(
            {
                "urgency": urgency,
                "severity": severity,
                "certainty": certainty,
                "category": category_code,
                "headline": headline,
                "description": description,
                "language": language,
                "areas": area_entries,
            }
        )

    if not all_areas:
        raise ValueError("CAP XML missing required area definitions")

    primary_info = info_blocks[0]
    urgency = primary_info["urgency"]
    severity = primary_info["severity"]
    certainty = primary_info["certainty"]
    category_code = primary_info["category"]
    headline = primary_info["headline"]
    description = primary_info["description"]

    base_confidence = URGENCY_CONFIDENCE.get(urgency, 0.75)
    multiplier = SEVERITY_MULTIPLIER.get(severity, 0.85)
    certainty_multiplier = CERTAINTY_MULTIPLIER.get(certainty, 0.75)
    confidence = min(1.0, base_confidence * multiplier * certainty_multiplier)

    category = CAP_CATEGORY_MAP.get(category_code, "weather")
    if "flood" in headline.lower() or "flood" in description.lower():
        category = "hydrology"
    elif "tsunami" in headline.lower():
        category = "geohazard"

    location: dict[str, Any] | None = None
    for area in all_areas:
        if area["polygon"]:
            coord_pairs = area["polygon"].split()
            coordinates: list[list[float]] = []
            for pair in coord_pairs:
                parts = pair.split(",")
                if len(parts) >= 2:
                    try:
                        coordinates.append([float(parts[1]), float(parts[0])])
                    except ValueError:
                        continue
            if coordinates:
                location = {
                    "type": "Polygon",
                    "coordinates": [coordinates],
                    "precisionMeters": 1000,
                }
                break
        if area["circle"]:
            parts = area["circle"].split()
            if parts:
                coords = parts[0].split(",")
                if len(coords) >= 2:
                    try:
                        location = {
                            "type": "Point",
                            "coordinates": [float(coords[1]), float(coords[0])],
                            "precisionMeters": 5000,
                        }
                        break
                    except ValueError:
                        continue

    if location is None:
        raise ValueError("CAP XML missing parseable area geometry")

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
            "status": status,
            "urgency": urgency,
            "severity": severity,
            "certainty": certainty,
            "infoBlocks": info_blocks,
        },
        "confidenceScore": confidence,
        "freshnessScore": 0.9,
        "validationStatus": "validated",
        "provenance": {
            "collectionMethod": "api_pull",
            "sourceUri": source_uri,
            "sourceTimestamp": sent,
        },
    }
