"""Tests for sanitise-real workflow (Phase 8 / US6)."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (_REPO_ROOT / "apps" / "eval-runner" / "src", _REPO_ROOT / "packages" / "eval-core" / "src"):
    sys.path.insert(0, str(p))

from ama_eval.sanitise import sanitise  # noqa: E402


def test_sanitise_redacts_phone_and_email():
    txt = "Call me on 0412 345 678 or email victim@example.com about the fire at 42 Smith Street."
    r = sanitise(txt, sanitiser_id="user@authority")
    assert "0412" not in r.sanitisedText
    assert "[REDACTED-MOBILE-AU]" in r.sanitisedText
    assert "[REDACTED-EMAIL]" in r.sanitisedText
    assert "[REDACTED-ADDRESS]" in r.sanitisedText
    assert r.log.redactionCount >= 3
    assert len(r.log.appliedPatterns) >= 3


def test_sanitise_flags_graphic_hazard():
    txt = "Responders found burned bodies in the wreckage."
    r = sanitise(txt, sanitiser_id="u")
    assert r.requiresGraphicHazardTag is True


def test_sanitise_log_includes_source_hash():
    r = sanitise("benign text", sanitiser_id="u")
    assert r.log.sourceHash.startswith("sha256:")
    assert len(r.log.sourceHash) == 71
