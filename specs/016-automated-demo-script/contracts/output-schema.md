# Output Schema Contract: Automated Demo Script

**Feature**: 016-automated-demo-script
**Date**: 2026-04-12

## JSON Output Schema

The demo script produces a single JSON object on stdout (or to a file via `--output`).

```json
{
  "run_id": "demo-20260412-143022",
  "scenario": "bushfire",
  "status": "pass",
  "started_at": "2026-04-12T14:30:22.000Z",
  "completed_at": "2026-04-12T14:30:28.200Z",
  "duration_seconds": 6.2,
  "phases": [
    {
      "phase": "setup",
      "order": 1,
      "status": "pass",
      "agent": "orchestrator",
      "duration_seconds": 0.8,
      "summary": "All 5 agents healthy, seed data validated (10 files)",
      "details": {
        "agents_healthy": 5,
        "agents_degraded": 0,
        "seed_files_validated": 10
      },
      "error": null
    },
    {
      "phase": "monitoring",
      "order": 2,
      "status": "pass",
      "agent": "monitoring",
      "duration_seconds": 1.2,
      "summary": "Bushfire signal ingested, 1 signal associated to incident",
      "details": {
        "signal_id": "signal-demo-001",
        "signals_associated": 1,
        "incident_id": "incident-demo-001"
      },
      "error": null
    },
    {
      "phase": "risk_assessment",
      "order": 3,
      "status": "pass",
      "agent": "risk_assessment",
      "duration_seconds": 1.5,
      "summary": "Risk assessed, recommendation approved by incident_commander",
      "details": {
        "recommendation_id": "rec-demo-001",
        "generation_method": "template_fallback",
        "override_action": "approve",
        "confidence": 0.72
      },
      "error": null
    },
    {
      "phase": "evacuation",
      "order": 4,
      "status": "pass",
      "agent": "evacuation",
      "duration_seconds": 0.9,
      "summary": "Evacuation replan triggered, plan approved",
      "details": {
        "plan_triggered": true,
        "override_action": "approve"
      },
      "error": null
    },
    {
      "phase": "resource_allocation",
      "order": 5,
      "status": "pass",
      "agent": "resource_allocation",
      "duration_seconds": 0.6,
      "summary": "Resource allocation plan approved",
      "details": {
        "override_action": "approve"
      },
      "error": null
    },
    {
      "phase": "communication",
      "order": 6,
      "status": "pass",
      "agent": "communication",
      "duration_seconds": 1.8,
      "summary": "Multilingual alerts generated in 6 languages",
      "details": {
        "alert_id": "alert-demo-001",
        "languages": ["en-AU", "zh-Hans", "ar", "vi", "el", "it"],
        "safety_validated": true,
        "confidence": 0.65
      },
      "error": null
    },
    {
      "phase": "summary",
      "order": 7,
      "status": "pass",
      "agent": "orchestrator",
      "duration_seconds": 0.1,
      "summary": "Audit report generated: 7 phases, 4 decisions, 4 handoffs",
      "details": {
        "total_decisions": 4,
        "total_handoffs": 4,
        "total_languages": 6
      },
      "error": null
    }
  ],
  "audit_trail": [
    {
      "timestamp": "2026-04-12T14:30:24.100Z",
      "decision_type": "risk_override",
      "agent": "risk_assessment",
      "approver_role": "incident_commander",
      "policy": "AIIMS_escalation",
      "outcome": "auto_approved",
      "supporting_data": ["signal-demo-001"]
    },
    {
      "timestamp": "2026-04-12T14:30:24.800Z",
      "decision_type": "evacuation_approval",
      "agent": "evacuation",
      "approver_role": "incident_commander",
      "policy": "AIIMS_escalation",
      "outcome": "auto_approved",
      "supporting_data": ["rec-demo-001"]
    },
    {
      "timestamp": "2026-04-12T14:30:25.300Z",
      "decision_type": "resource_approval",
      "agent": "resource_allocation",
      "approver_role": "incident_commander",
      "policy": "resource_threshold_policy",
      "outcome": "auto_approved",
      "supporting_data": ["rec-demo-001"]
    },
    {
      "timestamp": "2026-04-12T14:30:26.500Z",
      "decision_type": "alert_approval",
      "agent": "communication",
      "approver_role": "incident_commander",
      "policy": "AIIMS_alert_publication",
      "outcome": "auto_approved",
      "supporting_data": ["rec-demo-001", "alert-demo-001"]
    }
  ],
  "handoffs": [
    {
      "timestamp": "2026-04-12T14:30:24.000Z",
      "source_agent": "monitoring",
      "target_agent": "risk_assessment",
      "confidence": 0.92,
      "payload_summary": "Bushfire signal with FFDI data",
      "handoff_id": "handoff-demo-001"
    },
    {
      "timestamp": "2026-04-12T14:30:24.500Z",
      "source_agent": "risk_assessment",
      "target_agent": "evacuation",
      "confidence": 0.72,
      "payload_summary": "Evacuation recommendation with risk assessment",
      "handoff_id": "handoff-demo-002"
    },
    {
      "timestamp": "2026-04-12T14:30:25.000Z",
      "source_agent": "risk_assessment",
      "target_agent": "resource_allocation",
      "confidence": 0.72,
      "payload_summary": "Resource mobilisation recommendation",
      "handoff_id": "handoff-demo-003"
    },
    {
      "timestamp": "2026-04-12T14:30:25.500Z",
      "source_agent": "resource_allocation",
      "target_agent": "communication",
      "confidence": 0.65,
      "payload_summary": "Alert generation request with resource context",
      "handoff_id": "handoff-demo-004"
    }
  ],
  "alerts": {
    "total": 1,
    "languages": ["en-AU", "zh-Hans", "ar", "vi", "el", "it"],
    "safety_validated": true,
    "channel_targets": ["sms", "push", "broadcast"]
  }
}
```

## Schema Specification

### Root Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | Yes | Format: `demo-{YYYYMMDD}-{HHmmss}` |
| `scenario` | string | Yes | One of: `bushfire`, `cyclone`, `flood` |
| `status` | string | Yes | One of: `pass`, `fail` |
| `started_at` | string (ISO 8601) | Yes | UTC timestamp |
| `completed_at` | string (ISO 8601) | Yes | UTC timestamp (may be null if interrupted) |
| `duration_seconds` | number | Yes | Wall-clock time in seconds |
| `phases` | array[PhaseResult] | Yes | 1-7 phase results (7 on success) |
| `audit_trail` | array[DecisionRecord] | Yes | All decision records (may be empty on early failure) |
| `handoffs` | array[StageHandoff] | Yes | All handoff records (may be empty on early failure) |
| `alerts` | AlertSummary | Yes | Alert generation summary |

### PhaseResult Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phase` | string | Yes | Phase name (see enum below) |
| `order` | integer | Yes | 1-7 |
| `status` | string | Yes | One of: `pass`, `fail`, `skipped` |
| `agent` | string | Yes | Responsible agent or `orchestrator` |
| `duration_seconds` | number | Yes | Phase duration |
| `summary` | string | Yes | Human-readable result |
| `details` | object | Yes | Phase-specific structured data |
| `error` | string or null | Yes | Error message if failed, null otherwise |

**Phase names enum**: `setup`, `monitoring`, `risk_assessment`, `evacuation`, `resource_allocation`, `communication`, `summary`

### DecisionRecord Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string (ISO 8601) | Yes | UTC decision time |
| `decision_type` | string | Yes | Decision category |
| `agent` | string | Yes | Agent responsible |
| `approver_role` | string | Yes | Simulated approver role |
| `policy` | string | Yes | Applied governance policy |
| `outcome` | string | Yes | `auto_approved` or `auto_rejected` |
| `supporting_data` | array[string] | Yes | Supporting entity IDs |

### StageHandoff Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string (ISO 8601) | Yes | UTC handoff time |
| `source_agent` | string | Yes | Sending agent |
| `target_agent` | string | Yes | Receiving agent |
| `confidence` | number | Yes | 0.0-1.0 confidence level |
| `payload_summary` | string | Yes | Human-readable description |
| `handoff_id` | string | Yes | Unique identifier |

### AlertSummary Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total` | integer | Yes | Alert count |
| `languages` | array[string] | Yes | Language codes |
| `safety_validated` | boolean | Yes | Safety check status |
| `channel_targets` | array[string] | Yes | Delivery channels |

## Failure Output Example

When a phase fails, the output includes all attempted phases plus `skipped` entries:

```json
{
  "run_id": "demo-20260412-143022",
  "scenario": "bushfire",
  "status": "fail",
  "started_at": "2026-04-12T14:30:22.000Z",
  "completed_at": "2026-04-12T14:30:23.500Z",
  "duration_seconds": 1.5,
  "phases": [
    {
      "phase": "setup",
      "order": 1,
      "status": "pass",
      "agent": "orchestrator",
      "duration_seconds": 0.8,
      "summary": "All 5 agents healthy, seed data validated",
      "details": {},
      "error": null
    },
    {
      "phase": "monitoring",
      "order": 2,
      "status": "fail",
      "agent": "monitoring",
      "duration_seconds": 0.7,
      "summary": "Signal ingestion failed",
      "details": {
        "http_status": 503,
        "response_body": {"error": "repository_unavailable"}
      },
      "error": "POST /api/signals returned 503: repository_unavailable"
    },
    {
      "phase": "risk_assessment",
      "order": 3,
      "status": "skipped",
      "agent": "risk_assessment",
      "duration_seconds": 0.0,
      "summary": "Skipped due to previous phase failure",
      "details": {},
      "error": null
    }
  ],
  "audit_trail": [],
  "handoffs": [],
  "alerts": {
    "total": 0,
    "languages": [],
    "safety_validated": false,
    "channel_targets": []
  }
}
```

## CI Gate Usage

```bash
# Run demo and check exit code
python scripts/demo.py --output /tmp/demo-result.json
if [ $? -ne 0 ]; then
  echo "Demo smoke test failed"
  cat /tmp/demo-result.json | jq '.phases[] | select(.status == "fail")'
  exit 1
fi

# Validate specific assertions
python -c "
import json, sys
result = json.load(open('/tmp/demo-result.json'))
assert result['status'] == 'pass', f'Demo failed: {result[\"status\"]}'
assert len(result['phases']) == 7, f'Expected 7 phases, got {len(result[\"phases\"])}'
assert all(p['status'] == 'pass' for p in result['phases']), 'Not all phases passed'
assert len(result['alerts']['languages']) == 6, 'Not all 6 languages covered'
print('Demo smoke test passed')
"
```
