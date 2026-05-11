"""T-K05 — devops test for the Foundry carve-out review workflow."""

from __future__ import annotations

from pathlib import Path

from tools.foundry_carveout_eval_summary import main as eval_main
from tools.foundry_carveout_prompt_hash_diff import _format_diff, _index_by_model_id

WORKFLOW = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "foundry-carveout-review.yml"
)


def test_workflow_invokes_prompt_hash_diff_and_eval_summary() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "tools/foundry_carveout_prompt_hash_diff.py" in text
    assert "tools/foundry_carveout_eval_summary.py" in text
    assert "peter-evans/create-or-update-comment" in text


def test_workflow_triggers_on_pr_paths() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request:" in text
    assert "data/governance/foundry_carveout_registry.json" in text
    assert "packages/eval-dataset/data/telemetry_injection_v1/cases.jsonl" in text


def test_prompt_hash_diff_emits_added_removed_mutated() -> None:
    base = [
        {"model_id": "gpt-4o-au", "prompt_hash": "h1", "review_date": "2026-01-01"},
        {"model_id": "gpt-3.5-au", "prompt_hash": "old", "review_date": "2026-01-01"},
    ]
    head = [
        {"model_id": "gpt-4o-au", "prompt_hash": "h2", "review_date": "2026-01-01"},
        {"model_id": "gpt-4o-mini-au", "prompt_hash": "new", "review_date": "2026-01-01"},
    ]
    md = _format_diff(_index_by_model_id(base), _index_by_model_id(head))
    assert "Added carve-outs" in md
    assert "gpt-4o-mini-au" in md
    assert "Removed carve-outs" in md
    assert "gpt-3.5-au" in md
    assert "Mutated carve-outs" in md
    assert "h1" in md and "h2" in md


def test_prompt_hash_diff_unchanged_message() -> None:
    same = [
        {"model_id": "gpt-4o-au", "prompt_hash": "h1", "review_date": "2026-01-01"},
    ]
    md = _format_diff(_index_by_model_id(same), _index_by_model_id(same))
    assert "unchanged" in md.lower()


def test_eval_summary_writes_markdown(tmp_path: Path) -> None:
    dataset = (
        Path(__file__).resolve().parents[2]
        / "packages"
        / "eval-dataset"
        / "data"
        / "telemetry_injection_v1"
        / "cases.jsonl"
    )
    out = tmp_path / "summary.md"
    rc = eval_main(["--dataset", str(dataset), "--output", str(out)])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "Telemetry-injection eval" in text
    assert "Pass rate" in text
    assert "Mean score" in text
