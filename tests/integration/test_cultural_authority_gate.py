"""Integration: cultural authority gate (T194).

Per Plan §F-A2.4 + Constitution VI-C — three cases:

  (a) registry available + protected chunk + operator consent verified
      → chunk passes (audit `cultural_authority_gate_allowed`).
  (b) registry available + protected chunk + NO operator consent
      → chunk suppressed (audit `cultural_authority_gate_blocked`).
  (c) registry unreachable → fail-closed for protected chunks; non-protected
      chunks remain retrievable; audit
      `cultural_authority_registry_unavailable_blocked`.

Proves: T199 — apps/agents/common/cultural_authority_gate.py.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from apps.agents.common.cultural_authority_gate import apply_cultural_authority_gate
from apps.agents.common.cultural_authority_registry import (
    CulturalAuthorityConsent,
    CulturalAuthorityRegistry,
    CulturalAuthorityRegistryUnavailableError,
)


def _now() -> datetime:
    return datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)


def _consent(*, scope: str, expires_at: datetime | None = None) -> CulturalAuthorityConsent:
    return CulturalAuthorityConsent(
        operator_id="op-1@ama.local",
        land_council_id="central-land-council",
        granted_at=_now() - timedelta(days=10),
        expires_at=expires_at or (_now() + timedelta(days=30)),
        granted_by_authority="CLC Cultural Heritage Officer",
        scope=scope,
        signature="MEY...valid",
        revocation_reason=None,
    )


def _chunk(*, chunk_id: str, protected: bool, classification: str = "public") -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "cultural_authority_required": protected,
        "cultural_classification": classification,
        "text": f"chunk body {chunk_id}",
    }


def test_case_a_registry_available_with_consent_passes() -> None:
    """(a) protected chunk + operator consent → chunk passes."""
    registry = CulturalAuthorityRegistry(
        fetch_consents_fn=lambda op: (_consent(scope="site"),),
        signature_verifier=lambda c: True,
        now_fn=_now,
    )
    chunks = [
        _chunk(chunk_id="public-1", protected=False),
        _chunk(chunk_id="protected-1", protected=True, classification="sacred-site"),
    ]
    audit: list[dict[str, Any]] = []

    out = apply_cultural_authority_gate(
        chunks,
        operator_id="op-1@ama.local",
        registry=registry,
        audit_sink=audit.append,
        now_fn=_now,
    )

    assert {c["chunk_id"] for c in out} == {"public-1", "protected-1"}
    allowed = [e for e in audit if e["event_type"] == "cultural_authority_gate_allowed"]
    assert len(allowed) == 1
    assert allowed[0]["chunk_id"] == "protected-1"
    assert allowed[0]["operator_id"] == "op-1@ama.local"


def test_case_b_registry_available_no_consent_blocks() -> None:
    """(b) protected chunk + no consent → chunk suppressed."""
    registry = CulturalAuthorityRegistry(
        fetch_consents_fn=lambda op: (),  # empty registry
        signature_verifier=lambda c: True,
        now_fn=_now,
    )
    chunks = [
        _chunk(chunk_id="public-1", protected=False),
        _chunk(chunk_id="protected-1", protected=True, classification="sacred-site"),
    ]
    audit: list[dict[str, Any]] = []

    out = apply_cultural_authority_gate(
        chunks,
        operator_id="op-1@ama.local",
        registry=registry,
        audit_sink=audit.append,
        now_fn=_now,
    )

    assert {c["chunk_id"] for c in out} == {"public-1"}, "protected chunk must be suppressed"
    blocked = [e for e in audit if e["event_type"] == "cultural_authority_gate_blocked"]
    assert len(blocked) == 1
    assert blocked[0]["chunk_id"] == "protected-1"


def test_case_c_registry_unreachable_fail_closed_for_protected_only() -> None:
    """(c) registry unreachable → fail-closed for protected; public passes."""

    def boom(_op: str) -> tuple:
        raise CulturalAuthorityRegistryUnavailableError("cosmos timeout")

    registry = CulturalAuthorityRegistry(
        fetch_consents_fn=boom,
        signature_verifier=lambda c: True,
        now_fn=_now,
    )
    chunks = [
        _chunk(chunk_id="public-1", protected=False),
        _chunk(chunk_id="protected-1", protected=True, classification="indigenous-language"),
    ]
    audit: list[dict[str, Any]] = []

    out = apply_cultural_authority_gate(
        chunks,
        operator_id="op-1@ama.local",
        registry=registry,
        audit_sink=audit.append,
        now_fn=_now,
    )

    # Constitution Principle I: public chunks are NEVER suppressed by the gate.
    assert {c["chunk_id"] for c in out} == {"public-1"}
    blocked = [
        e for e in audit
        if e["event_type"] == "cultural_authority_registry_unavailable_blocked"
    ]
    assert len(blocked) == 1, "registry-unavailable audit must emit for protected chunk"
    assert blocked[0]["decision"] == "blocked_fail_closed"


def test_revoked_consent_treated_as_no_consent() -> None:
    """Revoked consent → blocked even though row exists."""
    revoked = CulturalAuthorityConsent(
        operator_id="op-1@ama.local",
        land_council_id="central-land-council",
        granted_at=_now() - timedelta(days=10),
        expires_at=_now() + timedelta(days=30),
        granted_by_authority="CLC",
        scope="site",
        signature="MEY...",
        revocation_reason="operator-role-change",
    )
    registry = CulturalAuthorityRegistry(
        fetch_consents_fn=lambda op: (revoked,),
        signature_verifier=lambda c: True,
        now_fn=_now,
    )
    chunks = [_chunk(chunk_id="protected-1", protected=True, classification="sacred-site")]
    audit: list[dict[str, Any]] = []

    out = apply_cultural_authority_gate(
        chunks,
        operator_id="op-1@ama.local",
        registry=registry,
        audit_sink=audit.append,
        now_fn=_now,
    )
    assert out == [], "revoked consent must NOT permit the chunk"


def test_expired_consent_treated_as_no_consent() -> None:
    """Expired consent → blocked."""
    expired = _consent(scope="site", expires_at=_now() - timedelta(days=1))
    registry = CulturalAuthorityRegistry(
        fetch_consents_fn=lambda op: (expired,),
        signature_verifier=lambda c: True,
        now_fn=_now,
    )
    chunks = [_chunk(chunk_id="protected-1", protected=True, classification="sacred-site")]
    audit: list[dict[str, Any]] = []

    out = apply_cultural_authority_gate(
        chunks,
        operator_id="op-1@ama.local",
        registry=registry,
        audit_sink=audit.append,
        now_fn=_now,
    )
    assert out == [], "expired consent must NOT permit the chunk"


def test_scope_mismatch_blocks() -> None:
    """Consent for `language` scope does NOT cover `sacred-site` chunk."""
    language_only = _consent(scope="language")
    registry = CulturalAuthorityRegistry(
        fetch_consents_fn=lambda op: (language_only,),
        signature_verifier=lambda c: True,
        now_fn=_now,
    )
    chunks = [_chunk(chunk_id="sacred-1", protected=True, classification="sacred-site")]
    out = apply_cultural_authority_gate(
        chunks,
        operator_id="op-1@ama.local",
        registry=registry,
        now_fn=_now,
    )
    assert out == [], "scope-narrow consent must not cover broader chunk classification"


def test_scope_all_covers_every_classification() -> None:
    """Consent with scope='all' covers every classification."""
    blanket = _consent(scope="all")
    registry = CulturalAuthorityRegistry(
        fetch_consents_fn=lambda op: (blanket,),
        signature_verifier=lambda c: True,
        now_fn=_now,
    )
    chunks = [
        _chunk(chunk_id="lang-1", protected=True, classification="indigenous-language"),
        _chunk(chunk_id="sacred-1", protected=True, classification="sacred-site"),
        _chunk(chunk_id="protocol-1", protected=True, classification="land-governance"),
    ]
    out = apply_cultural_authority_gate(
        chunks,
        operator_id="op-1@ama.local",
        registry=registry,
        now_fn=_now,
    )
    assert len(out) == 3
