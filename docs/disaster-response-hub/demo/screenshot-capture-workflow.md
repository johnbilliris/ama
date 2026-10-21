# Screenshot Capture Workflow (Feature 003)

This workflow captures the eight required demo surfaces deterministically from a seeded environment.

## Inputs

- Seeded app environment with incident data loaded.
- Base URL for the running web app.
- API URL for seeded incident verification.

## Deterministic capture order

1. Incident activation -> `demo-01-incident-activation.png`
2. Signal ingestion -> `demo-02-signal-ingestion.png`
3. Dashboard situation picture -> `demo-03-dashboard.png`
4. Persona workspace -> `demo-04-persona-workspace.png`
5. Recommendation review -> `demo-05-recommendation-review.png`
6. Multilingual alert drafting -> `demo-06-alert-drafting.png`
7. Publish and delivery -> `demo-07-alert-publish.png`
8. Scenario replay -> `demo-08-replay.png`

## Output directory

`docs/disaster-response-hub/demo/assets/`

## Execution

Run from repository root:

```powershell
pwsh scripts/spec_003_capture_demo_screens.ps1 -BaseUrl http://localhost:3000 -OutputDir docs/disaster-response-hub/demo/assets
```

The script enforces filename order and fails if any required capture is missing.

## Evidence note

Until this workflow is executed and the assets are committed, SC-008 remains evidence-pending.
