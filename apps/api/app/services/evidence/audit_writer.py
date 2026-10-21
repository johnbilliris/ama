from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._clients import BlobWriteReceipt, EvidenceClientRegistry, get_registry
from ._problem_details import ProblemDetails

logger = logging.getLogger(__name__)

RETRY_DELAYS_SECONDS = (0.0, 0.25, 1.0)
END_TO_END_BUDGET_SECONDS = 5.5


@dataclass(frozen=True)
class DurableAuditReceipt:
    entry: dict[str, Any]
    source_etag: str
    activity_id: str
    session_token: str
    blob: BlobWriteReceipt


class AuditWriteUnavailableError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Durable audit storage is unavailable.")

    def to_problem_details(self) -> ProblemDetails:
        return ProblemDetails.of(
            status=503,
            title="audit-write-unavailable",
            detail="The required durable audit receipt could not be recorded.",
            type="https://ama.example/errors/audit-write-unavailable",
        )


async def write_audit_entry(
    entry: dict[str, Any],
    *,
    registry: EvidenceClientRegistry | None = None,
) -> DurableAuditReceipt:
    return await asyncio.to_thread(
        write_audit_entry_sync,
        entry,
        registry=registry,
    )


def write_audit_entry_sync(
    entry: dict[str, Any],
    *,
    registry: EvidenceClientRegistry | None = None,
) -> DurableAuditReceipt:
    clients = registry or get_registry()
    canonical_entry = _with_payload_hash(entry)
    started = time.monotonic()
    last_transient: Exception | None = None

    for attempt, delay in enumerate(RETRY_DELAYS_SECONDS, start=1):
        if delay:
            remaining = END_TO_END_BUDGET_SECONDS - (time.monotonic() - started)
            if remaining <= delay:
                break
            time.sleep(delay)
        try:
            receipt = _write_once(canonical_entry, clients)
            logger.debug(
                "durable audit write succeeded",
                extra={"audit_id": canonical_entry["id"], "attempt": attempt},
            )
            return receipt
        except Exception as exc:
            if not _is_transient(exc):
                logger.error(
                    "durable audit write failed permanently",
                    extra={
                        "audit_id": canonical_entry.get("id"),
                        "attempt": attempt,
                        "error_type": type(exc).__name__,
                    },
                )
                raise AuditWriteUnavailableError() from exc
            last_transient = exc
            logger.warning(
                "durable audit write transient failure",
                extra={
                    "audit_id": canonical_entry.get("id"),
                    "attempt": attempt,
                    "error_type": type(exc).__name__,
                },
            )
            if time.monotonic() - started >= END_TO_END_BUDGET_SECONDS:
                break

    logger.error(
        "durable audit write exhausted",
        extra={
            "audit_id": canonical_entry.get("id"),
            "error_type": type(last_transient).__name__ if last_transient else "budget_exhausted",
        },
    )
    raise AuditWriteUnavailableError() from last_transient


def _write_once(
    entry: dict[str, Any],
    registry: EvidenceClientRegistry,
) -> DurableAuditReceipt:
    response_headers: dict[str, str] = {}

    def capture_headers(
        headers: Mapping[str, str],
        _: dict[str, Any],
    ) -> None:
        response_headers.update({str(key).lower(): str(value) for key, value in headers.items()})

    container = registry.get("evidence_audit")
    try:
        persisted = container.create_item(
            entry,
            response_hook=capture_headers,
        )
    except Exception as exc:
        if not _is_conflict(exc):
            raise
        persisted = container.read_item(
            entry["id"],
            partition_key=entry["audit_id"],
        )
        if persisted.get("payload_sha256") != entry["payload_sha256"]:
            raise RuntimeError("audit id collision with mismatched payload") from exc

    blob_name = _blob_name(entry)
    blob_receipt = registry.blob_archive.create_json(
        blob_name,
        entry,
        metadata={
            "audit_id": str(entry["audit_id"]),
            "entry_id": str(entry["id"]),
            "payload_sha256": str(entry["payload_sha256"]),
        },
    )
    return DurableAuditReceipt(
        entry=dict(persisted),
        source_etag=str(response_headers.get("etag") or persisted.get("_etag") or ""),
        activity_id=response_headers.get("x-ms-activity-id", ""),
        session_token=response_headers.get("x-ms-session-token", ""),
        blob=blob_receipt,
    )


def _with_payload_hash(entry: dict[str, Any]) -> dict[str, Any]:
    canonical = dict(entry)
    canonical.pop("payload_sha256", None)
    payload = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    canonical["payload_sha256"] = hashlib.sha256(payload).hexdigest()
    return canonical


def _blob_name(entry: Mapping[str, Any]) -> str:
    occurred = str(entry.get("occurred_at", "")).replace(":", "-")
    return f"audit/{entry['audit_id']}/{occurred[:10]}/{entry['id']}.json"


def _is_conflict(exc: Exception) -> bool:
    return isinstance(exc, PermissionError) or getattr(exc, "status_code", None) == 409


def _is_transient(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status is not None:
        return status in {408, 429} or 500 <= int(status) < 600
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    try:
        from azure.core.exceptions import ServiceRequestError, ServiceResponseError

        return isinstance(exc, (ServiceRequestError, ServiceResponseError))
    except ImportError:
        return False
