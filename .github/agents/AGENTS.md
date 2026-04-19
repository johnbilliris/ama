---
description: "Reference catalogue of all actor-specific agents — not an interactive agent."
---

# Actor Agent Catalogue

**Last Updated**: 2026-04-19
**Total Agents**: 94 (+ 6 archived)
**Feature**: [004-actor-github-agents](../../specs/004-actor-github-agents/spec.md)

This registry lists all actor-specific GitHub Copilot agents for the Autonomous Disaster Response Coordination Hub. Each agent provides domain-specific guidance for development-time use in VS Code.

## Operational Persona Agents (10)

AIIMS-aligned roles for incident management and coordination.

| Agent Name | Agent ID | File Path | Description |
|---|---|---|---|
| Incident Commander | incident-commander | operational/incident-commander.agent.md | AIIMS Incident Controller — overall coordination authority for multi-agency disaster response operations |
| Operations Officer | operations-officer | operational/operations-officer.agent.md | AIIMS Operations — tactical coordination, field deployment, and staging area management |
| Planning Officer | planning-officer | operational/planning-officer.agent.md | AIIMS Planning — situation assessment, resource forecasting, and action plan development |
| Logistics Officer | logistics-officer | operational/logistics-officer.agent.md | AIIMS Logistics — supply chain, transport coordination, medical supplies, and resource tracking |
| Public Information Officer | public-information-officer | operational/public-information-officer.agent.md | AIIMS Public Information — media liaison, multilingual community alerts, and accessibility compliance |
| Field Coordinator | field-coordinator | operational/field-coordinator.agent.md | Field operations — ground-level coordination and degraded-connectivity scenario management |
| Resilience Planner | resilience-planner | operational/resilience-planner.agent.md | Preparedness analysis — scenario rehearsal, gap identification, and framework modelling |
| Executive Leader | executive-leader | operational/executive-leader.agent.md | Executive oversight — strategic decisions, policy escalation, and inter-government liaison |
| Observer/Auditor | observer-auditor | operational/observer-auditor.agent.md | Read-only observer — audit trail review, compliance verification, and lessons learned |
| Risk Manager | risk-manager | operational/risk-manager.agent.md | Risk assessment, hazard analysis, risk register management, risk communication, and risk-informed decision support |

## Sector Agents — Jurisdiction-Specific (58)

Australian emergency management agencies organised by jurisdiction.

### New South Wales (6)

| Agent ID | File Path | Description |
|---|---|---|
| frnsw | sectors/nsw/frnsw.agent.md | Fire and Rescue NSW — urban fire suppression, hazmat response, structural and technical rescue |
| mrnsw | sectors/nsw/mrnsw.agent.md | Marine Rescue NSW — marine search and rescue, boating safety, and coastal emergency response |
| nsw-ambulance | sectors/nsw/nsw-ambulance.agent.md | NSW Ambulance — pre-hospital emergency medical care, patient triage, and medical evacuation |
| nsw-rfs | sectors/nsw/nsw-rfs.agent.md | NSW Rural Fire Service — bushfire suppression, rural fire management, and hazard reduction burns |
| nswpf | sectors/nsw/nswpf.agent.md | NSW Police Force — evacuation enforcement, traffic management, and search and rescue coordination |
| ses-nsw | sectors/nsw/ses-nsw.agent.md | NSW State Emergency Service — flood and storm combat agency operations, rescue, and community support |

### Victoria (5)

| Agent ID | File Path | Description |
|---|---|---|
| av | sectors/vic/av.agent.md | Ambulance Victoria — pre-hospital emergency medical care, patient triage, and medical evacuation |
| cfa-vic | sectors/vic/cfa-vic.agent.md | Country Fire Authority — bushfire suppression, rural fire management, and community preparedness |
| frv | sectors/vic/frv.agent.md | Fire Rescue Victoria — urban fire suppression, hazmat response, and structural rescue |
| ses-vic | sectors/vic/ses-vic.agent.md | Victoria SES — flood and storm combat agency operations, rescue, and community support |
| vicpol | sectors/vic/vicpol.agent.md | Victoria Police — evacuation enforcement, traffic management, and search and rescue coordination |

### Queensland (4)

| Agent ID | File Path | Description |
|---|---|---|
| qas | sectors/qld/qas.agent.md | Queensland Ambulance Service — pre-hospital emergency medical care and patient triage |
| qfd | sectors/qld/qfd.agent.md | Queensland Fire Department — fire suppression, rescue operations, and SES coordination |
| qps | sectors/qld/qps.agent.md | Queensland Police Service — evacuation enforcement, traffic management, and search and rescue |
| ses-qld | sectors/qld/ses-qld.agent.md | Queensland SES — flood and storm combat agency operations, rescue, and community support |

### South Australia (5)

| Agent ID | File Path | Description |
|---|---|---|
| saas | sectors/sa/saas.agent.md | SA Ambulance Service — pre-hospital emergency medical care and patient triage |
| sacfs | sectors/sa/sacfs.agent.md | SA Country Fire Service — bushfire suppression, rural fire management, and hazard reduction burns |
| samfs | sectors/sa/samfs.agent.md | SA Metropolitan Fire Service — urban fire suppression, hazmat response, and structural rescue |
| sapol | sectors/sa/sapol.agent.md | SA Police — evacuation enforcement, traffic management, and search and rescue coordination |
| ses-sa | sectors/sa/ses-sa.agent.md | SA State Emergency Service — flood and storm combat agency operations and community support |

### Western Australia (3)

| Agent ID | File Path | Description |
|---|---|---|
| dfes-wa | sectors/wa/dfes-wa.agent.md | WA Dept of Fire and Emergency Services — fire suppression, rescue, and SES coordination |
| sja-wa | sectors/wa/sja-wa.agent.md | St John WA — pre-hospital emergency medical care, patient triage, and medical evacuation |
| wapol | sectors/wa/wapol.agent.md | WA Police Force — evacuation enforcement, traffic management, and search and rescue coordination |

### Tasmania (4)

| Agent ID | File Path | Description |
|---|---|---|
| at | sectors/tas/at.agent.md | Ambulance Tasmania — pre-hospital emergency medical care, patient triage, and medical evacuation |
| ses-tas | sectors/tas/ses-tas.agent.md | Tasmania SES — flood and storm combat agency operations, rescue, and community support |
| taspol | sectors/tas/taspol.agent.md | Tasmania Police — evacuation enforcement, traffic management, and search and rescue coordination |
| tfs | sectors/tas/tfs.agent.md | Tasmania Fire Service — fire suppression, rescue operations, and emergency response |

### Australian Capital Territory (7)

| Agent ID | File Path | Description |
|---|---|---|
| act-ambulance | sectors/act/act-ambulance.agent.md | ACT Ambulance Service — pre-hospital emergency medical care and patient triage |
| act-esa | sectors/act/act-esa.agent.md | ACT Emergency Services Agency — umbrella coordination of fire, rescue, ambulance, and SES |
| act-fr | sectors/act/act-fr.agent.md | ACT Fire and Rescue — urban fire suppression, hazmat response, and structural rescue |
| act-policing | sectors/act/act-policing.agent.md | ACT Policing — evacuation enforcement, traffic management, and search and rescue coordination |
| act-rfs | sectors/act/act-rfs.agent.md | ACT Rural Fire Service — bushfire suppression, rural fire management, and hazard reduction burns |
| afp | sectors/act/afp.agent.md | Australian Federal Police (ACT) — federal law enforcement and counter-terrorism |
| ses-act | sectors/act/ses-act.agent.md | ACT State Emergency Service — flood and storm combat operations and community support |

### Northern Territory (5)

| Agent ID | File Path | Description |
|---|---|---|
| bushfires-nt | sectors/nt/bushfires-nt.agent.md | Bushfires NT — bushfire suppression, rural fire management, and hazard reduction burns |
| ntes | sectors/nt/ntes.agent.md | NT Emergency Service — cyclone, flood, and severe weather response including tropical cyclone preparedness |
| ntfrs | sectors/nt/ntfrs.agent.md | NT Fire and Rescue Service — fire suppression, rescue operations, and emergency response |
| ntpf | sectors/nt/ntpf.agent.md | NT Police Force — evacuation enforcement, traffic management, and search and rescue coordination |
| sja-nt | sectors/nt/sja-nt.agent.md | St John NT — pre-hospital emergency medical care, patient triage, and medical evacuation |

### Commonwealth (11)

| Agent ID | File Path | Description |
|---|---|---|
| abf | sectors/commonwealth/abf.agent.md | Australian Border Force — maritime emergency response and border security |
| adf | sectors/commonwealth/adf.agent.md | Australian Defence Force — Defence Assistance to the Civil Community (DACC) |
| afp | sectors/commonwealth/afp.agent.md | Australian Federal Police — federal law enforcement and counter-terrorism |
| arc | sectors/commonwealth/arc.agent.md | Australian Red Cross — humanitarian relief, evacuation centre support, and disaster recovery |
| asa | sectors/commonwealth/asa.agent.md | Airservices Australia — aviation fire and rescue services at major airports |
| bom-national | sectors/commonwealth/bom-national.agent.md | Bureau of Meteorology — weather forecasting, severe weather warnings, and fire weather intelligence |
| ga-national | sectors/commonwealth/ga-national.agent.md | Geoscience Australia — earthquake monitoring, tsunami warnings, and geological hazard assessment |
| nema | sectors/commonwealth/nema.agent.md | National Emergency Management Agency — national coordination and COMDISPLAN activation |
| rfds | sectors/commonwealth/rfds.agent.md | Royal Flying Doctor Service — aeromedical retrieval and remote area medical services |
| sja-national | sectors/commonwealth/sja-national.agent.md | St John Ambulance Australia — first aid training and event medical support |
| surf-lifesaving | sectors/commonwealth/surf-lifesaving.agent.md | Surf Life Saving Australia — coastal and surf rescue, beach safety, and marine emergency response |

### Cross-Sector (8)

| Agent ID | File Path | Description |
|---|---|---|
| community-ngos | sectors/cross-sector/community-ngos.agent.md | Community and NGO sector — Red Cross, Salvation Army, evacuation centre management, and emergency relief |
| health | sectors/cross-sector/health.agent.md | Health sector — public health emergencies, hospital surge, environmental health, and mental health response |
| local-government | sectors/cross-sector/local-government.agent.md | Local Government — municipal emergency management plans, community recovery, and evacuation centres |
| state-government | sectors/cross-sector/state-government.agent.md | State Government — state emergency management legislation, coordination centres, and lead agency designation |
| territory-government | sectors/cross-sector/territory-government.agent.md | Territory Government — territory emergency management ordinances, ACT and NT arrangements |
| transport | sectors/cross-sector/transport.agent.md | Transport sector — road and rail closure authorities, evacuation transport, and freight coordination |
| utility | sectors/cross-sector/utility.agent.md | Utility sector — energy, water, and telecommunications essential services restoration |
| volunteer | sectors/cross-sector/volunteer.agent.md | Volunteer sector — spontaneous volunteer management, protection legislation, and credentialing |

### Archived (6)

Generic sector agents superseded by jurisdiction-specific agents above.

| Agent ID | File Path |
|---|---|
| ambulance-paramedic | sectors/_archive/ambulance-paramedic.agent.md |
| commonwealth-government | sectors/_archive/commonwealth-government.agent.md |
| fire-services | sectors/_archive/fire-services.agent.md |
| meteorology-bom | sectors/_archive/meteorology-bom.agent.md |
| police | sectors/_archive/police.agent.md |
| ses | sectors/_archive/ses.agent.md |

## Technical Persona Agents (17)

Project contributor roles with architecture and convention guidance.

| Agent Name | Agent ID | File Path | Description |
|---|---|---|---|
| Solution Architect | solution-architect | technical/solution-architect.agent.md | System design, Azure architecture governance, NFR enforcement, and cross-cutting technical decisions |
| Software Developer | software-developer | technical/software-developer.agent.md | Python 3.12 and TypeScript 5.8 conventions, FastAPI/Next.js patterns, and PR workflow |
| Infrastructure/DevOps | infrastructure-devops | technical/infrastructure-devops.agent.md | Azure AU infrastructure, Bicep templates, Container Apps, and CI/CD pipelines |
| Data Engineer | data-engineer | technical/data-engineer.agent.md | Cosmos DB, signal ingestion pipelines, Event Hubs/Service Bus, and data model conventions |
| Security Engineer | security-engineer | technical/security-engineer.agent.md | Constitution IV compliance, tenant isolation, RBAC, content safety, and Australian data residency |
| QA/Test Engineer | qa-test-engineer | technical/qa-test-engineer.agent.md | Testing strategy — pytest, Playwright, contract/integration/simulation/e2e test conventions |
| UX Designer | ux-designer | technical/ux-designer.agent.md | Dashboard design for high-pressure ops, SC-007 rubric, accessibility per Constitution V |
| Product Owner/BA | product-owner-ba | technical/product-owner-ba.agent.md | Requirements methodology, acceptance criteria, success metrics, and speckit workflow |
| Azure Principal Architect | azure-principal-architect | technical/azure-principal-architect.agent.md | Azure WAF pillar assessment, Azure architecture patterns, and Microsoft best practices |
| API Architect | api-architect | technical/api-architect.agent.md | API design, service boundaries, resilience patterns, event-driven architecture, and layered service architecture |
| Principal Engineer | principal-engineer | technical/principal-engineer.agent.md | Engineering excellence, design patterns, technical debt management, and code review mentoring |
| SRE Engineer | sre-engineer | technical/sre-engineer.agent.md | SLI/SLO management, error budgets, chaos engineering, toil reduction, and reliability automation |
| AI/ML Engineer | ai-ml-engineer | technical/ai-ml-engineer.agent.md | AI agent system design, LLM architecture, Azure OpenAI integration, and prompt engineering |
| Accessibility Tester | accessibility-tester | technical/accessibility-tester.agent.md | WCAG 2.2 compliance, multilingual and RTL validation, and assistive technology testing |
| Chaos Engineer | chaos-engineer | technical/chaos-engineer.agent.md | Chaos experiment design, failure injection, resilience validation, and blast radius control |
| Compliance Auditor | compliance-auditor | technical/compliance-auditor.agent.md | Australian government regulatory compliance, privacy legislation, and data handling obligations |
| Docker & Container Engineer | docker-container-engineer | technical/docker-container-engineer.agent.md | Dockerfile optimisation, Azure Container Apps configuration, and container image security |

## Speckit Workflow Agents (9)

Feature specification, planning, and implementation workflow agents.

| Agent ID | File Path | Description |
|---|---|---|
| speckit.analyze | speckit.analyze.agent.md | Cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md |
| speckit.checklist | speckit.checklist.agent.md | Generate a custom checklist for the current feature based on user requirements |
| speckit.clarify | speckit.clarify.agent.md | Identify underspecified areas in the feature spec via targeted clarification questions |
| speckit.constitution | speckit.constitution.agent.md | Create or update the project constitution from principle inputs |
| speckit.implement | speckit.implement.agent.md | Execute the implementation plan by processing tasks defined in tasks.md |
| speckit.plan | speckit.plan.agent.md | Execute the implementation planning workflow to generate design artifacts |
| speckit.specify | speckit.specify.agent.md | Create or update the feature specification from a natural language description |
| speckit.tasks | speckit.tasks.agent.md | Generate an actionable, dependency-ordered tasks.md from design artifacts |
| speckit.taskstoissues | speckit.taskstoissues.agent.md | Convert tasks into dependency-ordered GitHub issues |
