"""Spec 036 / Phase F (T199) — Cultural Authority post-retrieval gate.

Per Pass 2 Q-P2-02 + ADR-12, the cultural-authority gate is invoked
**post-retrieval, in-process** between the AI Search round-trip
(``T060``) and Foundry inference (``T075..T077``). It applies uniformly
to all five grounded agents (Monitoring, RiskAssessment, Evacuation,
ResourceAllocation, Communication) and the Simulation Controller —
that's why the gate lives at the retrieval-result layer, not inside any
single agent.

Behaviour summary:

  - Public chunks (``cultural_authority_required != true``) are NEVER
    suppressed (Constitution Principle I no-silencing).
  - Protected chunks (``cultural_authority_required == true``) are
    suppressed UNLESS the operator has a current, non-revoked consent
    in the cultural-authority registry covering the chunk's
    ``cultural_classification`` scope.
  - Registry unreachable → fail closed for protected chunks; emit
    ``cultural_authority_registry_unavailable`` (already emitted by the
    registry client). Public chunks remain retrievable.

The gate emits one ``cultural_authority_check_result`` audit entry per
chunk evaluated (cross-cluster matrix A2→A5, T163 sink), so post-hoc
audit replay can confirm gating decisions per Constitution Principle IV.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from typing import Any

from apps.agents.common.cultural_authority_registry import (
    CulturalAuthorityRegistry,
    CulturalAuthorityRegistryUnavailableError,
)

logger = logging.getLogger(__name__)


def _chunk_get(chunk: Any, key: str, default: Any = None) -> Any:
    if isinstance(chunk, dict):
        return chunk.get(key, default)
    return getattr(chunk, key, default)


def apply_cultural_authority_gate(
    chunks: Iterable[Any],
    *,
    operator_id: str,
    registry: CulturalAuthorityRegistry,
    audit_sink: Callable[[dict[str, Any]], None] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> list[Any]:
    """Filter ``chunks`` per cultural-authority gating rules.

    Returns the chunks that survive the gate. Suppressed protected chunks
    emit ``cultural_authority_gate_blocked``; allowed protected chunks
    emit ``cultural_authority_gate_allowed``; public chunks pass through
    silently. Registry-unavailable on a protected chunk emits
    ``cultural_authority_registry_unavailable_blocked`` and the chunk is
    suppressed.
    """
    now = (now_fn or (lambda: datetime.now(tz=UTC)))()
    out: list[Any] = []

    for chunk in chunks:
        protected = bool(_chunk_get(chunk, "cultural_authority_required", False))
        classification = _chunk_get(chunk, "cultural_classification", "public") or "public"

        if not protected:
            out.append(chunk)
            continue

        # Protected chunk path.
        try:
            allowed = registry.is_consent_current(
                operator_id=operator_id,
                required_scope=_classification_to_scope(classification),
                now=now,
            )
        except CulturalAuthorityRegistryUnavailableError:
            _emit(
                audit_sink,
                {
                    "event_type": "cultural_authority_registry_unavailable_blocked",
                    "chunk_id": _chunk_get(chunk, "chunk_id"),
                    "operator_id": operator_id,
                    "cultural_classification": classification,
                    "decision": "blocked_fail_closed",
                    "timestamp": now.isoformat(),
                },
            )
            continue

        decision = "allowed" if allowed else "blocked"
        _emit(
            audit_sink,
            {
                "event_type": ("cultural_authority_gate_allowed" if allowed else "cultural_authority_gate_blocked"),
                "chunk_id": _chunk_get(chunk, "chunk_id"),
                "operator_id": operator_id,
                "cultural_classification": classification,
                "decision": decision,
                "timestamp": now.isoformat(),
            },
        )
        if allowed:
            out.append(chunk)

    return out


def _classification_to_scope(classification: str) -> str:
    """Map ``cultural_classification`` enum to consent ``scope`` enum.

    cultural_classification ∈ {public, indigenous-language, sacred-site,
    land-governance}
    consent.scope            ∈ {site, language, protocol, all}
    """
    table = {
        "public": "all",  # public should never be evaluated, but be safe
        "indigenous-language": "language",
        "sacred-site": "site",
        "land-governance": "protocol",
    }
    return table.get(classification, "all")


def _emit(audit_sink: Callable[[dict[str, Any]], None] | None, event: dict[str, Any]) -> None:
    if audit_sink is None:
        return
    try:
        audit_sink(event)
    except Exception as exc:  # noqa: BLE001
        logger.warning("cultural_authority_gate_audit_error err=%s", exc)


__all__ = ["apply_cultural_authority_gate"]
