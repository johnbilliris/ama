# Actor Agent Catalogue

**Last Updated**: 2026-03-23  
**Total Agents**: 41  
**Feature**: [004-actor-github-agents](../../specs/004-actor-github-agents/spec.md)

This registry lists all actor-specific GitHub Copilot agents for the Autonomous Disaster Response Coordination Hub. Each agent provides domain-specific guidance for development-time use in VS Code.

## Operational Persona Agents

AIIMS-aligned roles for incident management and coordination.

| Agent Name | Agent ID | File Path | Description | Key Handoffs |
|------------|----------|-----------|-------------|--------------|
| Incident Commander | incident-commander | .github/agents/operational/incident-commander.agent.md | AIIMS Incident Controller — overall coordination authority for multi-agency disaster response operations | operations-officer, planning-officer, logistics-officer, public-information-officer, executive-leader, risk-manager |
| Operations Officer | operations-officer | .github/agents/operational/operations-officer.agent.md | AIIMS Operations — tactical coordination, field deployment, and staging area management | incident-commander, field-coordinator, logistics-officer |
| Planning Officer | planning-officer | .github/agents/operational/planning-officer.agent.md | AIIMS Planning — situation assessment, resource forecasting, and action plan development | incident-commander, logistics-officer, resilience-planner, risk-manager |
| Logistics Officer | logistics-officer | .github/agents/operational/logistics-officer.agent.md | AIIMS Logistics — supply chain, transport coordination, medical supplies, and resource tracking | planning-officer, health, transport, incident-commander |
| Public Information Officer | public-information-officer | .github/agents/operational/public-information-officer.agent.md | AIIMS Public Information — media liaison, multilingual community alerts, and accessibility compliance | incident-commander, community-ngos, meteorology-bom |
| Field Coordinator | field-coordinator | .github/agents/operational/field-coordinator.agent.md | Field operations — ground-level coordination and degraded-connectivity scenario management | operations-officer, logistics-officer |
| Resilience Planner | resilience-planner | .github/agents/operational/resilience-planner.agent.md | Preparedness analysis — scenario rehearsal, gap identification, and framework modelling | planning-officer, executive-leader, observer-auditor, risk-manager |
| Executive Leader | executive-leader | .github/agents/operational/executive-leader.agent.md | Executive oversight — strategic decisions, policy escalation, and inter-government liaison | incident-commander, commonwealth-government, state-government, compliance-auditor, risk-manager |
| Observer/Auditor | observer-auditor | .github/agents/operational/observer-auditor.agent.md | Read-only observer — audit trail review, compliance verification, and lessons learned | resilience-planner, planning-officer, executive-leader, compliance-auditor |
| Risk Manager | risk-manager | .github/agents/operational/risk-manager.agent.md | Risk assessment, hazard analysis, risk register management, risk communication, and risk-informed decision support | incident-commander, planning-officer, resilience-planner, executive-leader, observer-auditor, compliance-auditor, meteorology-bom |

## Organisation Sector Agents

Australian emergency management sectors with jurisdictional context.

| Agent Name | Agent ID | File Path | Description | Key Handoffs |
|------------|----------|-----------|-------------|--------------|
| Fire Services | fire-services | .github/agents/sectors/fire-services.agent.md | Bushfire and structural fire response, lead agency designation, and evacuation zone management | police, ses, meteorology-bom, incident-commander, ambulance-paramedic |
| Commonwealth Government | commonwealth-government | .github/agents/sectors/commonwealth-government.agent.md | COMDISPLAN national coordination, EMA, NEMA, and Defence assistance | state-government, meteorology-bom, incident-commander, compliance-auditor |
| State Government | state-government | .github/agents/sectors/state-government.agent.md | State emergency management legislation, coordination centres, and lead agency designation | commonwealth-government, local-government, incident-commander, compliance-auditor |
| Territory Government | territory-government | .github/agents/sectors/territory-government.agent.md | Territory emergency management ordinances, ACT and NT arrangements | commonwealth-government, local-government |
| Local Government | local-government | .github/agents/sectors/local-government.agent.md | Municipal emergency management plans, community recovery, and evacuation centres | state-government, community-ngos, volunteer |
| Police | police | .github/agents/sectors/police.agent.md | Evacuation enforcement, traffic management, coronial engagement, and search and rescue | fire-services, ses, incident-commander, ambulance-paramedic |
| Ambulance/Paramedic | ambulance-paramedic | .github/agents/sectors/ambulance-paramedic.agent.md | Patient triage, medical evacuation, and mass casualty management | health, logistics-officer, police |
| State Emergency Service | ses | .github/agents/sectors/ses.agent.md | Flood and storm lead combat agency, rescue operations, and volunteer coordination | police, meteorology-bom, volunteer, fire-services |
| Meteorology (BoM) | meteorology-bom | .github/agents/sectors/meteorology-bom.agent.md | Authoritative weather warnings, fire weather intelligence, flood watches, and cyclone tracking | fire-services, ses, incident-commander, commonwealth-government |
| Health | health | .github/agents/sectors/health.agent.md | Public health emergencies, hospital surge, environmental health, and mental health response | ambulance-paramedic, logistics-officer, commonwealth-government |
| Utility | utility | .github/agents/sectors/utility.agent.md | Energy, water, and telecommunications essential services restoration | transport, local-government, incident-commander |
| Transport | transport | .github/agents/sectors/transport.agent.md | Road and rail closure authorities, evacuation transport, and freight coordination | police, logistics-officer, utility |
| Community (NGOs) | community-ngos | .github/agents/sectors/community-ngos.agent.md | Red Cross, Salvation Army, evacuation centre management, and emergency relief | local-government, volunteer, public-information-officer |
| Volunteer | volunteer | .github/agents/sectors/volunteer.agent.md | Spontaneous volunteer management, volunteer protection legislation, and credentialing | ses, community-ngos, local-government |

## Technical Persona Agents

Project contributor roles with architecture and convention guidance.

| Agent Name | Agent ID | File Path | Description | Key Handoffs |
|------------|----------|-----------|-------------|--------------|
| Solution Architect | solution-architect | .github/agents/technical/solution-architect.agent.md | System design, Azure architecture governance, NFR enforcement, and cross-cutting technical decisions | software-developer, infrastructure-devops, security-engineer, data-engineer, product-owner-ba, azure-principal-architect, api-architect, principal-engineer, ai-ml-engineer |
| Software Developer | software-developer | .github/agents/technical/software-developer.agent.md | Python 3.12 and TypeScript 5.6 conventions, FastAPI/Next.js patterns, and PR workflow | solution-architect, security-engineer, qa-test-engineer, api-architect, principal-engineer, ai-ml-engineer, accessibility-tester |
| Infrastructure/DevOps | infrastructure-devops | .github/agents/technical/infrastructure-devops.agent.md | Azure AU infrastructure, Bicep templates, Container Apps, and CI/CD pipelines | solution-architect, security-engineer, azure-principal-architect, sre-engineer, docker-container-engineer |
| Data Engineer | data-engineer | .github/agents/technical/data-engineer.agent.md | Cosmos DB, signal ingestion pipelines, Event Hubs/Service Bus, and data model conventions | solution-architect, security-engineer, azure-principal-architect, api-architect, ai-ml-engineer |
| Security Engineer | security-engineer | .github/agents/technical/security-engineer.agent.md | Constitution IV compliance, tenant isolation, RBAC, content safety, and Australian data residency | infrastructure-devops, software-developer, solution-architect, azure-principal-architect, compliance-auditor |
| QA/Test Engineer | qa-test-engineer | .github/agents/technical/qa-test-engineer.agent.md | Testing strategy — pytest, Playwright, contract/integration/simulation/e2e test conventions | software-developer, accessibility-tester, principal-engineer, chaos-engineer |
| UX Designer | ux-designer | .github/agents/technical/ux-designer.agent.md | Dashboard design for high-pressure ops, SC-007 rubric, accessibility per Constitution V | software-developer, product-owner-ba, accessibility-tester |
| Product Owner/BA | product-owner-ba | .github/agents/technical/product-owner-ba.agent.md | Requirements methodology, acceptance criteria, success metrics, and speckit workflow | solution-architect, ux-designer |
| Azure Principal Architect | azure-principal-architect | .github/agents/technical/azure-principal-architect.agent.md | Azure WAF pillar assessment, Azure architecture patterns, and Microsoft best practices | solution-architect, infrastructure-devops, security-engineer, data-engineer |
| API Architect | api-architect | .github/agents/technical/api-architect.agent.md | API design, service boundaries, resilience patterns, event-driven architecture, caching, observability, and layered service architecture | solution-architect, software-developer, data-engineer, azure-principal-architect, security-engineer, principal-engineer, sre-engineer, ai-ml-engineer |
| Principal Engineer | principal-engineer | .github/agents/technical/principal-engineer.agent.md | Engineering excellence, design patterns, technical debt management, code review mentoring, and pragmatic implementation | software-developer, solution-architect, qa-test-engineer, api-architect, security-engineer, ai-ml-engineer |
| SRE Engineer | sre-engineer | .github/agents/technical/sre-engineer.agent.md | SLI/SLO management, error budgets, chaos engineering, toil reduction, incident response, and reliability automation | infrastructure-devops, api-architect, azure-principal-architect, qa-test-engineer, security-engineer, solution-architect, chaos-engineer, docker-container-engineer |
| AI/ML Engineer | ai-ml-engineer | .github/agents/technical/ai-ml-engineer.agent.md | AI agent system design, LLM architecture, Azure OpenAI integration, prompt engineering, confidence scoring, and content safety | software-developer, solution-architect, data-engineer, security-engineer, api-architect, qa-test-engineer |
| Accessibility Tester | accessibility-tester | .github/agents/technical/accessibility-tester.agent.md | WCAG 2.2 compliance, multilingual and RTL validation, assistive technology testing, and inclusive design verification | ux-designer, qa-test-engineer, software-developer, public-information-officer, compliance-auditor |
| Chaos Engineer | chaos-engineer | .github/agents/technical/chaos-engineer.agent.md | Chaos experiment design, failure injection, resilience validation, blast radius control, and disaster-scenario stress testing | sre-engineer, infrastructure-devops, qa-test-engineer, api-architect, security-engineer, docker-container-engineer |
| Compliance Auditor | compliance-auditor | .github/agents/technical/compliance-auditor.agent.md | Australian government regulatory compliance, privacy legislation, emergency management legislation, and data handling obligations | security-engineer, observer-auditor, executive-leader, product-owner-ba, solution-architect, accessibility-tester |
| Docker & Container Engineer | docker-container-engineer | .github/agents/technical/docker-container-engineer.agent.md | Dockerfile optimization, Azure Container Apps configuration, container image security, and container runtime reliability | infrastructure-devops, software-developer, security-engineer, sre-engineer, azure-principal-architect |
