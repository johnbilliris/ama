# C4 Model — System Context

**Notation**: [C4 Model](https://c4model.com/) — System Context.
**Audience**: cross-agency reviewers (operational, technical, executive). Pairs with the Container view in `container.md`.

```mermaid
C4Context
  title System Context — Autonomous Disaster Response Coordination Hub

  Person(operator, "AIIMS Operator", "Incident Commander, Operations, Planning, Logistics, PIO, Field Coordinator, Risk Manager, Resilience Planner, Observer-Auditor, Executive Leader")
  Person(public, "Public", "Receives multilingual public alerts; CALD/ATSI accessibility-supported")
  Person_Ext(media, "Media", "Receives press releases via PIO")
  Person_Ext(partner, "Partner Agency Operator", "Federal/State/Territory/Commonwealth + cross-sector NGOs/utilities")

  System(ama, "Disaster Response Coordination Hub", "Multi-agent platform: monitoring, risk assessment, evacuation, resource allocation, communication, dependency notifier")

  System_Ext(bom, "Bureau of Meteorology", "Weather warnings + fire weather + cyclone forecasts")
  System_Ext(ga, "Geoscience Australia", "Earthquake, tsunami, volcano monitoring")
  System_Ext(state_systems, "State EM Systems", "State/Territory dispatch + jurisdictional CAD")
  System_Ext(nema, "NEMA / NCM", "National Emergency Management Agency, National Coordination Mechanism")
  System_Ext(comms, "Comms Channels", "SMS/Voice gateways, push notification, email, social, broadcast radio")
  System_Ext(aoai, "Azure OpenAI (AU East)", "Reasoning + drafting deployments")
  System_Ext(content_safety, "Azure AI Content Safety (AU East)", "LLM output safety validation")
  System_Ext(ai_search, "Azure AI Search (AU East)", "RAG over AIDR handbook corpus")
  System_Ext(foundry_phi, "Foundry Phi (non-AU, carve-out)", "Shadow path; deny-by-default classification gate")

  Rel(operator, ama, "Approves recommendations / publishes alerts / runs scenarios")
  Rel(ama, public, "Public warnings (AWS-compliant, multilingual)", "SMS/push/social/radio")
  Rel(ama, media, "Press releases (PIO-approved)")
  Rel(partner, ama, "Coordinates incidents + signals exchange (CAP/EDXL/GeoJSON)")

  Rel(bom, ama, "Weather signals + warnings", "API")
  Rel(ga, ama, "Geological signals", "API")
  Rel(state_systems, ama, "State CAD signals", "API/EDXL")
  Rel(ama, nema, "Escalation + COMDISPLAN signals")
  Rel(ama, comms, "Outbound public alerts")

  Rel(ama, aoai, "LLM calls (Private Endpoint)")
  Rel(ama, content_safety, "Output safety check (Private Endpoint)")
  Rel(ama, ai_search, "RAG retrieval (Private Endpoint)")
  Rel(ama, foundry_phi, "Shadow LLM calls (gateway: PII + PSPF + sensitive-ops filter; deny-by-default)")
```

## Boundaries

- **Tenant** boundary: each Australian jurisdiction (`act|nsw|vic|qld|sa|wa|tas|nt|commonwealth`) is a tenant; data is partitioned by `/tenant_id` in Cosmos and segregated by Entra group + RBAC.
- **AU residency** boundary: every data plane (Cosmos, Storage, App Insights, Log Analytics, Key Vault, ACR, AI Search, Content Safety, AOAI primary) is in **Australia East**, replicated to **Australia Southeast** for DR.
- **Foundry carve-out** boundary: only model-hosting endpoints listed in `infra/parameters/foundry-carveout.yaml` may be called outside Australia. Every call passes through the classification gate (ADR-033).

## Quality attributes (drivers)

- **Life safety primacy** — every recommendation requires human approval before life-safety publication.
- **AIIMS COP integrity** — single shared operating picture across operators.
- **Auditability** — append-only ledger with cryptographic continuity (spec-032 US1).
- **Graceful degradation** — when LLM/AI Search/Content Safety degraded, agents fall through deterministic templates.

## See also

- [Container view](container.md)
- [Sequence: Monitoring → Risk → Communication](../sequence/monitoring-risk-comms.md)
