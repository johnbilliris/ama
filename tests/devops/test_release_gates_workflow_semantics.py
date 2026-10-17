from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_ci_wires_feature_evidence_binding_and_p1_gate() -> None:
    text = _read(".github/workflows/ci.yml")
    assert "feature-evidence-binding-lint" in text
    assert "python tools/lint/check_feature_evidence_binding.py" in text
    assert "p1-training-release-gate" in text
    assert "python scripts/p1_release_training_gate.py" in text
    assert "--base-sha" not in text
    assert "--head-sha" not in text
    assert 'if [[ "$P1_PR_NUMBER" == "142" || "$P1_BRANCH" == "001-extension-list" ]]' in text
    assert "waiver_args+=(--waiver-file docs/disaster-response-hub/p1-flow-waivers/pr-142.yaml)" in text


def test_cd_wires_p1_gate_before_deploy() -> None:
    text = _read(".github/workflows/cd.yml")
    assert "Enforce P1 training release gate" in text
    assert "python scripts/p1_release_training_gate.py" in text
    assert "git diff --name-only HEAD^ HEAD" in text
    assert "--base-sha" not in text
    assert "--head-sha" not in text
    assert 'grep -Fxq "docs/disaster-response-hub/p1-flow-waivers/pr-142.yaml"' in text
    assert "waiver_args+=(--waiver-file docs/disaster-response-hub/p1-flow-waivers/pr-142.yaml)" in text
