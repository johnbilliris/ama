"""Wave C / T-AA17 — ``assert_sli_thresholds()`` Z6/Z7 invariants test.

Three scenarios:

* green dataset (sample_count ≥ 30 + thresholds inside budget) → passes;
* sample-size starvation (sample_count < 30) → ``StagingPromotionRefused``;
* threshold breach (Z6 latency over budget OR Z7 drift below 99.0 %) →
  ``StagingPromotionRefused``.

Cycle 3 / T-AA34 / A3-06 — Z7 breach band amended from < 99.5 % to
< 99.0 %; the warn band remains 99.5 % (distinct bands, per
``contracts/sli-thresholds.md`` §6b L271-274). Test fixture for the
breach scenario uses 98.5 % so the assertion remains active under the
new threshold.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import pytest

from tests.staging_gates import (
    MIN_SAMPLES_PER_SLI_24H,
    StagingPromotionRefused,
    assert_sli_thresholds,
)


def _green_results() -> dict:
    return {
        "SLI-Z6": {
            "sample_count": MIN_SAMPLES_PER_SLI_24H,
            "per_model": {
                "gpt-4o": {"p95_latency_ms": 3500},
                "gpt-4o-mini": {"p95_latency_ms": 1200},
            },
        },
        "SLI-Z7": {
            "sample_count": MIN_SAMPLES_PER_SLI_24H + 5,
            "drift_budget_pct": 99.7,
        },
    }


def test_assert_thresholds_green_dataset_passes() -> None:
    assert_sli_thresholds(sli_results=_green_results())


def test_assert_thresholds_z6_sample_starvation_refuses() -> None:
    res = _green_results()
    res["SLI-Z6"]["sample_count"] = 5
    with pytest.raises(StagingPromotionRefused, match="sample-size starvation"):
        assert_sli_thresholds(sli_results=res)


def test_assert_thresholds_z7_sample_starvation_refuses() -> None:
    res = _green_results()
    res["SLI-Z7"]["sample_count"] = 1
    with pytest.raises(StagingPromotionRefused, match="sample-size starvation"):
        assert_sli_thresholds(sli_results=res)


def test_assert_thresholds_z6_breach_gpt4o_refuses() -> None:
    res = _green_results()
    res["SLI-Z6"]["per_model"]["gpt-4o"] = {"p95_latency_ms": 5500}
    with pytest.raises(StagingPromotionRefused, match="SLI-Z6 BREACH"):
        assert_sli_thresholds(sli_results=res)


def test_assert_thresholds_z6_breach_gpt4omini_refuses() -> None:
    res = _green_results()
    res["SLI-Z6"]["per_model"]["gpt-4o-mini"] = {"p95_latency_ms": 2500}
    with pytest.raises(StagingPromotionRefused, match="SLI-Z6 BREACH"):
        assert_sli_thresholds(sli_results=res)


def test_assert_thresholds_z7_breach_refuses() -> None:
    res = _green_results()
    # Cycle 3 / T-AA34 / A3-06 / HIGH-1 — fixture lowered from 99.0 to
    # 98.5 because the breach band moved to < 99.0 %; 99.0 is no longer
    # below the threshold and would not trigger ``StagingPromotionRefused``.
    res["SLI-Z7"]["drift_budget_pct"] = 98.5
    with pytest.raises(StagingPromotionRefused, match="SLI-Z7 BREACH"):
        assert_sli_thresholds(sli_results=res)


def test_assert_thresholds_missing_z6_refuses() -> None:
    res = {"SLI-Z7": _green_results()["SLI-Z7"]}
    with pytest.raises(StagingPromotionRefused, match="SLI-Z6"):
        assert_sli_thresholds(sli_results=res)
