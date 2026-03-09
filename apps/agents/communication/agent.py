from packages.domain.src.domain.models.public_alert import PublicAlert


class CommunicationAgent:
    def draft_alert(self, incident_id: str, recommendation_id: str) -> PublicAlert:
        return PublicAlert(
            alert_id=f"alert-{recommendation_id}",
            incident_id=incident_id,
            status="pending_approval",
            audience_segments=["affected-community"],
            languages=["en-AU"],
            accessibility_attributes=["plain-language"],
            channel_set=["sms", "push"],
            content_blocks={"headline": "Prepare to evacuate if directed."},
        )
