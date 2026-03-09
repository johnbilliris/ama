# ama Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-09

## Active Technologies
- Python 3.12 for API and agent runtime; TypeScript 5.6 for responsive web UI + Microsoft Agent Framework for Python, FastAPI, Pydantic v2, Azure Identity, Azure Cosmos DB SDK, Azure Blob Storage SDK, Azure Service Bus or Event Hubs clients, Next.js 15, React 19, Tailwind CSS, Playwright (001-disaster-response-hub)
- Azure Cosmos DB for operational state and incident timelines; Azure Blob Storage for immutable audit artifacts and replay evidence; Azure Cache for Redis for low-latency dashboard caching (001-disaster-response-hub)
- Python 3.12 for API and agent runtime; TypeScript 5.6 for responsive web UI + Microsoft Agent Framework for Python, FastAPI, Pydantic v2, Azure Identity, Azure Cosmos DB SDK, Azure Blob Storage SDK, Azure Cache for Redis SDK, Azure Event Hubs or Service Bus SDK, Next.js 15, React 19, Tailwind CSS, Playwright (001-disaster-response-hub)
- Azure Cosmos DB for operational state and incident timelines; Azure Blob Storage for immutable audit artifacts and replay evidence; Azure Cache for Redis for low-latency incident dashboard state (001-disaster-response-hub)

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
- 001-disaster-response-hub: Added Python 3.12 for API and agent runtime; TypeScript 5.6 for responsive web UI + Microsoft Agent Framework for Python, FastAPI, Pydantic v2, Azure Identity, Azure Cosmos DB SDK, Azure Blob Storage SDK, Azure Cache for Redis SDK, Azure Event Hubs or Service Bus SDK, Next.js 15, React 19, Tailwind CSS, Playwright
- 001-disaster-response-hub: Added Python 3.12 for API and agent runtime; TypeScript 5.6 for responsive web UI + Microsoft Agent Framework for Python, FastAPI, Pydantic v2, Azure Identity, Azure Cosmos DB SDK, Azure Blob Storage SDK, Azure Service Bus or Event Hubs clients, Next.js 15, React 19, Tailwind CSS, Playwright

- 001-disaster-response-hub: Added Python 3.12 for API and agents; TypeScript 5.6 for web UI + Microsoft Agent Framework (Python SDK), FastAPI, Pydantic, Azure SDKs, Next.js 15, React 19, Tailwind CSS, Azure Cosmos DB client, Azure Service Bus/Event Hubs clients

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
