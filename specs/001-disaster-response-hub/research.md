# Research: Autonomous Disaster Response Coordination Hub

## Decision: Use a code-first deterministic orchestration layer on Azure Container Apps

**Rationale**: Microsoft’s multiple-agent workflow guidance favors a custom orchestrator when the workload needs explicit control over agent behavior, orchestration logic, and compute. This feature needs deterministic handoffs, reproducible incident flows, human approval gates, and auditable safety behavior, which are stronger requirements than a prompt-defined agent network can reliably satisfy.

**Alternatives considered**:

- Microsoft Foundry Agent Service as the primary orchestrator: rejected for the core control path because the workload requires stronger determinism and explicit execution control.
- Single-agent design: rejected because monitoring, risk, evacuation, resource allocation, and communication responsibilities need different inputs, outputs, and safety constraints.

## Decision: Deliver the mobile experience as a responsive PWA-style web application

**Rationale**: The requirement is mobile-ready operations, not separate native mobile products. A responsive Next.js application hosted on Azure App Service can deliver one codebase for desktop briefings, tablet command posts, and mobile field usage while retaining strong visual consistency, faster rollout, and simpler TDD coverage with Playwright.

**Alternatives considered**:

- Separate iOS and Android native apps: rejected for initial release due to duplicated delivery effort and slower iteration across agencies.
- Desktop-only operator console: rejected because field and low-connectivity users need mobile access.

## Decision: Align operating models to AIIMS concepts with jurisdiction overlays

**Rationale**: AIIMS emphasizes management by objectives, functional management, span of control, unity of command, and flexibility. Those principles map well to Australian multi-agency incident coordination and provide a stable anchor for modelling organisation roles, delegation, approval paths, and cross-jurisdiction differences.

**Alternatives considered**:

- Create a custom command model from scratch: rejected because it weakens alignment with established Australian emergency management practice.
- Treat every jurisdiction as structurally identical: rejected because the spec explicitly requires framework and decision-right differences to be represented.

## Decision: Use authoritative-first ingestion with provenance-scored multi-source fusion

**Rationale**: Bureau of Meteorology and Geoscience Australia are authoritative Australian sources for weather, warnings, and geohazard context. The system still needs IoT, field, and social inputs, but those signals must be normalized into a trust model that preserves source type, time, location precision, freshness, confidence, and contradiction status before they influence incident recommendations.

**Alternatives considered**:

- Authoritative-only ingestion: rejected because local field and community signals improve situational awareness.
- Treat all signals equally after normalization: rejected because safety-critical decisions require explicit trust weighting.

## Decision: Use Azure Cosmos DB, Blob Storage, and Redis as the operational data backbone

**Rationale**: Cosmos DB fits incident-centric, high-read, geo-aware operational state and event history. Blob Storage is suitable for immutable audit artifacts, evidence bundles, and replay payloads. Redis improves low-latency dashboard reads and short-lived coordination state without making it a system of record.

**Alternatives considered**:

- Single relational database for everything: rejected because incident documents, replay artifacts, and low-latency cached views have different storage patterns.
- Blob-only event store: rejected because the application requires fast filtered reads and operational queries.

## Decision: Make TDD and scenario replay the primary quality strategy

**Rationale**: The spec and constitution both require software development to be test-driven and operationally safe. Contract tests validate API semantics, integration tests validate orchestration and policy behavior, simulation tests validate disaster scenarios, and Playwright validates responsive operator flows.

**Alternatives considered**:

- Unit-test-heavy strategy without simulations: rejected because incident workflows must be proven end to end.
- Manual rehearsal only: rejected because replayability and regression safety are mandatory.

## Decision: Use a dual-model pattern rather than a single model role

**Rationale**: The control plane benefits from one high-capability model class for reasoning-heavy recommendation steps and one smaller, lower-cost model class for summarization, role-specific briefing views, and draft communications. The exact model deployment names should be selected during implementation from the active Azure AI Foundry catalog in Australian-supported regions.

**Alternatives considered**:

- One model for every task: rejected because it creates unnecessary cost and latency pressure.
- Hard-code a specific model deployment in planning artifacts: rejected because available model catalog entries can change and must be validated at implementation time.
