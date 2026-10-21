# Executive Deck: Disaster Response Coordination Hub

Canonical pair for feature 003 demo evidence:

- `docs/disaster-response-hub/demo/executive-deck.md`
- `docs/disaster-response-hub/demo/walkthrough.md`

## Slide 1 — Why This Matters

- Multi-agency incidents need shared situational awareness and faster coordinated decisions.
- The hub provides a single coordination surface across agencies and jurisdictions.

## Slide 2 — Value Proposition

- Better public safety outcomes through earlier risk detection and coordinated action.
- Reduced operator load via agent-assisted analysis and multilingual drafting.

## Slide 3 — Architecture Snapshot

- Web experience on App Service
- API and agents on Container Apps
- Cosmos DB + Redis + Blob Storage
- Microsoft Foundry model deployments for recommendation explanation and alert drafting
- Monitoring via App Insights + Log Analytics + Action Groups

## Slide 4 — KPI Before/After

| KPI | Baseline | Target Outcome | Measured |
| --- | ---: | ---: | --- |
| Response coordination time | 100% baseline | 50% faster | Not measured |
| Evacuation decision lead time | baseline | up to 24h earlier | Not measured |
| Resource allocation efficiency | baseline | 30% improvement | Not measured |
| Operator workflow quality | baseline | improved UX score | Not measured |

Measured values must remain `Not measured` until linked run IDs and artifacts are attached.

## Slide 5 — Incident Workflow

- Activation → ingestion → analysis → recommendation → approval → alert publishing.
- End-to-end orchestration with audit timeline and fallback behavior.

## Slide 6 — Safety and Governance

- Human approval for safety-critical outputs.
- Structured error handling, retries, and dead-letter review.
- Australian region alignment and managed identity posture.

## Slide 7 — Demonstrated Screens

- Incident activation
- Signal ingestion
- Dashboard situation picture
- Persona workspace
- Recommendation review
- Multilingual alert drafting
- Publish and delivery
- Scenario replay

## Slide 8 — Next Steps

- Complete remaining integration and contract tests.
- Run full CI + performance regression gates.
- Final rubric re-evaluation to confirm 60/60 readiness.
