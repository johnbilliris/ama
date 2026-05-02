"""Per-agent equivalence test (T040, FR-023, communication).

Note: equivalence runs against the legacy pipeline's pre-publication draft;
HITL is not exercised here (covered by T046 in Phase 4).
"""

from __future__ import annotations

from pathlib import Path

from apps.agents.maf_runtime.equivalence.runner import _load_fixture_pairs
from apps.agents.maf_runtime.equivalence.scorers import EquivalenceVerdict, score

AGENT_NAME = "communication"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_communication_equivalence() -> None:
    pairs = _load_fixture_pairs(AGENT_NAME, FIXTURES_DIR)
    report = score(agent_name=AGENT_NAME, pairs=pairs)
    assert report.verdict == EquivalenceVerdict.PASS, report.to_markdown()
