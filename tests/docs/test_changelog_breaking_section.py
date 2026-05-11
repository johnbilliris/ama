"""Wave D / T-AA22 — CHANGELOG breaking-section regression test.

Asserts the Cycle 2 amendment-cycle BREAKING entries are present in
the top-of-file ``[Unreleased]`` block. Locks the format so any future
edit that drops the BREAKING heading or the four Cycle 2 BREAKING
bullets will fail this test.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def _changelog_text() -> str:
    return CHANGELOG.read_text(encoding="utf-8")


def test_changelog_has_unreleased_section() -> None:
    text = _changelog_text()
    assert "## [Unreleased]" in text


def test_changelog_has_cycle_2_breaking_section() -> None:
    text = _changelog_text()
    assert "### Breaking changes (spec 036 — Cycle 2 amendment cycle)" in text


def test_changelog_documents_openapi_v030_breaking_bump() -> None:
    text = _changelog_text()
    assert "OpenAPI v0.2.x → v0.3.0" in text
    assert "TelemetryInjectionAck.triggered_sub_agents" in text


def test_changelog_documents_audit_envelope_entry_25() -> None:
    text = _changelog_text()
    assert "signal_pipeline.dispatch_failed" in text
    assert "24 → 25" in text


def test_changelog_documents_sub_agent_enum_alignment() -> None:
    text = _changelog_text()
    assert "9-PascalCase" in text
    assert "_KEBAB_TO_PASCAL" in text


def test_changelog_links_to_openapi_changelog() -> None:
    text = _changelog_text()
    assert "openapi-changelog.md" in text


def test_changelog_links_to_adr_036_010() -> None:
    text = _changelog_text()
    assert "ADR-036-010" in text
