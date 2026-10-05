"""Process-local operational entity storage, keyed by tenant (AUD-002).

Each module-level name below is a :class:`TenantScopedDict`: a mapping proxy
that transparently namespaces every key by the tenant bound to the active
request (``live`` when no request context is present). Two tenants may hold the
same entity id without colliding, and an unscoped ``.values()`` scan can only
ever observe the caller's own tenant.

Prefer :mod:`app.services.operational_store` for new code — it exposes the same
data with an explicit ``tenant_id`` instead of relying on ambient context.
"""

from collections.abc import Iterator, MutableMapping
from typing import Protocol, TypeVar

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


class _ClearableTenantStore(Protocol):
    def clear_all_tenants(self) -> None: ...

    def clear_tenant(self, tenant_id: str) -> None: ...


T = TypeVar("T")

DEFAULT_TENANT_ID = "live"


def _active_tenant_id() -> str:
    from app.core.tenant_context import get_current_tenant

    try:
        return get_current_tenant().tenant_id or DEFAULT_TENANT_ID
    except LookupError:
        return DEFAULT_TENANT_ID


class TenantScopedDict[T](MutableMapping[str, T]):
    """Mapping whose visible contents are limited to the active tenant."""

    __slots__ = ("_name", "_tenants")

    def __init__(self, name: str) -> None:
        self._name = name
        self._tenants: dict[str, dict[str, T]] = {}

    def bucket_for(self, tenant_id: str) -> dict[str, T]:
        return self._tenants.setdefault(tenant_id, {})

    def _bucket(self) -> dict[str, T]:
        return self.bucket_for(_active_tenant_id())

    def tenant_ids(self) -> list[str]:
        return [tenant_id for tenant_id, bucket in self._tenants.items() if bucket]

    def clear_all_tenants(self) -> None:
        self._tenants.clear()

    def clear_tenant(self, tenant_id: str) -> None:
        self._tenants.pop(tenant_id, None)

    def __getitem__(self, key: str) -> T:
        return self._bucket()[key]

    def __setitem__(self, key: str, value: T) -> None:
        self._bucket()[key] = value

    def __delitem__(self, key: str) -> None:
        del self._bucket()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(dict(self._bucket()))

    def __len__(self) -> int:
        return len(self._bucket())

    def __contains__(self, key: object) -> bool:
        return key in self._bucket()

    def __repr__(self) -> str:
        return f"TenantScopedDict({self._name!r}, tenant={_active_tenant_id()!r}, size={len(self)})"


INCIDENTS: TenantScopedDict[Incident] = TenantScopedDict("INCIDENTS")
SIGNALS: TenantScopedDict[Signal] = TenantScopedDict("SIGNALS")
RECOMMENDATIONS: TenantScopedDict[Recommendation] = TenantScopedDict("RECOMMENDATIONS")
APPROVALS: TenantScopedDict[ApprovalDecision] = TenantScopedDict("APPROVALS")
ALERTS: TenantScopedDict[PublicAlert] = TenantScopedDict("ALERTS")
PERSONAS: dict[str, Persona] = {}
TASKS: TenantScopedDict[CoordinationTask] = TenantScopedDict("TASKS")
DEAD_LETTERS: TenantScopedDict[DeadLetterEntry] = TenantScopedDict("DEAD_LETTERS")
HANDOFF_EVENTS: TenantScopedDict[list[dict[str, object]]] = TenantScopedDict("HANDOFF_EVENTS")
TIMELINE_EVENTS: TenantScopedDict[list[TimelineEvent]] = TenantScopedDict("TIMELINE_EVENTS")
SIGNAL_ACCEPTED_OUTCOMES: TenantScopedDict[dict[str, object]] = TenantScopedDict("SIGNAL_ACCEPTED_OUTCOMES")
SIGNAL_ACCEPTED_OUTBOX: TenantScopedDict[dict[str, object]] = TenantScopedDict("SIGNAL_ACCEPTED_OUTBOX")
AIIMS_ASSIGNMENTS: dict[str, AiimsRoleAssignment] = {}
EVACUATION_STAGES: dict[str, EvacuationStage] = {}
RECOVERY_TRACKERS: dict[str, RecoveryEnvironmentTracker] = {}
LESSONS: dict[str, Lesson] = {}
PPRR_CONTEXTS: dict[str, PprrPhaseContext] = {}

_TENANT_SCOPED: tuple[_ClearableTenantStore, ...] = (
    INCIDENTS,
    SIGNALS,
    RECOMMENDATIONS,
    APPROVALS,
    ALERTS,
    TASKS,
    DEAD_LETTERS,
    HANDOFF_EVENTS,
    TIMELINE_EVENTS,
    SIGNAL_ACCEPTED_OUTCOMES,
    SIGNAL_ACCEPTED_OUTBOX,
)


def reset_state() -> None:
    for scoped in _TENANT_SCOPED:
        scoped.clear_all_tenants()
    PERSONAS.clear()
    AIIMS_ASSIGNMENTS.clear()
    EVACUATION_STAGES.clear()
    RECOVERY_TRACKERS.clear()
    LESSONS.clear()
    PPRR_CONTEXTS.clear()


def clear_tenant_state(tenant_id: str) -> None:
    for scoped in _TENANT_SCOPED:
        scoped.clear_tenant(tenant_id)
