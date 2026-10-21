import logging
from datetime import UTC, datetime
from typing import Any
from xml.etree import ElementTree

from apps.ingestion.normalisers.timestamps import parse_iso_timestamp, to_utc_iso_z

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


def _find_child(parent: ElementTree.Element, tag: str) -> ElementTree.Element | None:
    namespaced = parent.find(f"p:{tag}", BOM_NS)
    if namespaced is not None:
        return namespaced
    return parent.find(tag)


def _find_text(parent: ElementTree.Element, tag: str) -> str:
    element = _find_child(parent, tag)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _findall(parent: ElementTree.Element, tag: str) -> list[ElementTree.Element]:
    namespaced = parent.findall(f".//p:{tag}", BOM_NS)
    if namespaced:
        return namespaced
    return parent.findall(f".//{tag}")


def extract_bom_product_metadata(raw_payload: dict[str, Any]) -> dict[str, str]:
    xml_content = raw_payload.get("xml", raw_payload.get("content", ""))
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8")
    if not xml_content:
        raise ValueError("Empty XML content in BoM payload")

    try:
        root = ElementTree.fromstring(xml_content)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc

    amoc = _find_child(root, "amoc")
    if amoc is None:
        raise ValueError("BoM XML missing required amoc element")

    product_id = _find_text(amoc, "identifier") or root.get("id", "").strip()
    if not product_id:
        raise ValueError("BoM XML missing required amoc.identifier")

    issue_time_raw = _find_text(amoc, "issue-time-utc")
    if not issue_time_raw:
        raise ValueError("BoM XML missing required amoc.issue-time-utc")
    issue_time_utc = to_utc_iso_z(parse_iso_timestamp(issue_time_raw, provider="bom_xml", field="issue-time-utc"))

    product_type = (_find_text(amoc, "product-type") or root.get("type", "")).strip().lower()
    if not product_type:
        raise ValueError("BoM XML missing required product type")

    return {
        "productId": product_id,
        "issueTimeUtc": issue_time_utc,
        "productType": product_type,
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

    source_uri = str(raw_payload.get("source_uri", "")).strip()
    if not source_uri:
        raise ValueError("BoM XML missing required source_uri")

    metadata = extract_bom_product_metadata(raw_payload)
    issue_time_str = metadata["issueTimeUtc"]
    identifier = metadata["productId"]
    product_type = metadata["productType"]

    schema_validator = raw_payload.get("xml_schema_validator")
    if callable(schema_validator):
        schema_validator(root)

    category = "weather"
    for key, cat in CATEGORY_MAP.items():
        if key in product_type:
            category = cat
            break

    warning_text = ""
    text_el = _find_child(root, "text")
    if text_el is not None and text_el.text:
        warning_text = text_el.text.strip()[:500]

    areas: list[str] = []
    area_points: list[list[float]] = []
    for area in _findall(root, "area"):
        aname = area.get("description", area.get("aac", ""))
        if aname:
            areas.append(aname)
        for point in area.findall("p:point", BOM_NS) + area.findall("point"):
            lat = point.get("latitude")
            lon = point.get("longitude")
            if lat and lon:
                try:
                    area_points.append([float(lon), float(lat)])
                except ValueError:
                    continue

    if not area_points:
        raise ValueError("BoM XML missing required area point coordinates")

    location = {
        "type": "Point",
        "coordinates": area_points[0],
        "precisionMeters": 10000,
    }

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
            "issueTimeUtc": issue_time_str,
            "warningText": warning_text,
            "affectedAreas": areas,
            "areaPoints": area_points,
        },
        "confidenceScore": 0.95,
        "freshnessScore": 0.9,
        "validationStatus": "validated",
        "provenance": {
            "collectionMethod": "api_pull",
            "sourceUri": source_uri,
            "sourceTimestamp": issue_time_str,
        },
    }
