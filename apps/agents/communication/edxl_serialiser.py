"""EDXL-DE message envelope serialiser for warning delivery.

Serializes PublicAlert with AWS fields to EDXL-DE XML format
per R-009/Constitution NN-4 (interoperability).
"""

from __future__ import annotations

from datetime import UTC, datetime
from xml.etree.ElementTree import Element, SubElement, fromstring, register_namespace, tostring

from apps.agents.communication.cap_serialiser import serialize_cap, validate_cap_xml
from packages.domain.src.domain.models.public_alert import PublicAlert

EDXL_NAMESPACE = "urn:oasis:names:tc:emergency:EDXL:DE:2.0"
register_namespace("", EDXL_NAMESPACE)


def serialize_to_edxl(alert: PublicAlert) -> str:
    """Serialize a PublicAlert to EDXL-DE 2.0 string with embedded CAP."""
    cap_xml = serialize_cap(alert)
    validate_cap_xml(cap_xml)
    cap_root = fromstring(cap_xml)

    root = Element(f"{{{EDXL_NAMESPACE}}}EDXLDistribution")
    SubElement(root, f"{{{EDXL_NAMESPACE}}}distributionID").text = alert.alert_id
    SubElement(root, f"{{{EDXL_NAMESPACE}}}senderID").text = (
        alert.content_blocks.get("sender") or "disaster-response-hub"
    )
    sent_at = alert.published_at or datetime.now(UTC)
    SubElement(root, f"{{{EDXL_NAMESPACE}}}dateTimeSent").text = sent_at.replace(microsecond=0).isoformat()
    SubElement(root, f"{{{EDXL_NAMESPACE}}}distributionStatus").text = (
        "Actual" if alert.status == "published" else "Exercise"
    )
    SubElement(root, f"{{{EDXL_NAMESPACE}}}distributionType").text = "Report"

    content = SubElement(root, f"{{{EDXL_NAMESPACE}}}contentObject")
    SubElement(content, f"{{{EDXL_NAMESPACE}}}contentDescription").text = alert.content_blocks.get(
        "headline", alert.alert_id
    )
    xml_content = SubElement(content, f"{{{EDXL_NAMESPACE}}}xmlContent")
    embedded = SubElement(xml_content, f"{{{EDXL_NAMESPACE}}}embeddedXMLContent")
    embedded.append(cap_root)

    return tostring(root, encoding="unicode", xml_declaration=True)
