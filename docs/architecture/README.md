# Architecture Navigation Index

Use this index to find the AMA architecture views by persona cluster and to trace each shipped feature spec to at least one architecture home.

- [Architecture Known Gaps](known-gaps.md)
- [ADR Navigation Index](adr/README.md)

> **How to add a new diagram**: follow the [architecture quickstart](../../specs/001-arch-docs-refresh/quickstart.md).

## Operational

Operational views help responders understand approval gates, AIIMS role hand-offs, recovery transitions, and degraded-mode behaviour.

- [SEQ-01 — Alert Approval Publication](sequence/alert-approval-publication.md) — End-to-end alert authoring, approval, and publication.
- [SEQ-02 — Cross-Agency Recommendation](sequence/cross-agency-recommendation.md) — Multi-agency recommendation, approval, and execution flow.
- [SEQ-03 — Evacuation Five-Stage Flow](sequence/evacuation-five-stage.md) — Human-gated evacuation actuation across five stages.
- [SEQ-04 — Recovery Transition](sequence/recovery-transition.md) — Response to recovery to normalisation transition view.
- [SEQ-05 — Audit-Trail Provenance Flow](sequence/audit-provenance.md) — Every actuation logged with human-gate and compliance evidence capture.
- [SEQ-06 — Graceful Degradation Behaviour](sequence/graceful-degradation.md) — What degrades, what stays up, and which fallback activates.
- [OPS-01 — AIIMS System Context](operational/aiims-system-context.md) — All 10 AIIMS roles mapped to hub components.
- [OPS-02 — Escalation Paths](operational/escalation-paths.md) — L1 to L3 triggers, owners, and system actions.
- [RISK-01 — Risk Register Lifecycle](operational/risk-register-lifecycle.md) — End-to-end risk record lifecycle from identification through treatment to closure.
- [OPS-03 — PPRR Phase Overlay](operational/pprr-phase-overlay.md) — Platform capabilities and AIIMS roles mapped to each PPRR phase.

## Sector

Sector views explain tenancy, ingestion, integration, and jurisdictional routing across the Australian emergency-management ecosystem.

- [SECTOR-01 — Multi-Jurisdiction Tenancy](data/multi-jurisdiction-tenancy.md) — 8 jurisdictions + Commonwealth tenant isolation and Cosmos partition alignment.
- [SECTOR-02 — Ingestion Data-Flow](data/ingestion-data-flow.md) — CAP/EDXL/GeoJSON signal path from external feeds to agent consumers.
- [SECTOR-03 — Integration-Point Map](data/integration-point-map.md) — BoM, GA, NEMA, and agency integration endpoints with data formats.
- [SECTOR-04 — Jurisdiction-Filter Behaviour](data/jurisdiction-filter.md) — Cross-state authority hand-off and filter rules (spec-022).
- [SECTOR-05 — Cross-Sector Touchpoints](data/cross-sector-touchpoints.md) — Data exchange protocols and lead-agency rules at each cross-sector boundary.

## Technical-Architecture

Technical-architecture views show the core structure of the platform, from system boundaries to container and component responsibilities.

- [C4-L1 — System Context](c4/system.md) — External actors, systems, and trust boundaries.
- [C4-L2 — Container](c4/container.md) — Primary runtime containers and their relationships.
- [C4-L3-API — Component: Coordination API](c4/component-api.md) — FastAPI internal components and request-handling path.
- [C4-L3-Web — Component: Web Dashboard](c4/component-web.md) — Next.js page and component hierarchy.
- [C4-L3-Agents — Component: Agents Runtime](c4/component-agents.md) — All 5 named agents and their service relationships.
- [C4-L3-Ingest — Component: Ingest Service](c4/component-ingest.md) — CAP/EDXL/GeoJSON adapters and signal normalisation.

## Technical-Build

Technical-build views describe delivery pipelines and deployed Azure topology for engineers operating or changing the platform.

- [DEPLOY-01 — CI/CD Pipeline](deployment/cicd-pipeline.md) — Branch-driven GitHub Actions deployment with external environment approvals.
- [DEPLOY-02 — Azure Resource Topology](deployment/azure-resource-topology.md) — Current `rg-drh-<env>` topology, with `rg-ama` retained only as a historical snapshot.
- [DEPLOY-03 — Cosmos DB Partitioning Scheme](deployment/cosmos-partitioning.md) — Partition keys, document routing, and multi-jurisdiction alignment.
- [BUILD-01 — Agent Runtime LLM Gateway](c4/agent-runtime-llm-gateway.md) — Internal path from agent invocation through prompt construction, model-gateway redaction, and Foundry endpoint dispatch.

## Technical-Quality

Technical-quality views capture the controls, boundaries, and quality guardrails that keep the platform secure, compliant, and supportable.

- [SEC-01 — AU-Residency and Data-Classification](security/au-residency-data-classification.md) — AU boundary, Foundry carve-out zone, and model-gateway redaction enforcement.
- [SEC-02 — RBAC Role/Permission Matrix](security/rbac-matrix.md) — All 10 AIIMS roles mapped to platform permissions.
- [SEC-03 — Trust-Boundary Diagram](security/trust-boundary.md) — Every cross-boundary auth/authz mechanism end-to-end.
- [SEC-04 — SLI/SLO Model](security/sli-slo-model.md) — SLIs, SLO targets, and error-budget burn-rate thresholds.
- [GOV-01 — WAF Pillar Mapping](governance/waf-pillar-mapping.md) — 5 WAF pillars mapped to platform components and spec citations.
- [QUAL-01 — Test Pyramid](quality/test-pyramid.md) — Five-tier test pyramid with relative volumes and tooling for the AMA platform.

## Technical-Experience

Technical-experience pages support onboarding and day-to-day comprehension for contributors who need narrative context around the diagrams.

- [Sequence — Monitoring → Risk Assessment → Communication](sequence/monitoring-risk-comms.md) — Existing narrative sequence for the end-to-end operational loop.
- [Capacity Model](capacity-model.md) — Supporting sizing assumptions and throughput notes.
- [Cosmos Partitioning](cosmos-partitioning.md) — Existing partitioning narrative pending migration into `deployment/`.
- [Middleware and Offline](spec-035-middleware-and-offline.md) — Existing middleware/offline architecture note pending migration.
- [EXP-01 — Ops Dashboard User Journey](accessibility/ops-dashboard-user-journey.md) — Incident Commander's ops dashboard journey with WCAG 2.2 AA touchpoint annotations.

## Adding New Diagrams

Use the [architecture quickstart](../../specs/001-arch-docs-refresh/quickstart.md) when adding a new Draw.io source, PNG export, Markdown page, and hash-manifest entry.

## Spec-to-Page Traceability

The table below is the canonical cross-reference map used by architecture reviewers.

| Spec | Spec Source | Primary Architecture Home |
| --- | --- | --- |
| spec-001 | [001-disaster-response-hub](../../specs/001-disaster-response-hub/spec.md) | [C4-L1 System Context](c4/system.md) |
| spec-003 | [003-rubric-gap-closure](../../specs/003-rubric-gap-closure/spec.md) | [C4-L2 Container](c4/container.md) |
| spec-004 | [004-actor-github-agents](../../specs/004-actor-github-agents/spec.md) | [C4-L3 Agents](c4/component-agents.md) |
| spec-005 | [005-data-source-governance](../../specs/005-data-source-governance/spec.md) | [SECTOR-03 Integration-Point Map](data/integration-point-map.md) |
| spec-006 | [006-data-ingestion-storage](../../specs/006-data-ingestion-storage/spec.md) | [C4-L3 Ingest](c4/component-ingest.md) |
| spec-007 | [007-simulation-tenant-isolation](../../specs/007-simulation-tenant-isolation/spec.md) | [SECTOR-01 Multi-Jurisdiction Tenancy](data/multi-jurisdiction-tenancy.md) |
| spec-008 | [008-communication-agent](../../specs/008-communication-agent/spec.md) | [SEQ-01 Alert Approval Publication](sequence/alert-approval-publication.md) |
| spec-009 | [009-evacuation-agent](../../specs/009-evacuation-agent/spec.md) | [SEQ-03 Evacuation Five-Stage Flow](sequence/evacuation-five-stage.md) |
| spec-010 | [010-monitoring-agent](../../specs/010-monitoring-agent/spec.md) | [SEQ-06 Graceful Degradation](sequence/graceful-degradation.md) |
| spec-011 | [011-resource-allocation-agent](../../specs/011-resource-allocation-agent/spec.md) | [OPS-02 Escalation Paths](operational/escalation-paths.md) |
| spec-012 | [012-risk-assessment-agent](../../specs/012-risk-assessment-agent/spec.md) | [RISK-01 Risk Register Lifecycle](operational/risk-register-lifecycle.md) |
| spec-013 | [013-root-readme](../../specs/013-root-readme/spec.md) | [Architecture Index](README.md) |
| spec-014 | [014-azure-openai-integration](../../specs/014-azure-openai-integration/spec.md) | [BUILD-01 Agent Runtime LLM Gateway](c4/agent-runtime-llm-gateway.md) |
| spec-015 | [015-performance-benchmarks](../../specs/015-performance-benchmarks/spec.md) | [SEC-04 SLI/SLO Model](security/sli-slo-model.md) |
| spec-016 | [016-automated-demo-script](../../specs/016-automated-demo-script/spec.md) | [DEPLOY-01 CI/CD Pipeline](deployment/cicd-pipeline.md) |
| spec-017 | [017-cd-pipeline](../../specs/017-cd-pipeline/spec.md) | [DEPLOY-01 CI/CD Pipeline](deployment/cicd-pipeline.md) |
| spec-018 | [018-aidr-guidance-integration](../../specs/018-aidr-guidance-integration/spec.md) | [C4-L3 Agents](c4/component-agents.md) |
| spec-019 | [019-aidr-additional-guidances](../../specs/019-aidr-additional-guidances/spec.md) | [OPS-01 AIIMS System Context](operational/aiims-system-context.md) |
| spec-020 | [020-disaster-mapper-ui](../../specs/020-disaster-mapper-ui/spec.md) | [EXP-01 Ops Dashboard User Journey](accessibility/ops-dashboard-user-journey.md) |
| spec-021 | [021-governance-dashboard](../../specs/021-governance-dashboard/spec.md) | [GOV-01 WAF Pillar Mapping](governance/waf-pillar-mapping.md) |
| spec-022 | [022-multi-jurisdiction-filter](../../specs/022-multi-jurisdiction-filter/spec.md) | [SECTOR-04 Jurisdiction Filter](data/jurisdiction-filter.md) |
| spec-023 | [023-dashboard-real-data](../../specs/023-dashboard-real-data/spec.md) | [DEPLOY-02 Azure Resource Topology](deployment/azure-resource-topology.md) |
| spec-024 | [024-simulation-control-chat](../../specs/024-simulation-control-chat/spec.md) | [C4-L3 Agents](c4/component-agents.md) |
| spec-025 | [025-agent-spec-compliance](../../specs/025-agent-spec-compliance/spec.md) | [SEQ-05 Audit Provenance](sequence/audit-provenance.md) |
| spec-026 | [026-sim-warp-playback](../../specs/026-sim-warp-playback/spec.md) | [OPS-03 PPRR Phase Overlay](operational/pprr-phase-overlay.md) |
| spec-027 | [027-spec-hardening](../../specs/027-spec-hardening/spec.md) | [SEC-03 Trust Boundary](security/trust-boundary.md) |
| spec-028 | [028-capstone-alignment](../../specs/028-capstone-alignment/spec.md) | [GOV-01 WAF Pillar Mapping](governance/waf-pillar-mapping.md) |
| spec-029 | [029-progressive-delivery-pipeline](../../specs/029-progressive-delivery-pipeline/spec.md) | [DEPLOY-01 CI/CD Pipeline](deployment/cicd-pipeline.md) |
| spec-030 | [030-llm-eval-framework](../../specs/030-llm-eval-framework/spec.md) | [C4-L3 Agents](c4/component-agents.md) |
| spec-031 | [031-simplify-cicd-pipeline](../../specs/031-simplify-cicd-pipeline/spec.md) | [DEPLOY-01 CI/CD Pipeline](deployment/cicd-pipeline.md) |
| spec-032 | [032-rubric-improvements](../../specs/032-rubric-improvements/spec.md) | [Capacity Model](capacity-model.md) |
| spec-033 | [033-maf-adoption](../../specs/033-maf-adoption/spec.md) | [BUILD-01 Agent Runtime LLM Gateway](c4/agent-runtime-llm-gateway.md) |
| spec-034 | [034-webapp-capstone-coverage](../../specs/034-webapp-capstone-coverage/spec.md) | [EXP-01 Ops Dashboard User Journey](accessibility/ops-dashboard-user-journey.md) |
| spec-035 | [035-webapp-capstone-closure](../../specs/035-webapp-capstone-closure/spec.md) | [Middleware and Offline](spec-035-middleware-and-offline.md) |
| spec-036 | [036-foundry-rag-grounding](../../specs/036-foundry-rag-grounding/spec.md) | [SEC-01 AU Residency and Data Classification](security/au-residency-data-classification.md) |
| spec-037 | [037-capstone-evidence-pack](../../specs/037-capstone-evidence-pack/spec.md) | [SEQ-05 Audit Provenance](sequence/audit-provenance.md) |

`spec-002` has no corresponding feature directory in this repository and is intentionally absent from the required inventory.
