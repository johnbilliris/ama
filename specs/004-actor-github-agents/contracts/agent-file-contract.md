# Agent File Contract

## Purpose

Defines the structural contract that every `.agent.md` file in the actor agent catalogue must satisfy for VS Code Copilot compatibility and catalogue consistency validation (SC-002).

## File Location Contract

```
.github/agents/{tier}/{agent-id}.agent.md
```

Where:
- `{tier}` is one of: `operational`, `sectors`, `technical`
- `{agent-id}` is a kebab-case identifier unique across all tiers

## YAML Frontmatter Contract

Every agent file MUST begin with YAML frontmatter containing:

```yaml
---
description: <string, max 200 chars, single-line purpose statement>
handoffs:                          # OPTIONAL but recommended
  - label: <string>                # Display name for the handoff
    agent: <string>                # Target agent ID (must exist in catalogue)
    prompt: <string>               # Instruction to pass to target agent
    send: true                     # Whether to forward context
---
```

### Required Fields

| Field | Type | Constraint |
|-------|------|-----------|
| `description` | string | Non-empty, max 200 characters, no line breaks |

### Optional Fields

| Field | Type | Constraint |
|-------|------|-----------|
| `handoffs` | array | Each entry must have `label`, `agent`, `prompt` |
| `handoffs[].send` | boolean | Defaults to `true` if omitted |

## Body Content Contract

After the YAML frontmatter, the agent body MUST contain the following Markdown sections in order:

```markdown
## Role Overview

<1-3 paragraphs describing who this actor is and their primary function>

## Responsibilities & Decision Rights

<Bulleted list of what this actor owns, can approve, or can escalate>

## Scope Boundaries

<What this agent does NOT cover, with handoff references to the correct agent>

## Key Relationships

<Which other actors this agent coordinates with and how>

## Contextual References

<Bulleted list of file paths to authoritative project artefacts this agent should read>
- `.specify/memory/constitution.md`
- `specs/001-disaster-response-hub/data-model.md`
- <additional tier-specific references>

## Guidance Notes

<Domain-specific knowledge relevant to this actor's scope>
```

### Tier-Specific Body Additions

**Operational agents** MUST also include:
- AIIMS function alignment in Role Overview
- `decisionRights` from the data model Persona entity
- Escalation pathways in Responsibilities

**Sector agents** MUST also include:
- Jurisdictional variations across Australian states and territories
- Statutory obligations and key legislation
- Coordination relationships with other sectors

**Technical agents** MUST also include:
- Relevant constitutional principles
- Technology stack conventions for their domain
- Quality gates and project conventions

## Registry Entry Contract

Every agent MUST have a corresponding entry in `.github/agents/AGENTS.md` with:

| Column | Description |
|--------|------------|
| Agent Name | Display name matching `description` theme |
| Agent ID | Kebab-case ID matching the file stem |
| File Path | Relative path from repo root |
| Tier | `operational`, `sector`, or `technical` |
| Description | Same as YAML frontmatter `description` |
| Key Handoffs | Comma-separated list of primary handoff agent IDs |

## Validation Rules

1. Every `.agent.md` file in a tier subdirectory MUST have valid YAML frontmatter
2. Every `description` field MUST be non-empty and under 200 characters
3. Every `handoffs[].agent` reference MUST point to an existing agent file
4. Every agent file MUST contain all required body sections
5. Every agent file MUST have a corresponding entry in `AGENTS.md`
6. No agent file MAY contain hard-coded incident data, credentials, API keys, or PII
7. `contextReferences` paths MUST point to files that exist in the repository
