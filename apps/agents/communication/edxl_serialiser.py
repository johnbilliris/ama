"""EDXL-DE message envelope serialiser for warning delivery.

Serializes PublicAlert with AWS fields to EDXL-DE XML format
per R-009/Constitution NN-4 (interoperability).
"""

from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring

from packages.domain.src.domain.models.public_alert import PublicAlert

EDXL_NAMESPACE = "urn:oasis:names:tc:emergency:EDXL:DE:1.0"


def serialize_to_edxl(alert: PublicAlert) -> str:
    """Serialize a PublicAlert to EDXL-DE XML string."""
    root = Element("EDXLDistribution", xmlns=EDXL_NAMESPACE)
    SubElement(root, "distributionID").text = alert.alert_id
    SubElement(root, "senderID").text = "disaster-response-hub"
    SubElement(root, "dateTimeSent").text = alert.published_at.isoformat() if alert.published_at else ""
    SubElement(root, "distributionStatus").text = "Actual"
    SubElement(root, "distributionType").text = "Alert"

    content = SubElement(root, "contentObject")
    content_desc = SubElement(content, "contentDescription")
    content_desc.text = alert.content_blocks.get("headline", alert.alert_id)

    # AWS-specific elements in embedded content
    if alert.warning_tier:
        aws = SubElement(content, "awsWarning")
        SubElement(aws, "warningTier").text = alert.warning_tier
        SubElement(aws, "colourCode").text = alert.colour_code or ""
        if alert.hazard_icon:
            SubElement(aws, "hazardIcon").text = alert.hazard_icon
        if alert.action_statement:
            SubElement(aws, "actionStatement").text = alert.action_statement

    if alert.is_all_clear:
        SubElement(content, "isAllClear").text = "true"

    return tostring(root, encoding="unicode", xml_declaration=True)
