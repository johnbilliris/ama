# Disaster Response Hub Demo Walkthrough

## 1) Incident Activation
- Open the incident commander dashboard for the active incident.
- Confirm tenant-scoped incident context, participating agencies, and current hazard level.
- Screenshot placeholder: `demo-01-incident-activation.png`

## 2) Signal Ingestion
- Ingest authoritative weather signal, community report, and IoT sensor signal.
- Show provenance and confidence in the incoming signal timeline.
- Screenshot placeholder: `demo-02-signal-ingestion.png`

## 3) Dashboard Situation Picture
- Show unified map and timeline updates within one minute.
- Highlight risk indicators and impacted zones.
- Screenshot placeholder: `demo-03-dashboard.png`

## 4) Persona Workspace
- Switch to agency persona workspace and show scoped task queue.
- Confirm recommended actions are filtered by operating framework.
- Screenshot placeholder: `demo-04-persona-workspace.png`

## 5) Recommendation Review
- Show Risk Assessment recommendation with explanation and supporting signal IDs.
- Demonstrate human approval gate for safety-critical recommendation.
- Screenshot placeholder: `demo-05-recommendation-review.png`

## 6) Multilingual Alert Drafting
- Show Communication agent draft in six languages: en-AU, zh-Hans, ar, vi, el, it.
- Confirm safety validation marker and fallback status where applicable.
- Screenshot placeholder: `demo-06-alert-drafting.png`

## 7) Publish and Delivery
- Approve and publish alert to configured channels.
- Show publication status and delivery audit trail.
- Screenshot placeholder: `demo-07-alert-publish.png`

## 8) Scenario Replay
- Run replay to show timeline consistency and handoff events.
- Highlight dead-letter handling for failed delivery simulation.
- Screenshot placeholder: `demo-08-replay.png`

## Demo Timing (Target: <5 min)
- Setup context: 45s
- Ingestion + dashboard: 60s
- Persona + recommendation: 75s
- Alerts + publish: 60s
- Replay + closeout: 60s
