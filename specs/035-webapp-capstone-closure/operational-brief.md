# Spec-035 — Operational Panel Input Brief

**To**: All 10 agents in `.github/agents/operational/`.
**From**: Spec author.
**Subject**: We need you to provide further user requirements and clarifications for spec-035 — Web Application Capstone Closure. Please read `00-overall-brief.md` first.

## Why you are being asked

Spec-034 cycle-1 built a 111-spec Playwright suite that drives every persona × outcome × hazard tuple end-to-end. The depth-profile contract you helped shape says, for example, that the public-information-officer must drive an AWS draft → IC approval → publish flow with multilingual variants and accessibility. **The current web application at `apps/web/src/` does not actually expose those workflows.** When the suite runs against the deployed UI, most operational persona assertions either time out, find no matching DOM affordance, or settle for the audit-emission stub spec-034 phase-13 retired. Spec-035 must close that delta.

## Web-app gaps confirmed by the operational panel review (`agent-review/operational-review.md`)

For each gap below, please return:
- The user requirement, expressed as a stated outcome (capstone-shaped, not feature-shaped)
- The minimum UI affordances you need to drive it (e.g. "an Approve button with rationale field, source field, confidence pill, and approver name")
- The audit-event shape you will assert against
- The accessibility / multilingual / offline / sovereignty constraints the constitution forces on the affordance

### IC — Cross-agency action approval
Today: opening the workspace, seeding a scenario, no approval surface drives a state change. Need: an Approve / Decline action card with rationale, source, confidence (low/medium/high), and approver-identity capture; pre-approval publication must be blocked at the UI; approval must immutably audit.

### Planning — Forecast + IAP draft + IC handoff
Today: situation-assessment surface is read-only summaries. Need: editable forecasts with source provenance pills, conflicting-source contradiction flagging, IAP draft surface, and a "send to IC" handoff with audit chain.

### PIO — AWS draft → IC approval → publish (CRITICAL)
Today: there is no AWS warning composer in the UI; the routes exist but no draft/approval/publish view. Need: a multi-language draft composer (en + at least 3 community languages tied to the jurisdiction), AWS-compliant level/nested-zone selection, accessibility validation (alt text, semantic landmarks, contrast, screen-reader announcements), an explicit IC-approval step, blocked publish without approval, and post-publish audit including approver identity + language variant evidence.

### Field Coordinator — Offline GPS hazard report
Today: only duplicate-submission idempotency is checked. Need: an offline mode (Service Worker + IndexedDB queue) that captures GPS hazard reports while offline, replays in original order on reconnect, preserves authoring timestamp + originator identity, surfaces a degraded-mode banner, and produces audit entries that include offline-window metadata.

### Observer-Auditor — Tamper attempt + read-back
Today: read-only timeline that does not prove immutability. Need: an attempted PATCH/DELETE surface (or surfaced API call) that demonstrably fails with append-only error UX, plus a read-back assertion proving original audit content unchanged. Export-to-evidence must produce a downloadable artefact.

### Risk Manager — Live risk matrix + recommendation
Today: static risk view. Need: live risk matrix updates as scenario state changes; route-risk comparison side-by-side; surface a "recommend evac" action that appears in IC and Planning queues with audit chain.

### Resilience Planner — Recovery handover artefact
Today: workspace-loads-only. Need: a real response→recovery handover composer that produces a downloadable artefact (PDF or signed JSON), captures gap analysis, framework-modelling outputs, and lessons integration. Audit must include artefact hash + signing identity.

### Logistics, Operations, Executive — Endorsed by panel
No web-app gap raised. Spec-035 is welcome to confirm via depth-profile passes that nothing has regressed.

## Cross-cutting (multiple personas)
- **AWS multilingual + accessibility surface**: PIO's gap is the most acute, but every persona that publishes to a public surface must reuse the same composer.
- **Offline + degraded-comms**: Field Coordinator's gap pattern repeats for any persona that operates in disconnected geographies (NT, WA Kimberley, TAS islands, SA outback).
- **Append-only proof**: Observer-Auditor's tamper pattern must work uniformly across all audit-bearing surfaces.

## Asks of you

For each gap above, please respond with:
1. Final user requirement statement(s)
2. Acceptance criteria (Given/When/Then format if possible)
3. Edge cases the implementation MUST handle (degraded comms, language fallback, role conflict, partial offline, etc.)
4. Audit-event field list
5. Anything from your persona that you feel is being under-spec'd and would lead to a false-pass in the cycle-2 implement
