# Research: Actor-Specific GitHub Agents

## 1. Agent File Conventions

**Decision**: Follow the existing `.agent.md` format established by the speckit agents.

**Rationale**: The project already has 9 working agents using a proven YAML frontmatter + Markdown body pattern. Consistency ensures VS Code Copilot discovers and loads agents correctly.

**Alternatives considered**: Custom prompt files (`.prompt.md`), skill files (SKILL.md). Rejected because `.agent.md` is the canonical format for named agents with handoff support, and the project already uses this format.

### Observed Schema

```yaml
---
description: <single-line purpose statement>
handoffs:
  - label: <display name>
    agent: <target agent name>
    prompt: <instruction to pass>
    send: <true|false>
---
```

**Body structure**: Free-form Markdown instructions. Operational/sector/technical agents will NOT use the `$ARGUMENTS` / script-execution pattern of speckit agents — they are knowledge agents, not workflow agents. Their body will contain domain knowledge, contextual references, and scope boundaries.

### File naming convention

- Pattern: `<kebab-case-role>.agent.md`
- Examples: `incident-commander.agent.md`, `fire-services.agent.md`, `solution-architect.agent.md`
- Agent name (for handoffs): matches the file stem without `.agent.md`, e.g., `incident-commander`

## 2. Agent Content Architecture

**Decision**: Each agent body will contain the following standardised sections:

1. **Role Overview** — who this actor is, their primary function
2. **Responsibilities & Decision Rights** — what they own, what they can approve/escalate
3. **Scope Boundaries** — what is NOT this agent's domain (with handoff references)
4. **Key Relationships** — which other actors this agent coordinates with
5. **Contextual References** — file paths to authoritative project artefacts
6. **Guidance Notes** — domain-specific knowledge relevant to this actor

**Rationale**: Standardised sections make agents predictable, maintainable, and machine-readable for future catalogue validation. Knowledge-style agents (vs workflow agents) work best with structured reference content rather than procedural scripts.

**Alternatives considered**: Unstructured prose per agent. Rejected because 31 agents with inconsistent formats would be difficult to maintain and validate against SC-002.

## 3. AIIMS Framework Alignment (Operational Personas)

**Decision**: Map operational persona agents directly to AIIMS functional areas.

**Rationale**: The constitution mandates AIIMS alignment (Principle II). The data model's `roleType` enum already maps to AIIMS functions. Using AIIMS as the authoritative source ensures persona agents reflect real Australian incident management governance.

### AIIMS Functional Area → Agent Mapping

| AIIMS Function | Agent | Data Model roleType |
|---------------|-------|-------------------|
| Incident Controller | incident-commander | `incident_commander` |
| Operations | operations-officer | `operations` |
| Planning | planning-officer | `planning` |
| Logistics | logistics-officer | `logistics` |
| Public Information | public-information-officer | `public_information` |
| Field Operations | field-coordinator | `field_coordinator` |
| Preparedness/Recovery | resilience-planner | `planner` |
| Executive Oversight | executive-leader | `executive` |
| Audit/Review | observer-auditor | `observer` |

## 4. Australian Emergency Management Sectors

**Decision**: Map sector agents to the organisation `category` enum in the data model, with Emergency Services expanded into 4 sub-sectors plus Meteorology added as identified in clarifications.

**Rationale**: The data model uses `category` as the primary sector classifier. Expanding Emergency Services into Fire, Police, Ambulance/Paramedic, and SES was confirmed in clarification because these sub-sectors have distinct legislation, command structures, and coordination obligations.

### Sector → Agent Mapping

| Sector | Agent File | Data Model category | Key Legislation/Framework |
|--------|-----------|-------------------|--------------------------|
| Commonwealth Government | commonwealth-government | `commonwealth` | COMDISPLAN, Emergency Management Act 2005 (Cth) |
| State Government | state-government | `state` | State emergency management acts (varies by state) |
| Territory Government | territory-government | `territory` | Territory emergency management ordinances |
| Local Government | local-government | `local_government` | Local government acts, municipal emergency plans |
| Fire Services | fire-services | `emergency_service` | CFA Act (VIC), Rural Fires Act (NSW), Fire and Emergency Services Act (WA) |
| Police | police | `emergency_service` | Police acts (state-specific), coroner engagement |
| Ambulance/Paramedic | ambulance-paramedic | `emergency_service` | Ambulance Services acts, health emergency legislation |
| State Emergency Service | ses | `emergency_service` | SES acts (state-specific), flood/storm lead agency |
| Meteorology (BoM) | meteorology-bom | `commonwealth` | Meteorology Act 1955 (Cth), authoritative warnings |
| Health | health | `health` | Public Health acts, pandemic preparedness frameworks |
| Utility | utility | `utility` | Energy security, water, telecommunications legislation |
| Transport | transport | `transport` | Transport safety acts, road/rail closure authorities |
| Community (NGOs) | community-ngos | `community` | Red Cross mandate, Salvation Army, community recovery |
| Volunteer | volunteer | `volunteer` | Volunteer protection legislation, spontaneous volunteer management |

## 5. Technical Persona Domain Mapping

**Decision**: Map technical agents to the project's technology stack and constitutional principles.

**Rationale**: Technical agents serve as onboarding and convention-enforcement tools. Each must reference the constitution, relevant specs, and the specific conventions for their domain.

### Technical Persona → Domain Mapping

| Agent | Primary Domain | Key References |
|-------|---------------|----------------|
| solution-architect | System design, Azure architecture, NFRs | Constitution, architecture.md, data-model.md |
| software-developer | Code conventions, patterns, PR workflow | copilot-instructions.md, ruff.toml, tsconfig.json |
| infrastructure-devops | Azure infra, Bicep, CI/CD, monitoring | infra/bicep/, Dockerfile, monitoring.bicep |
| data-engineer | Data pipelines, Cosmos DB, signal ingestion | data-model.md, signal-envelope.schema.json |
| security-engineer | Privacy, RBAC, tenant isolation, content safety | Constitution IV, safety-guardrails.rego, tenant-isolation.rego |
| qa-test-engineer | Testing strategy, pytest, Playwright, simulation | tests/, conftest.py, playwright.config.ts |
| ux-designer | Dashboard design, accessibility, SC-007 rubric | Constitution V, packages/ui/ |
| product-owner-ba | Requirements, acceptance criteria, success metrics | specs/, evaluation/ |

## 6. Handoff Relationship Design

**Decision**: Define handoff relationships using a tiered model where agents hand off to related agents within their tier first, then cross-tier when the question spans domains.

**Rationale**: The spec requires each agent to declare handoff relationships (FR-013). Cross-tier handoffs prevent dead ends — e.g., a Health sector agent should hand off to the Logistics persona agent for supply chain questions.

### Handoff Principles

1. **Operational agents** hand off laterally to other AIIMS functions (e.g., Incident Commander → Operations Officer for tactical detail)
2. **Sector agents** hand off laterally to related sectors (e.g., Fire Services → Police for evacuation enforcement)
3. **Sector agents** hand off upward to relevant operational personas (e.g., Health → Logistics Officer for medical supply coordination)
4. **Technical agents** hand off laterally for cross-cutting concerns (e.g., Software Developer → Security Engineer for auth patterns)
5. **All agents** can hand off to Solution Architect for architectural questions

## 7. Registry Format

**Decision**: Use an `AGENTS.md` file in `.github/agents/` as the catalogue registry.

**Rationale**: VS Code Copilot supports `AGENTS.md` as a discovery document. Placing it in the agents root makes it discoverable by both humans and tooling.

**Format**: Markdown table grouped by tier with columns: Agent Name, File Path, Description, Key Handoffs.
