# Spec-035 — Sector Panel: Eastern Jurisdictions (NSW + VIC + QLD)

**To**: All eastern-state sector agents in `.github/agents/sectors/{nsw,vic,qld,nsw-*,vic-*,qld-*}/`.
**From**: Spec author.
**Subject**: We need user requirements and clarifications for spec-035 — Web Application Capstone Closure.

## Why you are being asked

Spec-034 cycle-1 review **endorsed** your panel — no material objections raised against the validation. That endorsement was, however, against the test suite. Now spec-035 is asking whether the **deployed web application** actually delivers the capstone outcomes for your jurisdictions when the spec-034 suite is run end-to-end against it. We are concerned that, because your panel did not surface objections, the implementation team will assume the UI is "fine for the east" — but cycle-1's depth-profile work introduces new assertion depth that none of the existing UI explicitly satisfies for any state.

## Web-app gaps to confirm or deny for your jurisdictions

For each operational persona that has a presence in NSW / VIC / QLD (incident-commander, planning-officer, public-information-officer, field-coordinator, observer-auditor, risk-manager, resilience-planner — see `operational-brief.md` for the full list), please tell us:

1. **NSW SES + RFS + ABF + NSW Health + NSW Police**: does the web UI in its current form let your operators drive their persona depth-profile to completion? Specifically — multi-agency approval routing, AWS publish for cyclonic / flood / bushfire, evacuation-network coordination across LGAs, and recovery handover to NSW Reconstruction Authority? If gaps, name the affordance gap.
2. **VIC CFA + SES + Ambulance Victoria + Victoria Police + DEECA + EMV**: same question with EMV state-control-centre coordination, Code Red day mechanics, and CFA-DELWP joint command flows.
3. **QLD QFES + QPS + QAS + QRA + Department of Resources**: same question with cyclone evacuation, Coastal Hazard Plan activation, and QRA recovery hand-down.

## Ask: requirements you may want to add

Even though the cycle-1 review found no gaps in the suite, your panel's silence on UI depth means we have no positive evidence the UI satisfies the cycle-1 depth-profiles for your states. Please surface any of the following if applicable:

- Persona affordances that you assumed were tested but, looking at `apps/web/src/`, are not actually present (e.g. no IC approval-action UI; no PIO multilingual composer)
- Multi-LGA coordination surfaces (e.g. NSW SES coordinating across 128 LGAs in a flood)
- Insurance Council Australia / state-recovery-funding handoff surfaces
- AWS warning composer with NSW-Health / VIC-Health / QLD-Health language variants
- Any state-specific compliance UI (e.g. NSW Coronial Inquiry export, VIC IGEM acknowledgements, QLD IGEM)
- Offline behavior for areas with poor coverage (Snowy / Hume / Western QLD / Cape York)

## Asks of you

1. For each persona × state intersection, state PASS / FAIL on UI depth, or NEED-TO-VERIFY
2. For every FAIL, write a user requirement that closes the gap in the web app
3. List any state-specific compliance UI surface that the spec-034 suite cannot test today because it is not in the UI
4. Acceptance criteria for any new requirement, in Given/When/Then form
5. State explicitly whether you continue to **endorse** spec-035's web-app scope as written, or whether you have a NEW material objection
