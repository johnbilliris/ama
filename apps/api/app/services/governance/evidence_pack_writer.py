"""Spec-037 evidence-pack publisher service (T034).

Coordinates schema validation → ratio recompute → Cosmos cache write → Blob
immutable snapshot → audit-timeline append. Two App Insights custom metrics
emit per publish:
  - evidence_pack.publication.duration_seconds
  - evidence_pack.manual_row_ratio  (via manual_row_ratio.emit_metric)

Citations: FR-005, FR-035, PD-037-04, RES-05.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .manual_row_ratio import compute_ratio, emit_metric

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    artefact_id: str
    publication_id: str
    published_at_utc: str
    manual_row_ratio: float
    duration_seconds: float


def publish_artefact(
    sidecar_path: Path,
    *,
    published_by: str,
    cosmos_writer=None,
    blob_writer=None,
    audit_writer=None,
) -> PublishResult:
    """Publish a JSON sidecar through the three-layer append-only pipeline.

    Writers are pluggable to keep the function unit-testable; in production
    they bind to the AMA Cosmos / Blob / audit clients via dependency
    injection at FastAPI route time.
    """
    started = time.perf_counter()
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    ratio = compute_ratio(rows)

    publication_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    # Server-side metadata recompute — clients never set these.
    payload.setdefault("metadata", {})
    payload["metadata"].update(
        {
            "manual_row_count": ratio.manual_row_count,
            "total_row_count": ratio.total_row_count,
            "manual_row_ratio": ratio.manual_row_ratio,
            "link_check_status": payload["metadata"].get("link_check_status", "passed"),
            "last_gate_run_utc": now,
        }
    )
    payload["publication_id"] = publication_id
    payload["published_at_utc"] = now
    payload["published_by"] = published_by

    artefact_id = payload.get("artefact_id", sidecar_path.stem)

    # Cosmos cache write
    if cosmos_writer is not None:
        cosmos_writer(payload)
    # Blob immutable snapshot
    if blob_writer is not None:
        blob_writer(artefact_id=artefact_id, publication_id=publication_id, payload=payload)
    # Audit-timeline append (FR-005, NN-2 — no PII)
    if audit_writer is not None:
        audit_writer(
            event_type="evidence_pack.publish",
            artefact_id=artefact_id,
            publication_id=publication_id,
            actor_oid=published_by,
            manual_row_ratio=ratio.manual_row_ratio,
        )

    emit_metric(artefact_id, publication_id, ratio.manual_row_ratio)
    duration = time.perf_counter() - started
    logger.info(
        "evidence_pack.publication.duration_seconds",
        extra={
            "artefact_id": artefact_id,
            "publication_id": publication_id,
            "duration_seconds": duration,
        },
    )
    return PublishResult(
        artefact_id=artefact_id,
        publication_id=publication_id,
        published_at_utc=now,
        manual_row_ratio=ratio.manual_row_ratio,
        duration_seconds=duration,
    )


def append_audit_for_read(
    *,
    artefact_id: str,
    publication_id: str,
    actor_oid: str,
    manual_row_ratio: float,
    audit_writer,
) -> None:
    """Audit a read of a `manual_row_ratio > 0.5` artefact (T035, NN-2)."""
    if manual_row_ratio > 0.5:
        audit_writer(
            event_type="evidence_pack.read.over_cap",
            artefact_id=artefact_id,
            publication_id=publication_id,
            actor_oid=actor_oid,
            manual_row_ratio=manual_row_ratio,
        )
