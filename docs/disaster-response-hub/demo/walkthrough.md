# Disaster Response Hub Demo Walkthrough

Canonical pair for feature 003 demo evidence:

- `docs/disaster-response-hub/demo/walkthrough.md`
- `docs/disaster-response-hub/demo/executive-deck.md`

The screenshot set is produced by the deterministic workflow in
`docs/disaster-response-hub/demo/screenshot-capture-workflow.md`. Until that run
is executed against a seeded environment, this walkthrough remains evidence-pending.

## 1) Incident Activation

- Open the incident commander dashboard for the active incident.
- Confirm tenant-scoped incident context, participating agencies, and current hazard level.
- Capture target: docs/disaster-response-hub/demo/assets/demo-01-incident-activation.png

## 2) Signal Ingestion

- Ingest authoritative weather signal, community report, and IoT sensor signal.
- Show provenance and confidence in the incoming signal timeline.
- Capture target: docs/disaster-response-hub/demo/assets/demo-02-signal-ingestion.png

## 3) Dashboard Situation Picture

- Show unified map and timeline updates within one minute.
- Highlight risk indicators and impacted zones.
- Capture target: docs/disaster-response-hub/demo/assets/demo-03-dashboard.png

## 4) Persona Workspace

- Switch to agency persona workspace and show scoped task queue.
- Confirm recommended actions are filtered by operating framework.
- Capture target: docs/disaster-response-hub/demo/assets/demo-04-persona-workspace.png

## 5) Recommendation Review

- Show Risk Assessment recommendation with explanation and supporting signal IDs.
- Demonstrate human approval gate for safety-critical recommendation.
- Capture target: docs/disaster-response-hub/demo/assets/demo-05-recommendation-review.png

## 6) Multilingual Alert Drafting

- Show Communication agent draft in six languages: en-AU, zh-Hans, ar, vi, el, it.
- Confirm safety validation marker and fallback status where applicable.
- Capture target: docs/disaster-response-hub/demo/assets/demo-06-alert-drafting.png

## 7) Publish and Delivery

- Approve and publish alert to configured channels.
- Show publication status and delivery audit trail.
- Capture target: docs/disaster-response-hub/demo/assets/demo-07-alert-publish.png

## 8) Scenario Replay

- Run replay to show timeline consistency and handoff events.
- Highlight dead-letter handling for failed delivery simulation.
- Capture target: docs/disaster-response-hub/demo/assets/demo-08-replay.png

## Demo Timing (Target: <5 min)

- Setup context: 40s
- Ingestion + dashboard: 55s
- Persona + recommendation: 65s
- Alerts + publish: 55s
- Replay + closeout: 50s

Total planned duration: 265s (35s margin below 300s).
