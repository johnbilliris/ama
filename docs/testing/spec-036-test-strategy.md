# Spec 036 — Test Strategy

> **Authority**: Plan §F-A10.5 (T223). Closes finding F-DEL-07 — the prior
> spec-036 test corpus had no clear unit/integration/contract/e2e split,
> which made selection in CI awkward.
>
> This document is the canonical reference for which test markers map to
> which CI lane, what they assert, and where to add new tests.

## Marker taxonomy

| Marker        | Scope                                                | Trigger                                  |
|---------------|------------------------------------------------------|------------------------------------------|
| `unit`        | Pure-Python, in-process, < 100ms / case              | Per-PR (`tests/unit/`)                   |
| `contract`    | Schema / API parity (mirrored to `packages/schemas`) | Per-PR (`tests/contract/`)               |
| `integration` | Mocked external services (Cosmos, Service Bus, ...)  | Per-PR (`tests/integration/`)            |
| `e2e`         | End-to-end against deployed infra or in-proc double  | Nightly (`tests/e2e/`)                   |
| `load`        | Locust / stress harnesses                            | Weekly (`tests/load/`, FR-RAG-TEST-02)   |
| `simulation`  | Multi-day scenario simulations                       | Quarterly chaos game-day                 |

Markers are configured in `pyproject.toml::[tool.pytest.ini_options].markers`
and re-checked by `ruff check` (none today, but the marker string is the
single source of truth).

## CI lane mapping

```
                 per-PR (≤5min)                weekly cron        nightly cron
                 ───────────────                ───────────        ────────────
unit             ✓                              –                  –
contract         ✓                              –                  –
integration      ✓                              –                  –
e2e (in-proc)    ✓ (T221 in-proc body)          –                  ✓ (full body)
e2e (staging)    –                              –                  ✓ (`AMA_E2E_AGAINST_STAGING=1`)
load burst       –                              –                  –
```

CI workflow file mapping:

- `.github/workflows/ci.yml` — `quality` (Linux contract+integration+coverage),
  `quality-windows` (Windows contract+integration), `golden-set-canonical`
  (T220 lint).

- `.github/workflows/spec-036-blue-green-e2e.yml` — nightly blue-green E2E
  against staging.
- `.github/workflows/corpus-ingest.yml` — daily drift detection (cron
  `0 14 * * *` UTC; T213).

## Where to add tests

| You are adding...                     | Goes in                              | Marker         |
|---------------------------------------|--------------------------------------|----------------|
| Pure helper / model unit logic        | `tests/unit/`                        | `unit`         |
| Cross-package schema parity           | `tests/contract/`                    | `contract`     |
| Service interaction with mock infra   | `tests/integration/`                 | `integration`  |
| Multi-service scenario, real infra OK | `tests/e2e/`                         | `e2e`          |
| Load / soak / stress                  | `tests/load/`                        | `load`         |
| Resilience drill                      | `tests/simulation/`                  | `simulation`   |

## Required tags / fixtures

- **Windows-only cases**: gate with
  `@pytest.mark.skipif(sys.platform != "win32", reason="windows-only")`.
- **Temp-dir fixture**: prefer `clean_tmp_path` (in `tests/conftest.py`) over
  the bare `tmp_path` for tests that mmap files (closes F-DEL-01).
- **UTF-8**: stdio is forced to UTF-8 by `tests/conftest.py` so emoji and
  Indigenous-language graphemes round-trip safely (closes F-DEL-08).
- **Golden-set fixtures**: there is exactly one golden-set fixture
  (`tests/fixtures/golden-set-v1.json`); duplicates are rejected by
  `tools/lint/check_golden_set_canonical.py` (T220).

## Coverage ratchet

Per-tier coverage targets are owned by spec-032 FR-T01 (`scripts/coverage-ratchet.ps1`).
Spec-036 currently sits in the *unit* tier — Phase A grace; Phase B ratchets
in the same PR that lands ADR-19 (T251).

## Change log

| Date       | Change                                  | Author             |
|------------|-----------------------------------------|--------------------|
| 2026-XX-XX | Initial draft (T223 / Plan §F-A10.5)    | Implementation     |
