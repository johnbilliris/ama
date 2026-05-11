"""T-J09 helper — assert plan-canonical SLI thresholds against a Locust CSV summary.

Reads `locust-report_stats.csv` produced by `--csv locust-report`,
extracts p95 latencies for the request name `inject-telemetry`, and
exits non-zero if the thresholds in `plan.md` are breached.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

P95_PARSE_TO_PIPELINE_MS = 5_000
ERROR_RATE_THRESHOLD = 0.01


def main(csv_path: str) -> int:
    p = Path(csv_path)
    if not p.exists():
        print(f"locust stats CSV not found: {csv_path}")
        return 1
    with p.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    rows = [r for r in rows if r.get("Name") == "inject-telemetry"]
    if not rows:
        print("no inject-telemetry rows in stats CSV")
        return 1
    row = rows[0]
    p95 = float(row.get("95%") or 0)
    fail_count = float(row.get("Failure Count") or 0)
    request_count = float(row.get("Request Count") or 1)
    error_rate = fail_count / max(1, request_count)
    breaches: list[str] = []
    if p95 > P95_PARSE_TO_PIPELINE_MS:
        breaches.append(f"parse-to-pipeline p95={p95:.0f}ms > {P95_PARSE_TO_PIPELINE_MS}ms")
    if error_rate > ERROR_RATE_THRESHOLD:
        breaches.append(f"error_rate={error_rate:.4f} > {ERROR_RATE_THRESHOLD}")
    if breaches:
        print("LOCUST_FAIL:", "; ".join(breaches))
        return 2
    print(f"LOCUST_OK: p95={p95:.0f}ms, error_rate={error_rate:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "locust-report_stats.csv"))
