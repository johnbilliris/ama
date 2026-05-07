# Spec-035 — Sector Panel: Southwest Jurisdictions (SA + WA + TAS)

**To**: All southwest-state sector agents in `.github/agents/sectors/{sa,wa,tas,sa-*,wa-*,tas-*}/`.
**From**: Spec author.
**Subject**: We need user requirements and clarifications for spec-035 — Web Application Capstone Closure.

## Why you are being asked

Spec-034 cycle-1 review surfaced 6 material gaps from your panel (consolidated-review.md §C). Cycle-1 implement closed them **in the test suite** by adding 5 net-new specs (T187..T191): SA control-centre RBAC, SA multi-LGA evac, WA ATSI, WA iron-ore, TAS island isolation, TAS palawa multilingual. Those specs now exist and either bail at the UI affordance lookup or hit timeouts — which means **the web application does not yet support the workflows your specs assert**. Spec-035 must close that delta.

## Web-app gaps you raised (confirm or escalate)

### SA — control-centre RBAC scenarios for multi-LGA coordination
Spec needs: a control-centre operator role with delegated-authority view, multi-LGA coordination dashboard, role-separation (operator vs approver vs publisher), and an RBAC audit chain. Web app today: no such persona surface in `apps/web/src/`; SA workflows currently render the same single-tier view as every other state.

### SA — Long-distance multi-LGA evacuation logistics
Spec needs: convoy staging UI, inter-LGA shelter routing, degraded-comms fallback (offline-first plan + delayed sync), and air-bridge coordination with SES-SA / SAPOL. Web app today: evacuation routing exists at single-LGA scope only.

### WA — ATSI handoff with culturally-safe messaging + audit trail
Spec needs: a culturally-safe messaging template (Kimberley / Pilbara dialect support, community-elder approval routing) and an ATSI-handoff surface with audit. Web app today: generic English-only messaging UI; no community-elder approval flow.

### WA — Iron-ore region critical-infrastructure protection
Spec needs: port / rail / power-corridor prioritisation surface, mutual-aid sequencing UI for DFES + WA Police + private-sector operators (BHP, Rio Tinto, Fortescue), and recovery-handoff artefact. Web app today: not present.

### TAS — Island ferry / air medevac disruption + rescue-to-care handoff
Spec needs: a maritime-disruption surface that shows ferry/air status, alternative-routing decisions, and a rescue-to-care handoff (Ambulance Tasmania ↔ State Health). Web app today: not present.

### TAS — palawa multilingual at persona level (FR-012 + AWS)
Spec needs: palawa-language variant in the AWS composer (PIO surface from operational-brief.md) for TAS jurisdiction, plus accessibility checks specific to small-population community channels. Web app today: language-pack does not include palawa; AWS composer itself is missing for all states (see operational-brief.md PIO gap).

## Cross-cutting for your panel

- **Degraded-comms**: SA outback, WA Pilbara/Kimberley, TAS islands all need offline-capable persona affordances. The Field-Coordinator pattern from operational-brief.md must be available in your jurisdictions, with state-specific test coverage.
- **Cultural safety**: WA + TAS both raised cultural-safety requirements (ATSI / palawa). The web app should have a single cultural-safety subsystem (template, approval, audit) that scales across jurisdictions with their language and protocol packs.
- **Mining/maritime/infrastructure overlay**: WA iron-ore + TAS island both raise an infrastructure-overlay requirement that does not currently exist in `apps/web/src/`.

## Asks of you

For each web-app gap, please respond with:
1. Final user requirement statement
2. Acceptance criteria (Given/When/Then form)
3. Cultural-safety / language / accessibility / sovereignty constraints binding the requirement
4. Edge cases (degraded comms, language fallback, role conflict, multi-LGA cascade, mining-corridor cascade)
5. Whether the existing spec-034 cycle-1 net-new spec for your jurisdiction (T187..T191) correctly captures the depth your persona needs (PASS / NEEDS-DEEPENING)
6. Any net-new gap that has emerged since cycle-1 review
