---
purpose: Trust-boundary diagram showing every cross-boundary authentication and authorisation mechanism in the platform.
personas:
  - Technical-Quality
diagrams:
  - SEC-03
specs:
  - spec-001
  - spec-017
---

# SEC-03 — Trust Boundary Diagram

[→ Architecture index](../README.md)

![SEC-03 — Trust Boundary Diagram](./trust-boundary.png)

## Overview

FR-018 requires every trust-boundary crossing to show the authentication and authorisation mechanism that permits the flow.

Primary references: spec-001 and spec-017.

## Cross-boundary mechanisms

| Crossing | Mechanism | Purpose |
| --- | --- | --- |
| External agency to ingestion gateway | Protocol-specific (for example anonymous BoM FTP polling, provider API keys, or OAuth where supported) | Documents feed-specific trust assumptions instead of implying a single universal auth scheme |
| Ingestion and API services to data plane | Managed Identity | Removes shared secrets from service-to-service access |
| Operators to dashboard and API | Entra ID + OAuth 2.0 | Enforces workforce identity, tenant policy, and session scopes |
| API to external notification channels | API key | Documents third-party publication integration boundaries |

## End-to-end ingestion path

The diagram traces the external agency path through the ingestion gateway, signal ingestion workload, coordination API, and data-plane services so the full auth/authz chain is visible in one view.
