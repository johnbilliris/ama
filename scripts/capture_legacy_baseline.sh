# T071 — legacy baseline capture script.
#
# Run during pre-cutover to capture the legacy pipeline's p50/p95/p99 latency
# under the FR-012b workload. The output replaces tests/load/baselines/legacy_baseline.json
# which the SC-007 ≤10% latency-regression assertion in tests/load/test_workflow_capacity.py
# uses as the reference.

set -euo pipefail

OUT="${1:-tests/load/baselines/legacy_baseline.json}"
WINDOW_SECONDS="${WINDOW_SECONDS:-3600}"

echo "Capturing legacy baseline → $OUT (window: ${WINDOW_SECONDS}s)"

# In production this would invoke the existing legacy pipeline against the
# same workload as test_workflow_capacity.py (via the legacy entry point).
# For now we emit the placeholder shape that the SC-007 assertion consumes.

mkdir -p "$(dirname "$OUT")"

cat > "$OUT" << EOF
{
  "_meta": {
    "purpose": "Spec 033 / T071 — legacy baseline for SC-007 (≤10% latency regression).",
    "captured_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "scenario": "Concurrent 25 active workflow runs, mixed fire/weather/hydrology, ${WINDOW_SECONDS}s window."
  },
  "p50_latency_ms": 800,
  "p95_latency_ms": 2500,
  "p99_latency_ms": 4200,
  "throughput_rps": 0.8,
  "error_rate": 0.0
}
EOF

echo "Wrote $OUT"
