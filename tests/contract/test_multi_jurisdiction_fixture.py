"""T134 — Contract test for the 50-query multi-jurisdiction golden set (Spec 036 / FR-RAG-AG-04, US7).

Validates the structural integrity of
``apps/eval-runner/fixtures/spec036/multi_jurisdiction.jsonl`` so the eval-runner
can rely on it for parity / regression scoring during cutover and
post-cutover bi-weekly regressions.

Invariants:

1. **Exactly 50 queries** (5 × 10 jurisdictions).
2. **Even balance** — every jurisdiction in
   ``{act, nsw, nt, qld, sa, tas, vic, wa, national, aidr}`` carries exactly 5
   queries.
3. **Schema** — each row has ``id``, ``jurisdiction``, ``agent``,
   ``corpus_build_sha``, ``embedding_model_id``, ``prompt``, and an
   ``expected`` block with ``jurisdictions`` (list including ``national`` &
   ``aidr`` for every state, and ``aidr`` for ``aidr`` rows),
   ``requires_citation`` (bool), ``min_citation_precision`` (float in
   [0.5, 1.0]), ``expected_topics`` (non-empty list), and
   ``forbid_jurisdictions`` (list).
4. **Disambiguation correctness** — for every state row, the
   ``forbid_jurisdictions`` list MUST NOT contain the row's own jurisdiction
   nor any of ``national``/``aidr``.
5. **Agent coverage** — at least 5 distinct agents are exercised across the
   set.
6. **Embedding model parity** — every row uses the same embedding model
   identifier (no silent drift to a different model that would break
   citation-precision SC-007).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "apps" / "eval-runner" / "fixtures" / "spec036" / "multi_jurisdiction.jsonl"

ALL_JURISDICTIONS = {"act", "nsw", "nt", "qld", "sa", "tas", "vic", "wa", "national", "aidr"}
STATES = {"act", "nsw", "nt", "qld", "sa", "tas", "vic", "wa"}


def _rows() -> list[dict]:
    if not FIXTURE.exists():
        pytest.fail(f"fixture missing: {FIXTURE}")
    out: list[dict] = []
    with FIXTURE.open(encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                pytest.fail(f"{FIXTURE.name}:{ln} — invalid JSON: {exc}")
    return out


def test_fixture_has_exactly_50_rows() -> None:
    assert len(_rows()) == 50, "T134 mandates a 50-query golden set"


def test_every_jurisdiction_has_five_queries() -> None:
    counts = Counter(r["jurisdiction"] for r in _rows())
    missing = ALL_JURISDICTIONS - set(counts.keys())
    assert not missing, f"missing jurisdictions: {sorted(missing)}"
    bad = {j: n for j, n in counts.items() if n != 5}
    assert not bad, f"unbalanced jurisdiction counts: {bad}"


def test_every_row_has_required_fields() -> None:
    required = {
        "id",
        "jurisdiction",
        "agent",
        "corpus_build_sha",
        "embedding_model_id",
        "prompt",
        "expected",
    }
    for r in _rows():
        missing = required - set(r.keys())
        assert not missing, f"row {r.get('id')!r} missing fields: {sorted(missing)}"
        exp = r["expected"]
        for k in (
            "jurisdictions",
            "requires_citation",
            "min_citation_precision",
            "expected_topics",
            "forbid_jurisdictions",
        ):
            assert k in exp, f"row {r['id']!r} expected.{k} missing"


def test_state_rows_union_with_national_and_aidr() -> None:
    """US7: every state-jurisdiction query MUST be unioned with national + aidr."""
    for r in _rows():
        if r["jurisdiction"] in STATES:
            j = r["expected"]["jurisdictions"]
            assert "national" in j, f"row {r['id']!r} missing national union"
            assert "aidr" in j, f"row {r['id']!r} missing aidr union"
            assert r["jurisdiction"] in j, f"row {r['id']!r} missing own jurisdiction"


def test_aidr_rows_do_not_pin_a_state() -> None:
    """AIDR rows should retrieve from aidr + national but not pin a single state."""
    for r in _rows():
        if r["jurisdiction"] == "aidr":
            assert "aidr" in r["expected"]["jurisdictions"]
            assert STATES.isdisjoint(set(r["expected"]["jurisdictions"]))


def test_forbid_jurisdictions_excludes_self_national_aidr() -> None:
    """forbid_jurisdictions MUST never list the row's own / national / aidr."""
    for r in _rows():
        forb = set(r["expected"]["forbid_jurisdictions"])
        assert r["jurisdiction"] not in forb
        assert "national" not in forb
        assert "aidr" not in forb


def test_min_citation_precision_in_range() -> None:
    for r in _rows():
        v = r["expected"]["min_citation_precision"]
        assert isinstance(v, (int, float))
        assert 0.5 <= float(v) <= 1.0, f"row {r['id']!r} precision out of [0.5, 1.0]: {v}"


def test_expected_topics_non_empty() -> None:
    for r in _rows():
        topics = r["expected"]["expected_topics"]
        assert isinstance(topics, list) and topics, f"row {r['id']!r} expected_topics empty"


def test_at_least_five_distinct_agents() -> None:
    agents = {r["agent"] for r in _rows()}
    assert len(agents) >= 5, f"only {len(agents)} agents exercised: {agents}"


def test_embedding_model_parity() -> None:
    models = {r["embedding_model_id"] for r in _rows()}
    assert len(models) == 1, (
        f"embedding model drift across the fixture: {models} — citation precision "
        "(SC-007) is only meaningful when every row uses the same model."
    )
