from app.validators.signal_envelope import SignalEnvelope
from common.handoffs import AgentHandoffEvent, build_handoff


class MonitoringAgent:
    def summarize_signal(self, envelope: SignalEnvelope) -> dict[str, object]:
        return {
            "category": envelope.category,
            "sourceKind": envelope.source.kind,
            "incidentId": envelope.incidentId,
        }

    def build_high_risk_handoff(self, envelope: SignalEnvelope) -> AgentHandoffEvent | None:
        is_high_risk = envelope.category in {"fire", "weather", "hydrology"} and envelope.confidenceScore >= 0.8
        if not is_high_risk or not envelope.incidentId:
            return None

        return build_handoff(
            incident_id=envelope.incidentId,
            source_agent="monitoring",
            target_agent="risk_assessment",
            scope_key=envelope.incidentId,
            payload={
                "category": envelope.category,
                "sourceKind": envelope.source.kind,
                "signalSummary": self.summarize_signal(envelope),
            },
            confidence=envelope.confidenceScore,
        )
