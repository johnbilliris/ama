# Implementation Plan: Actor-Specific GitHub Agents for Disaster Response Hub

**Branch**: `004-actor-github-agents` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-actor-github-agents/spec.md`

## Summary

Create 31 dedicated GitHub Copilot agent definition files (`.agent.md`) covering all actors in the disaster response hub — 9 operational personas (AIIMS-aligned), 14 organisation sectors (Australian emergency management), and 8 technical personas (project contributors). Agents are organised in tier subdirectories under `.github/agents/` and reference shared project artefacts (constitution, data model, operating frameworks) rather than duplicating content. A registry index provides catalogue-level discovery and handoff relationships.

## Technical Context

**Language/Version**: Markdown (`.agent.md` files with YAML frontmatter) — no compiled code  
**Primary Dependencies**: VS Code GitHub Copilot agent infrastructure (existing in `.github/agents/`)  
**Storage**: N/A — static files in the repository  
**Testing**: Manual structured evaluation against data model and AIIMS documentation (SC-003, SC-004)  
**Target Platform**: VS Code with GitHub Copilot  
**Project Type**: Developer tooling — agent definition files (content authoring, not software build)  
**Performance Goals**: N/A — static files parsed at agent load time  
**Constraints**: Each agent must stay within VS Code Copilot context limits; references to project artefacts via relative file paths  
**Scale/Scope**: 35 agent files + 1 registry index + 3 tier directories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Life Safety First | PASS | Agents encode safety-critical escalation pathways for operational personas; do not bypass human override |
| II. Multi-Agent Coordination | PASS | Agents reference AIIMS-aligned roles and explicit handoff relationships between persona/sector agents |
| III. Data Trust & Provenance | PASS | Sector agents (especially Meteorology) encode BoM authority and provenance requirements |
| IV. Privacy, Security & Compliance | PASS | FR-010 prohibits hard-coded incident data, credentials, or API keys in agent definitions |
| V. Multilingual & Accessible Communication | PASS | `public-information-officer` (operational) and `community-ngos` (sector) agents encode multilingual alert obligations per Constitution V |
| VI. Cloud Platform (Azure AU) | PASS | Technical persona agents encode Azure AU-region constraint from constitution |

**Gate Result**: PASS — no violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/004-actor-github-agents/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (agent catalogue model)
├── quickstart.md        # Phase 1 output (validation guide)
├── contracts/           # Phase 1 output (agent file contract)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
.github/agents/
├── copilot-instructions.md          # Existing — auto-generated dev guidelines
├── speckit.*.agent.md               # Existing 9 speckit workflow agents (untouched)
├── AGENTS.md                        # NEW — actor agent registry/index
├── operational/
│   ├── incident-commander.agent.md
│   ├── operations-officer.agent.md
│   ├── planning-officer.agent.md
│   ├── logistics-officer.agent.md
│   ├── public-information-officer.agent.md
│   ├── field-coordinator.agent.md
│   ├── resilience-planner.agent.md
│   ├── executive-leader.agent.md
│   └── observer-auditor.agent.md
├── sectors/
│   ├── commonwealth-government.agent.md
│   ├── state-government.agent.md
│   ├── territory-government.agent.md
│   ├── local-government.agent.md
│   ├── fire-services.agent.md
│   ├── police.agent.md
│   ├── ambulance-paramedic.agent.md
│   ├── ses.agent.md
│   ├── meteorology-bom.agent.md
│   ├── health.agent.md
│   ├── utility.agent.md
│   ├── transport.agent.md
│   ├── community-ngos.agent.md
│   └── volunteer.agent.md
└── technical/
    ├── solution-architect.agent.md
    ├── software-developer.agent.md
    ├── infrastructure-devops.agent.md
    ├── data-engineer.agent.md
    ├── security-engineer.agent.md
    ├── qa-test-engineer.agent.md
    ├── ux-designer.agent.md
    └── product-owner-ba.agent.md
```

**Structure Decision**: Tier subdirectories under `.github/agents/` as confirmed in clarification session. Existing speckit agents remain in root. The registry `AGENTS.md` sits in the agents root for discoverability.

## Complexity Tracking

No constitution violations to justify. This feature adds only static Markdown files — no new runtime projects, no additional infrastructure, no new dependencies.
