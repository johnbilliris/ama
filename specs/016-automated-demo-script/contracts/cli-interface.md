# CLI Interface Contract: Automated Demo Script

**Feature**: 016-automated-demo-script
**Date**: 2026-04-12

## Command Signature

```
python scripts/demo.py [--verbose] [--scenario <type>] [--output <path>]
```

## Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--verbose` | flag | No | `False` | Enable narrated output on stderr for live demonstrations |
| `--scenario` | string | No | `bushfire` | Disaster scenario type. Valid: `bushfire`, `cyclone`, `flood` |
| `--output` | path | No | (stdout) | Write JSON summary to file instead of stdout |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All 7 pipeline phases completed successfully |
| `1` | One or more phases failed (fail-fast) |
| `2` | Invalid arguments (argparse error) |
| `130` | Interrupted by user (Ctrl+C / SIGINT) |

## Output Channels

| Channel | CI Mode (default) | Verbose Mode (`--verbose`) |
|---------|-------------------|---------------------------|
| **stdout** | JSON summary | JSON summary |
| **stderr** | Errors only | Rich narrated phase descriptions |

## Invocation Examples

### CI smoke test (default)
```bash
python scripts/demo.py
# Exit code 0 + JSON on stdout
```

### CI with output file
```bash
python scripts/demo.py --output results/demo-summary.json
# Exit code 0, JSON written to file, nothing on stdout
```

### Live demonstration
```bash
python scripts/demo.py --verbose
# Narrated output on stderr, JSON on stdout
```

### Cyclone scenario demo
```bash
python scripts/demo.py --verbose --scenario cyclone
# Narrated cyclone scenario on stderr, JSON on stdout
```

## Verbose Mode Narration Format

Narration is printed to stderr with phase headers and timestamps:

```
══════════════════════════════════════════════════════════════
  DISASTER RESPONSE HUB — Automated Demo (Bushfire Scenario)
══════════════════════════════════════════════════════════════

[14:30:22] ▶ Phase 1/7: SETUP — Activating agents and validating seed data
           ✓ Monitoring Agent ......... healthy (v1.0.0)
           ✓ Risk Assessment Agent .... healthy (v1.0.0)
           ✓ Evacuation Agent ......... healthy (v1.0.0)
           ✓ Resource Allocation Agent  healthy (v1.0.0)
           ✓ Communication Agent ...... healthy (v1.0.0)
           ✓ Seed data validated (10 files)
           ✓ Phase completed in 0.8s

[14:30:23] ▶ Phase 2/7: MONITORING — Ingesting bushfire signals
           → Injecting authoritative bushfire signal from BoM sensor network
           → Signal ID: signal-demo-001 | Confidence: 0.92 | Category: fire
           → Dashboard updated: 1 active signal, severity SEVERE
           ✓ Phase completed in 1.2s

[14:30:24] ▶ Phase 3/7: RISK ASSESSMENT — Analysing hazard and generating recommendation
           → Hazard assessment generated: FFDI 85 (Extreme)
           → Recommendation: Evacuation of affected zones
           ⚠ APPROVAL GATE: Incident Commander reviewing recommendation...
           ✓ AUTO-APPROVED (simulated human review)
           → Decision recorded in audit trail
           ✓ Phase completed in 1.5s

...

[14:30:28] ▶ Phase 7/7: SUMMARY — Generating audit report
           ═══════════════════════════════════
           ✓ ALL PHASES PASSED
           ✓ 5/5 agents exercised
           ✓ 4 approval gates passed
           ✓ 4 cross-agent handoffs recorded
           ✓ Alerts in 6 languages
           ✓ Total duration: 6.2s
           ═══════════════════════════════════
```

## Dependency Requirements

- Python 3.12+
- All dependencies from `pyproject.toml` (no additional packages)
- No network access, Azure credentials, or running databases
- Seed data files in `data/` directory (committed to repository)
