# Coverage Ratchet — Phase Activation Tracker

**Purpose**: Single source of truth for the active phase of the FR-T01 coverage ratchet. Read by CI (`COVERAGE_PHASE` GitHub Actions variable) and `scripts/coverage-ratchet.ps1`.

| Phase | Floors (unit / integration / contract) | Activation criteria | Activated on | Activated by | Notes |
|---|---|---|---|---|---|
| **A** | no-regression vs prior CI run | (default) | 2026-04-30 | spec-032 Stream 1 | Active now. |
| **B** | 63 / 40 / 49 (baseline) | Stream 1 fully merged AND `tests/unit` ≥ baseline measured for 7 consecutive green CI runs on `main` | _pending_ | _pending_ | |
| **C** | **80 / 60 / 50** (rubric target) | Stream 6 + Stream 7 application code merged AND coverage ≥ target on three consecutive green CI runs on `main` | _pending_ | _pending_ | This is the rubric-Excellent target. |

## How to advance phase

1. Verify activation criteria for the next phase are met.
2. Open a small PR that:
   - Updates this file (fill `Activated on` + `Activated by` for the new phase).
   - Updates the GitHub Actions variable `COVERAGE_PHASE` (Repo → Settings → Variables → Actions).
   - Optional: bump `--cov-fail-under` defaults in `scripts/coverage-ratchet.ps1` if you prefer hard-coded floors.
3. Run `ci.yml` once on `main` to confirm green.
4. Communicate the change in `CHANGELOG.md`.

## Bypass (escape valve)

Per FR-T01: a documented one-time `--coverage-bypass=incident-{id}` requires Executive + Principal Engineer co-approval and audit logging. The bypass is **never** advancing phase — it only suppresses the gate for one PR.

## Status

**Active phase**: A (no-regression).
