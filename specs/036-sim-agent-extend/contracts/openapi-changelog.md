# OpenAPI Changelog — `openapi-simulation.yaml`

This file is the durable migration ledger for breaking and notable
non-breaking changes to the spec-036 Telemetry-Injection Simulation
OpenAPI contract. Each row documents the version delta, the
business-driver reference, and an SDK migration recipe.

> **Co-authored-by**: Copilot <223556219+Copilot@users.noreply.github.com>

---

## v0.3.0 — Cycle 2 amendment cycle (BREAKING)

**Date**: 2026-05-22
**Driver**: spec-036 Cycle 2 amendments A2-01..A2-08
**ADR**: [ADR-036-010 — Cycle 2 Amendment Cycle](../../docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md)

### Breaking changes

| # | Schema | Before (v0.2.x) | After (v0.3.0) | Driver |
|---|--------|-----------------|----------------|--------|
| 1 | `TelemetryInjectionAck.triggered_sub_agents` items | `string` (sub-agent name) | `TriggeredSubAgent` object `{correlation_id, dispatch_status, sub_agent, trigger_source}` | A2-01 / FR-067 |
| 2 | `TelemetryInjectionAck.degraded_dispatch` | (absent) | `boolean` (required, defaults `false`) | A2-04 / FR-068 |
| 3 | Audit-envelope `sub_agent` enum | 7-kebab `{communication, evacuation, health, monitoring, logistics, operations, planning, resource-allocation, risk-assessment}` | 9-PascalCase `{Comms, Evac, Health, Intel, Logistics, Operations, Planning, Resource, Risk}` for **new writes** | A2-07 |
| 4 | Audit-envelope entry types | 24 enum members | 25 enum members (NEW: `signal_pipeline.dispatch_failed`) | A2-04 / FR-068 |

### Non-breaking additions

| # | Surface | Addition |
|---|---------|----------|
| 5 | New schema `TriggeredSubAgent` | `{correlation_id: uuid, dispatch_status: "acknowledged"\|"failed"\|"timed_out", sub_agent: PascalCaseEnum, trigger_source: "primary"\|"cascade"}` |
| 6 | New schema `SignalPipelineDispatchFailedAuditDetails` | Body of the 25th audit envelope; arrays canonicalised under RFC 8785 JCS |
| 7 | New SLI rows | Z6 (P95 sub-agent latency) + Z7 (map-overlay drift) added to `infra/observability/sli-kql.json` with `sample_count` column |
| 8 | New middleware allow-list | `SPEC_036_PROBLEM_JSON_ROUTES` exposes 5 routes that emit RFC 9457 problem+json responses on 4xx and 5xx |

### Deprecation notices

| # | Item | Window | Replacement |
|---|------|--------|-------------|
| D-1 | Reading legacy 7-kebab `sub_agent` audit rows via `_KEBAB_TO_PASCAL` shim | Until Cycle 1 evidence-retention window expires (≥ 12 months under FR-048) | New writes in 9-PascalCase only |
| D-2 | Cascade `fan_out_rules:` block in `apps/api/app/config/cascade_rules.yaml` | Removed in v0.3.0 (was unused since Cycle 1; `CASCADE_MATRIX` is canonical) | `packages/domain/src/domain/sim_cascade_matrix.py::CASCADE_MATRIX` |
| D-3 | `cascade.depth2_refused` placeholder `"sequence_number": 1` literal | Removed in v0.3.0 | Gap-free allocator (ADR-036-007) is the sole source of truth |

### SDK migration recipe (consumer steps)

For each consumer of the Telemetry-Injection contract:

1. **Bump the pinned `openapi-simulation.yaml` reference** to v0.3.0
   in your client codegen (e.g. `pnpm exec openapi-typescript`,
   `dotnet kiota`, `python -m openapi_python_client`).
2. **Update `TelemetryInjectionAck.triggered_sub_agents` consumers**.
   In TypeScript:

   ```typescript
   // Before (v0.2.x)
   const names: string[] = ack.triggered_sub_agents;
   // After (v0.3.0)
   const triggered = ack.triggered_sub_agents;  // TriggeredSubAgent[]
   const names = triggered.map(t => t.sub_agent);
   const failed = triggered.filter(t => t.dispatch_status === "failed");
   ```

3. **Surface `degraded_dispatch=true`** in your operator UI. When the
   degraded-dispatch banner shows, point operators to the audit
   timeline filtered on `entry_type == "signal_pipeline.dispatch_failed"`.
4. **Update Application Insights workbooks** to query the new
   `signal_pipeline.dispatch_failed` entry type (KQL filter:
   `customEvents | where name == "audit.signal_pipeline.dispatch_failed"`).
5. **If you author audit envelopes directly** (rare — most consumers
   are read-only), switch new writes to the 9-PascalCase `sub_agent`
   enum. Historical kebab-case rows remain readable via the
   `_KEBAB_TO_PASCAL` shim.
6. **Re-run contract tests** against v0.3.0 fixtures:
   - `pytest tests/contract/test_openapi_v030_schema.py`
   - `pytest tests/contract/test_audit_envelope_entry_25_schema.py`
   - `pytest tests/contract/test_dispatch_failed_body_audit_byte_equality.py`

### Backward-compatibility guarantees

- **Read tolerance**: any audit envelope written before v0.3.0
  remains readable via the `_KEBAB_TO_PASCAL` shim in
  `apps/api/app/services/simulation/audit_writer.py`. The shim is
  read-only and never mutates persisted data.
- **Idempotency-cache compatibility**: ADR-036-009 idempotency cache
  entries from v0.2.x are case-insensitive on the verb tuple and
  remain valid through the 24-hour TTL window after deployment.
- **Sequence-number invariant**: the gap-free allocator
  (ADR-036-007) is unchanged; v0.3.0 only strengthens the writer-side
  guard against caller-supplied placeholders.

---

## v0.2.0 — Cycle 1 closure (REFERENCE — pre-existing)

**Date**: 2026-04-30
**Driver**: spec-036 Cycle 1 final-sweep verdict 🟢 GREEN
**ADR**: ADR-036-001..ADR-036-009

This row is intentionally brief. The Cycle 1 contract was the
foundational shape; consult `specs/036-sim-agent-extend/spec.md` and
the per-feature ADRs for full provenance.

---

## Migration timeline

| Window | Action | Owner |
|--------|--------|-------|
| T-0 (Cycle 2 PR merged) | v0.3.0 deployed to staging; consumers receive deprecation notice | Spec-036 release manager |
| T+7 days | Consumers complete SDK migration recipe | Each consumer team |
| T+14 days | v0.3.0 promoted to prod after staging gates green for 7 consecutive days | Release manager + observability engineer |
| T+12 months | Re-evaluate `_KEBAB_TO_PASCAL` shim retirement (after Cycle 1 evidence-retention window) | Compliance auditor |

---

## References

- ADR-036-010 (Cycle 2 amendment cycle, primary) — `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md`
- Spec — `specs/036-sim-agent-extend/spec.md`
- Plan §§ C2.1-C2.6 — `specs/036-sim-agent-extend/plan.md`
- Data-model §11 — `specs/036-sim-agent-extend/data-model.md`
- Audit envelope — `specs/036-sim-agent-extend/contracts/audit-envelope.md`
- SLI thresholds — `specs/036-sim-agent-extend/contracts/sli-thresholds.md`
- Quality checklist — `specs/036-sim-agent-extend/checklists/quality.md`
- RFC 8785 (JCS) — <https://www.rfc-editor.org/rfc/rfc8785>
- RFC 9457 (Problem Details) — <https://www.rfc-editor.org/rfc/rfc9457>
- W3C TraceContext — <https://www.w3.org/TR/trace-context/>
