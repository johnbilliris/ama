from packages.domain.src.domain.models.approval_decision import ApprovalDecision
from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.persona import Persona
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation
from packages.domain.src.domain.models.signal import Signal


INCIDENTS: dict[str, Incident] = {}
SIGNALS: dict[str, Signal] = {}
RECOMMENDATIONS: dict[str, Recommendation] = {}
APPROVALS: dict[str, ApprovalDecision] = {}
ALERTS: dict[str, PublicAlert] = {}
PERSONAS: dict[str, Persona] = {}
TASKS: dict[str, CoordinationTask] = {}


def reset_state() -> None:
    INCIDENTS.clear()
    SIGNALS.clear()
    RECOMMENDATIONS.clear()
    APPROVALS.clear()
    ALERTS.clear()
    PERSONAS.clear()
    TASKS.clear()

