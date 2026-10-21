from __future__ import annotations

import json
from pathlib import Path

from tests.benchmark.compare_benchmarks import compare_benchmarks

REQUIRED_DASHBOARD = "test_api_dashboard_p95_concurrent"
REQUIRED_SIGNALS = "test_api_signals_list_p95_concurrent"


def _write_benchmark_json(
    path: Path,
    benchmarks: list[dict],
    *,
    machine_info: dict[str, str] | None = None,
) -> None:
    path.write_text(
        json.dumps(
            {
                "benchmarks": benchmarks,
                "machine_info": machine_info
                or {
                    "system": "Linux",
                    "machine": "x86_64",
                    "python_implementation": "CPython",
                    "python_version": "3.12.0",
                },
            }
        ),
        encoding="utf-8",
    )


def _bench(name: str, *, median_s: float, p95_s: float, group: str = "api-lightweight") -> dict:
    return {
        "name": name,
        "group": group,
        "stats": {
            "median": median_s,
            "data": [median_s, p95_s, p95_s, p95_s, p95_s],
        },
        "extra_info": {
            "agent": "api",
            "p95_s": p95_s,
        },
    }


def test_compare_benchmarks_fails_when_current_is_missing(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    _write_benchmark_json(baseline, [_bench(REQUIRED_DASHBOARD, median_s=0.1, p95_s=0.2)])

    report = compare_benchmarks(current_path=tmp_path / "current-missing.json", baseline_path=baseline)

    assert report.overall_status == "FAILURE"
    assert report.has_failures is True
    assert "missing or invalid" in report.summary


def test_compare_benchmarks_fails_when_current_is_corrupt(tmp_path: Path) -> None:
    current = tmp_path / "current.json"
    baseline = tmp_path / "baseline.json"
    current.write_text("{not json", encoding="utf-8")
    _write_benchmark_json(baseline, [_bench(REQUIRED_DASHBOARD, median_s=0.1, p95_s=0.2)])

    report = compare_benchmarks(current_path=current, baseline_path=baseline)

    assert report.overall_status == "FAILURE"
    assert report.has_failures is True


def test_compare_benchmarks_fails_on_missing_required_metric(tmp_path: Path) -> None:
    current = tmp_path / "current.json"
    baseline = tmp_path / "baseline.json"
    _write_benchmark_json(current, [_bench(REQUIRED_DASHBOARD, median_s=0.1, p95_s=0.2)])
    _write_benchmark_json(
        baseline,
        [
            _bench(REQUIRED_DASHBOARD, median_s=0.1, p95_s=0.2),
            _bench(REQUIRED_SIGNALS, median_s=0.1, p95_s=0.2),
        ],
    )

    report = compare_benchmarks(current_path=current, baseline_path=baseline)

    assert report.overall_status == "FAILURE"
    assert report.has_failures is True
    assert any("missing required metric" in result.message for result in report.results)


def test_compare_benchmarks_fails_first_run_when_p95_breaches_slo(tmp_path: Path) -> None:
    current = tmp_path / "current.json"
    _write_benchmark_json(
        current,
        [
            _bench(REQUIRED_DASHBOARD, median_s=0.1, p95_s=2.1),
            _bench(REQUIRED_SIGNALS, median_s=0.1, p95_s=0.2),
        ],
    )

    report = compare_benchmarks(current_path=current, baseline_path=tmp_path / "missing-baseline.json")

    assert report.overall_status == "FAILURE"
    assert report.has_failures is True
    assert any(
        result.benchmark_name == REQUIRED_DASHBOARD and "breaches SLO" in result.message for result in report.results
    )


def test_compare_benchmarks_uses_p95_not_median(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CI", "true")
    current = tmp_path / "current.json"
    baseline = tmp_path / "baseline.json"
    _write_benchmark_json(
        current,
        [
            _bench(REQUIRED_DASHBOARD, median_s=0.10, p95_s=0.30),
            _bench(REQUIRED_SIGNALS, median_s=0.10, p95_s=0.70),
        ],
    )
    _write_benchmark_json(
        baseline,
        [
            _bench(REQUIRED_DASHBOARD, median_s=0.30, p95_s=0.35),
            _bench(REQUIRED_SIGNALS, median_s=0.30, p95_s=0.20),
        ],
    )

    report = compare_benchmarks(current_path=current, baseline_path=baseline)

    assert report.overall_status == "FAILURE"
    assert report.has_failures is True
    assert any(result.benchmark_name == REQUIRED_SIGNALS and result.current_p95_s == 0.70 for result in report.results)


def test_compare_benchmarks_uses_slo_for_incompatible_environment(tmp_path: Path) -> None:
    current = tmp_path / "current.json"
    baseline = tmp_path / "baseline.json"
    _write_benchmark_json(
        current,
        [
            _bench(REQUIRED_DASHBOARD, median_s=0.15, p95_s=0.16),
            _bench(REQUIRED_SIGNALS, median_s=0.08, p95_s=0.09),
        ],
        machine_info={
            "system": "Linux",
            "machine": "x86_64",
            "python_implementation": "CPython",
            "python_version": "3.12.14",
        },
    )
    _write_benchmark_json(
        baseline,
        [
            _bench(REQUIRED_DASHBOARD, median_s=0.08, p95_s=0.10),
            _bench(REQUIRED_SIGNALS, median_s=0.03, p95_s=0.04),
        ],
        machine_info={
            "system": "Windows",
            "machine": "AMD64",
            "python_implementation": "CPython",
            "python_version": "3.12.10",
        },
    )

    report = compare_benchmarks(current_path=current, baseline_path=baseline)

    assert report.overall_status == "PASS"
    assert report.has_failures is False
    assert {result.status for result in report.results} == {"FIRST_RUN"}
    assert all("No compatible baseline" in result.message for result in report.results)


def test_compare_benchmarks_fails_on_empty_benchmark_list(tmp_path: Path) -> None:
    current = tmp_path / "current.json"
    baseline = tmp_path / "baseline.json"
    _write_benchmark_json(current, [])
    _write_benchmark_json(baseline, [_bench(REQUIRED_DASHBOARD, median_s=0.1, p95_s=0.2)])

    report = compare_benchmarks(current_path=current, baseline_path=baseline)

    assert report.overall_status == "FAILURE"
    assert report.has_failures is True
