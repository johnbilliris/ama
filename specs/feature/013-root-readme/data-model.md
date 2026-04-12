# Data Model: Root README.md

**Feature**: 013-root-readme
**Date**: 2025-07-17
**Input**: [spec.md](../../013-root-readme/spec.md), [research.md](research.md)

## Document Entity Model

This feature produces a single Markdown file (`README.md`). The "data model" is the document structure — each section is an entity with defined content, ordering, visibility, and validation rules.

### Entity: README Document

| Property | Value |
|----------|-------|
| **File** | `README.md` (repository root) |
| **Format** | GitHub-Flavoured Markdown + HTML `<details>` blocks |
| **Max Length** | 500 lines (NFR-001) |
| **Target Length** | ~420–480 lines |
| **Encoding** | UTF-8 |

### Entity: Section

Each section is an ordered content block within the README.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique section identifier (e.g., `overview`, `agents`) |
| `heading` | string | Markdown heading text |
| `heading_level` | int | Heading depth (2 for main sections, 3 for subsections) |
| `order` | int | Position in document per FR-016 |
| `collapsible` | boolean | Whether section uses `<details>` block |
| `fk_grade_target` | float \| null | FK Grade Level ceiling (8.0 for applicable sections) |
| `required_content` | string[] | Content elements that MUST appear |
| `links_out` | string[] | Internal file paths this section links to |

### Section Instances (FR-016 Order)

```
┌─────────────────────────────────────────────────────┐
│  README.md                                          │
│                                                     │
│  1. Title + One-liner                               │
│  2. Table of Contents (FR-017)                      │
│  3. Project Overview (FR-001)           FK8 ✓       │
│  4. Agents (FR-014)                     Collapsible │
│  5. AIIMS Personas & Authority (FR-005) FK8 ✓       │
│  6. Architecture Diagram (FR-002)       NOT coll.   │
│  7. Quickstart (FR-003, FR-004)         FK8 ✓       │
│     ├── Local Dev Prerequisites         Collapsible │
│     ├── Azure Deploy Prerequisites      Collapsible │
│     └── Commands (always visible)                   │
│  8. Repository Structure (FR-009)       Collapsible │
│  9. Technology Stack (FR-008)                       │
│ 10. Success Metrics (FR-007)                        │
│ 11. Contributing (FR-010, FR-011)                   │
│ 12. Documentation Links (FR-006)                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Section Detail: 1 — Title

| Property | Value |
|----------|-------|
| **Order** | 1 |
| **Heading** | `# Autonomous Disaster Response Agent Coordination Hub` |
| **Heading Level** | 1 |
| **Collapsible** | No |
| **FK Grade Target** | 8.0 |
| **Required Content** | Project name, one-sentence description |
| **Links Out** | None |

### Section Detail: 2 — Table of Contents

| Property | Value |
|----------|-------|
| **Order** | 2 |
| **Heading** | `## Table of Contents` (or inline after overview) |
| **Heading Level** | 2 |
| **Collapsible** | No |
| **FK Grade Target** | N/A |
| **Required Content** | Linked list of all 10 main sections |
| **Links Out** | Internal anchors to all sections |
| **Spec Ref** | FR-017 |

### Section Detail: 3 — Project Overview

| Property | Value |
|----------|-------|
| **Order** | 3 |
| **Heading** | `## Overview` |
| **Heading Level** | 2 |
| **Collapsible** | No |
| **FK Grade Target** | 8.0 (FR-015, NFR-003) |
| **Required Content** | Multi-agent system description, Australian emergency management context, four stakeholder audiences, link to constitution |
| **Links Out** | `.specify/memory/constitution.md` |
| **Spec Ref** | FR-001, FR-015, NFR-003 |
| **Validation** | `textstat.flesch_kincaid_grade(section_text) <= 8.0` |

### Section Detail: 4 — Agents

| Property | Value |
|----------|-------|
| **Order** | 4 |
| **Heading** | `## Agents` |
| **Heading Level** | 2 |
| **Collapsible** | Detailed descriptions in `<details>` blocks; summary line for each always visible |
| **FK Grade Target** | N/A (technical audience) |
| **Required Content** | All 5 agents: Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication. Use "agent" not "service" (FR-014). |
| **Links Out** | None (agent specs are under `specs/`) |
| **Spec Ref** | FR-014, FR-017 |

### Section Detail: 5 — AIIMS Personas & Human Authority

| Property | Value |
|----------|-------|
| **Order** | 5 |
| **Heading** | `## AIIMS Personas & Human Authority` |
| **Heading Level** | 2 |
| **Collapsible** | No |
| **FK Grade Target** | 8.0 (FR-015) |
| **Required Content** | AIIMS role mapping table, IC authority callout (blockquote, standalone, NOT in `<details>`), link to constitution |
| **Links Out** | `.specify/memory/constitution.md` |
| **Spec Ref** | FR-005, FR-013 (primary IC statement per CHK018), FR-015 |
| **Validation** | IC authority in blockquote, not buried in list (SC-004) |

### Section Detail: 6 — Architecture Diagram

| Property | Value |
|----------|-------|
| **Order** | 6 |
| **Heading** | `## Architecture` |
| **Heading Level** | 2 |
| **Collapsible** | No (FR-017: MUST NOT be collapsible) |
| **FK Grade Target** | N/A |
| **Required Content** | Mermaid `graph TD` diagram showing 3 runtimes + Azure services, brief explanation, link to full architecture |
| **Links Out** | `docs/disaster-response-hub/architecture.md` |
| **Spec Ref** | FR-002 |
| **Constraints** | Simplified summary; ≤30 lines of Mermaid; use "runtime" not "service" |

### Section Detail: 7 — Quickstart

| Property | Value |
|----------|-------|
| **Order** | 7 |
| **Heading** | `## Quickstart` |
| **Heading Level** | 2 |
| **Collapsible** | Prerequisites in `<details>` blocks; commands always visible |
| **FK Grade Target** | 8.0 (NFR-003) |
| **Required Content** | Clone, install, run commands for all 3 runtimes; no Azure credentials needed; "Deploy to Azure" subsection linking to `infra/` |
| **Subsections** | |
| **7a. Prerequisites (Local Dev)** | `<details>`: Python ≥3.12, Node.js ≥22, pnpm 10.6.3, uv, Docker, Git |
| **7b. Prerequisites (Azure Deploy)** | `<details>`: Azure CLI ≥2.60, Azure subscription, azd |
| **7c. Run Locally** | Always visible: clone + install + run commands |
| **7d. Deploy to Azure** | Link to `infra/` docs |
| **Links Out** | `infra/` |
| **Spec Ref** | FR-003, FR-004 |

### Section Detail: 8 — Repository Structure

| Property | Value |
|----------|-------|
| **Order** | 8 |
| **Heading** | `## Repository Structure` |
| **Heading Level** | 2 |
| **Collapsible** | Yes — file tree inside `<details>` block |
| **FK Grade Target** | N/A |
| **Required Content** | Monorepo layout: `apps/` (api, agents, web, ingestion), `packages/` (domain, schemas, ui), `infra/`, `specs/`, `tests/`, `docs/`, `scripts/` |
| **Links Out** | None |
| **Spec Ref** | FR-009, FR-017 |

### Section Detail: 9 — Technology Stack

| Property | Value |
|----------|-------|
| **Order** | 9 |
| **Heading** | `## Technology Stack` |
| **Heading Level** | 2 |
| **Collapsible** | No |
| **FK Grade Target** | N/A |
| **Required Content** | Core technologies (FastAPI, Python, Next.js), Azure services (Container Apps, App Service, Cosmos DB, Redis, Blob Storage), deployment target ("Azure regions within Australia", primary: Australia East) |
| **Links Out** | None |
| **Spec Ref** | FR-008 |

### Section Detail: 10 — Success Metrics

| Property | Value |
|----------|-------|
| **Order** | 10 |
| **Heading** | `## Success Metrics` |
| **Heading Level** | 2 |
| **Collapsible** | No |
| **FK Grade Target** | N/A |
| **Required Content** | 5 capstone targets: 1,000+ lives, 50% response time, 24h earlier evacuations, 30% resource efficiency, 30% economic loss reduction |
| **Links Out** | `capstone.md` |
| **Spec Ref** | FR-007 |

### Section Detail: 11 — Contributing

| Property | Value |
|----------|-------|
| **Order** | 11 |
| **Heading** | `## Contributing` |
| **Heading Level** | 2 |
| **Collapsible** | No |
| **FK Grade Target** | N/A |
| **Required Content** | Branching conventions, PR workflow, local quality check commands (lint + test per runtime), CI pipeline reference |
| **Links Out** | `.github/workflows/ci.yml` |
| **Spec Ref** | FR-010, FR-011 |

### Section Detail: 12 — Documentation Links

| Property | Value |
|----------|-------|
| **Order** | 12 |
| **Heading** | `## Documentation` |
| **Heading Level** | 2 |
| **Collapsible** | No (FR-017: MUST remain visible) |
| **FK Grade Target** | N/A |
| **Required Content** | Links organized by audience |
| **Audience: Evaluators** | `AMA_Rubric_Asia.md`, `capstone.md`, `docs/disaster-response-hub/demo/executive-deck.md` |
| **Audience: Developers** | `docs/disaster-response-hub/architecture.md`, `specs/`, `.specify/memory/constitution.md` |
| **Audience: Operators** | `docs/disaster-response-hub/operator-runbooks.md`, `docs/disaster-response-hub/demo/walkthrough.md` |
| **IC Cross-reference** | Brief sentence: see constitution for IC authority (CHK018) |
| **Spec Ref** | FR-006, FR-013 (cross-reference) |

## Validation Rules

| Rule ID | Target Section(s) | Validation | Tool |
|---------|--------------------|-----------|------|
| V-001 | Entire document | Line count ≤ 500 | `wc -l README.md` or `(Get-Content README.md).Count` |
| V-002 | Overview, Quickstart, Personas | FK Grade ≤ 8.0 | `textstat.flesch_kincaid_grade()` |
| V-003 | All sections | No broken internal links | Script: extract `[text](path)` → `test -f path` |
| V-004 | All sections | No "service" for agents, no "agent" for runtimes | `grep -n "service" README.md` (manual review) |
| V-005 | Personas section | IC authority in blockquote, not in list or `<details>` | Manual review |
| V-006 | `<details>` blocks | Blank line after `<summary>`, before `</details>` | markdownlint / manual |
| V-007 | Architecture section | Mermaid block NOT inside `<details>` | Manual review |
| V-008 | ToC | All 10 section anchors resolve | Script: extract anchors → verify headings exist |

## Relationships

```
README.md
├── links to → docs/disaster-response-hub/architecture.md
├── links to → .specify/memory/constitution.md
├── links to → .github/workflows/ci.yml
├── links to → AMA_Rubric_Asia.md
├── links to → capstone.md
├── links to → docs/disaster-response-hub/demo/executive-deck.md
├── links to → docs/disaster-response-hub/operator-runbooks.md
├── links to → docs/disaster-response-hub/demo/walkthrough.md
├── links to → specs/ (directory)
├── links to → infra/ (directory)
├── references → 5 agents (Monitoring, Risk, Evacuation, Resource, Communication)
├── references → 3 runtimes (API, Agent, Web)
├── references → 4 audiences (Developers, Operators, Government, Evaluators)
└── references → AIIMS roles (IC, Operations, Planning, Logistics, Public Info)
```
