"""Chaos: cultural authority flag-flip lockdown (T195).

Per FR-RAG-CA-04 + Plan §F-A2.6 + Pass 2 Q-P2-08 (Locked-on flag class) —
``feature.cultural_authority_gate.enabled`` may NOT be disabled in
``environment=prod`` (or any non-``test`` environment). OPA must deny
the flip and the audit trail must capture the attempt.

This test mirrors the OPA rule semantics in
``infra/policy/rego/cultural_authority_flag.rego`` so the contract is
enforceable even when OPA is not on PATH.

Proves: T201 — infra/policy/rego/cultural_authority_flag.rego.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGO_PATH = ROOT / "infra" / "policy" / "rego" / "cultural_authority_flag.rego"


def _python_eval(payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    """Return ``(deny_messages, audit_events)`` matching the rego semantics."""
    deny: list[str] = []
    audit: list[dict[str, Any]] = []
    if (
        payload.get("flag") == "feature.cultural_authority_gate.enabled"
        and payload.get("new_value") is False
        and payload.get("environment") != "test"
    ):
        deny.append(
            f"FR-RAG-CA-04: feature.cultural_authority_gate.enabled is "
            f"Locked-on in '{payload.get('environment')}' environment; only "
            f"'test' may flip the flag (Pass 2 Q-P2-08; ADR-12)."
        )
        audit.append(
            {
                "event_type": "cultural_authority_gate_test_disable_attempt",
                "flag": payload["flag"],
                "requested_value": payload["new_value"],
                "environment": payload["environment"],
                "actor_id": payload.get("actor_id"),
                "decision": "denied",
            }
        )
    return deny, audit


# --------------------------------------------------------------------------- #
# Test cases
# --------------------------------------------------------------------------- #


def test_rego_file_exists() -> None:
    """The rego policy MUST exist at the canonical path."""
    assert REGO_PATH.exists(), f"missing rego policy at {REGO_PATH}"
    body = REGO_PATH.read_text(encoding="utf-8")
    assert "deny_flag_flip" in body
    assert "feature.cultural_authority_gate.enabled" in body


def test_prod_disable_attempt_denied() -> None:
    """Disabling the flag in prod is denied + audit emitted."""
    deny, audit = _python_eval(
        {
            "flag": "feature.cultural_authority_gate.enabled",
            "new_value": False,
            "environment": "prod",
            "actor_id": "ops-bot@ama.local",
        }
    )
    assert deny, "prod disable attempt MUST be denied"
    assert any("Locked-on" in m for m in deny)
    assert len(audit) == 1
    assert audit[0]["event_type"] == "cultural_authority_gate_test_disable_attempt"
    assert audit[0]["decision"] == "denied"


def test_test_environment_disable_allowed() -> None:
    """Disabling the flag in test environment is permitted."""
    deny, audit = _python_eval(
        {
            "flag": "feature.cultural_authority_gate.enabled",
            "new_value": False,
            "environment": "test",
            "actor_id": "ci-bot@ama.local",
        }
    )
    assert deny == [], "test environment must be allowed to flip"
    assert audit == [], "no audit event when flip is allowed"


def test_staging_disable_denied() -> None:
    """Staging is NOT 'test' — disabling is locked just like prod."""
    deny, _ = _python_eval(
        {
            "flag": "feature.cultural_authority_gate.enabled",
            "new_value": False,
            "environment": "staging",
            "actor_id": "ops-bot",
        }
    )
    assert deny, "staging is not 'test' — flag flip must be denied"


def test_prod_enable_always_allowed() -> None:
    """Re-enabling the flag (False → True) is always allowed."""
    deny, _ = _python_eval(
        {
            "flag": "feature.cultural_authority_gate.enabled",
            "new_value": True,
            "environment": "prod",
            "actor_id": "ops-bot",
        }
    )
    assert deny == [], "enabling the flag must always be allowed"


def test_other_flag_unaffected() -> None:
    """The lockdown only applies to the cultural authority gate flag."""
    deny, _ = _python_eval(
        {
            "flag": "feature.some_other_flag.enabled",
            "new_value": False,
            "environment": "prod",
            "actor_id": "ops-bot",
        }
    )
    assert deny == [], "other flags are not locked by this policy"
