"""Per-agent equivalence test (T036, FR-023, monitoring).

Loads fixtures from ``tests/equivalence/fixtures/monitoring/`` (each fixture is
a JSON file with ``case_id``, ``input``, ``legacy_output``, ``maf_output``).
Asserts ≥95% decision-equivalence on categorical fields + 100% schema-equivalence
on populated fields, per FR-023.

When the fixtures directory is empty the harness produces a zero-cases PASS
report — this is the bootstrap state so the CI gate (T041) wires immediately
without blocking on fixture curation.
"""

from __future__ import annotations

from pathlib import Path

from apps.agents.maf_runtime.equivalence.runner import _load_fixture_pairs
from apps.agents.maf_runtime.equivalence.scorers import EquivalenceVerdict, score

AGENT_NAME = "monitoring"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_monitoring_equivalence() -> None:
    pairs = _load_fixture_pairs(AGENT_NAME, FIXTURES_DIR)
    report = score(agent_name=AGENT_NAME, pairs=pairs)
    assert report.verdict == EquivalenceVerdict.PASS, (
        f"Equivalence FAIL for {AGENT_NAME}: "
        f"decision={report.decision_match_rate:.2%}, schema={report.schema_match_rate:.2%}\n" + report.to_markdown()
    )
