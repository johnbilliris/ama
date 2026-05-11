"""Audit export — NDJSON gzip + SHA-256 sibling digest (T-H06 / FR-049).

Produces an export bundle from the in-memory or Cosmos-backed audit
store filtered by ``simulation_id``, ``entry_types``, and a
``time_range``. Returns the gzipped NDJSON body and the SHA-256 digest
in lock-step (one-doc-per-line, deterministic line ordering by
``sequence_number``).

Carve-out flag (Constitution v1.2.0 §Non-Negotiable #2): any entry
whose ``model_deployment`` field indicates a non-AU endpoint is tagged
``carve_out_review_required`` in the exported document — callers MUST
ensure the Foundry carve-out registry's ``review_date`` is honoured.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    AuditEnvelope,
)

logger = logging.getLogger(__name__)

AU_REGION_PREFIXES = ("australiaeast", "australia-east", "australiacentral")


@dataclass(frozen=True)
class ExportBundle:
    body: bytes
    """Gzipped NDJSON body."""

    sha256: str
    """Hex-digest of the *gzipped* body — written as the sibling ``.sha256`` file."""

    line_count: int


def _is_au_deployment(model_deployment: str | None) -> bool:
    if not model_deployment:
        return True  # absence of metadata -> default to safe
    needle = model_deployment.lower()
    return any(p in needle for p in AU_REGION_PREFIXES)


def _to_export_dict(env: AuditEnvelope) -> dict[str, Any]:
    """Serialise an envelope and tag carve-out review when relevant."""
    raw = env.model_dump(mode="json", by_alias=True)
    details = raw.get("details", {})
    model_deployment = None
    if isinstance(details, dict):
        model_deployment = details.get("model_deployment")
    if not _is_au_deployment(model_deployment):
        raw["carve_out_review_required"] = True
        raw["carve_out_reason"] = f"non-AU model_deployment={model_deployment!r}"
    return raw


def build_export(
    *,
    audit_entries: Iterable[AuditEnvelope],
    simulation_id: str,
    entry_types: Iterable[str] | None = None,
    time_range: tuple[datetime | None, datetime | None] | None = None,
) -> ExportBundle:
    allowed_types = set(entry_types) if entry_types is not None else None
    start, end = time_range if time_range is not None else (None, None)

    matched = [e for e in audit_entries if e.simulation_id == simulation_id]
    if allowed_types is not None:
        matched = [e for e in matched if e.entry_type in allowed_types]
    if start is not None:
        matched = [e for e in matched if e.timestamp >= start]
    if end is not None:
        matched = [e for e in matched if e.timestamp <= end]

    matched.sort(key=lambda e: e.sequence_number)

    lines = [json.dumps(_to_export_dict(e), default=str, separators=(",", ":")) for e in matched]
    ndjson = "\n".join(lines).encode("utf-8")
    body = gzip.compress(ndjson)
    digest = hashlib.sha256(body).hexdigest()
    return ExportBundle(body=body, sha256=digest, line_count=len(lines))


__all__ = ["ExportBundle", "build_export"]
