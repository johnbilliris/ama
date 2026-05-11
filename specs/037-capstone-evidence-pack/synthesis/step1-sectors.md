# Step 1 — Sector Cohort Synthesis (58 personas)

> Source: synthetic canvas of `.github/agents/sectors/**/*.agent.md` (excluding `_archive/`).

## Risk Register inputs
- **NSW (frnsw, mrnsw, nsw-ambulance, nsw-rfs, nswpf, ses-nsw)** — schema coverage for fire/bushfire, flood/storm, marine, medical triage/evac, police enforcement, volunteer coordination, escalation (`sectors/nsw/*.agent.md:18-40`).
- **VIC (av, cfa-vic, frv, ses-vic, vicpol)** — ambulance + fire + SES + police jurisdiction-specific risks and handoff clarity (`sectors/vic/*.agent.md:18-40`).
- **QLD (qas, qfd, qps, ses-qld)** — flood/cyclone, fire, search & rescue, evacuation enforcement, ambulance coordination as distinct risk domains (`sectors/qld/*.agent.md:18-40`).
- **Commonwealth (nema, bom-national, ga-national, afp, adf, abf, asa, rfds, arc, sja-national, surf-lifesaving)** — national-risk for cross-jurisdiction coordination, weather/geospatial intelligence, border/defence/aviation, recovery funding (`sectors/commonwealth/nema.agent.md:20-31`; `bom-national.agent.md:28-31`; `ga-national.agent.md:28-30`).
- **Cross-sector (health, local-government, transport, utility, volunteer, community-ngos, state-government, territory-government)** — operational, legal, data, supply-chain risks at the interface layer (`sectors/cross-sector/*.agent.md:20-33`).

## Adoption Roadmap inputs
- **Jurisdictional sequencing** — start with state/territory lead agencies + ambulance + police + SES/fire, then fold in local government, utilities, transport, volunteer/NGO, and Commonwealth coordination.
- **Change-management / training / exercise** — strong need from volunteer, local government, and health personas for training standards, exercise cadence, welfare/credentialing.
- **Decommission criteria** — legacy coordination channels can retire only when authority/escalation/mutual-aid workflows are demonstrably preserved.

## Executive KPI Surface inputs
- Lives saved / triage effectiveness (`nsw-ambulance, qas, av, rfds, sja-national`)
- Response-time reduction / dispatch-to-action (SES, fire, police)
- Earlier evacuation / warning lead time (SES, police, transport, bom-national)
- Logistics efficiency / asset utilization (transport, utility, nema, defence, abf)
- Economic loss reduction / restoration speed (utility, transport, local-government, commonwealth recovery)

## Responsible AI Register inputs
- **AI posture must be explicit per agent** for safety-critical triage, enforcement, recovery funding, public warnings, volunteer credentialing.
- **Cross-cutting RAI** — decision authority, human override, auditability, multilingual/accessibility, data minimisation, jurisdictional legality.

## Feature-Value Ledger inputs
- Map features to outcomes: coordination, triage, routing, restoration, public warning, mutual aid.
- **Tradeoffs to log** — speed vs. legality, automation vs. command authority, local autonomy vs. cross-jurisdiction standardisation, operational visibility vs. privacy/credentialing.

## Cross-cutting persona-specific concerns
- Police — enforcement, traffic control, missing persons, public order, DVI, incident escalation.
- Fire/SES — weather-linked hazard ops, resource deployment, volunteer-heavy coordination.
- Ambulance/Health — triage, evacuation, hospital surge, public health, supply-chain.
- Local govt / utilities / transport — community recovery, infrastructure restoration, evacuation centres, critical-services continuity.
- Commonwealth — national coordination, COMDISPLAN, DRFA, intelligence, weather/geospatial, cross-jurisdiction support.

