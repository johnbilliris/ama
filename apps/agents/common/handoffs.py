from dataclasses import dataclass


@dataclass(frozen=True)
class AgentHandoff:
    source_agent: str
    target_agent: str
    scope_key: str
    confidence: float
    payload: dict[str, object]


def build_handoff(*, source_agent: str, target_agent: str, scope_key: str, payload: dict[str, object], confidence: float) -> AgentHandoff:
    return AgentHandoff(
        source_agent=source_agent,
        target_agent=target_agent,
        scope_key=scope_key,
        payload=payload,
        confidence=confidence,
    )
