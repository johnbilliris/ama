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

## Resolved Gaps

| Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
| --- | --- | --- | --- | --- |
| _(none yet)_ | — | — | — | — |
