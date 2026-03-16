from dataclasses import dataclass


@dataclass(frozen=True)
class EventEnvelope:
    channel: str
    scope_key: str
    payload: dict[str, object]


class EventBus:
    def publish(self, envelope: EventEnvelope) -> EventEnvelope:
        return envelope
