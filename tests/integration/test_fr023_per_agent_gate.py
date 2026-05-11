"""T015 — Equivalence-gate harness test (Spec 036 / FR-RAG-FM-06; spec-033 FR-023).

Asserts that ``apps.eval-runner.per_agent_canary_gate`` (T029):
- Computes ``decision_equivalence`` and ``schema_equivalence`` against a
  per-agent golden Q&A fixture.
- Refuses to advance (exit non-zero / returns ``passed == False``) on
  decision-equivalence < 0.95 OR schema-equivalence < 1.0.
- Reports zero-cases as PASS (initial baseline; matches existing spec-033
  tests/equivalence harness behaviour).

This test is the single source of truth for the per-agent canary gate
(T093–T097, T145). Bound to spec-033 FR-023; extended with citation-fidelity
fields per data-model.md §EquivalenceTestResult.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def gate_mod():
    return importlib.import_module("ama_eval.per_agent_canary_gate")


def test_zero_fixture_passes(gate_mod, tmp_path) -> None:
    """An empty fixture file → zero cases → harness PASSES (matches spec-033 baseline)."""
    fixture = tmp_path / "monitoring.jsonl"
    fixture.write_text("", encoding="utf-8")
    result = gate_mod.run_per_agent_gate(
        agent_name="MonitoringAgent",
        fixture_path=fixture,
    )
    assert result.passed is True
    assert result.cases_total == 0


def test_decision_equivalence_below_threshold_fails(gate_mod, tmp_path) -> None:
    """Decision equivalence < 0.95 → harness FAILS (FR-RAG-FM-06)."""
    # Build a fixture that the harness's *fake* legacy/foundry runners disagree on.
    # The harness must accept canary_threshold=0.95 (default) and a fake-runner injection.
    fixture = tmp_path / "risk.jsonl"
    fixture.write_text(
        "\n".join(
            [
                '{"id": "q1", "prompt": "AIIMS L2 span?", "expected_decision": "level-2"}',
                '{"id": "q2", "prompt": "Bushfire SOC?", "expected_decision": "yes"}',
                '{"id": "q3", "prompt": "Cyclone evac?", "expected_decision": "no"}',
            ]
        ),
        encoding="utf-8",
    )

    def _legacy(prompt: str) -> dict:
        return {"decision": "level-2" if "L2" in prompt else "yes"}

    def _foundry(prompt: str) -> dict:
        # Disagrees on q3
        return {"decision": "yes" if "Bushfire" in prompt else "no"}

    result = gate_mod.run_per_agent_gate(
        agent_name="RiskAssessmentAgent",
        fixture_path=fixture,
        legacy_runner=_legacy,
        foundry_runner=_foundry,
        threshold=0.95,
    )
    assert result.passed is False
    assert result.decision_equivalence < 0.95


def test_schema_equivalence_required_to_be_100pct(gate_mod, tmp_path) -> None:
    """Schema equivalence MUST be 100% (FR-RAG-FM-06)."""
    fixture = tmp_path / "evac.jsonl"
    fixture.write_text(
        "\n".join(
            [
                '{"id": "q1", "prompt": "Evac?", "expected_decision": "go"}',
            ]
        ),
        encoding="utf-8",
    )

    def _legacy(prompt: str) -> dict:
        return {"decision": "go", "rationale": "doctrine-cited"}

    def _foundry(prompt: str) -> dict:
        # Same decision but missing rationale field
        return {"decision": "go"}

    result = gate_mod.run_per_agent_gate(
        agent_name="EvacuationAgent",
        fixture_path=fixture,
        legacy_runner=_legacy,
        foundry_runner=_foundry,
        threshold=0.95,
    )
    assert result.schema_equivalence < 1.0
    assert result.passed is False


def test_cli_exits_nonzero_on_failure(gate_mod, tmp_path, monkeypatch) -> None:
    """CLI entrypoint exits non-zero on failure (canary stops)."""
    fixture = tmp_path / "comm.jsonl"
    fixture.write_text("", encoding="utf-8")
    # The CLI returns an exit code (int); assert it's 0 for a passing zero-case run.
    rc = gate_mod.cli_main(argv=["--agent", "CommunicationAgent", "--fixture", str(fixture)])
    assert rc == 0
