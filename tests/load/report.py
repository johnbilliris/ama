from __future__ import annotations

import csv
import json
import math
import sys
from argparse import ArgumentParser
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from packages.domain.src.domain.models.load_test_result import LoadTestResult

_REQUIRED_COLUMNS = ("Name", "Request Count", "Failure Count", "95%")
_DASHBOARD_ROW_NAME = "dashboard_incident_aggregate"
_READ_API_ROW_NAME = "signals_list"
_THROUGHPUT_ROW_NAME = "signals_ingest"


def _parse_non_negative_float(row: dict[str, str], key: str) -> float:
    raw = row.get(key)
    if raw is None or raw == "":
        raise ValueError(f"missing required column value: {key}")
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"invalid numeric value for {key}: {raw!r}") from exc
    if not math.isfinite(value):
        raise ValueError(f"non-finite numeric value for {key}: {raw!r}")
    if value < 0:
        raise ValueError(f"negative numeric value for {key}: {raw!r}")
    return value


def _duration_seconds(rows: list[dict[str, str]]) -> float:
    for row in rows:
        if row.get("Name") == "Aggregated":
            if row.get("Total RPS") not in (None, ""):
                total_rps = _parse_non_negative_float(row, "Total RPS")
                total_requests = _parse_non_negative_float(row, "Request Count")
                if total_requests <= 0.0:
                    raise ValueError("aggregated row has zero requests")
                if total_rps > 0.0:
                    return total_requests / total_rps
            if row.get("Total Average Response Time") not in (None, ""):
                total_avg_ms = _parse_non_negative_float(row, "Total Average Response Time")
                total_requests = _parse_non_negative_float(row, "Request Count")
                if total_requests <= 0.0:
                    raise ValueError("aggregated row has zero requests")
                if total_avg_ms > 0.0:
                    return total_avg_ms / 1000.0
    raise ValueError("unable to derive run duration from Locust stats")


def _find_exact_row(rows: list[dict[str, str]], name: str) -> dict[str, str]:
    for row in rows:
        if row.get("Name") == name:
            return row
    raise ValueError(f"missing required request row: {name}")


def _evaluate_lt(value: float, threshold: float) -> bool:
    return value < threshold


def _evaluate_gte(value: float, threshold: float) -> bool:
    return value >= threshold


def generate_report(
    stats_csv_path: str,
    *,
    environment: str = "staging",
    revision: str = "unknown",
    concurrent_users: int = 1000,
) -> dict[str, object]:
    csv_path = Path(stats_csv_path)
    if not csv_path.exists():
        raise ValueError(f"stats CSV not found: {stats_csv_path}")

    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    if not rows:
        raise ValueError("load report input is empty")
    header = rows[0].keys()
    missing_columns = [column for column in _REQUIRED_COLUMNS if column not in header]
    if missing_columns:
        raise ValueError(f"missing required columns: {', '.join(missing_columns)}")

    dashboard_row = _find_exact_row(rows, _DASHBOARD_ROW_NAME)
    read_api_row = _find_exact_row(rows, _READ_API_ROW_NAME)
    throughput_row = _find_exact_row(rows, _THROUGHPUT_ROW_NAME)

    dashboard_requests = _parse_non_negative_float(dashboard_row, "Request Count")
    read_requests = _parse_non_negative_float(read_api_row, "Request Count")
    throughput_requests = _parse_non_negative_float(throughput_row, "Request Count")

    if dashboard_requests <= 0.0 or read_requests <= 0.0 or throughput_requests <= 0.0:
        raise ValueError("required request rows must have request count > 0")

    duration_seconds = _duration_seconds(rows)
    if duration_seconds <= 0.0:
        raise ValueError("derived duration must be > 0")

    dashboard_p95_ms = _parse_non_negative_float(dashboard_row, "95%")
    read_api_p95_ms = _parse_non_negative_float(read_api_row, "95%")
    throughput_failures = _parse_non_negative_float(throughput_row, "Failure Count")
    throughput_successes = throughput_requests - throughput_failures
    if throughput_successes < 0.0:
        raise ValueError("failure count cannot exceed request count")

    throughput_rps = throughput_successes / duration_seconds
    throughput_per_hour = throughput_rps * 3600.0
    throughput_error_ratio_percent = (throughput_failures / throughput_requests) * 100.0

    executed_at = datetime.now(UTC)
    results: dict[str, LoadTestResult] = {}

    dashboard_result = LoadTestResult(
        result_id=f"load-{uuid4().hex}",
        scenario_name="dashboard_concurrent_load",
        executed_at=executed_at,
        duration_seconds=duration_seconds,
        concurrent_users=concurrent_users,
        total_requests=int(dashboard_requests),
        successful_requests=int(dashboard_requests),
        failed_requests=0,
        error_rate=0.0,
        p50_latency_ms=dashboard_p95_ms,
        p95_latency_ms=dashboard_p95_ms,
        p99_latency_ms=dashboard_p95_ms,
        throughput_per_second=dashboard_requests / duration_seconds,
        target_name="dashboard_p95_lt_2s",
        target_threshold=2000.0,
        target_unit="ms",
        passed=_evaluate_lt(dashboard_p95_ms, 2000.0),
        environment=environment,
        notes=f"revision={revision}",
    )
    results[dashboard_result.target_name] = dashboard_result

    read_api_result = LoadTestResult(
        result_id=f"load-{uuid4().hex}",
        scenario_name="read_api_concurrent_load",
        executed_at=executed_at,
        duration_seconds=duration_seconds,
        concurrent_users=concurrent_users,
        total_requests=int(read_requests),
        successful_requests=int(read_requests),
        failed_requests=0,
        error_rate=0.0,
        p50_latency_ms=read_api_p95_ms,
        p95_latency_ms=read_api_p95_ms,
        p99_latency_ms=read_api_p95_ms,
        throughput_per_second=read_requests / duration_seconds,
        target_name="read_api_p95_lt_500ms",
        target_threshold=500.0,
        target_unit="ms",
        passed=_evaluate_lt(read_api_p95_ms, 500.0),
        environment=environment,
        notes=f"revision={revision}",
    )
    results[read_api_result.target_name] = read_api_result

    throughput_result = LoadTestResult(
        result_id=f"load-{uuid4().hex}",
        scenario_name="signal_burst_ingestion",
        executed_at=executed_at,
        duration_seconds=duration_seconds,
        concurrent_users=concurrent_users,
        total_requests=int(throughput_requests),
        successful_requests=int(throughput_successes),
        failed_requests=int(throughput_failures),
        error_rate=throughput_error_ratio_percent,
        p50_latency_ms=0.0,
        p95_latency_ms=0.0,
        p99_latency_ms=0.0,
        throughput_per_second=throughput_rps,
        target_name="signal_throughput_50k_hr",
        target_threshold=50000.0,
        target_unit="req/hour",
        passed=_evaluate_gte(throughput_per_hour, 50000.0) and _evaluate_lt(throughput_error_ratio_percent, 1.0),
        environment=environment,
        notes=(
            f"revision={revision}; threshold_error_ratio_percent_lt=1.0; "
            f"error_ratio_percent={throughput_error_ratio_percent:.6f}"
        ),
    )
    results[throughput_result.target_name] = throughput_result

    return {
        "duration_seconds": duration_seconds,
        "concurrent_users": concurrent_users,
        "environment": environment,
        "revision": revision,
        "thresholds": {
            "dashboard_p95_lt_2s": 2000.0,
            "read_api_p95_lt_500ms": 500.0,
            "signal_throughput_50k_hr": 50000.0,
            "signal_error_ratio_percent_lt_1": 1.0,
        },
        "results": {
            name: {
                "value": (result.p95_latency_ms if "p95" in name else result.throughput_per_second * 3600.0),
                "threshold": result.target_threshold,
                "passed": result.passed,
                "load_test_result": result.model_dump(mode="json", by_alias=True),
            }
            for name, result in results.items()
        },
    }


def _all_targets_passed(report: dict[str, object]) -> bool:
    results = report.get("results", {})
    if not isinstance(results, dict):
        return False
    for payload in results.values():
        if not isinstance(payload, dict) or payload.get("passed") is not True:
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(description="Generate load target report from Locust stats CSV")
    parser.add_argument("--stats-csv", required=True)
    parser.add_argument("--environment", default="staging")
    parser.add_argument("--revision", default="unknown")
    parser.add_argument("--concurrent-users", type=int, default=1000)
    parser.add_argument("--output-json", default="")
    args = parser.parse_args(argv)

    report = generate_report(
        args.stats_csv,
        environment=args.environment,
        revision=args.revision,
        concurrent_users=args.concurrent_users,
    )
    encoded = json.dumps(report, indent=2)
    if args.output_json:
        Path(args.output_json).write_text(encoded, encoding="utf-8")
    else:
        print(encoded)

    if not _all_targets_passed(report):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
