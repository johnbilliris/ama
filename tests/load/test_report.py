from __future__ import annotations

import csv
from pathlib import Path

import pytest

from tests.load.report import generate_report


def _write_stats_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "Type",
        "Name",
        "Request Count",
        "Failure Count",
        "Median Response Time",
        "Average Response Time",
        "Min Response Time",
        "Max Response Time",
        "Average Content Size",
        "Requests/s",
        "Failures/s",
        "50%",
        "66%",
        "75%",
        "80%",
        "90%",
        "95%",
        "98%",
        "99%",
        "99.9%",
        "99.99%",
        "100%",
        "Total Request Count",
        "Total Failure Count",
        "Total Median Response Time",
        "Total Average Response Time",
        "Total Min Response Time",
        "Total Max Response Time",
        "Total Average Content Size",
        "Total RPS",
        "Total Failures/s",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _base_rows() -> list[dict[str, str]]:
    return [
        {
            "Type": "GET",
            "Name": "dashboard_incident_aggregate",
            "Request Count": "200",
            "Failure Count": "0",
            "95%": "1500",
            "Total RPS": "100",
            "Total Average Response Time": "2000",
        },
        {
            "Type": "GET",
            "Name": "signals_list",
            "Request Count": "200",
            "Failure Count": "0",
            "95%": "450",
            "Total RPS": "100",
            "Total Average Response Time": "2000",
        },
        {
            "Type": "POST",
            "Name": "signals_ingest",
            "Request Count": "100000",
            "Failure Count": "500",
            "95%": "250",
            "Total RPS": "100",
            "Total Average Response Time": "2000",
        },
        {
            "Type": "Aggregated",
            "Name": "Aggregated",
            "Request Count": "100000",
            "Failure Count": "500",
            "95%": "1600",
            "Total RPS": "100",
            "Total Average Response Time": "1000",
        },
    ]


def test_generate_report_uses_endpoint_specific_p95_and_true_counts(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    _write_stats_csv(csv_path, _base_rows())

    report = generate_report(
        str(csv_path),
        environment="staging",
        revision="rev-123",
        concurrent_users=1000,
    )

    dashboard = report["results"]["dashboard_p95_lt_2s"]
    read_api = report["results"]["read_api_p95_lt_500ms"]
    throughput = report["results"]["signal_throughput_50k_hr"]

    assert dashboard["value"] == 1500.0
    assert dashboard["passed"] is True
    assert read_api["value"] == 450.0
    assert read_api["passed"] is True

    # Hand-computed: duration = 100000 / 100 = 1000 s
    # successful_signals_per_hour = ((100000 - 500) / 1000) * 3600 = 358200
    assert throughput["value"] == 358200.0
    assert throughput["passed"] is True

    payload = throughput["load_test_result"]
    assert payload["totalRequests"] == 100000
    assert payload["successfulRequests"] == 99500
    assert payload["failedRequests"] == 500
    assert payload["durationSeconds"] == 1000.0
    assert payload["concurrentUsers"] == 1000
    assert payload["environment"] == "staging"
    assert "revision=rev-123" in payload["notes"]


def test_generate_report_fails_dashboard_only_when_read_api_is_fast(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    rows = _base_rows()
    rows[0]["95%"] = "2100"
    rows[1]["95%"] = "300"
    _write_stats_csv(csv_path, rows)

    report = generate_report(str(csv_path))

    assert report["results"]["dashboard_p95_lt_2s"]["passed"] is False
    assert report["results"]["read_api_p95_lt_500ms"]["passed"] is True


def test_generate_report_enforces_strict_latency_thresholds(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    rows = _base_rows()
    rows[0]["95%"] = "2000"
    rows[1]["95%"] = "500"
    _write_stats_csv(csv_path, rows)

    report = generate_report(str(csv_path))

    assert report["results"]["dashboard_p95_lt_2s"]["passed"] is False
    assert report["results"]["read_api_p95_lt_500ms"]["passed"] is False


@pytest.mark.parametrize(
    "rows, expected_error",
    [
        ([], "load report input is empty"),
        ([{"Name": "dashboard_incident_aggregate"}], "missing required request row"),
    ],
)
def test_generate_report_fails_closed_for_empty_and_header_only(
    tmp_path: Path,
    rows: list[dict[str, str]],
    expected_error: str,
) -> None:
    csv_path = tmp_path / "stats.csv"
    if rows:
        _write_stats_csv(csv_path, rows)
    else:
        csv_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match=expected_error):
        generate_report(str(csv_path))


def test_generate_report_rejects_missing_required_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    csv_path.write_text("Name\n dashboard_incident_aggregate\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        generate_report(str(csv_path))


@pytest.mark.parametrize(
    "field,value,expected_error",
    [
        ("95%", "NaN", "non-finite numeric value"),
        ("95%", "-1", "negative numeric value"),
        ("Request Count", "0", "required request rows must have request count > 0"),
    ],
)
def test_generate_report_rejects_nan_negative_and_zero_requests(
    tmp_path: Path,
    field: str,
    value: str,
    expected_error: str,
) -> None:
    csv_path = tmp_path / "stats.csv"
    rows = _base_rows()
    rows[0][field] = value
    _write_stats_csv(csv_path, rows)

    with pytest.raises(ValueError, match=expected_error):
        generate_report(str(csv_path))


def test_generate_report_rejects_missing_required_row(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    rows = [row for row in _base_rows() if row["Name"] != "signals_list"]
    _write_stats_csv(csv_path, rows)

    with pytest.raises(ValueError, match="missing required request row: signals_list"):
        generate_report(str(csv_path))


def test_generate_report_rejects_missing_duration_inputs(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    rows = _base_rows()
    rows[-1]["Total RPS"] = ""
    rows[-1]["Total Average Response Time"] = ""
    _write_stats_csv(csv_path, rows)

    with pytest.raises(ValueError, match="unable to derive run duration"):
        generate_report(str(csv_path))
