"""Optimistic concurrency version counter for evacuation plans.

Uses Cosmos DB etag-based optimistic concurrency to assign monotonically
increasing version numbers per incident combination.
"""

from __future__ import annotations

import logging
import random
import time
from uuid import uuid4

logger = logging.getLogger(__name__)

# Maximum OCC retries before falling back to UUID-suffixed version
_MAX_RETRIES = 3


class VersionConflictError(Exception):
    """Raised when optimistic concurrency check fails after all retries."""


class VersionCounter:
    """Assigns monotonically increasing version numbers with optimistic concurrency.

    Counter documents are stored in Cosmos DB with pattern:
    ``{incident_id}_plan_counter``

    Concurrency pattern:
    1. Read counter + _etag
    2. Increment current_version
    3. replace_item with If-Match: {_etag}
    4. On 412 Precondition Failed: re-read, re-increment, retry (max 3)
    """

    def __init__(self, cosmos_container: object | None = None) -> None:
        self._container = cosmos_container

    def assign_version(
        self,
        incident_id: str,
        incident_scope_key: str = "",
    ) -> int:
        """Assign the next version number for an incident.

        Returns the assigned version number (≥ 1).
        Falls back to a UUID-suffixed version number if all retries exhausted.
        """
        if self._container is None:
            # No Cosmos DB — return version 1 (for testing/local dev)
            return 1

        counter_id = f"{incident_id}_plan_counter"

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                return self._try_increment(counter_id, incident_scope_key)
            except VersionConflictError:
                logger.warning(
                    "Version conflict on attempt %d/%d for %s",
                    attempt, _MAX_RETRIES, counter_id,
                )
                if attempt < _MAX_RETRIES:
                    # Jittered backoff
                    jitter = random.uniform(0.05, 0.2) * attempt
                    time.sleep(jitter)

        # Exhausted retries — fallback to UUID-suffixed version
        logger.error(
            "All %d OCC retries exhausted for %s; using UUID fallback",
            _MAX_RETRIES, counter_id,
        )
        return self._fallback_version(counter_id, incident_scope_key)

    def format_plan_id(self, incident_id: str, version: int) -> str:
        """Format a plan ID string from incident ID and version number."""
        return f"ep-{incident_id}-v{version}"

    def _try_increment(self, counter_id: str, partition_key: str) -> int:
        """Attempt to read-increment-replace the counter document."""
        try:
            # Read existing counter
            doc = self._container.read_item(
                item=counter_id,
                partition_key=partition_key,
            )
            current_version = doc.get("current_version", 0)
            etag = doc.get("_etag", "")

            new_version = current_version + 1
            doc["current_version"] = new_version

            # Replace with etag check
            self._container.replace_item(
                item=counter_id,
                body=doc,
                if_match=etag,
            )
            return new_version

        except Exception as exc:
            exc_str = str(exc)
            # Check for 404 — counter doesn't exist yet
            if "404" in exc_str or "NotFound" in exc_str:
                return self._create_counter(counter_id, partition_key)
            # Check for 412 — optimistic concurrency failure
            if "412" in exc_str or "PreconditionFailed" in exc_str:
                raise VersionConflictError(f"OCC conflict for {counter_id}") from exc
            raise

    def _create_counter(self, counter_id: str, partition_key: str) -> int:
        """Create a new counter document starting at version 1."""
        doc = {
            "id": counter_id,
            "current_version": 1,
            "incident_scope_key": partition_key,
        }
        try:
            self._container.create_item(body=doc)
            return 1
        except Exception as exc:
            # If another instance already created it, try increment
            if "409" in str(exc) or "Conflict" in str(exc):
                raise VersionConflictError(f"Concurrent create for {counter_id}") from exc
            raise

    def _fallback_version(self, counter_id: str, partition_key: str) -> int:
        """Generate a fallback version using UUID suffix to avoid collision."""
        # Read current version if possible, or default to 1
        try:
            doc = self._container.read_item(
                item=counter_id,
                partition_key=partition_key,
            )
            return doc.get("current_version", 0) + 1
        except Exception:
            return 1
