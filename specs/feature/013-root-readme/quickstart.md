# Implementation Quickstart: Root README.md

**Feature**: 013-root-readme
**Date**: 2025-07-17
**Input**: [plan.md](plan.md), [data-model.md](data-model.md), [research.md](research.md)

## What You're Building

A single `README.md` file at the repository root (`C:\code\ama\README.md`). This is a documentation-only feature — no code, no infrastructure, no tests to write beyond validation scripts.

## Before You Start

### Prerequisite Knowledge

- GitHub-Flavoured Markdown (headings, links, tables, code blocks)
- HTML `<details><summary>` pattern for collapsible sections
- Mermaid diagram syntax (`graph TD`)
- Flesch-Kincaid readability concepts (short sentences, simple words, active voice)

### Files to Read First

1. **This plan**: `specs/feature/013-root-readme/plan.md` — section ordering, constitution check, conflict resolutions
2. **Feature spec**: `specs/013-root-readme/spec.md` — all 17 functional requirements
3. **Data model**: `specs/feature/013-root-readme/data-model.md` — exact section structure and validation rules
4. **Architecture doc**: `docs/disaster-response-hub/architecture.md` — source for simplified diagram
5. **Constitution**: `.specify/memory/constitution.md` — governance principles to reference
6. **Capstone**: `capstone.md` — success metrics to quote

### Key Constraints to Remember

| Constraint | Value | Spec Ref |
|-----------|-------|----------|
| Max line count | 500 lines | NFR-001 |
| FK Grade Level ceiling | ≤ 8.0 | NFR-003, FR-015 |
| FK-validated sections | Overview, Quickstart, Personas | CHK016 resolution |
| Section order | FR-016 (universal-first) | FR-016 |
| Terminology: AI components | "agent" (never "service") | FR-014 |
| Terminology: execution envs | "runtime" (never "service") | FR-014 |
| IC authority placement | Primary in Personas, cross-ref in docs | CHK018 resolution |
| Prerequisites split | Local dev vs Azure deployment | CHK017 resolution |
| Architecture diagram | Mermaid inline, NOT in `<details>` | FR-002, FR-017 |

## Step-by-Step Implementation

### Step 1: Create the File

Create `README.md` at the repository root. Start with the document skeleton following FR-016 order:

```markdown
# Autonomous Disaster Response Agent Coordination Hub

> One-sentence description here.

## Table of Contents

- [Overview](#overview)
- [Agents](#agents)
- [AIIMS Personas & Human Authority](#aiims-personas--human-authority)
- [Architecture](#architecture)
- [Quickstart](#quickstart)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Success Metrics](#success-metrics)
- [Contributing](#contributing)
- [Documentation](#documentation)

## Overview
## Agents
## AIIMS Personas & Human Authority
## Architecture
## Quickstart
## Repository Structure
## Technology Stack
## Success Metrics
## Contributing
## Documentation
```

### Step 2: Write FK-Validated Sections First

Write the **Overview**, **Quickstart**, and **Personas** sections first because they have the FK Grade 8 constraint. Tips for FK8:

- Use short sentences (15–20 words average)
- Prefer common words over technical jargon
- Use active voice ("The system coordinates..." not "Coordination is performed by...")
- Avoid nested clauses
- Define acronyms on first use (e.g., "Australian Interagency Incident Management System (AIIMS)")

Validate as you go:

```python
import textstat
text = """[paste section text here, stripped of Markdown formatting]"""
print(textstat.flesch_kincaid_grade(text))  # Must be ≤ 8.0
```

### Step 3: Create the Mermaid Architecture Diagram

Simplify the ASCII diagram from `architecture.md` into a Mermaid `graph TD`:

```markdown
```mermaid
graph TD
    WEB["Web Runtime<br/>(Next.js)"] -->|HTTPS| API["API Runtime<br/>(FastAPI)"]
    API --> AGENTS["Agent Runtime<br/>(Python)"]
    AGENTS --> MON[Monitoring Agent]
    AGENTS --> RISK[Risk Assessment Agent]
    AGENTS --> EVAC[Evacuation Agent]
    AGENTS --> RES[Resource Allocation Agent]
    AGENTS --> COMM[Communication Agent]
    API --> COSMOS[(Cosmos DB)]
    API --> REDIS[(Redis)]
    API --> BLOB[(Blob Storage)]

    style WEB fill:#4DB8FF
    style API fill:#47D147
    style AGENTS fill:#FFB84D
```​
```

Keep it under 30 lines. Use "runtime" not "service" in labels.

### Step 4: Build Collapsible Sections

Use the `<details>` pattern from research.md. Sections that MUST be collapsible:
- Detailed agent descriptions (inside the Agents section)
- Full prerequisites list (inside Quickstart)
- Repository structure file tree

**Critical**: Always include blank lines after `<summary>` and before `</details>`:

```html
<details>
<summary>📋 Prerequisites for Local Development</summary>

| Tool | Version | Install |
|------|---------|---------|
| Python | ≥ 3.12 | [python.org](https://python.org) |
| Node.js | ≥ 22 | [nodejs.org](https://nodejs.org) |
| pnpm | 10.6.3 | `corepack enable` |
| uv | latest | [docs.astral.sh](https://docs.astral.sh/uv/) |
| Docker | latest | [docker.com](https://docker.com) |
| Git | ≥ 2.x | [git-scm.com](https://git-scm.com) |

</details>
```

### Step 5: Add the IC Authority Statement

In the **AIIMS Personas & Human Authority** section, add a prominent blockquote:

```markdown
> **⚠️ Human Authority**: The Incident Commander retains final decision
> authority over all safety-critical system outputs, including evacuations,
> public alerts, and resource dispatch recommendations. The platform
> recommends; humans decide.
```

This MUST be:
- A standalone blockquote (not buried in a list)
- NOT inside a `<details>` block
- Visible without any user interaction

Then add the cross-reference in the **Documentation** section:

```markdown
See the [Project Constitution](.specify/memory/constitution.md) for complete
life-safety principles, including the Incident Commander's final authority
over all safety-critical decisions.
```

### Step 6: Organize Documentation Links by Audience

```markdown
## Documentation

### For Evaluators
- [Evaluation Rubric](AMA_Rubric_Asia.md)
- [Project Capstone](capstone.md)
- [Executive Deck](docs/disaster-response-hub/demo/executive-deck.md)

### For Developers
- [Architecture](docs/disaster-response-hub/architecture.md)
- [Feature Specifications](specs/)
- [Project Constitution](.specify/memory/constitution.md)

### For Operators
- [Operator Runbooks](docs/disaster-response-hub/operator-runbooks.md)
- [Demo Walkthrough](docs/disaster-response-hub/demo/walkthrough.md)
```

### Step 7: Validate

Run these checks before submitting:

```powershell
# 1. Line count (must be ≤ 500)
(Get-Content README.md).Count

# 2. All internal links resolve
Select-String -Path README.md -Pattern '\[.*?\]\(((?!http)[^)]+)\)' -AllMatches |
  ForEach-Object { $_.Matches } |
  ForEach-Object { $_.Groups[1].Value } |
  ForEach-Object { if (-not (Test-Path $_)) { Write-Warning "BROKEN: $_" } }

# 3. Terminology check — no "service" for agents
Select-String -Path README.md -Pattern '\bservice\b' -CaseSensitive

# 4. FK Grade Level (Python)
python -c "
import textstat
with open('README.md') as f:
    text = f.read()
# Extract sections between headings for targeted analysis
print(f'Full doc FK: {textstat.flesch_kincaid_grade(text):.1f}')
"
```

## Common Pitfalls

| Pitfall | How to Avoid |
|---------|-------------|
| `<details>` content renders as raw text | Always add blank line after `<summary>` tag |
| Mermaid diagram doesn't render | Don't nest inside `<details>`; verify backtick count |
| FK score too high | Shorten sentences, replace jargon with plain words |
| Line count over 500 | Move verbose content into `<details>` blocks |
| "service" used for agents | Search-and-replace before commit; use "agent" or "runtime" |
| Broken links | All target files confirmed to exist (see research.md RT-006) |

## Definition of Done

- [ ] `README.md` exists at repository root
- [ ] All 10 FR-016 content sections present in specified order
- [ ] Line count ≤ 500 (NFR-001)
- [ ] Overview, Quickstart, Personas sections FK ≤ 8.0 (NFR-003, FR-015)
- [ ] All internal links resolve to existing files (SC-007)
- [ ] IC authority in standalone blockquote in Personas section (SC-004, CHK018)
- [ ] Mermaid architecture diagram renders on GitHub (FR-002)
- [ ] All `<details>` blocks have descriptive `<summary>` labels (NFR-004)
- [ ] Prerequisites split into local dev and Azure deployment (CHK017)
- [ ] "Agent" used for 5 AI components, "runtime" for 3 execution envs (SC-010)
- [ ] Renders correctly on GitHub desktop and mobile (FR-012)
