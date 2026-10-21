"""Tenant-keyed facade over operational entity storage (AUD-002).

Operational routes and services MUST read and write through this facade rather
than touching the process-global dictionaries directly. Every accessor is keyed
by ``(tenant_id, entity_id)`` so that ``live`` and ``sim-*`` records with
identical ids never collide, and a caller bound to one tenant can never observe
another tenant's records through an unscoped scan.

Deliberate cross-agency sharing is expressed through
:meth:`OperationalStore.cross_agency_projection`, which returns an explicitly
allow-listed field subset rather than the full record.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, TypeVar

from app.core.tenant_context import get_current_tenant
from app.services import state_store

from packages.domain.src.domain.models.approval_decision import ApprovalDecision
from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation
from packages.domain.src.domain.models.signal import Signal

T = TypeVar("T")

DEFAULT_TENANT_ID = "live"

#: Fields an agency outside the owning tenant may observe for a shared incident.
CROSS_AGENCY_INCIDENT_FIELDS: tuple[str, ...] = (
    "incident_id",
    "title",
    "incident_type",
    "status",
    "severity",
    "affected_jurisdiction_ids",
)


def current_tenant_id() -> str:
    """Resolve the tenant bound to the active request, defaulting to ``live``."""
    try:
        return get_current_tenant().tenant_id or DEFAULT_TENANT_ID
    except LookupError:
        return DEFAULT_TENANT_ID


class _Collection[T]:
    """Tenant-keyed accessor over one :class:`state_store.TenantScopedDict`."""

    def __init__(self, backing: state_store.TenantScopedDict[T], tenant_id: str) -> None:
        self._backing = backing
        self._tenant_id = tenant_id

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    def get(self, entity_id: str) -> T | None:
        return self._backing.bucket_for(self._tenant_id).get(entity_id)

    def require(self, entity_id: str) -> T:
        record = self.get(entity_id)
        if record is None:
            raise KeyError(entity_id)
        return record

    def put(self, entity_id: str, record: T) -> T:
        self._backing.bucket_for(self._tenant_id)[entity_id] = record
        return record

    def contains(self, entity_id: str) -> bool:
        return entity_id in self._backing.bucket_for(self._tenant_id)

    def values(self) -> list[T]:
        return list(self._backing.bucket_for(self._tenant_id).values())

    def items(self) -> list[tuple[str, T]]:
        return list(self._backing.bucket_for(self._tenant_id).items())

    def where(self, predicate: Callable[[T], bool]) -> list[T]:
        return [record for record in self.values() if predicate(record)]

    def __iter__(self) -> Iterator[T]:
        return iter(self.values())

    def __len__(self) -> int:
        return len(self._backing.bucket_for(self._tenant_id))


class OperationalStore:
    """Single scoped entry point for operational entity reads and writes."""

    def __init__(self, tenant_id: str | None = None) -> None:
        self._tenant_id = tenant_id or current_tenant_id()

    @classmethod
    def current(cls) -> OperationalStore:
        return cls(current_tenant_id())

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    @property
    def incidents(self) -> _Collection[Incident]:
        return _Collection(state_store.INCIDENTS, self._tenant_id)

    @property
    def signals(self) -> _Collection[Signal]:
        return _Collection(state_store.SIGNALS, self._tenant_id)

    @property
    def recommendations(self) -> _Collection[Recommendation]:
        return _Collection(state_store.RECOMMENDATIONS, self._tenant_id)

    @property
    def approvals(self) -> _Collection[ApprovalDecision]:
        return _Collection(state_store.APPROVALS, self._tenant_id)

    @property
    def alerts(self) -> _Collection[PublicAlert]:
        return _Collection(state_store.ALERTS, self._tenant_id)

    @property
    def tasks(self) -> _Collection[CoordinationTask]:
        return _Collection(state_store.TASKS, self._tenant_id)

    def cross_agency_projection(self, incident_id: str) -> dict[str, Any] | None:
        """Return the allow-listed field subset shared with partner agencies."""
        incident = self.incidents.get(incident_id)
        if incident is None:
            return None
        dumped = incident.model_dump(mode="json")
        return {field: dumped[field] for field in CROSS_AGENCY_INCIDENT_FIELDS if field in dumped}


def get_operational_store(tenant_id: str | None = None) -> OperationalStore:
    return OperationalStore(tenant_id)
