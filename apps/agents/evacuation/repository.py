"""Scoped lifecycle and history repository for evacuation plans."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from azure.core import MatchConditions
from evacuation.models import EvacuationPlan, PlanStatus

_ACTIVE_STATUSES = {
    PlanStatus.proposed,
    PlanStatus.approved,
    PlanStatus.paused,
}
_TERMINAL_STATUSES = {
    PlanStatus.rejected,
    PlanStatus.superseded,
    PlanStatus.expired,
    PlanStatus.cancelled,
}


class EvacuationPlanRepository:
    """Read and transition plan history inside a tenant/incident partition."""

    def __init__(self, container: Any = None) -> None:
        self._container = container

    def get(self, plan_id: str, incident_scope_key: str) -> dict[str, Any] | None:
        if self._container is None:
            return None
        try:
            document = self._container.read_item(
                item=plan_id,
                partition_key=incident_scope_key,
            )
        except Exception as exc:
            if _is_not_found(exc):
                return None
            raise
        plan = EvacuationPlan.model_validate(document)
        if plan.incident_scope_key != incident_scope_key:
            raise ValueError("retrieved plan does not match requested incident scope")
        return document

    def list_history(
        self,
        incident_id: str,
        incident_scope_key: str,
    ) -> list[dict[str, Any]]:
        if self._container is None:
            return []
        documents = self._container.query_items(
            query=(
                "SELECT * FROM c WHERE c.incident_id = @incident_id "
                "AND c.incident_scope_key = @incident_scope_key "
                "AND c.tenant_id = @tenant_id "
                "AND IS_DEFINED(c.plan_id) ORDER BY c.version DESC"
            ),
            parameters=[
                {"name": "@incident_id", "value": incident_id},
                {
                    "name": "@incident_scope_key",
                    "value": incident_scope_key,
                },
                {
                    "name": "@tenant_id",
                    "value": incident_scope_key.split(":", 1)[0],
                },
            ],
            partition_key=incident_scope_key,
        )
        history = []
        for document in documents:
            plan = EvacuationPlan.model_validate(document)
            if plan.incident_id != incident_id or plan.incident_scope_key != incident_scope_key:
                raise ValueError("plan history row does not match requested scope")
            history.append(document)
        return sorted(history, key=lambda item: int(item["version"]), reverse=True)

    def expire_due(
        self,
        incident_id: str,
        incident_scope_key: str,
        *,
        now: datetime | None = None,
    ) -> list[EvacuationPlan]:
        current_time = now or datetime.now(UTC)
        expired = []
        for document in self.list_history(incident_id, incident_scope_key):
            plan = EvacuationPlan.model_validate(document)
            if plan.status not in {PlanStatus.proposed, PlanStatus.paused}:
                continue
            if plan.valid_until is None or plan.valid_until > current_time:
                continue
            etag = str(document.get("_etag") or "")
            if not etag:
                raise RuntimeError(f"Plan {plan.plan_id} has no concurrency token")
            update = _write_body(document)
            update.update(
                {
                    "status": PlanStatus.expired.value,
                    "updated_at": current_time.isoformat(),
                }
            )
            persisted = self._container.replace_item(
                item=plan.plan_id,
                body=update,
                partition_key=incident_scope_key,
                etag=etag,
                match_condition=MatchConditions.IfNotModified,
            )
            expired.append(EvacuationPlan.model_validate(persisted or update))
        return expired

    def active_plans(
        self,
        incident_id: str,
        incident_scope_key: str,
        *,
        now: datetime | None = None,
    ) -> list[EvacuationPlan]:
        current_time = now or datetime.now(UTC)
        self.expire_due(incident_id, incident_scope_key, now=current_time)
        return [
            plan
            for document in self.list_history(incident_id, incident_scope_key)
            if (plan := EvacuationPlan.model_validate(document)).status in _ACTIVE_STATUSES
        ]

    def latest_active(
        self,
        incident_id: str,
        incident_scope_key: str,
        *,
        now: datetime | None = None,
    ) -> EvacuationPlan | None:
        active = self.active_plans(incident_id, incident_scope_key, now=now)
        return max(active, key=lambda plan: plan.version, default=None)

    def authoritative_plan(
        self,
        incident_id: str,
        incident_scope_key: str,
        *,
        now: datetime | None = None,
    ) -> EvacuationPlan | None:
        active = self.active_plans(incident_id, incident_scope_key, now=now)
        approved = [plan for plan in active if plan.status == PlanStatus.approved]
        if approved:
            return max(approved, key=lambda plan: plan.version)
        paused = [plan for plan in active if plan.status == PlanStatus.paused]
        if paused:
            return max(paused, key=lambda plan: plan.version)
        proposed = [plan for plan in active if plan.status == PlanStatus.proposed]
        return max(proposed, key=lambda plan: plan.version, default=None)

    def active_count(
        self,
        incident_id: str,
        incident_scope_key: str,
        *,
        now: datetime | None = None,
    ) -> int:
        return len(self.active_plans(incident_id, incident_scope_key, now=now))

    def total_active_count(
        self,
        tenant_id: str,
        *,
        now: datetime | None = None,
    ) -> int:
        if self._container is None:
            return 0
        current_time = now or datetime.now(UTC)
        values = self._container.query_items(
            query=(
                "SELECT VALUE COUNT(1) FROM c WHERE IS_DEFINED(c.plan_id) "
                "AND c.tenant_id = @tenant_id "
                "AND c.status IN ('proposed', 'approved', 'paused') "
                "AND (NOT IS_DEFINED(c.valid_until) OR IS_NULL(c.valid_until) "
                "OR c.valid_until > @now)"
            ),
            parameters=[
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@now", "value": current_time.isoformat()},
            ],
            enable_cross_partition_query=True,
        )
        return int(next(iter(values), 0))

    def expire_all_due(self, *, now: datetime | None = None) -> list[EvacuationPlan]:
        if self._container is None:
            return []
        current_time = now or datetime.now(UTC)
        documents = self._container.query_items(
            query=(
                "SELECT * FROM c WHERE IS_DEFINED(c.plan_id) "
                "AND c.status IN ('proposed', 'paused') "
                "AND IS_DEFINED(c.valid_until) AND NOT IS_NULL(c.valid_until) "
                "AND c.valid_until <= @now"
            ),
            parameters=[{"name": "@now", "value": current_time.isoformat()}],
            enable_cross_partition_query=True,
        )
        expired = []
        for document in documents:
            plan = EvacuationPlan.model_validate(document)
            etag = str(document.get("_etag") or "")
            if not etag:
                raise RuntimeError(f"Plan {plan.plan_id} has no concurrency token")
            update = _write_body(document)
            update.update(
                {
                    "status": PlanStatus.expired.value,
                    "updated_at": current_time.isoformat(),
                }
            )
            persisted = self._container.replace_item(
                item=plan.plan_id,
                body=update,
                partition_key=plan.incident_scope_key,
                etag=etag,
                match_condition=MatchConditions.IfNotModified,
            )
            expired.append(EvacuationPlan.model_validate(persisted or update))
        return expired


def _write_body(document: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in document.items() if not key.startswith("_")}


def _is_not_found(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
    return status == 404 or "404" in str(exc) or "NotFound" in type(exc).__name__


__all__ = ["EvacuationPlanRepository"]
