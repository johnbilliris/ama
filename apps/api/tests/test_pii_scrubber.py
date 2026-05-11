"""T-C04 PII scrubber unit tests (FR-031)."""

from __future__ import annotations

from apps.agents.simulation_telemetry_injection.pii_scrubber import scrub


def test_scrubs_email() -> None:
    r = scrub("contact me at jane.doe@example.com today")
    assert "jane.doe@example.com" not in r.text
    assert r.redactions["email"] == 1


def test_scrubs_phone() -> None:
    r = scrub("call 0412 345 678 immediately")
    assert "0412 345 678" not in r.text
    assert r.redactions.get("phone", 0) >= 1


def test_scrubs_ahpra() -> None:
    r = scrub("AHPRA NUR1234567890 holds this license")
    assert "NUR1234567890" not in r.text
    assert r.redactions["ahpra"] == 1


def test_no_pii_pass_through_unchanged() -> None:
    text = "temperature 41C in penrith at 14:00"
    r = scrub(text)
    assert r.text == text
    assert r.total_redactions == 0
