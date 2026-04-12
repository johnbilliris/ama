# Implementation Plan: Automated Demo Script

**Branch**: `016-automated-demo-script` | **Date**: 2026-04-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-automated-demo-script/spec.md`

## Summary

Create a reproducible, automated demo script (`scripts/demo.py`) that exercises the full five-agent disaster response pipeline end-to-end using in-process ASGI TestClients, seed data from `data/`, and template-based LLM fallback. The script orchestrates 7 pipeline phases (setup → monitoring → risk → evacuation → resource → communication → summary), produces a JSON summary with per-phase pass/fail status, and supports both CI mode (<60s, silent, exit-code gate) and verbose mode (<5min, narrated output for live demonstrations). All approval gates are auto-approved deterministically. The default scenario is bushfire, configurable via `--scenario`.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI, httpx (TestClient), argparse, Pydantic, existing agent modules
**Storage**: In-memory state stores (`state_store.py` dicts); seed JSON files in `data/`
**Testing**: pytest with `simulation` marker, pytest-benchmark (already in CI)
**Target Platform**: Linux CI (GitHub Actions) and local Windows/macOS dev machines
**Project Type**: CLI script (orchestration tool)
**Performance Goals**: CI mode <60s wall-clock; verbose mode <5min wall-clock
**Constraints**: Zero external dependencies (no Azure credentials, no network, no databases); deterministic output
**Scale/Scope**: Single script file ~600-800 LOC, one test file ~200-300 LOC

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Relevant? | Status | Notes |
|---|-----------|-----------|--------|-------|
| I | Life Safety First | ✅ Yes | ✅ PASS | Demo uses auto-approve for safety-critical gates but narrates them as human-reviewed in verbose mode. Fail-fast on errors = conservative guidance. Script never overrides safety logic in agents. |
| II | Multi-Agent Coordination | ✅ Yes | ✅ PASS | Script exercises all 5 agents with explicit handoffs, logs source/target/confidence/timestamp per handoff. Aligns with AIIMS workflow. |
| III | Data Trust & Provenance | ✅ Yes | ✅ PASS | All simulated signals carry full provenance metadata (`collectionMethod: "simulation"`). Seed data from `data/` directory is validated on startup. |
| IV | Privacy & Security | ⚠️ Marginal | ✅ PASS | Demo uses synthetic data only; no real PII. Data residency N/A (in-memory only). No cross-border transfer. |
| V | Multilingual Communication | ✅ Yes | ✅ PASS | Demo produces alerts in 6 languages (en-AU, zh-Hans, ar, vi, el, it) using seeded templates from `data/alert-templates/`. |
| VI | Cloud Platform | ⚠️ Marginal | ✅ PASS | Script runs locally without Azure; this is intentional per FR-003. Production deployment on Azure is orthogonal. |
| NFR | Audit Trail | ✅ Yes | ✅ PASS | Script records decision records for every approval gate and cross-agent handoff. Summary includes full audit trail. |
| NFR | Scenario Testing | ✅ Yes | ✅ PASS | Default bushfire scenario; `--scenario` flag supports cyclone/flood. Directly fulfills constitution's scenario-based testing requirement. |
| QG | Quality Gates | ✅ Yes | ✅ PASS | Script serves as the CI smoke test gate. Fail-fast + exit code semantics align with quality gate requirements. |

**Gate Result**: ✅ ALL PASS — no violations. Proceed to Phase 0.

### Post-Phase 1 Re-check

| # | Principle | Status | Design Alignment |
|---|-----------|--------|------------------|
| I | Life Safety First | ✅ PASS | `ApprovalGate` model tracks approver role, policy, and decision for every safety-critical action. Fail-fast ensures no silent failures. |
| II | Multi-Agent Coordination | ✅ PASS | `StageHandoff` model captures source→target with confidence and payload summary. Pipeline phases mirror AIIMS activation→alert flow. |
| III | Data Trust & Provenance | ✅ PASS | `SimulatedSignal` model includes provenance fields. `SeedValidator` checks file existence and schema before pipeline starts. |
| V | Multilingual Communication | ✅ PASS | `AlertDraft` model tracks per-language content, safety validation, and channel targets. 6 template files validated on startup. |
| NFR | Audit Trail | ✅ PASS | `DecisionRecord` model with append-only semantics. `DemoRun.audit_trail` is an ordered list of all decisions. |

**Post-Design Gate Result**: ✅ ALL PASS

## Project Structure

### Documentation (this feature)

```text
specs/016-automated-demo-script/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: How to run the demo
├── contracts/           # Phase 1: CLI contract, output schema
│   ├── cli-interface.md
│   └── output-schema.md
└── tasks.md             # Phase 2: Task breakdown (not created by plan)
```

### Source Code (repository root)

```text
scripts/
└── demo.py              # Main demo script (new)

tests/
└── simulation/
    └── test_demo_script.py  # Demo script tests (new)
```

**Structure Decision**: The demo script is a standalone orchestration tool at `scripts/demo.py`, consistent with existing scripts (`scripts/seed_loader.py`, `scripts/gen_sample_data.py`). It imports the existing `create_app()` factories from each agent package and uses FastAPI's `TestClient` for in-process ASGI communication — the same pattern proven in `tests/benchmark/conftest.py` and `tests/simulation/test_quickstart_rehearsals.py`. No new packages or structural changes required.

## Complexity Tracking

> No constitution violations to justify. The design adds one script file and one test file.

*No entries required.*
