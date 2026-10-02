"""Optimistic concurrency version counter for public alerts.

Uses Cosmos DB etag-based optimistic concurrency to assign monotonically
increasing version numbers per incident. Format: ``ca-{incident_id}-v{N}``

Supports alert lifecycle: supersede, expire, and version history queries.
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import UTC, datetime

from common.async_bridge import run_async
from communication.config import CommunicationConfig

logger = logging.getLogger(__name__)


class VersionConflictError(Exception):
    """Raised when optimistic concurrency check fails after all retries."""


class VersionCounter:
    """Assigns monotonically increasing version numbers with optimistic concurrency.

    Counter documents are stored in Cosmos DB with pattern:
    ``{incident_id}_alert_counter``
    """

    def __init__(
        self,
        config: CommunicationConfig | None = None,
        cosmos_container: object | None = None,
    ) -> None:
        self._config = config or CommunicationConfig()
        self._container = cosmos_container
        self._local_counters: dict[tuple[str, str], int] = {}
        self._local_reservations: dict[tuple[str, str, str], int] = {}
        self._locks: dict[tuple[str, str], asyncio.Lock] = {}

    async def assign_version(
        self,
        incident_id: str,
        tenant_id: str,
        *,
        reservation_key: str | None = None,
    ) -> int:
        """Assign the next version number for an incident.

        Returns the assigned version number (≥ 1).
        """
        key = (tenant_id, incident_id)
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            return await self._assign_locked(incident_id, tenant_id, reservation_key)

    async def _assign_locked(self, incident_id: str, tenant_id: str, reservation_key: str | None) -> int:
        max_retries = self._config.version_conflict_max_retries

        if self._container is None:
            counter_key = (tenant_id, incident_id)
            if reservation_key is not None:
                reserved = self._local_reservations.get((tenant_id, incident_id, reservation_key))
                if reserved is not None:
                    return reserved
            current = self._local_counters.get(counter_key, 0)
            new_version = current + 1
            self._local_counters[counter_key] = new_version
            if reservation_key is not None:
                self._local_reservations[(tenant_id, incident_id, reservation_key)] = new_version
            return new_version

        counter_id = f"{incident_id}_alert_counter"

        for attempt in range(1, max_retries + 1):
            try:
                return await asyncio.to_thread(
                    self._try_increment,
                    counter_id,
                    tenant_id,
                    reservation_key,
                )
            except VersionConflictError:
                logger.warning(
                    "Version conflict on attempt %d/%d for %s",
                    attempt,
                    max_retries,
                    counter_id,
                )
                if attempt < max_retries:
                    jitter = random.uniform(0.05, 0.2) * attempt
                    await asyncio.sleep(jitter)

        logger.error(
            "All %d OCC retries exhausted for %s",
            max_retries,
            counter_id,
        )
        raise VersionConflictError(f"Version allocation exhausted for {counter_id}")

    def format_alert_id(self, incident_id: str, version: int) -> str:
        """Format alert_id as ``ca-{incident_id}-v{N}``."""
        return f"ca-{incident_id}-v{version}"

    def _try_increment(self, counter_id: str, partition_key: str, reservation_key: str | None) -> int:
        """Attempt to read-increment-replace the counter document."""
        try:
            doc = self._container.read_item(
                item=counter_id,
                partition_key=partition_key,
            )
            current_version = doc.get("current_version", 0)
            reservations = dict(doc.get("reservations", {}))
            if reservation_key is not None and reservation_key in reservations:
                return int(reservations[reservation_key])
            etag = doc.get("_etag", "")

            new_version = current_version + 1
            doc["current_version"] = new_version
            if reservation_key is not None:
                reservations[reservation_key] = new_version
                doc["reservations"] = reservations

            self._container.replace_item(
                item=counter_id,
                body=doc,
                if_match=etag,
            )
            return new_version

        except Exception as exc:
            exc_str = str(exc)
            if "404" in exc_str or "NotFound" in exc_str:
                return self._create_counter(counter_id, partition_key, reservation_key)
            if "412" in exc_str or "PreconditionFailed" in exc_str:
                raise VersionConflictError(f"OCC conflict for {counter_id}") from exc
            raise

    def _create_counter(self, counter_id: str, partition_key: str, reservation_key: str | None) -> int:
        """Create a new counter document starting at version 1."""
        doc = {
            "id": counter_id,
            "current_version": 1,
            "tenant_id": partition_key,
            "reservations": {reservation_key: 1} if reservation_key is not None else {},
        }
        try:
            self._container.create_item(body=doc)
            return 1
        except Exception as exc:
            if "409" in str(exc) or "Conflict" in str(exc):
                raise VersionConflictError(f"Concurrent create for {counter_id}") from exc
            raise

    def supersede_previous(
        self,
        incident_id: str,
        current_version: int,
        tenant_id: str = "live",
    ) -> bool:
        """Mark previous active version as superseded per FR-018.

        Returns True if a previous version was superseded.
        """
        if current_version <= 1:
            return False  # No previous version

        previous_version = current_version - 1
        previous_alert_id = self.format_alert_id(incident_id, previous_version)

        if self._container is not None:
            try:
                doc = self._container.read_item(
                    item=previous_alert_id,
                    partition_key=tenant_id,
                )
                current_status = doc.get("status", "")
                # Only supersede active versions
                if current_status in (
                    "delivered",
                    "partially_delivered",
                    "approved",
                    "pending_review",
                    "delivering",
                ):
                    doc["status"] = "superseded"
                    doc["updated_at"] = datetime.now(UTC).isoformat()
                    self._container.upsert_item(body=doc)
                    logger.info("Superseded alert %s (was %s)", previous_alert_id, current_status)
                    return True
            except Exception:
                logger.warning("Failed to supersede %s", previous_alert_id)

        return False

    def create_update_version(
        self,
        incident_id: str,
        change_summary: str,
        tenant_id: str,
    ) -> tuple[int, str]:
        """Create a new update version. Returns (version, alert_id)."""
        version = run_async(self.assign_version(incident_id, tenant_id))
        alert_id = self.format_alert_id(incident_id, version)
        return version, alert_id

    def create_correction_version(
        self,
        incident_id: str,
        original_alert_id: str,
        tenant_id: str,
    ) -> tuple[int, str]:
        """Create a new correction version. Returns (version, alert_id)."""
        version = run_async(self.assign_version(incident_id, tenant_id))
        alert_id = self.format_alert_id(incident_id, version)
        return version, alert_id

    def create_all_clear_version(
        self,
        incident_id: str,
        original_alert_id: str,
        tenant_id: str,
    ) -> tuple[int, str]:
        """Create a new all-clear version. Returns (version, alert_id)."""
        version = run_async(self.assign_version(incident_id, tenant_id))
        alert_id = self.format_alert_id(incident_id, version)
        return version, alert_id

    def expire_alert(
        self,
        alert_id: str,
        tenant_id: str,
    ) -> bool:
        """Transition alert to expired after ALERT_EXPIRY_HOURS.

        Expired is independent of superseded per R-011/CHK024.
        """
        if self._container is not None:
            try:
                doc = self._container.read_item(
                    item=alert_id,
                    partition_key=tenant_id,
                )
                current_status = doc.get("status", "")
                if current_status in ("delivered", "partially_delivered"):
                    doc["status"] = "expired"
                    doc["updated_at"] = datetime.now(UTC).isoformat()
                    self._container.upsert_item(body=doc)
                    return True
            except Exception:
                logger.warning("Failed to expire %s", alert_id)
        return False

    def get_version_history(
        self,
        incident_id: str,
        tenant_id: str,
    ) -> list[dict]:
        """Retrieve all versions for an incident ordered by version number."""
        if self._container is None:
            return []

        try:
            query = "SELECT * FROM c WHERE c.incident_id = @incident_id ORDER BY c.version ASC"
            results = list(
                self._container.query_items(
                    query=query,
                    parameters=[{"name": "@incident_id", "value": incident_id}],
                    partition_key=tenant_id,
                )
            )
            return results
        except Exception:
            logger.warning("Failed to query version history for %s", incident_id)
            return []
