from packages.domain.src.domain.models.aiims_role_assignment import AiimsRoleAssignment
from packages.domain.src.domain.models.approval_decision import ApprovalDecision
from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.dead_letter_entry import DeadLetterEntry
from packages.domain.src.domain.models.evacuation_stage import EvacuationStage
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.lesson import Lesson
from packages.domain.src.domain.models.persona import Persona
from packages.domain.src.domain.models.pprr_phase_context import PprrPhaseContext
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation
from packages.domain.src.domain.models.recovery_environment_tracker import RecoveryEnvironmentTracker
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
AIIMS_ASSIGNMENTS: dict[str, AiimsRoleAssignment] = {}
EVACUATION_STAGES: dict[str, EvacuationStage] = {}
RECOVERY_TRACKERS: dict[str, RecoveryEnvironmentTracker] = {}
LESSONS: dict[str, Lesson] = {}
PPRR_CONTEXTS: dict[str, PprrPhaseContext] = {}


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
    AIIMS_ASSIGNMENTS.clear()
    EVACUATION_STAGES.clear()
    RECOVERY_TRACKERS.clear()
    LESSONS.clear()
    PPRR_CONTEXTS.clear()
