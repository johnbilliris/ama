# Agent File Contract

## Purpose

Defines the structural contract that every `.agent.md` file in the actor agent catalogue must satisfy for VS Code Copilot compatibility and catalogue consistency validation (SC-002).

## File Location Contract

```
.github/agents/operational/{agent-id}.agent.md
.github/agents/technical/{agent-id}.agent.md
.github/agents/sectors/{jurisdiction}/{agent-id}.agent.md
```

Where:
- `{agent-id}` is a kebab-case identifier that is globally unique across active actor files, case-insensitive
- `{jurisdiction}` is a kebab-case jurisdiction or grouping token (for example: `act`, `commonwealth`, `cross-sector`)
- The file stem is the canonical actor identity used by `handoffs[].agent`
- Frontmatter `name` aliases are not part of the active contract unless explicitly approved in a documented alias table

## YAML Frontmatter Contract

Every agent file MUST begin with YAML frontmatter containing:

```yaml
---
description: <string, max 199 chars, single-line purpose statement>
tools: <array<string>, explicit tool IDs only; no profile aliases>
handoffs:                          # REQUIRED for active actor files
  - label: <string>                # Display name for the handoff
    agent: <string>                # Target agent ID (must exist in catalogue)
    prompt: <string>               # Instruction to pass to target agent
    send: true|false               # Auto-submit prompt when handoff is clicked
---
```

### Required Fields

| Field | Type | Constraint |
|-------|------|-----------|
| `description` | string | Non-empty, max 199 characters, no line breaks |
| `tools` | array | Required for active actor files; must enumerate concrete allowed tool IDs |
| `handoffs` | array | Required for active actor files; each entry must have `label`, `agent`, `prompt` |

### Optional Fields

| Field | Type | Constraint |
|-------|------|-----------|
| `handoffs` | array | Optional only for non-invocable catalogue/index docs that are not active actor files |
| `handoffs[].send` | boolean | Auto-submit flag; defaults to `false` if omitted (per VS Code custom-agents behavior) |

## Tool Capability Contract

Active actor files use contract profile labels for review, but frontmatter MUST list concrete tool IDs under `tools`.
Do not place profile labels such as `advisory-readonly` directly in frontmatter.

### Contract Labels and Allowed Tool IDs

| Contract Label | Allowed Tool IDs |
|---|---|
| `advisory-readonly` | `codebase`, `changes`, `fetch`, `findTestFiles`, `githubRepo`, `problems`, `search`, `searchResults`, `terminalLastCommand`, `terminalSelection`, `testFailure`, `usages`, `vscodeAPI`, `microsoft.docs.mcp` |
| `advisory-plus-docs` | `codebase`, `changes`, `fetch`, `findTestFiles`, `githubRepo`, `problems`, `search`, `searchResults`, `terminalLastCommand`, `terminalSelection`, `testFailure`, `usages`, `vscodeAPI`, `microsoft.docs.mcp`, `edit/editFiles` |
| `implementation` | `changes`, `codebase`, `edit/editFiles`, `extensions`, `fetch`, `findTestFiles`, `githubRepo`, `new`, `openSimpleBrowser`, `problems`, `runCommands`, `runTasks`, `runTests`, `search`, `searchResults`, `terminalLastCommand`, `terminalSelection`, `testFailure`, `usages`, `vscodeAPI`, `microsoft.docs.mcp`, `todos` |

### Role Mapping Rules

- Every active operational actor and every active sector actor MUST declare explicit `advisory-readonly` tool IDs.
- Observer-Auditor MUST remain least privilege and MUST NOT include `edit/editFiles`, `new`, `runCommands`, `runTasks`, `runTests`, or `todos`.
- Azure Principal Architect MUST use `advisory-plus-docs` tool IDs only and MUST NOT include command/task/test/code-creation mutators.
- `infrastructure-devops` is an approved `implementation` exception and MUST keep explicit tool IDs in frontmatter.
- `principal-engineer` is an approved `implementation` exception while current responsibilities include hands-on remediation guidance; this exception MUST be reviewed when responsibilities change.
- Omitted `tools` is invalid for active actor files and MUST fail validation.

### Profile Boundary Notes

- VS Code host tool selection does not support path-restricted mutators. For `advisory-plus-docs`, editing is limited by explicit written scope in the agent body.
- Tool scope in agent frontmatter is not a substitute for application RBAC and runtime authorization.

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

1. Every `.agent.md` file in a tier subdirectory MUST have valid YAML frontmatter parseable as a mapping.
2. Every `description` field MUST be non-empty and under 200 characters (max 199), including Unicode-aware boundary checks.
3. Active actor IDs (file stems) MUST be globally unique, case-insensitive.
4. Every `handoffs[].agent` reference in active actor files MUST resolve to exactly one active actor file.
5. Every active actor file MUST declare at least one handoff (FR-013).
6. Frontmatter type checks for active actor files are strict: `tools` is `array<string>`, `handoffs` is `array<object>`, and each handoff has non-empty `label`, `agent`, `prompt`; `send` MUST be boolean when present.
7. Non-invocable catalogue/index docs may omit handoffs and are validated separately from active actor files.
8. Frontmatter `name` MUST either be absent or match the canonical file stem unless explicitly approved in an alias table.
9. Every active actor file MUST contain the six required body sections in the specified order, and each section body MUST be non-empty.
10. Every agent file MUST have a corresponding entry in `AGENTS.md`.
11. No agent file MAY contain hard-coded incident data, credentials, API keys, or PII.
12. `contextReferences` paths MUST point to files that exist in the repository.
13. Every active actor file MUST declare a non-empty explicit `tools` list.
14. Every active actor claiming read-only/advisory scope MUST have no intersection with mutator denylist: `edit/editFiles`, `new`, `runCommands`, `runTasks`, `runTests`, `todos`.
15. Approved `implementation` exceptions MUST be allowlisted by actor ID and documented in this contract.
16. Operational actors MUST include explicit AIIMS alignment or explicit non-AIIMS governance/advisory status and MUST include a `decisionRights` statement.
17. Sector actors MUST include substantive `Guidance Notes` with authority status, activation/approval conditions, jurisdictional variation, and named counterpart boundaries.
18. If an agent includes `agents`, then `tools` MUST include `agent` and handoff targets must be coherent with declared subagent permissions.
