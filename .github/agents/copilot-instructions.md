---
description: "AMA development guidelines and project conventions shared with all agents."
---

# AMA Development Guidelines

## Project Overview

Autonomous Disaster Response Coordination Hub — a monorepo for Australian emergency management with AI-assisted governance, preparedness analysis, and multi-agency coordination.

## Project Structure

```text
apps/
  api/          # FastAPI backend (Python 3.12)
  web/          # Next.js 16 frontend (TypeScript 5.8, React 19)
  agents/       # AI agent runtime modules
  ingestion/    # Data ingestion pipelines
packages/
  domain/       # Pydantic domain models and seed data
  ui/           # Shared React component library (@ama/ui)
  schemas/      # Shared schema definitions
tests/
  unit/         # pytest unit tests
  integration/  # Integration tests (mock external services)
  contract/     # API contract tests
  e2e/          # Playwright end-to-end tests
  benchmark/    # Performance benchmarks
  simulation/   # Scenario simulation tests
  load/         # Load tests (Locust)
  devops/       # CI/CD pipeline tests
infra/          # Azure Bicep IaC templates
data/           # Seed JSON data files
scripts/        # Utility and deployment scripts
specs/          # Feature specifications (speckit workflow)
docs/           # Project documentation
```

## Active Technologies
- Python 3.11+ (agents, API), TypeScript/Next.js 14 (web dashboard) + FastAPI, Pydantic, Azure OpenAI SDK, Azure AI Content Safety SDK, Azure Service Bus SDK, numpy, shapely (025-agent-spec-compliance)
- Azure Cosmos DB (assessments, plans, dead-letters), Azure Blob Storage (audit) (025-agent-spec-compliance)
- Python 3.11+ (agents, API), TypeScript 5.x (Next.js dashboard) + FastAPI, Pydantic, Shapely, azure-ai-contentsafety, azure-iot-device, azure-cosmos, httpx, numpy, Next.js 14 (025-agent-spec-compliance)
- Azure Cosmos DB (dead-letters, radius lookup table, assessments), Azure Blob Storage (signal archives), Azure IoT Hub (device telemetry) (025-agent-spec-compliance)
- Python 3.11 (backend), TypeScript/Next.js 16 (frontend) + FastAPI, Pydantic v2, azure-cosmos, Next.js App Router (026-sim-warp-playback)
- Azure Cosmos DB (containers: `simulation`, `sim-events` [new], `sim-chat`) (026-sim-warp-playback)
- Python 3.12 (backend + agents), TypeScript/React 19 (frontend) + FastAPI, Pydantic, azure-cosmos, azure-identity (API); Next.js 16.2, React 19 (web); asyncio, azure-cosmos (agents) (026-sim-warp-playback)
- Azure Cosmos DB — containers: `simulation` (tenants, scheduler state), `sim-events` (events, snapshots, annotations), `sim-chat` (chat history) (026-sim-warp-playback)
- Markdown (CommonMark + GitHub-flavoured Markdown); no runtime language used by this feature. (027-spec-hardening)
- Git (version-controlled markdown under `specs/` and `.github/`). No database, no blob store. (027-spec-hardening)
- [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION] (028-capstone-alignment)
- [if applicable, e.g., PostgreSQL, CoreData, files or N/A] (028-capstone-alignment)
- N/A — documentation-only feature. (Portfolio-wide ambient stack, for reviewer context only: Python 3.12 (FastAPI API + agents), TypeScript / Next.js 16 (web dashboard), Bicep (infra). This feature does not edit any of these.) + `specs/shared/gap-id-register.md` (monotonic ID source); `specs/027-spec-hardening/contracts/persona-profile.md` (YAML persona schema); `capstone.md` (authoritative brief); `AMA_Rubric_Asia.md` (SC-009 measurement surface); `ama-rubric-grader` skill (SC-009 automation). (028-capstone-alignment)
- N/A — Markdown files under version control only. (028-capstone-alignment)
- Python 3.13 (FastAPI api, evaluation worker, dataset packages); TypeScript 5.x on Next.js 16 (web) + `azure-ai-evaluation`, `azure-ai-projects`, `azure-identity`, `azure-cosmos`, `azure-storage-blob`, `azure-monitor-opentelemetry`, `presidio-analyzer`, `presidio-anonymizer`, FastAPI, Pydantic v2, Pydantic Settings; React 19, Next.js 16, native fetch (no SWR/React Query, per existing AMA convention); Bicep modules + Bicep AVM where available (030-llm-eval-framework)
- Cosmos DB (Australia East) — new containers `eval_datasets`, `eval_runs`, `eval_metric_definitions`, `eval_audit`; Azure Blob Storage with time-based 7-year immutability policy for dataset versions, run artefacts, and audit archive; Azure Key Vault for Foundry endpoint URIs; Log Analytics workspace (existing AMA workspace) for telemetry (030-llm-eval-framework)
- N/A for the pipeline itself. Deployed runtimes (api, agents, ingestion, web) continue to use their existing Cosmos DB / Storage / Service Bus resources provisioned by `infra/main.bicep`. (031-simplify-cicd-pipeline)
- Python 3.12 (apps/api, apps/agents, apps/ingestion, apps/eval-runner), TypeScript 5.8 (apps/web on Next.js 16.2) + FastAPI, Pydantic v2, Azure SDK for Python, Azure OpenAI SDK, Next.js 16.2, React 19, openai, opentelemetry (NEW), pybreaker (NEW — replaces hand-rolled circuit breaker), import-linter (NEW), mypy (existing, now `--strict`), ruff (existing, now `format` enforced), cosign (NEW), Azure AI Search SDK (NEW) (032-rubric-improvements)
- Cosmos DB (existing — partition strategy expanded; CMK + Private Endpoint added), Azure Storage (CMK + Private Endpoint added), Azure AI Search (NEW — `Standard S1` AU East, indexes the `docs/aidr/` corpus + a future prompt library mirror) (032-rubric-improvements)

**Backend**: Python 3.12, FastAPI, Pydantic v2, Azure Cosmos DB SDK, Azure Blob Storage SDK, Azure Identity, Azure OpenAI SDK, tenacity
**Frontend**: TypeScript 5.8, Next.js 16.2, React 19, Tailwind CSS, @ama/ui component library
**Testing**: pytest, Playwright, Locust
**Infrastructure**: Azure Bicep (AVM-first), Azure Container Apps, Azure Cosmos DB, Azure Cache for Redis, Azure Service Bus / Event Hubs
**Tooling**: pnpm (workspaces), uv (Python), ruff (linting), ESLint

## Commands

```bash
# Python linting
ruff check .

# Python tests
pytest                                    # all tests
pytest tests/unit                         # unit tests only
pytest tests/contract                     # contract tests only

# Frontend
pnpm --filter @ama/web dev                # dev server
pnpm --filter @ama/web build              # production build
pnpm --filter @ama/web lint               # ESLint
pnpm --filter @ama/web test:e2e           # Playwright e2e

# IaC
bicep build infra/main.bicep
bicep lint infra/main.bicep
```

## Code Style

- **Python**: 120-char line length, ruff (E/F/I/UP rules), type hints required, Pydantic v2 models
- **TypeScript**: ESLint, strict mode, App Router conventions
- **Commits**: Conventional Commits format
- **Comments**: Minimal — explain WHY not WHAT (see `.github/instructions/code-commenting.instructions.md`)
- **Security**: TLS 1.2+, HTTPS-only, managed identity preferred, no secrets in code

## Key Patterns

- **API**: Thin FastAPI route → service → seed/repository data pattern
- **Frontend**: Server components by default, client components opt-in; API clients in `apps/web/src/lib/api/`
- **Domain**: Pydantic models in `packages/domain/`; seed data via `SeedService` → `bootstrap_seed_data()`
- **Data**: Cosmos DB with type-discriminator partition pattern; in-memory backends for tests
- **Agents**: 94 Copilot agents (operational, sector, technical, speckit) in `.github/agents/`

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
