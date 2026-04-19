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
