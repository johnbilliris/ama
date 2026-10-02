from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from .._clients import EvidenceClientRegistry

logger = logging.getLogger(__name__)

CHECKPOINT_KIND = "audit_mirror_checkpoint"
DLQ_KIND = "audit_mirror_failure"
HEARTBEAT_KIND = "audit_mirror_heartbeat"


def mirror_batch(
    *,
    registry: EvidenceClientRegistry,
    batch_size: int = 100,
) -> int:
    if batch_size < 1 or batch_size > 1000:
        raise ValueError("batch_size must be between 1 and 1000")

    checkpoint = _latest_checkpoint(registry)
    audit = registry.get("evidence_audit")
    items, continuation = audit.read_change_feed_page(
        continuation=checkpoint,
        max_item_count=batch_size,
    )
    if not items:
        _record_heartbeat(registry)
        return 0

    for item in items:
        mirror_payload = {key: value for key, value in item.items() if not key.startswith("_")}
        try:
            registry.blob_archive.create_json(
                _blob_name(mirror_payload),
                mirror_payload,
                metadata={
                    "audit_id": str(mirror_payload["audit_id"]),
                    "entry_id": str(mirror_payload["id"]),
                    "payload_sha256": str(mirror_payload["payload_sha256"]),
                },
            )
        except Exception as exc:
            _record_dlq(registry, mirror_payload, exc)
            raise

    if continuation is not None and continuation != checkpoint:
        _record_checkpoint(registry, continuation)
    _record_heartbeat(registry)
    return len(items)


async def run_mirror_loop(
    *,
    registry: EvidenceClientRegistry,
    batch_size: int = 100,
    stop_event: asyncio.Event | None = None,
) -> None:
    interval = float(os.environ.get("AUDIT_MIRROR_INTERVAL_S", "5"))
    if interval <= 0:
        raise ValueError("AUDIT_MIRROR_INTERVAL_S must be greater than zero")

    while stop_event is None or not stop_event.is_set():
        try:
            mirror_batch(registry=registry, batch_size=batch_size)
        except Exception:
            logger.exception("audit mirror batch failed; checkpoint was not advanced")
        if stop_event is not None:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except TimeoutError:
                continue
        else:
            await asyncio.sleep(interval)


def _latest_checkpoint(registry: EvidenceClientRegistry) -> str | None:
    rows = [row for row in registry.get("evidence_audit_dlq").all() if row.get("kind") == CHECKPOINT_KIND]
    if not rows:
        return None
    latest = max(rows, key=lambda row: str(row.get("recorded_at", "")))
    return str(latest["continuation"])


def _record_checkpoint(
    registry: EvidenceClientRegistry,
    continuation: str,
) -> None:
    digest = hashlib.sha256(continuation.encode("utf-8")).hexdigest()[:20]
    registry.get("evidence_audit_dlq").create_item(
        {
            "id": f"checkpoint-{digest}",
            "audit_id": "audit-mirror",
            "kind": CHECKPOINT_KIND,
            "continuation": continuation,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
    )


def _record_heartbeat(registry: EvidenceClientRegistry) -> None:
    now = datetime.now(UTC)
    registry.get("evidence_audit_dlq").create_item(
        {
            "id": f"heartbeat-{now.timestamp():.6f}",
            "audit_id": "audit-mirror",
            "kind": HEARTBEAT_KIND,
            "recorded_at": now.isoformat(),
        }
    )


def _record_dlq(
    registry: EvidenceClientRegistry,
    item: dict[str, Any],
    error: Exception,
) -> None:
    payload = json.dumps(
        item,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    failure_id = f"mirror-failure-{item.get('id', 'unknown')}-{digest}"
    dlq = registry.get("evidence_audit_dlq")
    try:
        dlq.create_item(
            {
                "id": failure_id,
                "audit_id": str(item.get("audit_id", "audit-mirror")),
                "kind": DLQ_KIND,
                "original_id": str(item.get("id", "")),
                "error_type": type(error).__name__,
                "failed_at": datetime.now(UTC).isoformat(),
            }
        )
    except Exception as dlq_error:
        try:
            existing = dlq.read_item(
                failure_id,
                partition_key=str(item.get("audit_id", "audit-mirror")),
            )
        except Exception:
            raise RuntimeError("audit mirror and DLQ persistence both failed") from dlq_error
        if existing.get("original_id") != item.get("id"):
            raise RuntimeError("audit mirror DLQ id collision") from dlq_error


def _blob_name(item: dict[str, Any]) -> str:
    occurred = str(item.get("occurred_at", "")).replace(":", "-")
    return f"audit/{item['audit_id']}/{occurred[:10]}/{item['id']}.json"
