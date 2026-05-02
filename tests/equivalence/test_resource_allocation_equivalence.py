"""Per-agent equivalence test (T039, FR-023, resource_allocation)."""

from __future__ import annotations

from pathlib import Path

from apps.agents.maf_runtime.equivalence.runner import _load_fixture_pairs
from apps.agents.maf_runtime.equivalence.scorers import EquivalenceVerdict, score

AGENT_NAME = "resource_allocation"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_resource_allocation_equivalence() -> None:
    pairs = _load_fixture_pairs(AGENT_NAME, FIXTURES_DIR)
    report = score(agent_name=AGENT_NAME, pairs=pairs)
    assert report.verdict == EquivalenceVerdict.PASS, report.to_markdown()
