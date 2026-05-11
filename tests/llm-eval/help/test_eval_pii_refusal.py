"""spec-038 LLM-eval — FR-035 PII redaction notice.

Pass-through evaluator: walks the JSONL fixture and asserts each row has the
required minimal shape so the eval harness is wired. Real LLM-driven evaluation
is invoked by the eval workflow runbook (see docs/runbooks/help/llm-eval.md).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE = (
    Path(__file__).resolve().parents[3] / "apps" / "agents" / "help_assistant" / "eval_fixtures" / "refusal_pii.jsonl"
)


def _rows() -> list[dict]:
    if not FIXTURE.exists():
        pytest.skip(f"fixture missing: {FIXTURE}")
    return [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_fixture_has_rows() -> None:
    assert len(_rows()) >= 1, "fixture must contain at least one row"


def test_each_row_has_question_and_expectation() -> None:
    for row in _rows():
        assert "input" in row, row
        # at least one of: expected_min_citations, expected_refusal, expected_outcome
        expected_keys = ("expected_min_citations", "expected_refusal", "expected_redaction", "expected")
        assert any(k in row for k in expected_keys), row
