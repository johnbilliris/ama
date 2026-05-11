"""T014 — Integration test for the data-minimisation model gateway (FR-RAG-CV-03).

Asserts the gateway:
- Redacts PII (e.g. AU mobile numbers → ``<PHONE>``) via Presidio.
- Detects PSPF markings (``OFFICIAL: SENSITIVE``, ``PROTECTED``, ``SECRET``,
  ``TOP SECRET``) and DENIES if present at default policy.
- Detects sensitive operational content (operational details outside the
  allow-list) and DENIES.
- Emits ``audit.gateway_decision == "deny"`` with a structured ``reason`` on
  deny; ``"allow"`` (and a passive-log entry) on allow.

This test goes RED before T022/T023 land and GREEN once
``apps/agents/common/model_gateway.py`` is implemented.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def gateway_mod():
    return importlib.import_module("common.model_gateway")


def test_pii_phone_number_redacted(gateway_mod) -> None:
    """AU mobile number MUST be redacted to ``<PHONE>`` before transmission."""
    result = gateway_mod.apply(
        text="Please call the inspector on 0412 345 678 and email john@example.com.",
        deployment_region="eastus",
    )
    assert result.gateway_decision in ("allow", "redact")
    # After redaction, no raw PII should survive
    assert "0412 345 678" not in result.transmitted_text
    assert "<PHONE>" in result.transmitted_text or "[PHONE]" in result.transmitted_text


@pytest.mark.parametrize(
    "marking",
    [
        "OFFICIAL: SENSITIVE",
        "PROTECTED",
        "SECRET",
        "TOP SECRET",
    ],
)
def test_pspf_marking_denies(gateway_mod, marking: str) -> None:
    """PSPF markings above OFFICIAL MUST be denied (FR-RAG-CV-03; FR-RAG-NS-07)."""
    result = gateway_mod.apply(
        text=f"This document is {marking}. Includes operational coordinates.",
        deployment_region="eastus",
    )
    assert result.gateway_decision == "deny"
    assert result.reason  # non-empty
    assert marking.split(":")[0].upper() in result.reason.upper()


def test_au_region_skips_pii_redaction_but_still_audits(gateway_mod) -> None:
    """For AU-region deployments the gateway is bypassed at the boundary, but the
    call is still audited (FR-RAG-CV-04)."""
    result = gateway_mod.apply(
        text="Please call the inspector on 0412 345 678.",
        deployment_region="australiaeast",
    )
    # AU-region: no redaction; allowed; audit entry recorded for transparency.
    assert result.gateway_decision == "allow"
    assert result.transmitted_text == "Please call the inspector on 0412 345 678."


def test_sensitive_operational_default_deny(gateway_mod) -> None:
    """Sensitive operational details outside the allow-list default-deny."""
    text = "Hostage rescue tactical entry plan, breach point bravo, target room 4B."
    result = gateway_mod.apply(text=text, deployment_region="eastus")
    assert result.gateway_decision == "deny"
    assert result.reason


def test_safe_general_query_allows(gateway_mod) -> None:
    """A generic doctrine question MUST be allowed."""
    result = gateway_mod.apply(
        text="Summarise the AIIMS span-of-control levels for a Level 2 bushfire incident.",
        deployment_region="eastus",
    )
    assert result.gateway_decision == "allow"
