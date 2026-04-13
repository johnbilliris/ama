# Autonomous Disaster Response Agent Coordination Hub Constitution
<!-- System Constitution for an Australia-focused, multi-agency, multi-agent disaster response coordination platform. -->

## Core Principles

### I. Primacy of Life and Harm Reduction

All agent decisions and coordination actions MUST prioritise the protection
of human life above all other objectives. Property, environmental, and
economic considerations are secondary to life safety.

> *"The protection of human life is the first priority of all agencies
> involved in emergency management."*
> — AIDR Incident Management Handbook (2023), Principle 1

### II. National Emergency Management Principles

The platform SHALL align with the eleven (11) Australian emergency management
principles as defined in the *Australian Emergency Management Arrangements*
(AEMA, 2023):

1. **Primacy of life** — Protect human life above all
2. **Comprehensive** — Cover all hazards, all phases (PPRR)
3. **Collaborative** — Work across agencies and jurisdictions
4. **Coordinated** — Unified effort, no duplication
5. **Flexible** — Adapt to scale, severity, and complexity
6. **Risk-based** — Decisions informed by assessed risk
7. **Shared responsibility** — All levels of government, community, individuals
8. **Resilience** — Build community capacity before, during, and after
9. **Communication** — Clear, timely, and accessible information flow
10. **Integrated** — Seamless across organisations and systems
11. **Continual improvement** — Learn from every event and exercise

### II-A. AIIMS Functional Alignment

Agents operating within the platform SHALL map to the Australasian
Inter-service Incident Management System (AIIMS) functional structure:

| AIIMS Function      | Agent Responsibility                            |
| ------------------- | ----------------------------------------------- |
| Control             | Incident Controller agent — overall direction   |
| Intelligence        | Situational-awareness and data-fusion agents    |
| Planning            | Planning and resource-forecasting agents        |
| Operations          | Tactical and field-coordination agents          |
| Logistics           | Supply-chain and logistics-support agents       |
| Public Information  | Warning-generation and community-comms agents   |

#### Incident Levels

| Level | Scope                        | Agent Behaviour                              |
| ----- | ---------------------------- | -------------------------------------------- |
| 1     | Local, single-agency         | Autonomous local response, minimal escalation |
| 2     | Significant, multi-agency    | Cross-agency coordination, shared COP        |
| 3     | Major, regional/state-wide   | Full multi-tier coordination, NCM integration |

- Agents MUST support a **Common Operating Picture (COP)** — a shared,
  real-time information environment enabling consistent situational
  awareness across all participating entities.
- **Command** (vertical, within an entity), **Control** (horizontal,
  across entities), and **Coordination** (bringing together resources
  and efforts) are distinct functions that agents MUST respect.

### III. Multi-Hazard, Multi-Agency Design

The system MUST support coordination across all natural and human-caused
hazard types relevant to Australia (bushfire, flood, cyclone, earthquake,
tsunami, storm, extreme heat, pandemic, and others) and across local,
state/territory, and Commonwealth agencies.

### IV. Transparency and Auditability

Every agent action, recommendation, and decision MUST be logged with
full provenance and rationale. Human operators MUST be able to audit
any agent decision chain at any time.

### V. Warning and Public Information

Agents generating public-facing warnings or information MUST comply
with Australian standards for emergency communication.

#### V-A. Australian Warning System (AWS)

Warnings MUST use the three-tier Australian Warning System:

| Level             | Colour | Meaning                                      |
| ----------------- | ------ | -------------------------------------------- |
| Advice            | Yellow | An incident has started; no immediate danger |
| Watch and Act     | Orange | Conditions are changing; you need to act now |
| Emergency Warning | Red    | You are in danger and need to act immediately |

Each warning MUST follow the AWS **nested model**:
`Warning Level` + `Hazard/Location` + `Action Statement`

Hazard icons (cyclone, fire, flood, heat, storm, other) MUST be used
where graphical output is supported. De-escalation and "all clear"
notifications MUST be issued when threat reduces.

#### V-B. Ten Warning Principles

Agents generating warnings SHALL adhere to the ten (10) principles
from the *Public Information and Warnings Handbook* (2021):

1. Warnings are **life-saving**
2. Warnings are **empowering** — they enable informed decisions
3. Warnings are **trusted, authoritative, and verifiable**
4. Warnings are **scaled based on risk**
5. Warnings are **timely, targeted, and tailored**
6. Warnings convey **impact**
7. Warnings include a **call to action**
8. Warnings are **clearly communicated**
9. Warnings are **readily accessible**
10. Warnings are **part of a bigger picture** (not isolated)

#### V-C. Total Warning System

The platform SHALL implement all six (6) elements of the Total Warning
System:

1. **Situational awareness** — understanding the environment
2. **Monitoring and prediction** — tracking hazard development
3. **Message construction** — creating effective warning content
4. **Interpretation** — ensuring meaning is understood
5. **Communication** — delivering via appropriate channels
6. **Community response** — enabling protective action

### VI. Evacuation Framework

Agents supporting evacuation planning and execution MUST implement
the five-stage evacuation process from the *Evacuation Planning
Handbook* (2023):

#### VI-A. Five-Stage Evacuation Process

| Stage      | Description                                          |
| ---------- | ---------------------------------------------------- |
| Decision   | Authority decides whether evacuation is warranted    |
| Warning    | Community is informed of the need to evacuate        |
| Withdrawal | Physical movement of people from the threat area     |
| Shelter    | Temporary accommodation and welfare support          |
| Return     | Managed re-entry when area is deemed safe            |

#### VI-B. Evacuation Types and Approaches

- **Pre-warned** evacuations (flood, cyclone, bushfire with lead time)
  versus **Immediate** evacuations (earthquake, structural collapse)
- Approaches: **Directed** (mandatory), **Recommended** (advisory),
  and **Self-initiated** (individual decision)
- Evacuations may be **total**, **partial**, or **phased**
- **Shelter-in-place** MUST be supported as an alternative strategy
  where evacuation is infeasible or more dangerous

#### VI-C. Vulnerable Populations

Agents MUST give priority consideration to vulnerable and at-risk
populations during evacuation, including but not limited to:
Aboriginal and Torres Strait Islander communities, culturally and
linguistically diverse (CALD) communities, people with disability,
children, older persons, people experiencing homelessness, tourists
and transient populations, and people in institutional care.

### VII. Recovery Support

The platform MUST support disaster recovery as a distinct, long-term
phase that overlaps with response.

#### VII-A. Six National Principles for Disaster Recovery

Recovery operations SHALL align with the six (6) National Principles
from the *Community Recovery Handbook* (2018):

1. **Understand the context** — Each disaster and community is unique
2. **Recognise complexity** — Recovery is non-linear and multi-layered
3. **Use community-led approaches** — Affected communities drive their
   own recovery
4. **Coordinate all activities** — Across agencies, sectors, and phases
5. **Communicate effectively** — Timely, accurate, and empathetic
6. **Acknowledge and build capacity** — Strengthen community resilience

#### VII-B. Four Recovery Environments

Recovery agents MUST address all four recovery environments:

| Environment | Scope                                         |
| ----------- | --------------------------------------------- |
| Social      | Health, wellbeing, community connectedness     |
| Built       | Infrastructure, housing, essential services    |
| Economic    | Livelihoods, businesses, financial systems     |
| Natural     | Ecosystems, waterways, biodiversity, land      |

#### VII-C. Recovery Transition

- Recovery MUST be planned for from the onset of response
- Recovery agents SHOULD activate in parallel with response agents
- Handover from response to recovery MUST be a managed transition,
  not an abrupt switch

### VIII. Cloud Platform and Infrastructure

- All infrastructure MUST run on Microsoft Azure
- Infrastructure as Code (Bicep preferred, Terraform accepted)
- Deployment via CI/CD (GitHub Actions)
- Azure-native services preferred (Azure AI, Azure OpenAI, Cosmos DB,
  Event Grid, Service Bus, Azure Maps, Azure Communication Services)

## Emergency Management Framework Alignment

### PPRR Lifecycle

The platform SHALL support all four phases of the PPRR lifecycle as
defined in AEMA (2023). Phases are **not sequential** — they overlap
and recur:

- **Prevention** — Eliminating or reducing the level of a hazard
- **Preparedness** — Building capacity and readiness
- **Response** — Containing, controlling, and minimising impact
- **Recovery** — Restoring and rebuilding communities

### Shared Responsibility Model

The platform SHALL embody the shared responsibility model:
- **Individuals and households** — personal preparedness and action
- **Communities** — mutual support and local resilience
- **Businesses** — continuity planning and economic recovery
- **Local government** — front-line emergency management
- **State/Territory government** — coordination, policy, resources
- **Australian Government** — national coordination, supplementary
  assistance (NEMA, Emergency Management Australia)

### National Coordination

- The platform MUST be capable of integrating with the **National
  Coordination Mechanism (NCM)** for consequence management
- Agents SHOULD support data exchange with the **National Joint
  Common Operating Picture (NJCOP)**
- The platform MUST respect the **Australian-New Zealand Emergency
  Management Committee (ANZEMC)** governance structure

## NON-NEGOTIABLE Requirements

1. **Human-in-the-loop** — No agent may take irreversible real-world
   action without explicit human authorisation.
2. **Data sovereignty** — All data MUST remain within Australian
   borders (Azure Australia East / Australia Southeast regions).
3. **Privacy by design** — PII handling MUST comply with the Australian
   Privacy Act 1988 and applicable state/territory legislation.
4. **Interoperability** — Agents MUST expose standards-based APIs
   (CAP, EDXL, GeoJSON, OpenAPI) for integration with existing
   Australian emergency management systems.
5. **Graceful degradation** — The platform MUST continue to function
   (at reduced capability) if any single agent, service, or region
   becomes unavailable.

## Quality Gates

- Every Pull Request MUST pass automated linting, unit tests, and
  integration tests before merge.
- Infrastructure changes MUST include a What-If / Plan review.
- Public-facing outputs (warnings, maps, dashboards) MUST be reviewed
  by a human operator before dissemination.
- **Lessons management** — After each significant incident or exercise,
  the platform MUST support capture, analysis, and integration of
  lessons identified, in accordance with AIDR continuous-improvement
  principles.

## Governance

- The project lead has final authority on architectural decisions.
- Specification changes require a Pull Request with at least one
  reviewer approval.
- This Constitution may only be amended by explicit project-lead
  approval.

## AIDR Handbook Collection Reference

| Handbook                                | Year | Sections Incorporated       |
| --------------------------------------- | ---- | --------------------------- |
| Incident Management Handbook            | 2023 | I, II, II-A                 |
| Evacuation Planning Handbook            | 2023 | VI, VI-A, VI-B, VI-C       |
| Public Information and Warnings         | 2021 | V, V-B, V-C                |
| Australian Warning System Companion     | 2022 | V-A                        |
| Community Recovery Handbook             | 2018 | VII, VII-A, VII-B, VII-C   |
| Emergency Management Arrangements       | 2023 | II, PPRR, Shared Resp, NCM |
| Emergency Planning Handbook             | 2020 | FR-001–007, FR-007a          |
| M&E Framework for Disaster Recovery     | v2   | FR-008–014, VII-A            |
| Outcomes, Activities and Indicators     | 2020 | FR-015–024, VII-B            |

---
*Version 1.1.0 · Last Amended 2025-07-17*