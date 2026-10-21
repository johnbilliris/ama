# Data Model: Actor-Specific GitHub Agents

## AgentDefinition

**Purpose**: Represents a single GitHub Copilot agent file that encodes an actor's domain knowledge for development-time guidance.

**Fields**:
- `agentId`: string, kebab-case identifier matching the file stem (e.g., `incident-commander`)
- `tier`: enum (`operational`, `sector`, `technical`)
- `displayName`: string, human-readable name for the agent (e.g., "Incident Commander")
- `description`: string, single-line purpose statement used in YAML frontmatter
- `filePath`: string, relative path from repo root (e.g., `.github/agents/operational/incident-commander.agent.md`)
- `handoffs`: array of HandoffRelationship records
- `contextReferences`: array of file paths to authoritative project artefacts
- `scopeBoundary`: string, concise description of what this agent does NOT cover

**Relationships**:
- One AgentDefinition belongs to one AgentTier.
- One AgentDefinition has many HandoffRelationships.
- One AgentDefinition references many project artefacts.

**Validation rules**:
- `agentId` must be unique across all tiers.
- `tier` is required.
- `description` must be non-empty and under 200 characters (max 199).
- `handoffs` must declare at least one relationship for active actor files.
- `contextReferences` must include at least one valid file path.
- `filePath` must match one of:
	- `.github/agents/operational/{agentId}.agent.md`
	- `.github/agents/technical/{agentId}.agent.md`
	- `.github/agents/sectors/{jurisdiction}/{agentId}.agent.md`
- Canonical identity is the file stem (`agentId`); frontmatter `name` aliases are unsupported unless explicitly approved by contract.

## HandoffRelationship

**Purpose**: A declared link between two agents indicating scope-transfer guidance.

**Fields**:
- `label`: string, display name for the handoff (e.g., "Ask about tactical operations")
- `targetAgentId`: string, reference to another AgentDefinition
- `prompt`: string, instruction text to pass to the target agent
- `autoSend`: boolean, whether to auto-submit prompt after handoff click (default: false)

**Relationships**:
- Many HandoffRelationships belong to one source AgentDefinition.
- Each HandoffRelationship references one target AgentDefinition.

**Validation rules**:
- `targetAgentId` must reference exactly one existing AgentDefinition (case-insensitive exact actor ID resolution).
- `label` must be non-empty.

## AgentCatalogue

**Purpose**: The complete registry of all agent definitions, materialised as the `AGENTS.md` index file.

**Fields**:
- `lastUpdated`: date
- `totalAgents`: integer
- `agents`: array of AgentDefinition references grouped by tier

**Relationships**:
- One AgentCatalogue contains all AgentDefinitions.

**Validation rules**:
- `totalAgents` must equal the sum of agents across all tiers.
- Every agent file on disk in tier subdirectories must have a corresponding entry in the catalogue.

## Actor-to-Agent Mapping

### Operational Personas (9)

| Actor | Agent ID | AIIMS Function | Data Model roleType |
|-------|----------|---------------|-------------------|
| Incident Commander | `incident-commander` | Incident Controller | `incident_commander` |
| Operations Officer | `operations-officer` | Operations | `operations` |
| Planning Officer | `planning-officer` | Planning | `planning` |
| Logistics Officer | `logistics-officer` | Logistics | `logistics` |
| Public Information Officer | `public-information-officer` | Public Information | `public_information` |
| Field Coordinator | `field-coordinator` | Field Operations | `field_coordinator` |
| Resilience Planner | `resilience-planner` | Preparedness/Recovery | `planner` |
| Executive/Senior Leader | `executive-leader` | Executive Oversight | `executive` |
| Observer/Auditor | `observer-auditor` | Audit/Review | `observer` |

### Organisation Sectors (14)

| Actor | Agent ID | Data Model category | Sub-sector of |
|-------|----------|-------------------|---------------|
| Commonwealth Government | `commonwealth-government` | `commonwealth` | — |
| State Government | `state-government` | `state` | — |
| Territory Government | `territory-government` | `territory` | — |
| Local Government | `local-government` | `local_government` | — |
| Fire Services | `fire-services` | `emergency_service` | Emergency Services |
| Police | `police` | `emergency_service` | Emergency Services |
| Ambulance/Paramedic | `ambulance-paramedic` | `emergency_service` | Emergency Services |
| State Emergency Service | `ses` | `emergency_service` | Emergency Services |
| Meteorology (BoM) | `meteorology-bom` | `commonwealth` | — |
| Health | `health` | `health` | — |
| Utility | `utility` | `utility` | — |
| Transport | `transport` | `transport` | — |
| Community (NGOs) | `community-ngos` | `community` | — |
| Volunteer | `volunteer` | `volunteer` | — |

### Technical Personas (8)

| Actor | Agent ID | Primary Domain |
|-------|----------|---------------|
| Solution Architect | `solution-architect` | System design, Azure architecture, NFRs |
| Software Developer | `software-developer` | Code conventions, patterns, PR workflow |
| Infrastructure/DevOps Engineer | `infrastructure-devops` | Azure infra, Bicep, CI/CD, monitoring |
| Data Engineer | `data-engineer` | Data pipelines, Cosmos DB, signal ingestion |
| Security Engineer | `security-engineer` | Privacy, RBAC, tenant isolation, content safety |
| QA/Test Engineer | `qa-test-engineer` | Testing strategy, pytest, Playwright, simulation |
| UX Designer | `ux-designer` | Dashboard design, accessibility, evaluation rubric |
| Product Owner/Business Analyst | `product-owner-ba` | Requirements, acceptance criteria, success metrics |
