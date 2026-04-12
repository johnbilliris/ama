# Implementation Plan: Root README.md

**Branch**: `feature/013-root-readme` | **Date**: 2025-07-17 | **Spec**: [spec.md](../../013-root-readme/spec.md)
**Input**: Feature specification from `/specs/013-root-readme/spec.md`

## Summary

Create a comprehensive root `README.md` for the Autonomous Disaster Response Agent Coordination Hub that serves as the primary entry point for all stakeholders — developers, operators, government agencies, and evaluators. The README is a single Markdown file (~400–500 lines) using GitHub-Flavoured Markdown with inline Mermaid diagrams and collapsible HTML `<details>` blocks, following a universal-first section ordering (FR-016) to satisfy 2-minute evaluator and 3-minute developer comprehension targets. No Azure resources or code changes are required — this is a documentation-only feature.

## Technical Context

**Language/Version**: Markdown (GitHub-Flavoured Markdown with Mermaid support)
**Primary Dependencies**: GitHub GFM renderer, Mermaid diagram renderer (built into GitHub)
**Storage**: N/A (single static file at repository root)
**Testing**: `wc -l` (line count ≤500), `textstat` Python library (FK Grade ≤8.0), markdownlint, link validation (`grep` + `test -f`), terminology check (`grep` for "service" misuse)
**Target Platform**: GitHub.com web interface (desktop and mobile), VS Code Markdown preview
**Project Type**: Documentation (single-file)
**Performance Goals**: ≤2 min evaluator comprehension, ≤3 min developer scan, ≤15 min quickstart completion, ≤30 sec link discovery
**Constraints**: ≤500 lines Markdown source (NFR-001), FK Grade ≤8.0 for overview/quickstart/personas (NFR-003/FR-015), all internal links must resolve (SC-007)
**Scale/Scope**: Single file, 4 audience personas, 10 content sections, ~25 internal links

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Constitution Principle | Applicable? | Status | Notes |
|---|----------------------|-------------|--------|-------|
| I | Life Safety First | ✅ Yes | **PASS** | FR-013 requires standalone IC authority statement; FR-005 maps AIIMS roles. IC override is prominently placed per CHK018 resolution. |
| II | Multi-Agent Coordination | ✅ Yes | **PASS** | FR-014 describes all 5 agents with explicit roles. FR-002 shows agent relationships in architecture diagram. |
| III | Data Trust & Provenance | ⚠️ Indirect | **PASS** | README links to architecture.md (authoritative data source details) and constitution. No data-handling decisions made in README itself. |
| IV | Privacy & Security | ⚠️ Indirect | **PASS** | README links to constitution for privacy principles. No PII handling in README. Data residency (Australia) mentioned in FR-008. |
| V | Multilingual & Accessible | ✅ Yes | **PASS** | FR-015/NFR-003 enforce FK Grade 8 plain language. README is English-only (appropriate for developer documentation); multilingual capability is documented as a system feature. |
| VI | Cloud Platform (Azure, Australia) | ✅ Yes | **PASS** | FR-008 explicitly requires "Azure regions within Australia" with Australia East as primary. |

**Gate Result**: ✅ **ALL GATES PASS** — no violations requiring justification.

### Checklist Conflict Resolutions

| Conflict | Resolution | Rationale |
|----------|-----------|-----------|
| **CHK016** (FK scope): FR-015 targets overview+personas; NFR-003 targets overview+quickstart — different section sets | FK Grade 8 applies to **overview, quickstart, AND personas** (union of both requirements) | Both requirements serve the same goal (accessibility to non-technical readers). Applying the union is stricter but ensures consistency. |
| **CHK017** (Azure CLI prereqs): FR-004 lists Azure CLI as prerequisite but FR-003/Assumptions say quickstart needs no Azure credentials | Split prerequisites into **"Required for local development"** (Python, Node.js, pnpm, uv, Docker) and **"Required for Azure deployment"** (Azure CLI, Azure subscription) | Resolves the apparent conflict — Azure CLI is a real prerequisite but only for deployment, not for the quickstart path. |
| **CHK018** (IC authority placement): FR-005 and FR-013 both require IC authority statement — one or two statements? | **Single primary statement** in AIIMS roles section (FR-005) with a **brief cross-reference** in the safety principles mention near FR-013's constitution link | Avoids duplication; the personas section is the natural home for governance roles. The cross-reference ensures discoverability from the safety angle. |

## Project Structure

### Documentation (this feature)

```text
specs/feature/013-root-readme/
├── plan.md              # This file
├── research.md          # Phase 0: research findings
├── data-model.md        # Phase 1: document structure model
├── quickstart.md        # Phase 1: implementation quickstart
└── tasks.md             # Phase 2 output (NOT created by plan)
```

### Source Code (repository root)

```text
README.md                # ← The single deliverable (new file at repo root)
```

**Structure Decision**: This feature produces a single file (`README.md`) at the repository root. No source code directories, test files, or contracts are needed. The README references existing project structure but does not modify it. The existing monorepo layout that the README will document:

```text
apps/
├── api/                 # FastAPI runtime (Azure Container Apps)
├── agents/              # Python agent runtime (Azure Container Apps)
│   ├── communication/
│   ├── evacuation/
│   ├── monitoring/
│   ├── resource_allocation/
│   └── risk_assessment/
├── ingestion/           # Data ingestion pipeline
└── web/                 # Next.js runtime (Azure App Service)

packages/
├── domain/              # Shared domain models
├── schemas/             # OpenAPI + JSON Schema definitions
└── ui/                  # Shared UI component library

infra/                   # Bicep IaC templates
├── main.bicep
├── bicep/
├── modules/
└── policies/

specs/                   # Feature specifications
tests/                   # Test suites (unit, integration, contract, e2e, load, simulation, benchmark)
docs/                    # Project documentation
scripts/                 # Utility scripts
```

## Complexity Tracking

> No constitution violations to justify. This is a documentation-only feature with no architectural complexity.
