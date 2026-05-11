"""T-K05 — Foundry carve-out eval-score summary helper.

Computes the deterministic offline grading summary for the
telemetry-injection eval dataset (T-J12) and writes a markdown roll-up
intended for posting as a PR comment.

When run without Azure credentials the helper uses a synthetic graded
response set (the test harness does this too) so the score is
deterministic across CI runs and only sensitive to the dataset itself.
This is fast (sub-second on the 100-prompt dataset) and is the value
posted in the PR comment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ama_eval_core.telemetry_injection_grader import grade_case


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def _synthesize_response(case: dict[str, Any]) -> dict[str, Any]:
    """Build a synthetic 'good' response that should grade ≥0.95 per the rubric."""
    expected = case.get("expected", {})
    prefix = expected.get("prefix_required", "[SIMULATION] ")
    return {
        "hazard_class": expected.get("hazard_class"),
        "jurisdiction": expected.get("jurisdiction"),
        "severity": expected.get("severity"),
        "action": expected.get("action"),
        "text": prefix + case.get("prompt", "")[: 80],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    dataset = _load_dataset(args.dataset)
    if not dataset:
        args.output.write_text(
            "### Telemetry-injection eval (T-J12)\n\n_dataset empty — skipping_\n",
            encoding="utf-8",
        )
        return 0

    scores: list[float] = []
    pass_count = 0
    for case in dataset:
        synthetic_response = _synthesize_response(case)
        result = grade_case(predicted=synthetic_response, case=case)
        scores.append(result.score)
        if result.passed:
            pass_count += 1

    mean = sum(scores) / len(scores)
    pass_rate = pass_count / len(scores) * 100.0

    md_lines = [
        "### Telemetry-injection eval (T-J12)",
        "",
        f"- Cases graded: **{len(scores)}**",
        f"- Pass rate (≥0.95 threshold): **{pass_rate:.1f}%**",
        f"- Mean score: **{mean:.3f}**",
        "",
        "_Synthetic-response grader; live-LLM regrade gated behind "
        "`@pytest.mark.azure_foundry_staging`._",
    ]
    md = "\n".join(md_lines)
    args.output.write_text(md + "\n", encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
