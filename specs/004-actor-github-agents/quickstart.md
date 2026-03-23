# Quickstart: Actor-Specific GitHub Agents

## Purpose

Validate the agent catalogue by creating the directory structure, building one agent per tier as a reference, creating the registry, and running a structured evaluation to confirm agents provide accurate, role-grounded guidance.

## Prerequisites

- VS Code with GitHub Copilot extension (agent support enabled)
- Access to the repository on branch `004-actor-github-agents`
- Familiarity with the agent file contract at `specs/004-actor-github-agents/contracts/agent-file-contract.md`

## Setup sequence

1. Create the tier subdirectories under `.github/agents/`:
   ```
   .github/agents/operational/
   .github/agents/sectors/
   .github/agents/technical/
   ```

2. Create the registry file `.github/agents/AGENTS.md` with the header structure and tier sections.

3. Create the first reference agent for each tier:
   - `operational/incident-commander.agent.md` — the P1 operational persona
   - `sectors/fire-services.agent.md` — a representative sector agent
   - `technical/solution-architect.agent.md` — the architectural guidance agent

4. Validate each reference agent against the agent file contract.

## Validation flow

### Structural validation (SC-002)

For each created agent file, verify:
- [ ] YAML frontmatter is valid and parseable
- [ ] `description` field is present, non-empty, under 200 characters
- [ ] All handoff `agent` references point to existing or planned agent files
- [ ] Body contains all required sections: Role Overview, Responsibilities & Decision Rights, Scope Boundaries, Key Relationships, Contextual References, Guidance Notes
- [ ] No hard-coded incident data, credentials, or API keys
- [ ] All `contextReferences` paths point to files that exist in the repository

### Accuracy evaluation (SC-003, SC-004)

For each reference agent, pose 5 role-specific questions and verify responses:

**Incident Commander agent (operational)**:
1. "What is my authority to approve evacuation recommendations?"
2. "Which AIIMS function am I responsible for?"
3. "Who should I escalate to if the disaster crosses state boundaries?"
4. "What information should I see in the shared operating picture?"
5. "Can I directly issue public alerts without approval?"

**Fire Services agent (sector)**:
1. "Which organisations provide fire services in Victoria vs NSW?"
2. "How does the fire service coordinate with police during evacuations?"
3. "What statutory authority does the fire service have for road closures?"
4. "How does bushfire response differ between states?"
5. "What is the fire service's relationship with the SES during floods?"

**Solution Architect agent (technical)**:
1. "Which Azure regions can I deploy to?"
2. "What database is used for operational state?"
3. "What are the non-negotiable constitutional principles?"
4. "How should I structure a new agent within the AIIMS framework?"
5. "What testing frameworks does the project use?"

### Pass criteria

- At least 4/5 questions per agent receive accurate, contextually grounded responses (80% threshold per SC-003/SC-004)
- Responses reference the correct project artefacts (data model, constitution, or sector documentation)
- Responses correctly identify scope boundaries and handoff to other agents when appropriate

## Rollout sequence

After reference agents pass validation:

1. Create remaining 6 operational persona agents following the incident-commander pattern
2. Create remaining 13 sector agents following the fire-services pattern
3. Create remaining 7 technical persona agents following the solution-architect pattern
4. Update `AGENTS.md` registry with all 31 entries
5. Run full catalogue structural validation
6. Run sample accuracy evaluations across tiers

## Acceptance checks

- All 31 agent files exist in the correct tier subdirectories
- `AGENTS.md` registry lists all 31 agents with correct metadata
- No YAML parsing errors across all agent files
- Reference agents pass the 80% accuracy threshold on structured questions
- No agent contains hard-coded incident data, credentials, or sensitive information
