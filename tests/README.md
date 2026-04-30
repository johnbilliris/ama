# tests/ — Test Tiers

This directory holds **all** automated tests for the Autonomous Disaster Response Coordination Hub. Each tier serves a specific purpose; CI runs the canonical unit + integration + contract suite as the primary gate, with additional tiers running on schedules or manually.

> **Canonical CI command** (see `.github/workflows/ci.yml`):
> `python -m pytest tests/unit tests/integration tests/contract -q --tb=line --cov`

## Tiers

| Tier | Path | Purpose | Run command | Expected runtime |
|---|---|---|---|---|
| **Unit** | `tests/unit/` | Fast, isolated tests of individual functions/classes. No I/O. ~110 files. | `pytest tests/unit -q` | < 60 s |
| **Integration** | `tests/integration/` | Cross-module + repository tests against in-memory or local Cosmos emulator. | `pytest tests/integration -q` | 1–3 min |
| **Contract** | `tests/contract/` | API + event contract tests (OpenAPI conformance, schema). ~53 files. | `pytest tests/contract -q` | 1–3 min |
| **Simulation** | `tests/simulation/` | Multi-agent simulations under canned scenarios. | `pytest tests/simulation -q` | 2–5 min |
| **Benchmark** | `tests/benchmark/` | `pytest-benchmark` perf gates with JSON output. | `pytest tests/benchmark -q --benchmark-json=.benchmarks/current.json` | 1–2 min |
| **DevOps** | `tests/devops/` | Infra/runbook scripts (smoke + dry-run). | `pytest tests/devops -q` | < 60 s |
| **E2E (web)** | `apps/web/e2e/` (Playwright) | Browser-driven critical journeys. | `pnpm --filter ./apps/web test:e2e` | 3–8 min |
| **E2E (back)** | `tests/e2e/` | Backend full-stack flows (containerised services). | `pytest tests/e2e -q` | 5–10 min |
| **Load** | `tests/load/` | Locust/k6-style load tests. Run **nightly** in CI against staging. | `pytest tests/load -q` (smoke) or `locust -f tests/load/<file>.py` | 30+ min |
| **Pipeline** | `tests/pipeline/` | Tests of CI/CD pipeline scripts and helpers. | `pytest tests/pipeline -q` | < 60 s |
| **Chaos** *(NEW, spec 032)* | `tests/chaos/` | Chaos / fault-injection on resilience middleware. | `pytest tests/chaos -q` | 1–3 min |
| **Security** *(NEW, spec 032)* | `tests/security/` | Bicep policy unit tests + secret-canary scans + SAST harness. | `pytest tests/security -q` | < 60 s |
| **Web (Vitest)** *(NEW, spec 032)* | `apps/web/__tests__/` | Component + hook unit tests. | `pnpm --filter ./apps/web test` | < 60 s |

## Coverage gates (FR-T01, ratcheting)

Coverage is enforced by `pytest --cov` with three phases:

- **Phase A (current)** — CI fails on any *regression* against the previous successful run.
- **Phase B** — floors set to baseline: 63 % (unit) / 40 % (integration) / 49 % (contract).
- **Phase C** — floors raised to **80 % / 60 % / 50 %** (the rubric target) once Stream 6 + Stream 7 land enough new unit tests.

The active phase + floors live in `scripts/coverage-ratchet.ps1`.

## Authoring a new contract test

See [`tests/contract/CONTRIBUTING.contract.md`](contract/CONTRIBUTING.contract.md) (added by spec 032 task T906).

## Authoring a new chaos experiment

See [`docs/chaos/authoring.md`](../docs/chaos/authoring.md) (added by spec 032 Stream 8).

## Traceability

Each spec under `specs/` should ship a requirement → test traceability matrix (FR-T07). Spec 032's matrix lives at `specs/032-rubric-improvements/traceability.md`.
