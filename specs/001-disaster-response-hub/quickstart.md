# Quickstart: Autonomous Disaster Response Coordination Hub

## Purpose

Validate the design through a development-ready setup, failing tests first, and a scenario rehearsal that exercises the shared operating picture, role-specific workspaces, and approval-controlled alerts.

## Prerequisites

- Python 3.12
- Node.js 22 and pnpm
- Azure Developer CLI or equivalent Azure deployment tooling
- Access to Azure resources in Australian regions only
- A Microsoft Agent Framework-compatible Python environment
- Test credentials for Entra ID-backed development tenants

## Planned workspace shape

```text
apps/web
apps/api
apps/agents
packages/domain
packages/schemas
packages/ui
tests
```

## Setup sequence

1. Create the monorepo folders and initialize the Python and TypeScript workspaces described in the plan.
2. Install Python dependencies for the API and agent runtime.
   - Reminder: `agent-framework-azure-ai --pre` is required while Agent Framework remains in preview.
3. Install the web dependencies and initialize Next.js, Tailwind, and Playwright.
4. Configure `.env` files for Azure App Service, Azure Container Apps, Cosmos DB, Blob Storage, Redis, and identity settings.
5. Seed the local development dataset with Australian jurisdictions, organisations, personas, and framework assignments.

## Test-first validation flow

1. Write and run the failing contract tests for organisation intelligence, signal ingestion, dashboard, approvals, and scenario replay.
2. Write and run the failing integration tests for orchestration, provenance scoring, task coordination, and approval gates.
3. Write and run the failing Playwright tests for responsive dashboard, persona workspace, and live signal pages.
4. Write and run the failing simulation tests for bushfire, flood, and cyclone replays.
5. Implement the minimum code required to make each test group pass in priority order.

## Scenario rehearsal

1. Seed a multi-jurisdiction flood or bushfire incident involving at least two Australian jurisdictions.
2. Ingest one authoritative weather warning, one IoT or field signal, and one social-community report.
3. Verify the dashboard shows provenance, freshness, participating organisations, framework context, and a recommendation under review.
4. Open a persona-specific workspace and confirm role-relevant tasks and dependencies are filtered correctly.
5. Approve a public alert through the human approval workflow and publish it to a simulated channel set.
6. Run a scenario replay and verify audit artifacts are written for post-incident review.

## Acceptance checks

- Shared operating picture loads in under 2 seconds on a throttled mobile browser profile.
- A first coordinated action plan is visible within 10 minutes of incident activation in rehearsal.
- Role-specific workspaces show only relevant tasks while preserving dependency visibility.
- No public alert is published without a recorded approval decision unless the configuration explicitly allows an alternate mode.
- Degraded-source mode clearly marks stale or untrusted signals without removing the rest of the operating picture.

## Validated Results

The following validations have been confirmed through automated test execution:

### Python test suite (14 tests)
- ✅ Contract tests: signal ingestion, dashboard, alert lifecycle, persona workspace, preparedness catalog
- ✅ Integration tests: provenance scoring, recommendation guardrails, tenant isolation, cross-agency access control, degraded-mode behavior
- ✅ Simulation tests: bushfire, flood, and cyclone preparedness replays

### Playwright e2e suite (3 tests)
- ✅ Incident commander dashboard with alert approval workflow
- ✅ Persona workspace with task status updates
- ✅ Dashboard decision-support validation (signal health, degraded banner, agency list, approval action)

### Exercise metrics validation
- ✅ SC-004 coordinated response time comparison (baseline vs hub-enabled)
- ✅ SC-006 resource deployment efficiency comparison
- ✅ SC-007 UX evaluation dimension scoring and coverage validation

### Quickstart rehearsal flow
- ✅ Multi-jurisdiction flood rehearsal: signal ingestion → dashboard → approval → alert publish
- ✅ Preparedness rehearsal: organisation catalog → framework review → scenario replay → gap analysis
- ✅ Cross-agency isolation: persona workspace filtering and unauthorized access rejection

## Final Validation Guidance

To re-run the complete validation suite:

```bash
# Python tests (contract, integration, simulation, exercise metrics)
python -m pytest tests/ -x --tb=short

# Playwright e2e tests (requires pnpm and Chromium)
corepack pnpm --filter @ama/web exec playwright test --project chromium
```

To run a manual quickstart rehearsal:

1. Start the API: `cd apps/api && uvicorn app.main:app --reload`
2. Start the web: `cd apps/web && corepack pnpm dev`
3. Follow the scenario steps above, verifying each acceptance check
