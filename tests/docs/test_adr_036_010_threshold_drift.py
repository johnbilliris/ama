"""Cycle 3 / T-AA24 / A3-04 — ADR-036-010 + CHANGELOG threshold byte-equality regression test.

Asserts that the Z6 threshold values quoted in
``docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md`` and
``CHANGELOG.md`` are byte-equal to the canonical SLI bundle at
``infra/observability/sli-kql.json`` SLI-Z6 thresholds.

Per Cycle 3 amendment A3-04 (`spec.md:315-325`), the original Cycle 2
documents quoted stale thresholds (gpt-4o ``2 500 / 5 000`` ms;
gpt-4o-mini ``1 800 / 2 000`` ms) — Cycle 3 mandates byte-equality
with the canonical contract (gpt-4o ``4 000 / 5 000`` ms; gpt-4o-mini
``1 500 / 2 000`` ms — confirmed in ``infra/observability/sli-kql.json``,
``infra/bicep/modules/observability-alerts.bicep``, and
``contracts/sli-thresholds.md:218-228``).

The test fails on ANY drift, with a diagnostic that names the drifted
value so future PRs cannot silently re-introduce the stale numbers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_PATH = (
    REPO_ROOT
    / "docs"
    / "aidr"
    / "decisions"
    / "ADR-036-010-cycle-2-amendment-cycle.md"
)
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
SLI_PATH = REPO_ROOT / "infra" / "observability" / "sli-kql.json"


@pytest.fixture(scope="module")
def sli_z6_thresholds() -> dict[str, int]:
    """Canonical SLI-Z6 thresholds from the implementation bundle."""

    doc = json.loads(SLI_PATH.read_text(encoding="utf-8"))
    z6 = next(s for s in doc["slis"] if s["id"] == "SLI-Z6")
    return {
        "warn_threshold_ms_gpt4o": int(z6["warn_threshold_ms_gpt4o"]),
        "breach_threshold_ms_gpt4o": int(z6["breach_threshold_ms_gpt4o"]),
        "warn_threshold_ms_gpt4omini": int(z6["warn_threshold_ms_gpt4omini"]),
        "breach_threshold_ms_gpt4omini": int(z6["breach_threshold_ms_gpt4omini"]),
    }


def _strip_thin_spaces(text: str) -> str:
    """Drop ASCII / NBSP / thin-space digit separators (e.g. ``4 000`` → ``4000``)."""

    return re.sub(r"(\d)[\s\u00a0\u202f](\d)", r"\1\2", text)


def test_adr_036_010_z6_thresholds_byte_equal(sli_z6_thresholds: dict[str, int]) -> None:
    """ADR-036-010 §A2-02 quotes Z6 warn/breach pairs that match the SLI bundle."""

    text = _strip_thin_spaces(ADR_PATH.read_text(encoding="utf-8"))
    expected_substrings = (
        f"gpt-4o ≤ {sli_z6_thresholds['warn_threshold_ms_gpt4o']} ms warn",
        f"≤ {sli_z6_thresholds['breach_threshold_ms_gpt4o']} ms breach",
        f"gpt-4o-mini ≤ {sli_z6_thresholds['warn_threshold_ms_gpt4omini']} ms warn",
        f"≤ {sli_z6_thresholds['breach_threshold_ms_gpt4omini']} ms breach",
    )
    for needle in expected_substrings:
        assert needle in text, (
            f"ADR-036-010 missing canonical Z6 threshold substring {needle!r} — "
            "check `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md` "
            "§A2-02 against `infra/observability/sli-kql.json` SLI-Z6."
        )


def test_changelog_z6_thresholds_byte_equal(sli_z6_thresholds: dict[str, int]) -> None:
    """``CHANGELOG.md:19`` quotes Z6 warn/breach pairs that match the SLI bundle."""

    text = CHANGELOG_PATH.read_text(encoding="utf-8")
    expected_substrings = (
        f"warn={sli_z6_thresholds['warn_threshold_ms_gpt4o']} ms",
        f"breach={sli_z6_thresholds['breach_threshold_ms_gpt4o']} ms",
        f"warn={sli_z6_thresholds['warn_threshold_ms_gpt4omini']} ms",
        f"breach={sli_z6_thresholds['breach_threshold_ms_gpt4omini']} ms",
    )
    for needle in expected_substrings:
        assert needle in text, (
            f"CHANGELOG.md missing canonical Z6 threshold substring {needle!r} — "
            "check the Cycle 2 amendment-cycle entry against "
            "`infra/observability/sli-kql.json` SLI-Z6."
        )


def test_no_stale_2500_or_1800_in_z6_paragraphs() -> None:
    """The stale Cycle 2 thresholds (``2 500`` / ``1 800``) are absent in the Z6 paragraphs.

    Cycle 3 / A3-04 anti-regression — neither the ADR §A2-02 paragraph
    nor the CHANGELOG Z6 entry may carry the stale ``2 500`` or ``1 800``
    digits as part of a Z6 latency quotation. We scan both files for the
    Z6 paragraph specifically (so unrelated occurrences elsewhere — e.g.
    in another SLI's table — do not trip the guard).
    """

    adr_text = _strip_thin_spaces(ADR_PATH.read_text(encoding="utf-8"))
    changelog_text = CHANGELOG_PATH.read_text(encoding="utf-8")

    # ADR §A2-02 paragraph — bounded by the next "### " heading.
    adr_match = re.search(
        r"### A2-02 — Z6.+?(?=\n### |\n## )",
        adr_text,
        flags=re.DOTALL,
    )
    assert adr_match is not None, "Cannot locate ADR §A2-02 paragraph"
    adr_z6_block = adr_match.group(0)
    for stale in ("2500 ms", "1800 ms"):
        assert stale not in adr_z6_block, (
            f"ADR §A2-02 still carries stale Z6 threshold {stale!r} — "
            "Cycle 3 / A3-04 mandates removal."
        )

    # CHANGELOG Z6 line — recognised by the "Z6 SLI" prefix.
    z6_lines = [ln for ln in changelog_text.splitlines() if "Z6 SLI" in ln]
    assert z6_lines, "Cannot locate CHANGELOG Z6 entry"
    for ln in z6_lines:
        for stale in ("2 500 ms", "1 800 ms", "2500 ms", "1800 ms"):
            assert stale not in ln, (
                f"CHANGELOG Z6 line still carries stale threshold {stale!r}: {ln!r}"
            )
