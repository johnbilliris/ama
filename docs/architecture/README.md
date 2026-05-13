# Architecture Navigation Index

Use this index to find the AMA architecture views by persona cluster while the spec-001 inventory is completed across phased delivery.

- [Architecture Known Gaps](known-gaps.md)
- [ADR Navigation Index](adr/README.md)

> **How to add a new diagram**: follow the [architecture quickstart](../../specs/001-arch-docs-refresh/quickstart.md).
> Pages marked [forthcoming](../../specs/001-arch-docs-refresh/tasks.md) are planned in later phases.

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

- [DEPLOY-01 — CI/CD Pipeline](deployment/cicd-pipeline.md) — GitHub Actions stages with what-if gates and manual approvals.
- [DEPLOY-02 — Azure Resource Topology](deployment/azure-resource-topology.md) — All named resources in the rg-ama resource group.
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

## Spec Cross-Reference Manifest
<!-- SPEC CROSS-REFERENCE MANIFEST -->
<!-- spec-cross-ref: spec-001 -->
<!-- spec-cross-ref: spec-002 -->
<!-- spec-cross-ref: spec-003 -->
<!-- spec-cross-ref: spec-004 -->
<!-- spec-cross-ref: spec-005 -->
<!-- spec-cross-ref: spec-006 -->
<!-- spec-cross-ref: spec-007 -->
<!-- spec-cross-ref: spec-008 -->
<!-- spec-cross-ref: spec-009 -->
<!-- spec-cross-ref: spec-010 -->
<!-- spec-cross-ref: spec-011 -->
<!-- spec-cross-ref: spec-012 -->
<!-- spec-cross-ref: spec-013 -->
<!-- spec-cross-ref: spec-014 -->
<!-- spec-cross-ref: spec-015 -->
<!-- spec-cross-ref: spec-016 -->
<!-- spec-cross-ref: spec-017 -->
<!-- spec-cross-ref: spec-018 -->
<!-- spec-cross-ref: spec-019 -->
<!-- spec-cross-ref: spec-020 -->
<!-- spec-cross-ref: spec-021 -->
<!-- spec-cross-ref: spec-022 -->
<!-- spec-cross-ref: spec-023 -->
<!-- spec-cross-ref: spec-024 -->
<!-- spec-cross-ref: spec-025 -->
<!-- spec-cross-ref: spec-026 -->
<!-- spec-cross-ref: spec-027 -->
<!-- spec-cross-ref: spec-028 -->
<!-- spec-cross-ref: spec-029 -->
<!-- spec-cross-ref: spec-030 -->
<!-- spec-cross-ref: spec-031 -->
<!-- spec-cross-ref: spec-032 -->
<!-- spec-cross-ref: spec-033 -->
<!-- spec-cross-ref: spec-034 -->
<!-- spec-cross-ref: spec-035 -->
<!-- spec-cross-ref: spec-036 -->
<!-- spec-cross-ref: spec-037 -->
<!-- spec-cross-ref: spec-038 -->
<!-- spec-cross-ref: spec-039 -->
<!-- spec-cross-ref: spec-040 -->
