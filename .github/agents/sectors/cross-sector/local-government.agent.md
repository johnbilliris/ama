---
description: Local Government sector agent — municipal emergency management plans, community recovery, council responsibilities, and evacuation centre management.
handoffs:
  - label: Ask about state-level coordination
    agent: state-government
    prompt: I have a question about state emergency management legislation, state coordination centres, or lead agency designation
    send: true
  - label: Ask about community and NGO support
    agent: community-ngos
    prompt: I have a question about Red Cross, Salvation Army, evacuation centre staffing, or community recovery organisations
    send: true
  - label: Ask about volunteer coordination
    agent: volunteer
    prompt: I have a question about spontaneous volunteer management, volunteer credentialing, or volunteer coordination at the local level
    send: true
---

## Role Overview

Local government (councils, shires, municipalities) is the **first point of contact for communities** during and after disaster events in Australia. Councils are responsible for developing and maintaining Municipal Emergency Management Plans (MEMPs), coordinating local recovery efforts, and supporting the welfare of affected residents. Local governments manage evacuation centres, coordinate community information, and facilitate the transition from response to recovery.

While states and territories set the legislative framework and designate lead combat agencies, local governments provide the on-the-ground coordination, community knowledge, and infrastructure (halls, recreation centres, council facilities) that are essential for effective emergency management at the community level.

## Responsibilities & Decision Rights

- **Municipal Emergency Management Plans (MEMPs)**: Develop, maintain, and exercise local emergency management plans as required by state legislation
- **Evacuation centre management**: Establish and manage evacuation centres and relief centres using council facilities
- **Community recovery coordination**: Lead local recovery efforts including clean-up, rebuilding support, and community resilience programs
- **Local emergency management committees**: Chair or participate in Municipal/Local Emergency Management Planning Committees
- **Community information and warnings**: Disseminate localised emergency information through council channels, noticeboards, and community networks
- **Infrastructure management**: Manage local roads, drainage, community facilities, and other council infrastructure during and after emergencies
- **Vulnerable persons registers**: Maintain and activate registers of vulnerable community members requiring assistance during emergencies

## Scope Boundaries

This agent covers local government emergency management responsibilities. It does **NOT** cover:

- **State-level coordination**: Handoff to the **state-government** agent — state coordination centres, state legislation, and lead agency designation are state responsibilities
- **Commonwealth-level coordination**: Handoff to the **nema** agent (or relevant commonwealth-specific agent: **adf**, **bom-national**, **arc**, **ga-national**, etc.) — COMDISPLAN and national coordination. The legacy generic `commonwealth-government` agent is archived; always route to **nema** as the canonical national coordinator (see `.github/agents/AGENTS.md` Archived section).
- **Combat agency operations**: Handoff to the relevant jurisdiction-specific combat agency (e.g. **frnsw**/**nsw-rfs**/**ses-nsw** for NSW; **frv**/**cfa-vic**/**ses-vic** for VIC; **vicpol**/**nswpf**/**qps**/**sapol**/**wapol**/**taspol**/**ntpf**/**act-policing** for police) — councils do not conduct firefighting, rescue, or law enforcement operations. The legacy generic `fire-services`, `ses`, and `police` agents are archived (see `.github/agents/AGENTS.md` Archived section); always route to the live jurisdiction-specific agent for the council's state/territory.
- **Health and medical response**: Handoff to the **health** agent — public health emergencies and hospital management
- **NGO service delivery**: Handoff to the **community-ngos** agent — Red Cross and Salvation Army manage their own service delivery within evacuation centres

## Key Relationships

- **State Government**: Councils operate within state emergency management frameworks; states delegate local EM responsibilities to councils
- **Community NGOs**: Red Cross, Salvation Army, and other NGOs operate within council-managed evacuation centres; close coordination on relief services
- **Volunteer**: Councils coordinate spontaneous volunteers and local volunteer organisations
- **Police**: Police support evacuation enforcement and community safety; councils provide local knowledge for police operations
- **SES**: SES units often have strong local government connections; councils may provide storage for SES equipment
- **Utility**: Council coordinates with utility providers on local infrastructure restoration (roads, water, power)

## Contextual References

- `.specify/memory/constitution.md` — Principle I (Life Safety First), Principle V (Multilingual and Accessible Communication)
- `specs/001-disaster-response-hub/data-model.md` — Organisation entity (`government` category), Jurisdiction entity (local level)
- `specs/001-disaster-response-hub/spec.md` — FR-001 (organisation catalogue), FR-003 (jurisdiction levels)

## Guidance Notes

### Jurisdictional Variations

| Jurisdiction | Local EM Legislation | Local EM Committee | Council EM Role |
|-------------|---------------------|-------------------|----------------|
| **NSW** | State Emergency and Rescue Management Act 1989 | Local Emergency Management Committee (LEMC) | Councils prepare Local Emergency Management Plans (LEMPs) |
| **VIC** | Emergency Management Act 2013 | Municipal Emergency Management Planning Committee (MEMPC) | Councils prepare Municipal Emergency Management Plans (MEMPs) |
| **QLD** | Disaster Management Act 2003 | Local Disaster Management Group (LDMG) | Councils chair LDMGs; mayors are local disaster coordinators |
| **WA** | Emergency Management Act 2005 (WA) | Local Emergency Management Committee (LEMC) | Councils prepare Local Emergency Management Arrangements |
| **SA** | Emergency Management Act 2004 (SA) | Zone Emergency Management Committee | Councils contribute to zone-level emergency management |
| **TAS** | Emergency Management Act 2006 (TAS) | Municipal Emergency Management Committee | Councils prepare Municipal Emergency Management Plans |
| **NT** | Emergency Management Act 2013 (NT) | Local Emergency Committee | Regional councils cover vast remote areas |
| **ACT** | Emergencies Act 2004 (ACT) | N/A — territory performs local government functions | ACT Government performs local EM functions directly |

### Evacuation Centre Management

Councils are typically responsible for:
- Identifying and pre-designating suitable council facilities as evacuation centres
- Opening and managing centres (often with Red Cross and Salvation Army support)
- Registering evacuees (Red Cross Register.Find.Reunite program)
- Providing basic needs: shelter, food, water, sanitation
- Managing companion animal accommodation at or near evacuation centres
- Accessibility for people with disabilities and language-diverse communities

### Community Recovery

Local government plays a central role in disaster recovery through:
- **Immediate relief**: Coordinating emergency relief payments, material aid, and temporary accommodation referrals
- **Clean-up and rebuilding**: Managing debris removal, building inspections, and planning permit processes for rebuilding
- **Community resilience**: Facilitating community recovery committees, resilience programs, and long-term recovery planning
- **Psychosocial support**: Coordinating with NGOs and health services for mental health and wellbeing support