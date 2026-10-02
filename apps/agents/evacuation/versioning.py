"""Atomic scoped version reservation for evacuation plans."""

from __future__ import annotations

import asyncio
import logging
import random
import threading
from collections.abc import Awaitable, Callable

from azure.core import MatchConditions

logger = logging.getLogger(__name__)


class VersionConflictError(RuntimeError):
    """A concurrent writer changed or created the version counter."""


class VersionReservationError(RuntimeError):
    """No unique persisted version could be reserved within the retry budget."""


class VersionCounter:
    """Reserve monotonically increasing versions per tenant/incident scope."""

    def __init__(
        self,
        cosmos_container: object | None = None,
        *,
        max_retries: int = 5,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        jitter: Callable[[float, float], float] = random.uniform,
    ) -> None:
        self._container = cosmos_container
        self._max_retries = max_retries
        self._sleep = sleep
        self._jitter = jitter
        self._local_versions: dict[str, int] = {}
        self._local_lock = threading.Lock()

    async def assign_version(
        self,
        incident_id: str,
        incident_scope_key: str = "",
    ) -> int:
        """Return a uniquely reserved integer or raise without fabricating one."""
        if self._container is None:
            scope = incident_scope_key or incident_id
            with self._local_lock:
                version = self._local_versions.get(scope, 0) + 1
                self._local_versions[scope] = version
                return version

        counter_id = f"{incident_id}_plan_counter"
        for attempt in range(1, self._max_retries + 1):
            try:
                return self._try_increment(counter_id, incident_scope_key)
            except VersionConflictError as exc:
                if attempt >= self._max_retries:
                    raise VersionReservationError(
                        f"Version reservation exhausted for {counter_id} after {attempt} attempts"
                    ) from exc
                delay = min(0.4, 0.05 * (2 ** (attempt - 1)))
                await self._sleep(self._jitter(delay * 0.8, delay * 1.2))
        raise VersionReservationError(f"Version reservation failed for {counter_id}")

    def format_plan_id(self, incident_id: str, version: int) -> str:
        return f"ep-{incident_id}-v{version}"

    def _try_increment(self, counter_id: str, partition_key: str) -> int:
        try:
            document = self._container.read_item(
                item=counter_id,
                partition_key=partition_key,
            )
        except Exception as exc:
            if _status_code(exc) == 404:
                return self._create_counter(counter_id, partition_key)
            raise VersionReservationError(f"Failed to read version counter {counter_id}") from exc

        etag = str(document.get("_etag") or "")
        if not etag:
            raise VersionReservationError(f"Version counter {counter_id} has no concurrency token")
        try:
            current_version = int(document.get("current_version", 0))
        except (TypeError, ValueError) as exc:
            raise VersionReservationError(f"Version counter {counter_id} is malformed") from exc
        if current_version < 0:
            raise VersionReservationError(f"Version counter {counter_id} cannot be negative")

        version = current_version + 1
        body = {key: value for key, value in document.items() if not key.startswith("_")}
        body["current_version"] = version
        body["last_reserved_version"] = version
        body.setdefault("orphaned_versions", [])
        body.setdefault("uncertain_versions", [])
        body["incident_scope_key"] = partition_key
        try:
            self._container.replace_item(
                item=counter_id,
                body=body,
                etag=etag,
                match_condition=MatchConditions.IfNotModified,
            )
        except Exception as exc:
            if _status_code(exc) in {409, 412}:
                raise VersionConflictError(f"Concurrent reservation for {counter_id}") from exc
            raise VersionReservationError(f"Failed to reserve version for {counter_id}") from exc
        return version

    def _create_counter(self, counter_id: str, partition_key: str) -> int:
        document = {
            "id": counter_id,
            "current_version": 1,
            "last_reserved_version": 1,
            "orphaned_versions": [],
            "uncertain_versions": [],
            "incident_scope_key": partition_key,
        }
        try:
            self._container.create_item(body=document)
        except Exception as exc:
            if _status_code(exc) == 409:
                raise VersionConflictError(f"Concurrent counter creation for {counter_id}") from exc
            raise VersionReservationError(f"Failed to create version counter {counter_id}") from exc
        return 1

    def record_gap(
        self,
        incident_id: str,
        incident_scope_key: str,
        version: int,
        *,
        uncertain: bool,
        reason: str,
    ) -> None:
        """Record a reserved version that did not reach confirmed readability."""
        if self._container is None:
            return
        counter_id = f"{incident_id}_plan_counter"
        field = "uncertain_versions" if uncertain else "orphaned_versions"
        for _ in range(self._max_retries):
            try:
                document = self._container.read_item(
                    item=counter_id,
                    partition_key=incident_scope_key,
                )
            except Exception as exc:
                raise VersionReservationError(f"Failed to read version counter gap state for {counter_id}") from exc
            etag = str(document.get("_etag") or "")
            if not etag:
                raise VersionReservationError(f"Version counter {counter_id} has no concurrency token")
            entries = [entry for entry in document.get(field, []) if int(entry.get("version", -1)) != version]
            entries.append({"version": version, "reason": reason})
            body = {key: value for key, value in document.items() if not key.startswith("_")}
            body[field] = entries[-100:]
            try:
                self._container.replace_item(
                    item=counter_id,
                    body=body,
                    etag=etag,
                    match_condition=MatchConditions.IfNotModified,
                )
                return
            except Exception as exc:
                if _status_code(exc) == 412:
                    continue
                raise VersionReservationError(f"Failed to record version gap for {counter_id}") from exc
        raise VersionReservationError(f"Version gap recording exhausted for {counter_id}")


def _status_code(exc: Exception) -> int | None:
    status = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
    if isinstance(status, int):
        return status
    text = f"{type(exc).__name__} {exc}"
    for candidate in (404, 409, 412, 429, 500, 502, 503, 504):
        if str(candidate) in text:
            return candidate
    if "NotFound" in text:
        return 404
    if "PreconditionFailed" in text:
        return 412
    if "Conflict" in text:
        return 409
    return None
