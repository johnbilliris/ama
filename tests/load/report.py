import csv
from pathlib import Path


def evaluate_threshold(*, value: float, threshold: float, lower_is_better: bool = True) -> bool:
    if lower_is_better:
        return value <= threshold
    return value >= threshold


def generate_report(stats_csv_path: str) -> dict[str, dict[str, float | bool]]:
    rows = list(csv.DictReader(Path(stats_csv_path).read_text(encoding="utf-8").splitlines()))
    response_time_p95 = max(float(row.get("95%", 0.0) or 0.0) for row in rows) if rows else 0.0
    error_rate = max(float(row.get("Failure Count", 0.0) or 0.0) for row in rows) if rows else 0.0

    dashboard_target = evaluate_threshold(
        value=response_time_p95, threshold=2000.0, lower_is_better=True
    )
    read_api_target = evaluate_threshold(
        value=response_time_p95, threshold=500.0, lower_is_better=True
    )
    signal_error_target = evaluate_threshold(
        value=error_rate, threshold=1.0, lower_is_better=True
    )

    return {
        "dashboard_p95_lt_2s": {
            "value": response_time_p95, "threshold": 2000.0, "passed": dashboard_target
        },
        "read_api_p95_lt_500ms": {
            "value": response_time_p95, "threshold": 500.0, "passed": read_api_target
        },
        "signal_throughput_50k_hr": {
            "value": error_rate, "threshold": 1.0, "passed": signal_error_target
        },
    }
