"""Contract: cultural authority registry signature verifier (T193).

Per FR-RAG-CA-01..05 + Plan §F-A2.3 — the registry signature verifier (cosign
keyless OR age-encrypted detached, mirroring FR-RAG-LS-02 dual-sig pattern
from T129) MUST:

  - Accept a row whose detached signature passes verification.
  - Reject a row whose signature fails verification AND emit
    ``cultural_authority_signature_invalid`` to the audit sink.

Proves: T198 — apps/agents/common/cultural_authority_registry.py.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from apps.agents.common.cultural_authority_registry import (
    CulturalAuthorityConsent,
    CulturalAuthorityRegistry,
    _consent_from_dict,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "specs" / "036-foundry-rag-grounding" / "contracts" / "cultural-authority-registry.schema.json"


def _consent(*, signature: str, expires_in_days: int = 30) -> CulturalAuthorityConsent:
    now = datetime.now(tz=UTC)
    return CulturalAuthorityConsent(
        operator_id="op-1@ama.local",
        land_council_id="central-land-council",
        granted_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=expires_in_days),
        granted_by_authority="CLC Cultural Heritage Officer",
        scope="site",
        signature=signature,
        revocation_reason=None,
    )


def test_valid_signature_accepted() -> None:
    """Verifier returns True → consent surfaces in get_consents()."""
    consent = _consent(signature="MEY...valid-sigstore-bundle")
    audit_events: list[dict[str, Any]] = []

    registry = CulturalAuthorityRegistry(
        fetch_consents_fn=lambda op: (consent,) if op == consent.operator_id else (),
        signature_verifier=lambda c: True,
        audit_sink=audit_events.append,
    )
    out = registry.get_consents("op-1@ama.local")

    assert out == (consent,), "valid signature must surface the consent"
    assert not any(
        e.get("event_type") == "cultural_authority_signature_invalid" for e in audit_events
    ), "no signature-invalid audit event when signature is valid"


def test_tampered_signature_rejected_and_audit_emitted() -> None:
    """Verifier returns False → consent suppressed AND audit emitted."""
    consent = _consent(signature="tampered-sig")
    audit_events: list[dict[str, Any]] = []

    registry = CulturalAuthorityRegistry(
        fetch_consents_fn=lambda op: (consent,),
        signature_verifier=lambda c: False,
        audit_sink=audit_events.append,
    )
    out = registry.get_consents("op-1@ama.local")

    assert out == (), "tampered signature must be filtered out"
    invalid_events = [
        e for e in audit_events if e.get("event_type") == "cultural_authority_signature_invalid"
    ]
    assert len(invalid_events) == 1, "exactly one signature-invalid audit event"
    assert invalid_events[0]["operator_id"] == "op-1@ama.local"
    assert invalid_events[0]["land_council_id"] == "central-land-council"
    assert invalid_events[0]["scope"] == "site"


def test_signature_verifier_exception_treated_as_failure() -> None:
    """Verifier raises → treated as failed verification (fail-closed)."""
    consent = _consent(signature="raises-sig")

    def boom(_: CulturalAuthorityConsent) -> bool:
        raise RuntimeError("boom")

    audit_events: list[dict[str, Any]] = []
    registry = CulturalAuthorityRegistry(
        fetch_consents_fn=lambda op: (consent,),
        signature_verifier=boom,
        audit_sink=audit_events.append,
    )
    out = registry.get_consents("op-1@ama.local")

    assert out == (), "verifier exception must fail-closed"
    assert any(
        e.get("event_type") == "cultural_authority_signature_invalid" for e in audit_events
    ), "audit event must still emit when verifier raises"


def test_consent_round_trips_from_schema_example() -> None:
    """A row matching the schema's first example MUST round-trip."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    example = schema["examples"][0]
    consent = _consent_from_dict(example)
    assert consent.operator_id == "field-coordinator-nt-1@ama.local"
    assert consent.land_council_id == "central-land-council"
    assert consent.scope == "site"
    assert consent.is_current(now=datetime(2026, 5, 1, tzinfo=UTC))


def test_no_default_signature_acceptance_in_production_path() -> None:
    """The module-level :func:`seed_registry_from_signoff_file` HUMAN-IN-LOOP
    hook MUST refuse to seed without sign-off."""
    from apps.agents.common.cultural_authority_registry import seed_registry_from_signoff_file

    with pytest.raises(NotImplementedError) as excinfo:
        seed_registry_from_signoff_file("/no/such/path.json")
    assert "HANDOFF.md" in str(excinfo.value), "error must point operators to HANDOFF.md"
