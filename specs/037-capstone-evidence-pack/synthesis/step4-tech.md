# Step 4 — Technical Cohort Synthesis (17 personas)

> Source: synthetic canvas of `.github/agents/technical/*.agent.md`.

## Data model + JSON schema design
- **AI/ML Engineer** (`technical/ai-ml-engineer.agent.md:43-48,63-69,77-82,123-127`) — structured JSON outputs, Pydantic-validated, with confidence/provenance/timestamps; fallback templates when model unavailable.
- **Data Engineer** (`technical/data-engineer.agent.md:34-43,83-95`) — extend schema governance from `signal-envelope.schema.json`; audit artifacts stay immutable in Blob Storage; partition by `organisation_id`/`jurisdiction_id`; contract-test any schema change.
- **Solution Architect** (`technical/solution-architect.agent.md:50-57,112-117`) — govern schema evolution for OpenAPI + signal envelope; keep CQRS-lite/read-model separation and append-only audit.
- **API Architect** (`technical/api-architect.agent.md:50-58,75-82,205-210`) — Pydantic v2 DTOs, OpenAPI-first, RFC7807 errors, versioned contracts.
- **Software Developer** (`technical/software-developer.agent.md:42-50,87-95,96-107`) — implement Pydantic v2 models, typed handlers, preserve provenance/tenant isolation in code.

## API contracts + read-only endpoint surface
- **API Architect** (`technical/api-architect.agent.md:50-59,136-143,205-210`) — contract-first OpenAPI, URL versioning, pagination, RFC7807; provenance metadata in responses.
- **Solution Architect** (`technical/solution-architect.agent.md:50-57,112-117`) — approve system-level contract evolution; no silent state changes.
- **Security Engineer** (`technical/security-engineer.agent.md:34-44,88-99`) — tenant-scoped access on every API; JWT validation; no PII exposure.
- **Software Developer** (`technical/software-developer.agent.md:42-50,109-129`) — implement Next.js/FastAPI endpoints; web UI strictly read-only.

## Schema validation + CI publication gate
- **Infrastructure/DevOps** (`technical/infrastructure-devops.agent.md:57-65,122-163,232-246`) — Bicep/schema validation; CI must build/lint/validate before deploy.
- **QA/Test Engineer** (`technical/qa-test-engineer.agent.md:30-42,102-109`) — contract tests gate schema changes.
- **Data Engineer** (`technical/data-engineer.agent.md:91-102`) — all schema changes update canonical schema files and pass contract tests.
- **Principal Engineer** (`technical/principal-engineer.agent.md:55-66,142-150`) — meaningful test coverage and debt tracking around schema work.

## Web shell extension (governance/executive/)
- **UX Designer** (`technical/ux-designer.agent.md:24-35,72-90`) — read-only executive surfaces must be scannable, severity-distinct, degraded-mode aware.
- **Software Developer** (`technical/software-developer.agent.md:45-52,109-115`) — Next.js 15 App Router pages in `apps/web/src/app/`.
- **Accessibility Tester** (`technical/accessibility-tester.agent.md:38-45,54-68,129-135`) — keyboard/ARIA/live-region validation.
- **QA/Test Engineer** (`technical/qa-test-engineer.agent.md:34-41,91-96,105-107`) — Playwright + axe-core e2e.
- **Solution Architect** (`technical/solution-architect.agent.md:103-117`) — preserve CQRS-lite and graceful degradation.

## Security + AU-residency + append-only audit + auditor-signoff
- **Security Engineer** (`technical/security-engineer.agent.md:34-44,74-99`) — AU-only residency, RBAC, tenant isolation, Key Vault, no PII in logs/prompts.
- **Compliance Auditor** (`technical/compliance-auditor.agent.md:42-49,66-85,119-139`) — Privacy Act/APPs, DDA, PSPF, Records Acts mapping.
- **Azure Principal Architect** (`technical/azure-principal-architect.agent.md:39-56,90-95`) — AU-region service selection + WAF compliance.
- **Infrastructure/DevOps** (`technical/infrastructure-devops.agent.md:76-80,113-120`) — managed identities, immutable audit storage.
- **Data Engineer** (`technical/data-engineer.agent.md:74-87`) — immutable Blob audit artefacts; tenant-scoped partitions.

## Test strategy
- **QA/Test Engineer** (`technical/qa-test-engineer.agent.md:30-42,83-109`) — contract + integration + Playwright e2e + Locust scale.
- **Accessibility Tester** (`technical/accessibility-tester.agent.md:70-75,129-135`) — automated axe-core + WCAG AA gating.
- **Chaos Engineer** (`technical/chaos-engineer.agent.md:69-76,128-136`) — degraded publication and retrieval paths under failure.
- **SRE Engineer** (`technical/sre-engineer.agent.md:94-107,155-163`) — testable observable SLOs.
- **Principal Engineer** (`technical/principal-engineer.agent.md:55-66,142-150`) — pyramid discipline; safety-critical coverage.

## Infrastructure / deployment / observability
- **Infrastructure/DevOps** (`technical/infrastructure-devops.agent.md:47-80,141-170,224-246`) — no net-new resources; reuse existing Container Apps/App Service/Cosmos/App Insights.
- **Azure Principal Architect** (`technical/azure-principal-architect.agent.md:39-57,96-123`) — confirm AU availability + WAF tradeoffs.
- **SRE Engineer** (`technical/sre-engineer.agent.md:50-67,94-107,184-192`) — monitor publication pipeline + executive page latency as SLO-bearing.
- **Docker & Container Engineer** (`technical/docker-container-engineer.agent.md:52-82,135-149`) — thin containers, health probes, autoscaling.
- **Chaos Engineer** (`technical/chaos-engineer.agent.md:43-67,115-127`) — fail-soft validation.

## Documentation + governance-hub navigation
- **Product Owner/BA** (`technical/product-owner-ba.agent.md:22-31,72-85,93-98`) — measurable success metrics + BDD traceability.
- **Solution Architect** (`technical/solution-architect.agent.md:50-58,112-117`) — document architecture decisions in governance hub.
- **Compliance Auditor** (`technical/compliance-auditor.agent.md:80-85,119-139`) — compliance register/update evidence.
- **Principal Engineer** (`technical/principal-engineer.agent.md:61-71,133-150`) — document trade-offs and debt from ledger/ADR consolidation.
- **UX Designer** (`technical/ux-designer.agent.md:24-35,78-90`) — navigation hierarchy under degraded mode.

## Cross-cutting concerns
- **Accessibility Tester** — WCAG 2.2 AA, keyboard/screen-reader/RTL, 400% zoom, high-contrast.
- **Compliance Auditor** — legislative mapping, evidence, auditability.
- **Chaos Engineer** — blast-radius control, kill switches, staging-only experiments.
- **Principal Engineer** — keep scope lean, explicit assumptions, no unnecessary abstraction.
- **SRE Engineer** — graceful degradation, load shedding, actionable alerting.

