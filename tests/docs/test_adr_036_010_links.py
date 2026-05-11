"""Wave D / T-AA22 — ADR-036-010 link integrity test.

Verifies the Cycle 2 amendment-cycle ADR exists, has the expected
section structure (Status / Context / Decision / Consequences), and
cross-references the openapi-changelog and the eight Cycle 2
amendment IDs.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR = REPO_ROOT / "docs" / "aidr" / "decisions" / "ADR-036-010-cycle-2-amendment-cycle.md"
OPENAPI_CHANGELOG = REPO_ROOT / "specs" / "036-sim-agent-extend" / "contracts" / "openapi-changelog.md"


def test_adr_file_exists() -> None:
    assert ADR.exists(), "ADR-036-010 MUST exist"


def test_openapi_changelog_exists() -> None:
    assert OPENAPI_CHANGELOG.exists(), "openapi-changelog.md MUST exist"


def test_adr_has_required_sections() -> None:
    text = ADR.read_text(encoding="utf-8")
    for header in (
        "**Status**: Accepted",
        "## Context",
        "## Decision",
        "## Alternatives Considered",
        "## Consequences",
        "## Test Obligations",
        "## References",
    ):
        assert header in text, f"ADR-036-010 missing section: {header!r}"


def test_adr_documents_all_eight_amendments() -> None:
    text = ADR.read_text(encoding="utf-8")
    for amendment in (
        "A2-01",
        "A2-02",
        "A2-03",
        "A2-04",
        "A2-05",
        "A2-06",
        "A2-07",
        "A2-08",
    ):
        assert amendment in text, f"ADR-036-010 missing amendment ID: {amendment}"


def test_adr_documents_breaking_change() -> None:
    text = ADR.read_text(encoding="utf-8")
    assert "BREAKING" in text
    assert "v0.3.0" in text


def test_adr_cites_chk135() -> None:
    text = ADR.read_text(encoding="utf-8")
    assert "CHK135" in text, "ADR-036-010 MUST cite CHK135 (highest-risk JCS byte-equality)"


def test_openapi_changelog_has_v030_row() -> None:
    text = OPENAPI_CHANGELOG.read_text(encoding="utf-8")
    assert "v0.3.0" in text
    assert "BREAKING" in text


def test_openapi_changelog_has_six_step_recipe() -> None:
    text = OPENAPI_CHANGELOG.read_text(encoding="utf-8")
    assert "SDK migration recipe" in text
    for step in ("1. **Bump", "2. **Update", "3. **Surface", "4. **Update", "5. **If you", "6. **Re-run"):
        assert step in text, f"openapi-changelog.md missing step starting with {step!r}"


def test_openapi_changelog_documents_kebab_to_pascal_shim() -> None:
    text = OPENAPI_CHANGELOG.read_text(encoding="utf-8")
    assert "_KEBAB_TO_PASCAL" in text


def test_adr_links_to_openapi_changelog() -> None:
    text = ADR.read_text(encoding="utf-8")
    assert "openapi-changelog.md" in text
