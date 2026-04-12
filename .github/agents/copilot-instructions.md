# ama Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-09

## Active Technologies
- Python 3.12 for API and agent runtime; TypeScript 5.6 for responsive web UI + Microsoft Agent Framework for Python, FastAPI, Pydantic v2, Azure Identity, Azure Cosmos DB SDK, Azure Blob Storage SDK, Azure Service Bus or Event Hubs clients, Next.js 15, React 19, Tailwind CSS, Playwright (001-disaster-response-hub)
- Azure Cosmos DB for operational state and incident timelines; Azure Blob Storage for immutable audit artifacts and replay evidence; Azure Cache for Redis for low-latency dashboard caching (001-disaster-response-hub)
- Python 3.12 for API and agent runtime; TypeScript 5.6 for responsive web UI + Microsoft Agent Framework for Python, FastAPI, Pydantic v2, Azure Identity, Azure Cosmos DB SDK, Azure Blob Storage SDK, Azure Cache for Redis SDK, Azure Event Hubs or Service Bus SDK, Next.js 15, React 19, Tailwind CSS, Playwright (001-disaster-response-hub)
- Azure Cosmos DB for operational state and incident timelines; Azure Blob Storage for immutable audit artifacts and replay evidence; Azure Cache for Redis for low-latency incident dashboard state (001-disaster-response-hub)
- Python 3.12 for API and agent runtime; TypeScript 5.6 for responsive web UI + FastAPI, Pydantic v2, openai (Azure OpenAI Python SDK), tenacity (retry/backoff), Locust (load testing), Microsoft Agent Framework for Python; Next.js 15, React 19, Tailwind CSS, Playwright (003-rubric-gap-closure)
- Azure Cosmos DB (operational state); Azure Blob Storage (audit + dead-letter); Azure Cache for Redis (dashboard cache); in-memory implementations for local development (003-rubric-gap-closure)
- Markdown (`.agent.md` files with YAML frontmatter) — no compiled code + VS Code GitHub Copilot agent infrastructure (existing in `.github/agents/`) (004-actor-github-agents)
- N/A — static files in the repository (004-actor-github-agents)
- Python 3.12 for API, domain models, and governance services; TypeScript 5.6 for governance dashboard UI + FastAPI, Pydantic v2, Azure Cosmos DB SDK, Azure Cache for Redis SDK; Next.js 15, React 19, Tailwind CSS, Playwright (005-data-source-governance)
- Azure Cosmos DB for governance registry entries, constitutional assessments, agent assignments, handoff chains, and audit trail; Azure Cache for Redis for low-latency handoff-chain lookups and agent-side governance cache (005-data-source-governance)
- Python 3.12 for ingestion pipelines, API services, agent code, domain models, and simulators + FastAPI, Pydantic v2, Azure Cosmos DB SDK, Azure Blob Storage SDK, Azure Cache for Redis SDK, `ftplib`/`httpx` for source polling, `lxml` for BoM XML parsing, `jsonschema` for SignalEnvelope validation (006-data-ingestion-storage)
- Azure Cosmos DB for operational signal store (pending data-engineer review for polyglot alternatives); Azure Blob Storage for raw payloads, binary assets, and audit trail; Azure Cache for Redis for dedup hash cache and governance lookups (006-data-ingestion-storage)
- Python 3.12 (API + Agents + Ingestion), TypeScript 5.6 (Next.js 15 Web) + FastAPI, azure-cosmos, azure-identity, redis, azure-storage-blob, Next.js 15, @ama/ui (007-simulation-tenant-isolation)
- Cosmos DB (disaster-hub database — signals, simulation, seed, governance containers), Redis (distributed cache/dedup), Azure Blob Storage (raw-payloads, audit, simulation containers) (007-simulation-tenant-isolation)
- Python 3.12 + FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, tenacity (010-monitoring-agent)
- Azure Cosmos DB (monitoring-decisions container, append-only audit), Azure Service Bus (signal intake queue) (010-monitoring-agent)
- Python 3.12 + FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, azure-servicebus, tenacity (012-risk-assessment-agent)
- Azure Cosmos DB (risk-assessments, risk-recommendations, risk-assessment-decisions containers, append-only audit), Azure Service Bus (handoff intake queue) (012-risk-assessment-agent)
- Python 3.12 + FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, azure-servicebus, tenacity, shapely (009-evacuation-agent)
- Azure Cosmos DB (evacuation-plans, evacuation-decisions containers, append-only audit), Azure Service Bus (handoff intake queue) (009-evacuation-agent)
- Azure Cosmos DB (resource-deployment-plans, resource-allocation-decisions containers, append-only audit), Azure Service Bus (handoff intake queue) (011-resource-allocation-agent)
- Python 3.12 + FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, azure-servicebus, azure-communication-sms, azure-notificationhubs, tenacity, numpy (cosine similarity for back-translation) (008-communication-agent)
- Azure Cosmos DB (public-alerts, communication-decisions, delivery-records containers, append-only audit), Azure Service Bus (communication-handoffs intake queue, commander-approval-queue) (008-communication-agent)
- Markdown (GitHub-Flavoured Markdown with Mermaid support) + GitHub GFM renderer, Mermaid diagram renderer (built into GitHub) (feature/013-root-readme)
- N/A (single static file at repository root) (feature/013-root-readme)

- Python 3.12 for API and agents; TypeScript 5.6 for web UI + Microsoft Agent Framework (Python SDK), FastAPI, Pydantic, Azure SDKs, Next.js 15, React 19, Tailwind CSS, Azure Cosmos DB client, Azure Service Bus/Event Hubs clients (001-disaster-response-hub)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.12 for API and agents; TypeScript 5.6 for web UI: Follow standard conventions

## Recent Changes
- feature/013-root-readme: Added Markdown (GitHub-Flavoured Markdown with Mermaid support) + GitHub GFM renderer, Mermaid diagram renderer (built into GitHub)
- 008-communication-agent: Added Python 3.12 + FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, azure-servicebus, azure-communication-sms, azure-notificationhubs, tenacity, numpy (cosine similarity for back-translation)
- 011-resource-allocation-agent: Added Python 3.12 + FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, azure-servicebus, tenacity


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
