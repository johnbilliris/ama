from app.validators.signal_envelope import SignalEnvelope


class MonitoringAgent:
    def summarize_signal(self, envelope: SignalEnvelope) -> dict[str, object]:
        return {
            "category": envelope.category,
            "sourceKind": envelope.source.kind,
            "incidentId": envelope.incidentId,
        }
