# Quickstart: Automated Demo Script

**Feature**: 016-automated-demo-script
**Date**: 2026-04-12

## Prerequisites

- Python 3.12+
- Repository cloned with seed data in `data/` directory
- Python dependencies installed (`pip install -e .` or `uv sync` from repo root)
- **No Azure credentials required**
- **No network access required**
- **No running databases required**

## Quick Run

### CI smoke test (default — silent, <60s)

```bash
python scripts/demo.py
```

On success: JSON summary on stdout, exit code 0.
On failure: JSON summary with failed phase details, exit code 1.

### Live demonstration (verbose, narrated, <5min)

```bash
python scripts/demo.py --verbose
```

Narrated output appears on stderr. JSON summary on stdout.

### Save output to file

```bash
python scripts/demo.py --output results/demo-summary.json
```

### Different disaster scenario

```bash
python scripts/demo.py --verbose --scenario cyclone
python scripts/demo.py --verbose --scenario flood
```

## What It Does

The demo script exercises the full disaster response pipeline in 7 phases:

| Phase | Agent | What Happens |
|-------|-------|-------------|
| 1. Setup | Orchestrator | Start 5 agents in-process, health-check each, validate seed data |
| 2. Monitoring | Monitoring Agent | Ingest simulated disaster signal, associate to incident |
| 3. Risk Assessment | Risk Agent | Generate hazard assessment, approve recommendation |
| 4. Evacuation | Evacuation Agent | Trigger evacuation replan, approve evacuation plan |
| 5. Resource Allocation | Resource Agent | Approve resource allocation plan |
| 6. Communication | Communication Agent | Generate multilingual alerts (6 languages), validate safety |
| 7. Summary | Orchestrator | Compile audit trail, handoff log, and JSON summary |

### How It Works (Technical)

1. **No servers are started**. Each agent's `create_app()` factory is called to create a FastAPI ASGI app, then wrapped in httpx `TestClient` for in-process HTTP calls. This is the same pattern used by `tests/benchmark/conftest.py`.

2. **No LLM is needed**. All agents fall back to template-based responses when Azure OpenAI is unavailable. The circuit breaker in `LLMCallMixin` opens on the first failed call, and all subsequent requests use deterministic template output.

3. **Seed data drives the scenario**. Alert templates from `data/alert-templates/`, population data from `data/population/`, road networks from `data/road-networks/`, and resource inventories from `data/resource-inventories/` provide realistic inputs.

4. **Approval gates are auto-approved**. Every safety-critical decision (evacuation, resource allocation, alert publication) is automatically approved with a simulated `incident_commander` role. In verbose mode, these are narrated as human review decisions.

## Output

### JSON Summary (stdout)

```json
{
  "run_id": "demo-20260412-143022",
  "scenario": "bushfire",
  "status": "pass",
  "duration_seconds": 6.2,
  "phases": [ ... ],
  "audit_trail": [ ... ],
  "handoffs": [ ... ],
  "alerts": { "total": 1, "languages": ["en-AU", "zh-Hans", "ar", "vi", "el", "it"] }
}
```

See [contracts/output-schema.md](contracts/output-schema.md) for full schema.

### Verbose Narration (stderr)

```
══════════════════════════════════════════════════════════════
  DISASTER RESPONSE HUB — Automated Demo (Bushfire Scenario)
══════════════════════════════════════════════════════════════

[14:30:22] ▶ Phase 1/7: SETUP — Activating agents and validating seed data
           ✓ Monitoring Agent ......... healthy (v1.0.0)
           ...
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'monitoring'` | Run from repository root. Ensure Python path includes `apps/agents/`. |
| `FileNotFoundError: data/alert-templates/en-AU.json` | Ensure seed data is present. Run `git checkout -- data/` if files are missing. |
| Exit code 1 with `"setup"` phase failed | Check that all agent `create_app()` factories are importable. Run `python -c "from monitoring.agent import create_app"` to diagnose. |
| Verbose mode output garbled | Ensure terminal supports UTF-8. On Windows, run `chcp 65001` first. |
| CI timeout (>60s) | Check for unexpected network calls. Ensure no Azure environment variables are set that would cause LLM client to attempt real connections. |

## Architecture

```
scripts/demo.py
    │
    ├── TestClient(app.main.create_app())          # Platform API
    ├── TestClient(monitoring.agent.create_app())   # Monitoring Agent
    ├── TestClient(risk_assessment.agent.create_app())  # Risk Agent
    ├── TestClient(evacuation.agent.create_app())   # Evacuation Agent
    ├── TestClient(resource_allocation.agent.create_app())  # Resource Agent
    └── TestClient(communication.agent.create_app())  # Communication Agent

data/
    ├── alert-templates/{en-AU,zh-Hans,ar,vi,el,it}.json
    ├── population/sample-population.json
    ├── road-networks/far-north-qld-sample.json
    └── resource-inventories/sample-inventory.json
```
