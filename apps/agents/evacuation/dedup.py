"""Tenant-scoped local and durable handoff processing claims."""

from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from uuid import uuid4

from azure.core import MatchConditions
from evacuation.models import (
    EvacuationPlan,
    HandoffClaimStatus,
    HandoffProcessingClaim,
)

logger = logging.getLogger(__name__)


class HandoffClaimInProgressError(RuntimeError):
    """Raised when another replica owns an unexpired processing claim."""


class HandoffClaimStoreError(RuntimeError):
    """Raised when a durable claim cannot be read or changed safely."""


@dataclass(frozen=True)
class HandoffClaimResult:
    acquired: bool
    completed: bool = False
    rejected: bool = False
    plan_id: str | None = None


class HandoffDeduplicator:
    """Bounded tenant-aware claims with optional Cosmos replica coordination."""

    def __init__(
        self,
        window_minutes: int = 10,
        max_size: int = 100_000,
        *,
        cosmos_container: Any = None,
        lease_seconds: int = 300,
        monotonic: Any = time.monotonic,
        now: Any = lambda: datetime.now(UTC),
        owner_id: str | None = None,
    ) -> None:
        self._window_seconds = window_minutes * 60
        self._max_size = max_size
        self._container = cosmos_container
        self._lease_seconds = lease_seconds
        self._monotonic = monotonic
        self._now = now
        self._owner_id = owner_id or uuid4().hex
        self._cache: OrderedDict[str, float] = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def _scope_key(tenant_id: str, incident_id: str, handoff_id: str) -> str:
        return f"{tenant_id}:{incident_id}:{handoff_id}"

    @staticmethod
    def _claim_id(tenant_id: str, incident_id: str, handoff_id: str) -> str:
        digest = sha256(f"{tenant_id}\0{incident_id}\0{handoff_id}".encode()).hexdigest()
        return f"handoff-claim-{digest}"

    def _evict_expired(self, now: float | None = None) -> None:
        current = self._monotonic() if now is None else now
        cutoff = current - self._window_seconds
        while self._cache:
            key, timestamp = next(iter(self._cache.items()))
            if timestamp < cutoff:
                self._cache.pop(key)
            else:
                break

    def try_claim(
        self,
        tenant_id: str,
        incident_id: str,
        handoff_id: str,
        incident_scope_key: str,
    ) -> HandoffClaimResult:
        if self._container is None:
            return self._try_local_claim(tenant_id, incident_id, handoff_id)
        return self._try_durable_claim(
            tenant_id,
            incident_id,
            handoff_id,
            incident_scope_key,
        )

    def _try_local_claim(
        self,
        tenant_id: str,
        incident_id: str,
        handoff_id: str,
    ) -> HandoffClaimResult:
        key = self._scope_key(tenant_id, incident_id, handoff_id)
        with self._lock:
            now = self._monotonic()
            self._evict_expired(now)
            if key in self._cache:
                return HandoffClaimResult(acquired=False, completed=True)
            self._cache[key] = now
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)
        return HandoffClaimResult(acquired=True)

    def _try_durable_claim(
        self,
        tenant_id: str,
        incident_id: str,
        handoff_id: str,
        incident_scope_key: str,
    ) -> HandoffClaimResult:
        now = self._now()
        claim_id = self._claim_id(tenant_id, incident_id, handoff_id)
        claim = HandoffProcessingClaim(
            id=claim_id,
            handoff_id=handoff_id,
            incident_id=incident_id,
            tenant_id=tenant_id,
            incident_scope_key=incident_scope_key,
            owner_id=self._owner_id,
            claimed_at=now,
            lease_expires_at=now + timedelta(seconds=self._lease_seconds),
            ttl=self._window_seconds,
        )
        try:
            self._container.create_item(body=claim.model_dump(mode="json"))
            return HandoffClaimResult(acquired=True)
        except Exception as exc:
            if not _is_conflict(exc):
                raise HandoffClaimStoreError("Failed to create handoff claim") from exc

        document = self._read_claim(claim_id, incident_scope_key)
        status = HandoffClaimStatus(document.get("status", HandoffClaimStatus.processing))
        if status in {HandoffClaimStatus.completed, HandoffClaimStatus.rejected}:
            return HandoffClaimResult(
                acquired=False,
                completed=status == HandoffClaimStatus.completed,
                rejected=status == HandoffClaimStatus.rejected,
                plan_id=document.get("plan_id"),
            )
        plan_id = str(document.get("plan_id") or "")
        if plan_id and self._plan_exists(plan_id, incident_scope_key):
            self._transition(
                document,
                HandoffClaimStatus.completed,
                plan_id=plan_id,
            )
            return HandoffClaimResult(
                acquired=False,
                completed=True,
                plan_id=plan_id,
            )

        lease_expires_at = _parse_datetime(document.get("lease_expires_at"))
        if status == HandoffClaimStatus.processing and lease_expires_at > now:
            raise HandoffClaimInProgressError(f"Handoff {handoff_id} is already processing")
        takeover = dict(document)
        takeover.update(
            {
                "status": HandoffClaimStatus.processing.value,
                "owner_id": self._owner_id,
                "claimed_at": now.isoformat(),
                "lease_expires_at": (now + timedelta(seconds=self._lease_seconds)).isoformat(),
                "completed_at": None,
                "failure_reason": None,
                "plan_id": None,
            }
        )
        self._replace(document, takeover)
        return HandoffClaimResult(acquired=True)

    def assign_plan_id(
        self,
        tenant_id: str,
        incident_id: str,
        handoff_id: str,
        incident_scope_key: str,
        plan_id: str,
    ) -> None:
        if self._container is None:
            return
        document = self._read_claim(
            self._claim_id(tenant_id, incident_id, handoff_id),
            incident_scope_key,
        )
        self._require_ownership(document)
        update = dict(document)
        update["plan_id"] = plan_id
        self._replace(document, update)

    def complete(
        self,
        tenant_id: str,
        incident_id: str,
        handoff_id: str,
        incident_scope_key: str,
        plan_id: str,
    ) -> None:
        if self._container is None:
            return
        document = self._read_claim(
            self._claim_id(tenant_id, incident_id, handoff_id),
            incident_scope_key,
        )
        if document.get("status") == HandoffClaimStatus.completed.value:
            return
        self._require_ownership(document)
        self._transition(document, HandoffClaimStatus.completed, plan_id=plan_id)

    def reject(
        self,
        tenant_id: str,
        incident_id: str,
        handoff_id: str,
        incident_scope_key: str,
        reason: str,
    ) -> None:
        if self._container is None:
            return
        document = self._read_claim(
            self._claim_id(tenant_id, incident_id, handoff_id),
            incident_scope_key,
        )
        self._require_ownership(document)
        self._transition(
            document,
            HandoffClaimStatus.rejected,
            failure_reason=reason,
        )

    def release(
        self,
        handoff_id: str,
        *,
        tenant_id: str = "live",
        incident_id: str = "",
        incident_scope_key: str = "",
        reason: str = "retryable processing failure",
    ) -> None:
        if self._container is None:
            key = self._scope_key(tenant_id, incident_id, handoff_id)
            with self._lock:
                self._cache.pop(key, None)
                if not incident_id:
                    suffix = f":{handoff_id}"
                    for candidate in list(self._cache):
                        if candidate.endswith(suffix):
                            self._cache.pop(candidate, None)
            return
        document = self._read_claim(
            self._claim_id(tenant_id, incident_id, handoff_id),
            incident_scope_key,
        )
        if document.get("status") == HandoffClaimStatus.completed.value:
            return
        if document.get("owner_id") != self._owner_id:
            return
        self._transition(
            document,
            HandoffClaimStatus.abandoned,
            failure_reason=reason,
        )

    def is_duplicate(
        self,
        handoff_id: str,
        *,
        tenant_id: str = "live",
        incident_id: str = "",
        incident_scope_key: str = "",
    ) -> bool:
        return not self.try_claim(
            tenant_id,
            incident_id,
            handoff_id,
            incident_scope_key or f"{tenant_id}:{incident_id}",
        ).acquired

    def _read_claim(self, claim_id: str, partition_key: str) -> dict[str, Any]:
        try:
            return self._container.read_item(
                item=claim_id,
                partition_key=partition_key,
            )
        except Exception as exc:
            raise HandoffClaimStoreError("Failed to read handoff claim") from exc

    def _require_ownership(self, document: dict[str, Any]) -> None:
        if document.get("owner_id") != self._owner_id:
            raise HandoffClaimInProgressError("Another replica owns the handoff claim")

    def _plan_exists(self, plan_id: str, partition_key: str) -> bool:
        try:
            document = self._container.read_item(
                item=plan_id,
                partition_key=partition_key,
            )
        except Exception as exc:
            if _is_not_found(exc):
                return False
            raise HandoffClaimStoreError("Failed to recover claimed plan") from exc
        try:
            plan = EvacuationPlan.model_validate(document)
        except (TypeError, ValueError) as exc:
            raise HandoffClaimStoreError("Recovered claimed plan is invalid") from exc
        if plan.plan_id != plan_id or plan.incident_scope_key != partition_key:
            raise HandoffClaimStoreError("Recovered claimed plan has the wrong scope")
        return True

    def _transition(
        self,
        document: dict[str, Any],
        status: HandoffClaimStatus,
        *,
        plan_id: str | None = None,
        failure_reason: str | None = None,
    ) -> None:
        update = dict(document)
        update["status"] = status.value
        update["completed_at"] = self._now().isoformat()
        if plan_id is not None:
            update["plan_id"] = plan_id
        update["failure_reason"] = failure_reason
        self._replace(document, update)

    def _replace(self, source: dict[str, Any], update: dict[str, Any]) -> None:
        etag = source.get("_etag")
        if not etag:
            raise HandoffClaimStoreError("Handoff claim has no concurrency token")
        body = {key: value for key, value in update.items() if not key.startswith("_")}
        try:
            self._container.replace_item(
                item=source["id"],
                body=body,
                etag=etag,
                match_condition=MatchConditions.IfNotModified,
            )
        except Exception as exc:
            raise HandoffClaimStoreError("Failed to transition handoff claim") from exc

    @property
    def size(self) -> int:
        with self._lock:
            self._evict_expired()
            return len(self._cache)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _is_conflict(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
    return status_code == 409 or "409" in str(exc) or "Conflict" in type(exc).__name__


def _is_not_found(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
    return status_code == 404 or "404" in str(exc) or "NotFound" in type(exc).__name__
