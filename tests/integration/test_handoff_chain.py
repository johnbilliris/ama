from app.services.event_bus import EventBus, EventEnvelope
from app.services.state_store import HANDOFF_EVENTS, TIMELINE_EVENTS


def test_handoff_chain_records_delivery_and_timeline() -> None:
    HANDOFF_EVENTS.clear()
    TIMELINE_EVENTS.clear()

    bus = EventBus()

    def risk_assessment_handler(_: EventEnvelope) -> None:
        return None

    bus.subscribe("handoff.monitoring.risk", risk_assessment_handler)

    statuses = bus.publish(
        EventEnvelope(
            channel="handoff.monitoring.risk",
            scope_key="incident-chain-1",
            payload={
                "handoffId": "handoff-1",
                "incidentId": "incident-chain-1",
                "sourceAgent": "monitoring",
                "targetAgent": "risk_assessment",
                "confidence": 0.91,
            },
        )
    )

    assert statuses and statuses[0].success is True
    assert "incident-chain-1" in HANDOFF_EVENTS
    assert HANDOFF_EVENTS["incident-chain-1"][0]["status"] == "delivered"
    assert TIMELINE_EVENTS["incident-chain-1"][0].event_type == "handoff"
