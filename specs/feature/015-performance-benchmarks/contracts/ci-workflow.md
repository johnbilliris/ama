# Contract: CI Workflow Integration

**Feature**: 015-performance-benchmarks
**Date**: 2025-07-23
**Type**: CI/CD pipeline configuration

---

## Overview

The benchmark suite integrates with GitHub Actions CI via the existing `.github/workflows/ci.yml` workflow. The existing `perf-benchmark` step is modified and an artifact upload step is added.

## Current CI Step (to be replaced)

```yaml
- name: perf-benchmark
  run: pytest tests/benchmark/test_api_performance.py -q
```

## New CI Configuration

```yaml
- name: perf-benchmark
  timeout-minutes: 2
  run: pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q

- name: upload-benchmark-results
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: benchmark-results
    path: .benchmarks/current.json
    retention-days: 30
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| `timeout-minutes: 2` | SC-007 safeguard: hard-kill runaway benchmarks (suite target is < 60 s) |
| `--benchmark-json=.benchmarks/current.json` | FR-006: store results as structured JSON in `.benchmarks/` |
| `tests/benchmark/` (directory) | Run all benchmark files, not just one |
| `-q` | Minimize console noise; comparison wrapper produces human-readable output |
| `if: always()` on artifact upload | Ensure results are uploaded even when benchmarks fail (for investigation) |
| `retention-days: 30` | SC-006: enable historical comparison across ≥ 30 days |
| Single CI step | All categories run in one pytest invocation for simplicity |

## .gitignore Addition

```gitignore
# Benchmark outputs (current.json is CI artifact, not committed)
.benchmarks/current.json
```

## Branch Trigger Update

The CI workflow `on.push.branches` list should include the feature branch during development:

```yaml
on:
  push:
    branches:
      - main
      - "001-disaster-response-hub"
      - "003-rubric-gap-closure"
      - "015-performance-benchmarks"  # Added for feature development
  pull_request:
```

This is removed when the feature branch is merged to main.
