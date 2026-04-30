"""Per-agent equivalence test (T037, FR-023, risk_assessment)."""

from __future__ import annotations

from pathlib import Path

from apps.agents.maf_runtime.equivalence.runner import _load_fixture_pairs
from apps.agents.maf_runtime.equivalence.scorers import EquivalenceVerdict, score

AGENT_NAME = "risk_assessment"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_risk_assessment_equivalence() -> None:
    pairs = _load_fixture_pairs(AGENT_NAME, FIXTURES_DIR)
    report = score(agent_name=AGENT_NAME, pairs=pairs)
    assert report.verdict == EquivalenceVerdict.PASS, report.to_markdown()
