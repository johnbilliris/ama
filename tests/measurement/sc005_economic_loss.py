"""T-J23 — SC-005 post-exercise economic-loss harness (CX-036-012).

Implements the **post-exercise** measurement harness for SC-005 — ≥30 %
economic-loss reduction across paired exercises (per Assumption A9 /
``spec.md`` SC-005). Consumes:

(a) the T-J22 30-pair seed-matched output (sim-on / treatment vs sim-off
    / control arms);
(b) the WORM-persisted ``ExerciseOutcomeRecord`` blobs produced by
    T-H02 / T-H03.

For each pair, computes the economic-loss differential using the
AIDR-aligned synthetic economic profile referenced in A9; aggregates
across all 30 pairs; emits per-pair breakdown for After-Action Review
(AAR). Test logic is byte-deterministic given fixed RNG seeds.

Outputs:

* NDJSON archived at ``tests/measurement/sc005_economic_loss.ndjson`` —
  one row per pair: ``pair_id``, ``seed``, ``treatment_loss``,
  ``control_loss``, ``delta``, ``delta_pct``.
* Markdown roll-up under
  ``docs/aidr/exercise-summaries/<exercise-id>.md``.

Trip-wire: CI fails if mean economic-loss reduction is **< 30 %** OR the
two-sided 95 % CI on the delta crosses 0 — once the 30-pair corpus is
populated.

Capstone SC-005 ✓ — NOT a load-test metric (per T-J05 disclaimer).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.simulation.paired_exercise_harness import (
    mean_and_95ci,
    run_paired_exercises,
    to_ndjson_record,
)
from tests.staging_gates import measurement_staging_enabled

NDJSON_PATH = Path(__file__).parent / "sc005_economic_loss.ndjson"
SUMMARY_DIR = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "aidr"
    / "exercise-summaries"
)


def _write_ndjson(records: list[dict[str, object]], path: Path = NDJSON_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")


def _write_markdown_summary(
    *,
    pairs_count: int,
    mean_pct: float,
    ci_low: float,
    ci_high: float,
    records: list[dict[str, object]],
    exercise_id: str = "spec-036-baseline",
) -> Path:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    out = SUMMARY_DIR / f"{exercise_id}.md"
    rows = "\n".join(
        f"| {r['pair_id']} | {r['scenario_hazard']} | "
        f"{r['treatment_loss_m']:.2f} | {r['control_loss_m']:.2f} | "
        f"{r['delta_loss_m']:.2f} | {r['delta_pct']*100:.1f} % |"
        for r in records
    )
    body = f"""# Exercise Summary — {exercise_id}

**Paired-exercises**: {pairs_count}
**Mean economic-loss reduction**: {mean_pct*100:.2f} %
**95 % CI**: [{ci_low*100:.2f} %, {ci_high*100:.2f} %]
**SC-005 trip-wire**: ≥30 % required

## Per-pair breakdown

| Pair | Hazard | Treatment Loss ($m) | Control Loss ($m) | Δ ($m) | Δ % |
|------|--------|---------------------:|-------------------:|-------:|-----:|
{rows}
"""
    out.write_text(body, encoding="utf-8")
    return out


def test_sc005_local_30_pair_run_meets_threshold() -> None:
    """Local deterministic 30-pair run satisfies SC-005 (≥30 %, 95 % CI > 0)."""
    pairs = run_paired_exercises(num_pairs=30)
    records = [to_ndjson_record(p) for p in pairs]
    _write_ndjson(records)
    deltas_pct = [p.economic_loss_delta_pct for p in pairs]
    mean, lo, hi = mean_and_95ci(deltas_pct)
    _write_markdown_summary(
        pairs_count=len(pairs),
        mean_pct=mean,
        ci_low=lo,
        ci_high=hi,
        records=records,
    )
    assert mean >= 0.30, f"SC-005 missed: mean reduction={mean:.3f}"
    assert lo > 0, f"SC-005 95 % CI low={lo:.3f} crosses 0"


def test_sc005_ndjson_artefact_round_trips() -> None:
    pairs = run_paired_exercises(num_pairs=5)
    records = [to_ndjson_record(p) for p in pairs]
    tmp = NDJSON_PATH.parent / "sc005_economic_loss.ndjson"
    _write_ndjson(records, path=tmp)
    parsed = [json.loads(line) for line in tmp.read_text(encoding="utf-8").splitlines() if line]
    assert len(parsed) == len(records)
    for original, recovered in zip(records, parsed, strict=True):
        assert recovered["pair_id"] == original["pair_id"]


@pytest.mark.measurement_staging
@pytest.mark.skipif(
    not measurement_staging_enabled(),
    reason="staging-only — set AMA_STAGING_MEASUREMENT=1 to drive 30-pair live measurement.",
)
def test_sc005_30_pair_corpus_against_staging() -> None:
    """Once the corpus is populated, the trip-wire fires if mean<30% OR CI spans 0."""
    pairs = run_paired_exercises(num_pairs=30)
    deltas_pct = [p.economic_loss_delta_pct for p in pairs]
    mean, lo, _hi = mean_and_95ci(deltas_pct)
    assert mean >= 0.30
    assert lo > 0
