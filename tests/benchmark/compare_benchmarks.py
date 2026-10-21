"""Benchmark comparison wrapper for regression detection.

Compares pytest-benchmark JSON output against a stored baseline,
applying SLO targets and regression thresholds to produce a
human-readable report with pass/fail signals for CI.
"""

from __future__ import annotations

import json
import logging
import math
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────

WARNING_THRESHOLD: float = 0.20  # ≥ 20% p95 increase → warning
FAILURE_THRESHOLD: float = 0.50  # ≥ 50% p95 increase → failure

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
    # Lightweight CI concurrent API checks
    "test_api_dashboard_p95_concurrent": 2.0,
    "test_api_signals_list_p95_concurrent": 0.5,
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

REQUIRED_BENCHMARKS: tuple[str, ...] = (
    "test_api_dashboard_p95_concurrent",
    "test_api_signals_list_p95_concurrent",
)


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class MetricComparison:
    """A single benchmark's comparison result."""

    benchmark_name: str
    group: str
    agent: str | None
    baseline_p95_s: float | None
    current_p95_s: float
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


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        raise ValueError("cannot compute percentile for empty sample list")
    ordered = sorted(values)
    index = int(round((pct / 100.0) * (len(ordered) - 1)))
    index = max(0, min(index, len(ordered) - 1))
    return float(ordered[index])


def _extract_p95_seconds(benchmark: dict) -> float:
    extra = benchmark.get("extra_info", {}) or {}
    from_extra = extra.get("p95_s")
    if from_extra is not None:
        value = float(from_extra)
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"invalid p95_s in extra_info for {benchmark.get('name', 'unknown')}")
        return value

    stats = benchmark.get("stats", {}) or {}
    data = stats.get("data")
    if isinstance(data, list) and data:
        return _percentile([float(v) for v in data], 95.0)

    raise ValueError(f"missing p95 samples for benchmark {benchmark.get('name', 'unknown')}")


def _compatible_environment(current: dict, baseline: dict) -> bool:
    current_machine = current.get("machine_info")
    baseline_machine = baseline.get("machine_info")
    if not isinstance(current_machine, dict) or not isinstance(baseline_machine, dict):
        return False

    for key in ("system", "machine", "python_implementation"):
        current_value = current_machine.get(key)
        baseline_value = baseline_machine.get(key)
        if not isinstance(current_value, str) or not isinstance(baseline_value, str):
            return False
        if current_value.casefold() != baseline_value.casefold():
            return False

    current_version = current_machine.get("python_version")
    baseline_version = baseline_machine.get("python_version")
    if not isinstance(current_version, str) or not isinstance(baseline_version, str):
        return False

    current_version_parts = current_version.split(".")
    baseline_version_parts = baseline_version.split(".")
    if len(current_version_parts) < 2 or len(baseline_version_parts) < 2:
        return False
    if not all(part.isdigit() for part in current_version_parts[:2] + baseline_version_parts[:2]):
        return False
    return current_version_parts[:2] == baseline_version_parts[:2]


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
        report.overall_status = "FAILURE"
        report.has_failures = True
        report.summary = "Current benchmark results missing or invalid."
        return report

    # Load baseline (optional)
    baseline_data = load_benchmark_json(baseline_path)
    incompatible_baseline = baseline_data is not None and not _compatible_environment(current_data, baseline_data)
    if incompatible_baseline:
        logger.warning(
            "Benchmark baseline environment differs from current run; enforcing SLOs without relative comparison"
        )
        baseline_data = None

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

    for required_name in REQUIRED_BENCHMARKS:
        if required_name not in current_by_name:
            report.has_failures = True
            report.results.append(
                MetricComparison(
                    benchmark_name=required_name,
                    group="api-lightweight",
                    agent="api",
                    baseline_p95_s=None,
                    current_p95_s=0.0,
                    slo_target_s=targets.get(required_name),
                    slo_pass=False,
                    pct_change=None,
                    status="FAILURE",
                    message=f"missing required metric: {required_name}",
                )
            )

    # Compare current benchmarks against baseline
    for name, current_bench in current_by_name.items():
        group = current_bench.get("group", "unknown")
        extra = current_bench.get("extra_info", {})
        agent = extra.get("agent")
        slo_target = targets.get(name)
        try:
            current_p95 = _extract_p95_seconds(current_bench)
        except ValueError as exc:
            report.has_failures = True
            report.results.append(
                MetricComparison(
                    benchmark_name=name,
                    group=group,
                    agent=agent,
                    baseline_p95_s=None,
                    current_p95_s=0.0,
                    slo_target_s=slo_target,
                    slo_pass=False,
                    pct_change=None,
                    status="FAILURE",
                    message=str(exc),
                )
            )
            continue
        slo_pass = slo_target is None or current_p95 <= slo_target

        if name not in baseline_by_name:
            # First run for this metric
            status = "FIRST_RUN"
            message = (
                f"No compatible baseline for {name} — enforcing SLO only"
                if incompatible_baseline
                else f"First run for {name} — no baseline to compare"
            )
            if slo_target is not None and not slo_pass:
                status = "FAILURE"
                message = f"{name}: first run p95={current_p95:.3f}s breaches SLO={slo_target:.3f}s"
                report.has_failures = True
            report.results.append(
                MetricComparison(
                    benchmark_name=name,
                    group=group,
                    agent=agent,
                    baseline_p95_s=None,
                    current_p95_s=current_p95,
                    slo_target_s=slo_target,
                    slo_pass=slo_pass,
                    pct_change=None,
                    status=status,
                    message=message,
                )
            )
            continue

        baseline_bench = baseline_by_name[name]
        try:
            baseline_p95 = _extract_p95_seconds(baseline_bench)
        except ValueError as exc:
            report.has_failures = True
            report.results.append(
                MetricComparison(
                    benchmark_name=name,
                    group=group,
                    agent=agent,
                    baseline_p95_s=None,
                    current_p95_s=current_p95,
                    slo_target_s=slo_target,
                    slo_pass=False,
                    pct_change=None,
                    status="FAILURE",
                    message=f"baseline metric invalid for {name}: {exc}",
                )
            )
            continue

        if baseline_p95 <= 0:
            report.has_failures = True
            report.results.append(
                MetricComparison(
                    benchmark_name=name,
                    group=group,
                    agent=agent,
                    baseline_p95_s=baseline_p95,
                    current_p95_s=current_p95,
                    slo_target_s=slo_target,
                    slo_pass=False,
                    pct_change=None,
                    status="FAILURE",
                    message=f"baseline p95 for {name} must be > 0",
                )
            )
            continue

        pct_change = (current_p95 - baseline_p95) / baseline_p95

        if not slo_pass:
            status = "FAILURE"
            message = f"{name}: p95={current_p95:.3f}s breaches SLO={slo_target:.3f}s"
            report.has_failures = True
        elif pct_change >= FAILURE_THRESHOLD:
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
                baseline_p95_s=baseline_p95,
                current_p95_s=current_p95,
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
            try:
                baseline_p95 = _extract_p95_seconds(baseline_bench)
            except ValueError:
                baseline_p95 = 0.0
            logger.info(
                "Baseline metric %s not found in current run — logging as BASELINE_ONLY",
                name,
            )
            is_required = name in REQUIRED_BENCHMARKS
            if is_required:
                report.has_failures = True
            report.results.append(
                MetricComparison(
                    benchmark_name=name,
                    group=group,
                    agent=agent,
                    baseline_p95_s=baseline_p95,
                    current_p95_s=0.0,
                    slo_target_s=targets.get(name),
                    slo_pass=False if is_required else True,
                    pct_change=None,
                    status="FAILURE" if is_required else "BASELINE_ONLY",
                    message=(
                        f"missing required metric in current run: {name}"
                        if is_required
                        else f"{name}: present in baseline but not in current run"
                    ),
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
        ms = r.current_p95_s * 1000

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
        lines.append(f" {emoji}  {r.benchmark_name:<35} {ms:>8.1f} ms{slo_part}  {pct_str}")

    lines.append("─" * 55)
    lines.append(f" {report.summary}")
    lines.append("═" * 55)
    lines.append("")

    return "\n".join(lines)
