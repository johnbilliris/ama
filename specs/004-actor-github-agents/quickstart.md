# Quickstart: Actor-Specific GitHub Agents

## Purpose

Validate the agent catalogue by creating the directory structure, building one agent per tier as a reference, creating the registry, and running a structured evaluation scaffold for SC-003 through SC-006.

## Scope Evolution Snapshot (2026-09-15)

- Historical snapshots used in early authoring artifacts: 27 → 31 → 35 (minimum target).
- Current filesystem snapshot used for maintenance and validation: 85 active actor files, 12 workflow agents, 6 archived sector agents.
- Legacy rollout arithmetic below is updated to avoid implying only 31 total actors are in scope.

## Prerequisites

- VS Code with GitHub Copilot extension (agent support enabled)
- Access to the repository with the `specs/004-actor-github-agents/` artifacts and `.github/agents/` catalogue present
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

Run the feature gate:

```powershell
python tools/lint/check_actor_agent_catalogue.py --root .
```

Run the evidence scaffold gate:

```powershell
python tools/lint/check_actor_feature_evidence.py --root .
```

### Accuracy evaluation (SC-003, SC-004)

Operational question pack coverage is defined in:

- `specs/004-actor-github-agents/evidence/sc-003-operational.yaml`
- `specs/004-actor-github-agents/evidence/sc-003-operational.json`

The SC-003 schema requires all 10 current operational roles:

1. Incident Commander
2. Operations Officer
3. Planning Officer
4. Logistics Officer
5. Public Information Officer
6. Field Coordinator
7. Resilience Planner
8. Executive Leader
9. Observer Auditor
10. Risk Manager

Each role entry must include: `roleId`, `filePath`, `agentSha256`, fixed `questions[]`, authoritative `expectedAnswer`, and `citation`.

Sector question pack coverage is defined in:

- `specs/004-actor-github-agents/evidence/sc-004-sectors.yaml`
- `specs/004-actor-github-agents/evidence/sc-004-sectors.json`

The SC-004 schema requires all 14 sector families, with retired generic families retargeted to active successors:

1. Commonwealth Government
2. State Government
3. Territory Government
4. Local Government
5. Fire Services (retargeted to jurisdiction successors)
6. Police (retargeted to jurisdiction successors)
7. Ambulance/Paramedic (retargeted to jurisdiction successors)
8. SES (retargeted to jurisdiction successors)
9. Meteorology
10. Health
11. Utility
12. Transport
13. Community
14. Volunteer

Each family question must include cross-jurisdiction ownership (`ownerRole`) and a `primarySourceCitation`.

### Same-session role isolation protocol (SC-003)

In one editor session:

1. Evaluate Incident Commander question(s); record role-scoped rights.
2. Switch to Observer Auditor; verify no inherited command rights.
3. Switch to Planning Officer; verify no inherited observer-only constraints.

Record the sequence in `sameSessionRoleIsolation.sequence` exactly as:

- `incident-commander`
- `observer-auditor`
- `planning-officer`

### Onboarding survey scaffold (SC-005)

The survey scaffold is predeclared in:

- `specs/004-actor-github-agents/evidence/sc-005-onboarding.yaml`
- `specs/004-actor-github-agents/evidence/sc-005-onboarding.json`

Instrument rules:

1. Exactly one primary benefit question.
2. Fixed Likert scale and favourable rule (`score >= 4`).
3. Success threshold `>= 85%` favourable among eligible respondents.
4. Denominator, non-response handling, and duplicate handling are predefined.
5. Privacy rule forbids PII and requires anonymized respondent IDs.
6. Instrument version/date is frozen before first response.

### Timing scaffold (SC-006)

The timing scaffold is predefined in:

- `specs/004-actor-github-agents/evidence/sc-006-timing.yaml`
- `specs/004-actor-github-agents/evidence/sc-006-timing.json`

Timer semantics:

1. Start: catalogue review started.
2. Stop: new actor file + registry + handoffs + references pass validator.
3. Boundary: 1799 seconds passes; 1800 seconds fails.
4. Execution policy: independent/unfamiliar contributor, facilitator_authored=false, disposable workspace, no commit.

### Pass criteria

- SC-002: `check_actor_agent_catalogue.py` passes against the checked-in catalogue.
- SC-003 scaffold: denominator and threshold are defined (`>= 80%`), role coverage is complete, and same-session isolation protocol is encoded.
- SC-004 scaffold: denominator and threshold are defined (`>= 80%`), all required families are covered, and archived targets are absent.
- SC-005 scaffold: frozen instrument, denominator/privacy/duplicate rules are defined with threshold `>= 85%`.
- SC-006 scaffold: timing start/stop/boundary and independent execution policy are encoded.

Current expected status for SC-003 to SC-006 evidence artifacts in this repository state is `Not measured`.

## Rollout sequence

After reference agents pass validation:

1. If starting from the 3 reference agents only, complete the remaining actors required by the current target baseline (35 minimum).
2. If maintaining the current repository state, validate all active actor files and registry metadata against the current filesystem snapshot (85 active actors).
3. Update `AGENTS.md` counts and entries whenever actor files are added, renamed, archived, or retired.
4. Run full catalogue structural validation.
5. Run sample accuracy evaluations across tiers.
6. Keep SC-003 to SC-006 evidence scaffolds synchronized across `.yaml`, `.json`, and `.md` forms.

## Acceptance checks

- All required actor files for the chosen baseline exist in the correct tier subdirectories
- `AGENTS.md` registry counts and entries match the current filesystem snapshot
- No YAML parsing errors across all agent files
- SC-003 and SC-004 scaffolds contain complete denominator definitions and role/family coverage
- SC-005 and SC-006 scaffolds remain `Not measured` until separate authorized execution
- No agent contains hard-coded incident data, credentials, or sensitive information
