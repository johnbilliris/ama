# Implementation Plan: Actor-Specific GitHub Agents for Disaster Response Hub

**Branch**: `004-actor-github-agents` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-actor-github-agents/spec.md`

## Summary

Initial plan baseline created 31 dedicated GitHub Copilot agent definition files (`.agent.md`) — 9 operational personas, 14 organisation sectors, and 8 technical personas. The authoritative specification target is at least 35 actors (including 12 technical personas), and the current filesystem has expanded further. Agents are organised in tier subdirectories under `.github/agents/` and reference shared project artefacts (constitution, data model, operating frameworks) rather than duplicating content. A registry index provides catalogue-level discovery and handoff relationships.

## Technical Context

**Language/Version**: Markdown (`.agent.md` files with YAML frontmatter) — no compiled code  
**Primary Dependencies**: VS Code GitHub Copilot agent infrastructure (existing in `.github/agents/`)  
**Storage**: N/A — static files in the repository  
**Testing**: Manual structured evaluation against data model and AIIMS documentation (SC-003, SC-004)  
**Target Platform**: VS Code with GitHub Copilot  
**Project Type**: Developer tooling — agent definition files (content authoring, not software build)  
**Performance Goals**: N/A — static files parsed at agent load time  
**Constraints**: Each agent must stay within VS Code Copilot context limits; references to project artefacts via relative file paths  
**Scale/Scope**: Historical snapshots: 27 → 31 → 35 (minimum target). Current filesystem snapshot (2026-09-15): 85 active actor files + 12 workflow agents + 6 archived sector agents.

## Scope Evolution Snapshot (2026-09-15)

- Historical 27 actor count came from early draft scope before sector and technical expansion.
- Historical 31 actor count came from the first implementation baseline (9 operational + 14 sectors + 8 technical).
- Historical 35 actor count is the accepted minimum target after adding four technical roles.
- Current filesystem inventory is authoritative for validation and maintenance activity in this repository state: 85 active actor files, 12 workflow agents, 6 archived sector agents.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Historical Snapshot (2026-03-23)

The table below is preserved as the original historical authoring snapshot and is not a current acceptance gate.

| Principle | Historical status | Historical notes |
| --------- | ----------------- | ---------------- |
| I. Life Safety First | PASS | Agents encode safety-critical escalation pathways for operational personas; do not bypass human override |
| II. Multi-Agent Coordination | PASS | Agents reference AIIMS-aligned roles and explicit handoff relationships between persona/sector agents |
| III. Data Trust & Provenance | PASS | Sector agents (especially Meteorology) encode BoM authority and provenance requirements |
| IV. Privacy, Security & Compliance | PASS | FR-010 prohibits hard-coded incident data, credentials, or API keys in agent definitions |
| V. Multilingual & Accessible Communication | PASS | `public-information-officer` (operational) and `community-ngos` (sector) agents encode multilingual alert obligations per Constitution V |
| VI. Cloud Platform (Azure AU) | PASS | Technical persona agents encode Azure AU-region constraint from constitution |

### Current Gate (2026-09-15)

| Current constitution heading | Status | Notes |
| --- | --- | --- |
| I. Primacy of Life and Harm Reduction | Unverified | Requires role-by-role reconciliation against current agent content and escalation language. |
| II. National Emergency Management Principles | Unverified | Current conformance needs refreshed mapping across all actor tiers. |
| III. Multi-Hazard, Multi-Agency Design | Unverified | Coverage breadth exists, but consistency and authority depth remain under review. |
| IV. Transparency and Auditability | Unverified | Structural references exist; formal signoff evidence is tracked separately in `evidence/review-ledger.md`. |
| V. Warning and Public Information | Unverified | Warning taxonomy and nested model conformance are under active remediation. |
| VI. Evacuation Framework | Unverified | Evacuation boundary and authority consistency checks remain incomplete. |
| VII. Recovery Support | Unverified | Recovery-specific obligation mapping is not fully settled across all relevant roles. |
| VIII. Cloud Platform and Infrastructure | Unverified | Technical personas require current-stack and authority reconciliation. |
| NON-NEGOTIABLE #1 Human-in-the-loop | Unverified | Human consultation/signoff evidence remains explicit and separate from agent invocation records. |
| NON-NEGOTIABLE #2 Data sovereignty (+ bounded Foundry carve-out) | Unverified | Carve-out is bounded to non-AU model-hosting endpoints only; AU persistence/telemetry/secrets constraints remain mandatory. |
| NON-NEGOTIABLE #3 Privacy by design | Unverified | Requires explicit, current privacy controls mapping in the actor corpus. |
| NON-NEGOTIABLE #4 Interoperability | Unverified | Standards references exist but full consistency and applicability checks are incomplete. |
| NON-NEGOTIABLE #5 Graceful degradation | Unverified | No current feature-local evidence demonstrates completed degradation validation. |

**Current Gate Result**: Unverified. Historical PASS rows are retained for traceability only and do not constitute present acceptance.

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
