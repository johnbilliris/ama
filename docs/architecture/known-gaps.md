# Architecture Known Gaps

> Maintained as part of spec-001 (FR-023). CI fails if any row has an empty Follow-up Task Ref.
> See [quickstart.md](../../../specs/001-arch-docs-refresh/quickstart.md) for how to add an entry.

## Open Gaps

| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
| --- | --- | --- | --- | --- |
| BICEP-DEP-01 | Bicep module dependency graph deferred; requires auto-generation tooling from `infra/bicep/`; not hand-authored | <https://github.com/johnbilliris/ama/issues/new?title=BICEP-DEP-01+Bicep+module+dependency+graph> | 2026-05-11 | Open |
| DUPE-036 | Two `036-*` spec directories observed; counted as one shipped spec for cross-ref purposes; deduplication handled by `check_spec_cross_refs.py` prefix logic | `tasks.md#T061` | 2026-05-11 | Open |
| CAP-MIG-01 | `capacity-model.md` at repo root not yet migrated to `deployment/` or `governance/` subdir; kept in place with front-matter banner per FR-005 | `tasks.md#T067` | 2026-05-11 | Open |
| COSM-MIG-01 | Root-level `cosmos-partitioning.md` not yet migrated; superseded by `deployment/cosmos-partitioning.md` (T060); root copy kept with redirect banner | `tasks.md#T068` | 2026-05-11 | Open |
| MDW-MIG-01 | Root-level `spec-035-middleware-and-offline.md` not yet migrated to a named view-type subdir; kept with front-matter banner per FR-005 | `tasks.md#T069` | 2026-05-11 | Open |
| FOUNDRY-REGION | Specific non-AU Foundry inference regions not hard-coded in SEC-01 diagram; mechanism-zone label used per FR-016 and constitution NN-2; registry at `infra/parameters/foundry-carveout.yaml` is authoritative | `tasks.md#T044` | 2026-05-11 | Open |
| SPEC-037 | spec-037 has no confirmed architecture page home; to be mapped during implementation or formally archived if no matching component exists | `tasks.md#T064` | 2026-05-11 | Open |
| C4-L4 | C4 Level 4 (Code) diagrams deferred; to be added only if L3 Component diagrams lack sufficient clarity for any container; per spec assumption | `tasks.md#T071` | 2026-05-11 | Open |
| LYCHEE-CFG | `.lychee.toml` exclude patterns for spec deep-link anchor fragments not yet authored; RSK-03 mitigation pending; lychee may emit false positives on `specs/036-*/spec.md#fr-*` anchors | `tasks.md#T063` | 2026-05-11 | Open |
| WCAG-AUDIT-FULL | WCAG coverage map limited to documenting already-implemented accessibility features; full independent audit deferred to a separate accessibility sprint per RQ-10 | `tasks.md#T054` | 2026-05-11 | Open |
| SPEC-RANGE-VERIFY | Spec numbers 002–009, 011–014, 016, 018, 021, 023, 026–027, 031–034 require verified architecture citation homes; RSK-06 mitigation — if `check_spec_cross_refs.py` reports any missing after Phase 10, add individual known-gaps entries per spec | `tasks.md#T064` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SECTOR-01 | SECTOR-01 multi-jurisdiction-tenancy diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T021` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SECTOR-02 | SECTOR-02 ingestion-data-flow diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T022` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SECTOR-03 | SECTOR-03 integration-point-map diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T023` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SECTOR-04 | SECTOR-04 jurisdiction-filter diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T024` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SEQ-03 | SEQ-03 evacuation-five-stage diagram is skill-fallback authored (drawio CLI unavailable); PNG is a placeholder; requires Draw.io authoring before merge | `tasks.md#T006` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SEQ-04 | SEQ-04 recovery-transition diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T007` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SEQ-01 | SEQ-01 alert-approval-publication diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T011` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SEQ-02 | SEQ-02 cross-agency-recommendation diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T012` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SEQ-06 | SEQ-06 graceful-degradation diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T013` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-OPS-01 | OPS-01 aiims-system-context diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T014` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-OPS-02 | OPS-02 escalation-paths diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T015` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SEC-01 | SEC-01 au-residency-data-classification diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T044` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SEC-02 | SEC-02 rbac-matrix diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T045` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SEC-03 | SEC-03 trust-boundary diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T046` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SEC-04 | SEC-04 sli-slo-model diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T047` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SEQ-05 | SEQ-05 audit-provenance diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T048` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-DEPLOY-01 | DEPLOY-01 cicd-pipeline diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T055` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-DEPLOY-02 | DEPLOY-02 azure-resource-topology diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T056` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-DEPLOY-03 | DEPLOY-03 cosmos-partitioning diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T057` | 2026-05-11 | Open |

| DRAWIO-FALLBACK-C4-L1 | C4-L1 system context diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T029` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-C4-L2 | C4-L2 container diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T030` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-C4-L3-API | C4-L3-API component-api diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T031` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-C4-L3-Web | C4-L3-Web component-web diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T032` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-C4-L3-Agents | C4-L3-Agents component-agents diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T033` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-C4-L3-Ingest | C4-L3-Ingest component-ingest diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T034` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-GOV-01 | GOV-01 waf-pillar-mapping diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T035` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-RISK-01 | RISK-01 risk-register-lifecycle diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T074` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-OPS-03 | OPS-03 pprr-phase-overlay diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T075` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-SECTOR-05 | SECTOR-05 cross-sector-touchpoints diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T076` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-BUILD-01 | BUILD-01 agent-runtime-llm-gateway diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T077` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-QUAL-01 | QUAL-01 test-pyramid diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T078` | 2026-05-11 | Open |
| DRAWIO-FALLBACK-EXP-01 | EXP-01 ops-dashboard-user-journey diagram is skill-fallback authored; PNG is a placeholder | `tasks.md#T079` | 2026-05-11 | Open |

## Resolved Gaps

| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
| --- | --- | --- | --- | --- |
| _(none yet)_ | — | — | — | — |
