import logging
from datetime import UTC, datetime
from typing import Any
from xml.etree import ElementTree

logger = logging.getLogger(__name__)

BOM_NS = {"p": "http://www.bom.gov.au/schema/v1.7"}

CATEGORY_MAP: dict[str, str] = {
    "severe thunderstorm": "weather",
    "tropical cyclone": "weather",
    "fire weather": "fire",
    "flood": "hydrology",
    "coastal": "weather",
    "wind": "weather",
    "storm": "weather",
}


def normalise_bom_xml(raw_payload: dict[str, Any]) -> dict[str, Any]:
    """Parse BoM product XML (XSD v1.7) into a SignalEnvelope dict."""
    xml_content = raw_payload.get("xml", raw_payload.get("content", ""))
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8")

    if not xml_content:
        raise ValueError("Empty XML content in BoM payload")

    try:
        root = ElementTree.fromstring(xml_content)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc

    product_type = root.get("type", "").lower()
    issue_time_str = ""
    identifier = root.get("id", "")

    amoc = root.find(".//p:amoc", BOM_NS) or root.find(".//amoc")
    if amoc is not None:
        issue_el = amoc.find("p:issue-time-utc", BOM_NS) or amoc.find("issue-time-utc")
        if issue_el is not None and issue_el.text:
            issue_time_str = issue_el.text.strip()
        id_el = amoc.find("p:identifier", BOM_NS) or amoc.find("identifier")
        if id_el is not None and id_el.text:
            identifier = id_el.text.strip()

    if not issue_time_str:
        issue_time_str = datetime.now(UTC).isoformat()

    category = "weather"
    for key, cat in CATEGORY_MAP.items():
        if key in product_type:
            category = cat
            break

    warning_text = ""
    text_el = root.find(".//p:text", BOM_NS) or root.find(".//text")
    if text_el is not None and text_el.text:
        warning_text = text_el.text.strip()[:500]

    areas: list[str] = []
    for area in root.findall(".//p:area", BOM_NS) or root.findall(".//area") or []:
        aname = area.get("description", area.get("aac", ""))
        if aname:
            areas.append(aname)

    location = {"type": "Point", "coordinates": [149.13, -35.28], "precisionMeters": 50000}
    for area in root.findall(".//p:area", BOM_NS) or root.findall(".//area") or []:
        parent_el = area.get("parent-aac", "")
        for point in area.findall("p:point", BOM_NS) or area.findall("point") or []:
            lat = point.get("latitude")
            lon = point.get("longitude")
            if lat and lon:
                try:
                    location = {
                        "type": "Point",
                        "coordinates": [float(lon), float(lat)],
                        "precisionMeters": 10000,
                    }
                except ValueError:
                    pass
                break

    return {
        "source": {
            "dataSourceId": raw_payload.get("data_source_id", "bom-warnings"),
            "name": "Bureau of Meteorology",
            "kind": "authoritative",
        },
        "category": category,
        "occurredAt": issue_time_str,
        "receivedAt": datetime.now(UTC).isoformat(),
        "jurisdictionId": raw_payload.get("jurisdiction_id"),
        "location": location,
        "payload": {
            "productId": identifier,
            "productType": product_type,
            "warningText": warning_text,
            "affectedAreas": areas,
        },
        "confidenceScore": 0.95,
        "freshnessScore": 0.9,
        "validationStatus": "validated",
        "provenance": {
            "collectionMethod": "api_pull",
            "sourceUri": raw_payload.get("source_uri", "ftp://ftp.bom.gov.au/anon/gen/fwo/"),
            "sourceTimestamp": issue_time_str,
        },
    }
