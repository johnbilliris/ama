"""spec-038 — append-only audit event emitter.

Centralises the call sites that emit named audit events
(``audit.snapshot_published``, ``audit.snapshot_rollback``,
``audit.transcript_reconstructed``, ``audit.support_handoff_unack_timeout``,
``audit.chat_refusal``, ``audit.fabrication_audit_hit``). All five new
event names are reserved by spec-038 T-AA090.

The helper logs at INFO and tags the current OpenTelemetry span via
:func:`record_audit_outcome` so AppInsights queries can correlate events to
traces. When OTel is not initialised the helper is a no-op other than the
logger line — safe at import time.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .audit_span import record_audit_outcome

logger = logging.getLogger("ama.audit")

# Reserved spec-038 event names.
SPEC038_EVENTS = frozenset(
    {
        "audit.snapshot_published",
        "audit.snapshot_rollback",
        "audit.transcript_reconstructed",
        "audit.support_handoff_unack_timeout",
        "audit.chat_refusal",
        "audit.fabrication_audit_hit",
    }
)


def emit_audit_event(name: str, payload: dict[str, Any]) -> None:
    """Emit one append-only audit event named ``name`` with ``payload``."""
    if not name.startswith("audit."):
        raise ValueError("audit event names must start with 'audit.'")
    record_audit_outcome(name, attributes={"payload_bytes": len(json.dumps(payload, default=str))})
    logger.info("AUDIT %s %s", name, json.dumps(payload, default=str))


__all__ = ["emit_audit_event", "SPEC038_EVENTS"]
