"""Benchmark comparison wrapper for regression detection.

Compares pytest-benchmark JSON output against a stored baseline,
applying SLO targets and regression thresholds to produce a
human-readable report with pass/fail signals for CI.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────

WARNING_THRESHOLD: float = 0.20  # ≥ 20% median increase → warning
FAILURE_THRESHOLD: float = 0.50  # ≥ 50% median increase → failure

BASELINE_PATH: Path = Path(".benchmarks/baseline.json")
CURRENT_PATH: Path = Path(".benchmarks/current.json")

# ── SLO targets (seconds) ────────────────────────────────────────────────────

DEFAULT_SLO_TARGETS: dict[str, float] = {
    # Health endpoints
    "test_health_monitoring": 0.100,
    "test_health_risk": 0.075,
    "test_health_evacuation": 0.075,
    "test_health_resource": 0.100,
    "test_health_communication": 0.100,
    # Pipeline processing
    "test_pipeline_monitoring": 2.0,
    "test_pipeline_risk": 2.0,
    "test_pipeline_evacuation": 2.0,
    "test_pipeline_resource": 2.0,
    "test_pipeline_communication": 2.0,
    # LLM client
    "test_llm_client_overhead": 0.500,
    # Circuit breaker — SLO is dynamic (2× recovery_timeout),
    # validated inside the test, not in the wrapper
}


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class MetricComparison:
    """A single benchmark's comparison result."""

    benchmark_name: str
    group: str
    agent: str | None
    baseline_median_s: float | None
    current_median_s: float
    slo_target_s: float | None
    slo_pass: bool
    pct_change: float | None
    status: str  # PASS | WARNING | FAILURE | FIRST_RUN | BASELINE_ONLY | ERROR
    message: str


@dataclass
class ComparisonReport:
    """Structured regression detection report."""

    timestamp: str
    commit_sha: str
    baseline_file: str
    current_file: str
    overall_status: str  # PASS | WARNING | FAILURE
    has_failures: bool
    results: list[MetricComparison] = field(default_factory=list)
    summary: str = ""


# ── Helper functions ──────────────────────────────────────────────────────────


def load_benchmark_json(path: Path) -> dict | None:
    """Load and validate pytest-benchmark JSON from *path*.

    Returns the parsed dict on success, or ``None`` if the file is
    missing, corrupted, or does not contain a ``benchmarks`` array.
    """
    if not path.exists():
        logger.warning("Benchmark file not found: %s", path)
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to parse benchmark file %s: %s", path, exc)
        return None

    if not isinstance(data, dict) or "benchmarks" not in data:
        logger.warning("Benchmark file %s missing 'benchmarks' key", path)
        return None

    return data


def get_commit_sha() -> str:
    """Return the current git commit SHA, or ``'unknown'`` if unavailable."""
    try:
        result = subprocess.run(  # noqa: S603, S607
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


# ── Core comparison logic ─────────────────────────────────────────────────────


def compare_benchmarks(
    current_path: Path = CURRENT_PATH,
    baseline_path: Path = BASELINE_PATH,
    slo_targets: dict[str, float] | None = None,
) -> ComparisonReport:
    """Compare current benchmark results against stored baseline.

    Returns a :class:`ComparisonReport` with per-benchmark status and an
    overall pass/fail determination.
    """
    targets = slo_targets if slo_targets is not None else DEFAULT_SLO_TARGETS
    commit_sha = get_commit_sha()
    timestamp = datetime.now(UTC).isoformat()

    report = ComparisonReport(
        timestamp=timestamp,
        commit_sha=commit_sha,
        baseline_file=str(baseline_path),
        current_file=str(current_path),
        overall_status="PASS",
        has_failures=False,
    )

    # Load current results (required)
    current_data = load_benchmark_json(current_path)
    if current_data is None:
        report.summary = "No current benchmark results found — skipping comparison."
        return report

    # Load baseline (optional)
    baseline_data = load_benchmark_json(baseline_path)

    # Index baseline benchmarks by name
    baseline_by_name: dict[str, dict] = {}
    if baseline_data is not None:
        for bench in baseline_data.get("benchmarks", []):
            name = bench.get("name", "")
            if name:
                baseline_by_name[name] = bench

    # Index current benchmarks by name
    current_by_name: dict[str, dict] = {}
    for bench in current_data.get("benchmarks", []):
        name = bench.get("name", "")
        if name:
            current_by_name[name] = bench

    # Compare current benchmarks against baseline
    for name, current_bench in current_by_name.items():
        stats = current_bench.get("stats", {})
        current_median = stats.get("median", 0.0)
        group = current_bench.get("group", "unknown")
        extra = current_bench.get("extra_info", {})
        agent = extra.get("agent")
        slo_target = targets.get(name)
        slo_pass = slo_target is None or current_median <= slo_target

        if name not in baseline_by_name:
            # First run for this metric
            report.results.append(
                MetricComparison(
                    benchmark_name=name,
                    group=group,
                    agent=agent,
                    baseline_median_s=None,
                    current_median_s=current_median,
                    slo_target_s=slo_target,
                    slo_pass=slo_pass,
                    pct_change=None,
                    status="FIRST_RUN",
                    message=f"First run for {name} — no baseline to compare",
                )
            )
            continue

        baseline_bench = baseline_by_name[name]
        baseline_median = baseline_bench.get("stats", {}).get("median", 0.0)

        if baseline_median <= 0:
            logger.warning(
                "Baseline median is zero/negative for %s — skipping percentage comparison",
                name,
            )
            report.results.append(
                MetricComparison(
                    benchmark_name=name,
                    group=group,
                    agent=agent,
                    baseline_median_s=baseline_median,
                    current_median_s=current_median,
                    slo_target_s=slo_target,
                    slo_pass=slo_pass,
                    pct_change=None,
                    status="PASS",
                    message=f"Baseline median zero for {name} — skipped regression check",
                )
            )
            continue

        pct_change = (current_median - baseline_median) / baseline_median

        if pct_change >= FAILURE_THRESHOLD:
            status = "FAILURE"
            message = f"{name}: +{pct_change:.1%} regression (≥ {FAILURE_THRESHOLD:.0%} threshold)"
            report.has_failures = True
        elif pct_change >= WARNING_THRESHOLD:
            status = "WARNING"
            message = f"{name}: +{pct_change:.1%} regression (≥ {WARNING_THRESHOLD:.0%} threshold)"
            logger.warning(message)
        else:
            status = "PASS"
            if pct_change < 0:
                message = f"{name}: {pct_change:+.1%} (improved)"
            else:
                message = f"{name}: +{pct_change:.1%} (within threshold)"

        report.results.append(
            MetricComparison(
                benchmark_name=name,
                group=group,
                agent=agent,
                baseline_median_s=baseline_median,
                current_median_s=current_median,
                slo_target_s=slo_target,
                slo_pass=slo_pass,
                pct_change=pct_change,
                status=status,
                message=message,
            )
        )

    # Handle baseline-only metrics (present in baseline, absent from current)
    for name in baseline_by_name:
        if name not in current_by_name:
            baseline_bench = baseline_by_name[name]
            group = baseline_bench.get("group", "unknown")
            extra = baseline_bench.get("extra_info", {})
            agent = extra.get("agent")
            baseline_median = baseline_bench.get("stats", {}).get("median", 0.0)
            logger.info(
                "Baseline metric %s not found in current run — logging as BASELINE_ONLY",
                name,
            )
            report.results.append(
                MetricComparison(
                    benchmark_name=name,
                    group=group,
                    agent=agent,
                    baseline_median_s=baseline_median,
                    current_median_s=0.0,
                    slo_target_s=targets.get(name),
                    slo_pass=True,
                    pct_change=None,
                    status="BASELINE_ONLY",
                    message=f"{name}: present in baseline but not in current run",
                )
            )

    # Determine overall status (worst of all results)
    statuses = [r.status for r in report.results]
    if "FAILURE" in statuses:
        report.overall_status = "FAILURE"
    elif "WARNING" in statuses:
        report.overall_status = "WARNING"
    else:
        report.overall_status = "PASS"

    # Build summary
    n_pass = sum(1 for r in report.results if r.status == "PASS")
    n_warn = sum(1 for r in report.results if r.status == "WARNING")
    n_fail = sum(1 for r in report.results if r.status == "FAILURE")
    n_new = sum(1 for r in report.results if r.status == "FIRST_RUN")
    n_gone = sum(1 for r in report.results if r.status == "BASELINE_ONLY")

    parts: list[str] = []
    if n_fail:
        parts.append(f"{n_fail} failure{'s' if n_fail != 1 else ''}")
    if n_warn:
        parts.append(f"{n_warn} warning{'s' if n_warn != 1 else ''}")
    if n_new:
        parts.append(f"{n_new} new")
    if n_gone:
        parts.append(f"{n_gone} removed")
    if n_pass:
        parts.append(f"{n_pass} passed")

    report.summary = f"Overall: {report.overall_status} ({', '.join(parts)})"

    return report


# ── Report formatter ──────────────────────────────────────────────────────────

_STATUS_EMOJI = {
    "PASS": "✅ PASS",
    "WARNING": "⚠️ WARN",
    "FAILURE": "❌ FAIL",
    "FIRST_RUN": "🆕 NEW ",
    "BASELINE_ONLY": "⏭️ GONE",
    "ERROR": "💥 ERR ",
}


def format_report(report: ComparisonReport) -> str:
    """Render *report* as human-readable text for CI output."""
    lines: list[str] = [
        "",
        "═" * 55,
        f" Benchmark Regression Report — commit {report.commit_sha[:7]}",
        "═" * 55,
    ]

    for r in report.results:
        emoji = _STATUS_EMOJI.get(r.status, r.status)
        ms = r.current_median_s * 1000

        if r.slo_target_s is not None:
            if r.slo_target_s >= 1.0:
                slo_str = f"SLO: {r.slo_target_s:.0f} s"
            else:
                slo_str = f"SLO: {r.slo_target_s * 1000:.0f} ms"
        else:
            slo_str = ""

        if r.pct_change is not None:
            pct_str = f"{r.pct_change:+.1%}"
        elif r.status == "FIRST_RUN":
            pct_str = "first run"
        elif r.status == "BASELINE_ONLY":
            pct_str = "removed"
        else:
            pct_str = ""

        slo_part = f" ({slo_str})" if slo_str else ""
        lines.append(
            f" {emoji}  {r.benchmark_name:<35} {ms:>8.1f} ms{slo_part}  {pct_str}"
        )

    lines.append("─" * 55)
    lines.append(f" {report.summary}")
    lines.append("═" * 55)
    lines.append("")

    return "\n".join(lines)
