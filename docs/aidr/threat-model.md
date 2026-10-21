# Threat Model — Disaster-Response Hub (consolidated)

**Last updated**: 2026-05-09 (spec-036 amendment cycle, Wave 5 final-sweep)
**Owner**: Security and Compliance cohorts
**Companions**: `docs/aidr/decisions/ADR-036-007-distributed-sequence-allocator.md`,
`docs/aidr/decisions/ADR-036-008-sli-thresholds-rationale.md`,
`docs/aidr/decisions/ADR-036-009-idempotency-cache-design.md`.

This document records the active threat-model deltas for the disaster-response hub. It is a
living document; entries are added when an ADR or amendment cycle introduces a new attack
surface or modifies an existing mitigation. Each row references the constitutional
invariant(s) it defends (see `.specify/memory/constitution.md` v1.2.0).

---

## 1. Active threats and mitigations

| ID | Threat | Surface | STRIDE | Likelihood | Impact | Mitigation | Constitutional ref |
|----|--------|---------|--------|------------|--------|------------|---------------------|
| TM-001 | Tenant isolation bypass via cache key collision | Cosmos / Redis caches | I, T | Medium | High | Tenant-scoped cache keys (FR-058); `tenant_isolation.violation` audit | III. Transparency and Auditability |
| TM-002 | Sub-agent stub leak into production | API runtime | T, I | Low | High | Contract test rejects stub markers in production code | I. Primacy of Life |
| TM-003 | Foundry carve-out drift (data-residency) | AOAI deployments outside AU | I, R | Medium | High | `infra/foundry/carveout-registry.json` + 6-monthly review workflow; `azure-openai-deployments.bicep` AVM | II. Australian Data Residency |
| TM-004 | Public-warning watermark stripped before broadcast | Synthetic delivery surface | T, R | Low | High | `public_warning_watermark_guard.py` + `public_artefact_guard.py` post-parse filters; `audit.watermark.applied` envelope | I. Primacy of Life |
| TM-005 | Telemetry-injection path emits real warnings | Live agents during exercise | I, T, E | Low | Catastrophic | `synthetic_signal=True` Pydantic Literal + `[SIMULATION]` chat-receipt prefix gate (FR-035); `audit_writer` records every emit | I. Primacy of Life |

---

## 2. Spec-036 amendment-cycle deltas

The Step 8 amendment cycle adds five new mitigated threats. Each row links to the ADR
and to the FR/checklist item that pins the mitigation.

### TM-036-001 — Sequence-collision under distributed audit writers

- **Surface**: `simulation_audit_entries` Cosmos container; FR-048 gap-free invariant.
- **STRIDE**: Tampering (T), Repudiation (R).
- **Threat**: Two API replicas allocate the same `sequence_number` for distinct audit
  envelopes, producing ambiguous ordering and an FR-049 export-failure footgun.
- **Mitigation**: Distributed sequence allocator backed by `simulation_audit_sequence_counters`
  with `If-Match` ETag optimistic concurrency (ADR-036-007). On 5-attempt exhaustion the
  writer fails closed to `simulation_audit_dlq` with `sequence_number = -1` and an
  `audit.sequence.uncertainty` envelope; a SEV-2 PagerDuty alert fires immediately
  (SLI-Z2). The compromised simulation is gated to read-only via the FR-066
  idempotency-cache state-machine until the gap is reconciled by manual replay.
- **Test evidence**: `tests/unit/test_audit_sequence_fr048_fail_closed_036.py`,
  `tests/unit/test_audit_writer_sequence_wireup_036.py`,
  `tests/unit/test_simulation_sequence_repository_036.py`.
- **Constitutional ref**: III. Transparency and Auditability.

### TM-036-002 — Idempotency replay across users (cross-user replay)

- **Surface**: `simulation_idempotency_cache` Cosmos container; FR-066 24-hour replay
  window.
- **STRIDE**: Spoofing (S), Information Disclosure (I), Elevation of Privilege (E).
- **Threat**: A replayed `Idempotency-Key` from another tenant or another user could
  return the cached response of a request the current principal is not authorised to
  see, leaking state across the trust boundary.
- **Mitigation**: Cache scope key is `(tenant_id, simulation_id, HTTP verb, route)` —
  not `idempotency_key` alone — and the partition key is `simulation_id`. Cross-user
  hits emit `audit.idempotency.replay_cross_user` and return HTTP 403 with the
  RFC 9457 `idempotency-key-cross-user` problem detail (ADR-036-009 §6). Per FR-051
  (Amendment E STRENGTHEN) the RBAC deny decision is authoritative on every request,
  even when an `Idempotency-Key` matches a prior success: `audit.rbac.unauthorized_attempt`
  is written **before** any cached replay is served.
- **Test evidence**: `tests/contract/test_idempotency_fail_closed_036.py`,
  `tests/contract/test_jcs_canonicalisation_036.py`,
  `tests/integration/test_rbac_enforcement_036.py`,
  `tests/unit/test_audit_envelope_amendment_036.py`.
- **Constitutional ref**: II. Australian Data Residency, III. Transparency and Auditability.

### TM-036-003 — Privilege escalation at coordinator-only routes

- **Surface**: Direct REST lifecycle endpoints (`pause`, `resume`, `abort`,
  `inject-telemetry`).
- **STRIDE**: Elevation of Privilege (E), Spoofing (S).
- **Threat**: An anonymous, observer-role, or cross-tenant principal mutating
  simulation state could disrupt an active exercise or, worse, deactivate a
  controller's safety-relevant pause action.
- **Mitigation**: All four mutating routes are guarded by
  `apps/api/app/api/dependencies/simulation_rbac.py` (T-M01–M04 + T-AA05). On every
  deny path the route emits `audit.rbac.unauthorized_attempt` carrying the principal's
  actual roles and the attempted route — written before any cached idempotency replay
  is served. The `lifecycle_guard` dependency further blocks state-incompatible
  mutations (e.g., `inject-telemetry` while `paused`) and emits
  `lifecycle.refused_while_paused` with HTTP 409 (FR-059 / Amendment F).
- **Test evidence**: `tests/integration/test_rbac_enforcement_036.py` (15 negative +
  positive tests), `apps/api/tests/test_lifecycle_endpoints.py`.
- **Constitutional ref**: III. Transparency and Auditability, IV. AAD-only Authentication.

### TM-036-004 — Silent SLI degradation past staging promotion

- **Surface**: SLIs Z1–Z5 (inject→fan-out latency, audit gap-free, throughput,
  map-overlay drift, sub-agent reply latency).
- **STRIDE**: Denial of Service (D), Repudiation (R).
- **Threat**: A regression that breaches one of the five plan-canonical SLIs but
  whose alert routing is stale, miswired, or sampled-out could promote to production
  unnoticed and cause an FR-053 graceful-degradation event under load.
- **Mitigation**: Each SLI carries four enforcement artefacts pinned by
  `contracts/sli-thresholds.md` and ADR-036-008:
  1. Bicep alert rule (`infra/bicep/modules/simulation-app-insights-alerts.bicep`) with
     Action Groups `ag-sim-sre-warn` (Slack) and `ag-sim-sre-prod` (PagerDuty).
  2. KQL template (`infra/observability/sli-kql.json`) with 100 % sampling for
     life-safety SLIs (Z1, Z2, Z5).
  3. `tests/staging_gates.py` refuses promotion on any breach.
  4. End-to-end contract test (`tests/e2e/test_staging_promotion_gates.py`) asserts the
     release gate refuses promotion on synthetic breach inputs.
- **Test evidence**: `tests/devops/test_observability_alerts_bicep.py`,
  `tests/e2e/test_staging_promotion_gates.py`,
  `tests/devops/test_sev0_egress_alert.py`.
- **Constitutional ref**: V. Graceful Degradation.

### TM-036-005 — Audit trail forgery via prompt-hash spoofing

- **Surface**: `injection.attempted` / `injection.success` / `injection.refused`
  audit envelopes; FR-065 universal `prompt_hash`.
- **STRIDE**: Tampering (T), Repudiation (R).
- **Threat**: An attacker (or a buggy client) could submit a synthetic-signal
  payload whose recorded `prompt_hash` does not correspond to any real artefact,
  defeating post-incident reconstruction.
- **Mitigation**: `prompt_hash_source` is a closed enum `{raw_user_input,
  canonical_llm_prompt, system_only}` (Amendment R / pass-1 Q5); the audit envelope
  schema rejects any other value. The hash is computed in
  `apps/api/app/services/simulation/audit_writer.py` over the canonical UTF-8
  byte representation of the chosen source. Any injection path missing
  `prompt_hash` is refused at envelope validation time — there is no nullable code
  path on the wire.
- **Test evidence**: `tests/unit/test_audit_envelope_prompt_hash_source.py`,
  `tests/unit/test_audit_envelope_amendment_036.py`,
  `apps/api/tests/test_compute_prompt_hash.py`.
- **Constitutional ref**: III. Transparency and Auditability.

---

## 3. Pending threats (open)

None as of 2026-05-09. The five spec-036 amendment-cycle deltas above are all
mitigated and have full test coverage.

---

## 4. Review cadence

- Quarterly review by Security cohort.
- Refresh on every ADR revision in `docs/aidr/decisions/`.
- Spec-036 carve-out review window: 6 months per Constitution v1.2.0
  Non-Negotiable #2 (next review: 2026-11-09).
