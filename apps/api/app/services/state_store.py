from packages.domain.src.domain.models.approval_decision import ApprovalDecision
from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.dead_letter_entry import DeadLetterEntry
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.persona import Persona
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation
from packages.domain.src.domain.models.signal import Signal
from packages.domain.src.domain.models.timeline_event import TimelineEvent

INCIDENTS: dict[str, Incident] = {}
SIGNALS: dict[str, Signal] = {}
RECOMMENDATIONS: dict[str, Recommendation] = {}
APPROVALS: dict[str, ApprovalDecision] = {}
ALERTS: dict[str, PublicAlert] = {}
PERSONAS: dict[str, Persona] = {}
TASKS: dict[str, CoordinationTask] = {}
DEAD_LETTERS: dict[str, DeadLetterEntry] = {}
HANDOFF_EVENTS: dict[str, list[dict[str, object]]] = {}
TIMELINE_EVENTS: dict[str, list[TimelineEvent]] = {}


def reset_state() -> None:
    INCIDENTS.clear()
    SIGNALS.clear()
    RECOMMENDATIONS.clear()
    APPROVALS.clear()
    ALERTS.clear()
    PERSONAS.clear()
    TASKS.clear()
    DEAD_LETTERS.clear()
    HANDOFF_EVENTS.clear()
    TIMELINE_EVENTS.clear()

