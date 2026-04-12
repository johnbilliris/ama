# Quickstart: Performance Benchmarks

**Feature**: 015-performance-benchmarks
**Date**: 2025-07-23

---

## Prerequisites

- Python 3.12+
- All agent packages installed: `pip install -e apps/agents`
- Test dependencies: `pip install pytest pytest-benchmark pytest-asyncio`

## Run Benchmarks Locally

### Full suite

```bash
pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q
```

### Single category

```bash
# Health endpoints only
pytest tests/benchmark/test_api_performance.py -q

# Pipeline benchmarks only
pytest tests/benchmark/test_pipeline_performance.py -q

# LLM client only
pytest tests/benchmark/test_llm_performance.py -q

# Circuit breaker only
pytest tests/benchmark/test_circuit_breaker_performance.py -q
```

### With verbose benchmark output

```bash
pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -v --benchmark-group-by=group
```

### Skip benchmarks (run other tests only)

```bash
pytest tests/contract tests/integration --benchmark-skip
```

## Understand Results

After running, you'll see:

1. **Console output**: pytest-benchmark table showing median, mean, min, max per benchmark.
2. **Regression report**: Human-readable comparison against baseline (if baseline exists).
3. **JSON file**: `.benchmarks/current.json` with full statistical data.

### Status indicators

| Symbol | Meaning | Impact |
|--------|---------|--------|
| ✅ PASS | Within SLO, < 20% regression | None |
| ⚠️ WARN | ≥ 20% regression | Warning logged, test passes |
| ❌ FAIL | ≥ 50% regression | Test fails, CI blocks merge |
| 🆕 NEW | No baseline for this metric | First run recorded, test passes |

## Update Baseline

When you intentionally change performance characteristics (e.g., added validation logic):

```bash
# 1. Run benchmarks to produce current results
pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q

# 2. Review results
cat .benchmarks/current.json | python -m json.tool | head -50

# 3. Accept current results as new baseline
cp .benchmarks/current.json .benchmarks/baseline.json

# 4. Commit
git add .benchmarks/baseline.json
git commit -m "Update benchmark baseline: [reason for change]"
```

## Common Tasks

### Investigate a regression

```bash
# Run with extra detail
pytest tests/benchmark/ -v --benchmark-group-by=group --benchmark-warmup=on

# Compare visually
pytest tests/benchmark/ --benchmark-compare=.benchmarks/baseline.json
```

### Check if a specific agent regressed

```bash
pytest tests/benchmark/test_api_performance.py -k "monitoring" -v
```

### Run in CI-equivalent mode

```bash
pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q
# Comparison runs automatically via conftest.py pytest_sessionfinish hook
```

## File Layout

```
tests/benchmark/
├── conftest.py                        # Shared fixtures + session finish hook
├── test_api_performance.py            # Health endpoint benchmarks (5 agents)
├── test_pipeline_performance.py       # Pipeline processing benchmarks (5 agents)
├── test_llm_performance.py            # LLM client overhead benchmark
├── test_circuit_breaker_performance.py # Circuit breaker transition benchmarks
└── compare_benchmarks.py             # Comparison wrapper module

.benchmarks/
├── baseline.json                      # Committed reference baseline
└── current.json                       # Latest run (gitignored, CI artifact)
```
