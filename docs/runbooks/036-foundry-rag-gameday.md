# Spec 036 — Foundry RAG cutover game-day runbook (T138–T141)

> **Owner**: Lead Architect (J.B.)
> **Audience**: SRE on-call rotation, Lead Architect, Comms Owner
> **Cadence**: 1 dry-run before cutover; 1 live game-day immediately
> after enabling the per-agent feature flag at 25%; quarterly thereafter
> (paired with the Spec-035 quarterly chaos drill).
> **Scope**: 3 game-day scenarios + a "post-incident replay-within-48h"
> template that closes every game-day.

This runbook is the operator-facing procedure that complements the
SRE-facing alerts in `infra/bicep/modules/foundry-rag-cutover-alerts.bicep`.
Every alert in that module has a numbered playbook step in this document.

## 0. Pre-flight (every game-day)

1. Confirm the active branch is `036-foundry-rag-grounding` (or `main`
   post-cutover) and that `pwsh scripts/verify-carveout.ps1` exits 0.
2. Confirm `python tools/lint/check_rag_optout_bindings.py` exits 0.
3. Confirm the on-call SRE has access to:
   - Application Insights workbook **Foundry RAG cutover overview**.
   - The four scheduled-query alerts:
     `foundry-rag-gateway-deny`, `foundry-rag-citation-drop`,
     `foundry-rag-equivalence-regression`, `foundry-rag-offline-cache-ttl`.
   - The per-agent feature flags surface
     (`apps/agents/maf_runtime/feature_flags.py`).
4. Pre-stage the canary rollback CLI:
   `pwsh infra/scripts/canary-rollback-drill.ps1 -Agent <name>`.
5. Comms Owner posts a #change-window banner in the on-call channel with the
   game-day scenario name + planned duration + rollback DRI.

## Scenario 1 — Foundry endpoint flap (FR-RAG-FM-04, FR-RAG-FM-06)

**Trigger**: deliberate fault — toggle the per-agent flag for one life-safety
agent (recommended: `MonitoringAgent`) for 5 minutes while injecting a 503
from the Foundry chat client via the `FR-RAG-FM-07` test seam.

**Expected behaviour**:

1. Within 30 s, retrieval-client fail-closed kicks in: agent emits the
   recommendation **without** citations, with `confidence: low` and
   `degraded_mode: retrieval-unavailable` on the SSE stream.
2. The `<DegradedModeBadge mode="retrieval-unavailable" />` renders red on
   every operator surface that consumed the agent's stream.
3. `customMetrics.citation_count == 0` triggers
   `foundry-rag-citation-drop` alert within 5 minutes.
4. Audit records carry `rag_used=false`,
   `rag_optout_reason="retrieval-unavailable"` and the same
   `correlation_id` as the original request.

**Pass criteria**:

- [ ] No agent crash, no silent fall-through to a non-grounded response
      with `confidence: high`.
- [ ] Operator UI surfaces the badge within 1 second of the SSE event.
- [ ] Alert page reaches on-call SRE within the 5-minute SLO.
- [ ] Post-incident audit replay (`/audit/replay`) reproduces the byte-for-byte
      degraded response from archived events.

**Rollback** (always): re-toggle the flag to `enabled` and confirm the
next request emits ≥ 1 citation event. Drill the rollback CLI even if the
agent self-heals.

## Scenario 2 — Offline-cache TTL exhaustion (FR-RAG-LS-02, R-07)

**Trigger**: deliberately stale-fixture a Field-Coordinator-aligned tenant
by overriding `OFFLINE_CACHE_GENERATED_AT` to `now - 12 days` so the cache
crosses the 11-day stale-warning but is still inside the 14-day TTL.

**Expected behaviour**:

1. `<DegradedModeBadge mode="stale-cache" ttlDaysRemaining="2" />` renders
   orange.
2. `customMetrics.offline_cache_ttl_days_remaining == 2` triggers
   `foundry-rag-offline-cache-ttl` alert within 15 minutes.
3. Telemetry gauge stays under 3 days remaining; SRE pages the
   Field-Coordinator owner to schedule a re-sync.
4. After re-sync, audit-spool drain completes within 60 seconds (SC-009)
   preserving original timestamps; verify with
   `python -m pytest tests/integration/test_offline_cache.py::test_audit_spool_drain_within_60s -q`.

**Pass criteria**:

- [ ] Banner copy matches the exact text in
      `packages/ui/src/components/citation/degraded-mode-badge.tsx`.
- [ ] Alert page reaches on-call SRE within the 15-minute SLO.
- [ ] Re-sync replays every spooled audit record (no loss, no reorder).
- [ ] `verify-offline-cache.ps1` passes for the new bundle on the device.

**Rollback**: rotate `OFFLINE_CACHE_GENERATED_AT` back to today's date and
confirm the badge clears.

## Scenario 3 — Equivalence regression on per-agent canary (FR-RAG-FM-06)

**Trigger**: shadow-traffic the `CommunicationAgent` at 25 % and inject a
prompt-template diff that drops `decision_equivalence` below 0.95 over a
30-minute rolling window.

**Expected behaviour**:

1. Within 15 minutes, `foundry-rag-equivalence-regression` alert fires for
   `agent_name=CommunicationAgent`.
2. Per-agent canary gate
   (`apps/eval-runner/src/ama_eval/per_agent_canary_gate.py`) blocks
   any further promotion past 25 %.
3. SRE runs `pwsh infra/scripts/canary-rollback-drill.ps1 -Agent CommunicationAgent`,
   which flips the flag back to `legacy_only` for that agent within 60 s.
4. Bi-weekly parity report (`docs/reports/spec036-bi-weekly-parity.md`)
   carries the regression as a follow-up item with an owner.

**Pass criteria**:

- [ ] Alert fires within 15 min of injection.
- [ ] Rollback CLI returns `[OK]` and the next 100 requests show
      `legacy_or_foundry: legacy` in audit records.
- [ ] No life-safety directive was issued during the 15-minute regression
      window without a citation. (Verified by querying
      `customEvents | where decision_equivalence < 0.95 and
      requires_citation == false`.)

**Rollback**: per CLI above. Promotion past 25 % is blocked until the
prompt-template diff is reverted **and** equivalence ≥ 0.95 over a fresh
30-minute window.

## 4. Post-incident replay-within-48h template

For every game-day scenario (and every real production incident) the
following replay artefact MUST exist within 48 hours of the close of the
incident.

```yaml
# docs/runbooks/spec036/incidents/<incident-id>/replay.yml
incident_id: GD-2026-05-08-001
spec: 036
scenario: scenario-1-endpoint-flap
opened_at: 2026-05-08T05:00:00Z
closed_at: 2026-05-08T05:25:00Z
participants: [sre-oncall, lead-architect, comms-owner]
artefacts:
  alert_screenshot: artifacts/...
  workbook_screenshot: artifacts/...
  audit_replay_log: artifacts/replay-<correlation-id>.json
  rollback_cli_output: artifacts/canary-rollback-...txt
findings:
  - what_worked: "..."
  - what_didnt: "..."
  - follow_up_actions: [{ owner: ..., due: ..., issue: ... }]
sign_off:
  lead_architect: J.B. 2026-05-09
  sre_dri: ...
```

The replay file lives under `docs/runbooks/spec036/incidents/<incident-id>/`
and is committed to the repo within 48 hours. CI does NOT block on the
replay file itself, but the bi-weekly parity report
(`docs/reports/spec036-bi-weekly-parity.md`) lists every game-day held in
the previous fortnight; absence of a replay file for a held game-day is a
follow-up action assigned to the on-call SRE.

## 5. Frequency

| Cadence | Scope |
|---------|-------|
| Pre-cutover | Scenarios 1, 2, 3 dry-run on `036-foundry-rag-grounding`. |
| Cutover day | Scenarios 1 + 3 live at the 25 % canary checkpoint. |
| Quarterly | All 3 scenarios; pair with Spec 035 quarterly chaos drill. |
| Ad-hoc | Triggered by any **Sev-1** Foundry incident or carve-out drift. |

## 6. Definition of "done" for a Phase D game-day

A game-day is considered complete only when **all** of the following are
true:

- [ ] Each scenario reached its declared pass criteria.
- [ ] Each in-scope alert fired within its SLO and was acknowledged.
- [ ] Rollback CLI was exercised at least once (drill — not because the
      scenario forced it).
- [ ] A `replay.yml` artefact was committed within 48 h.
- [ ] The bi-weekly parity report was updated.
- [ ] Any follow-up actions were filed as GitHub issues with owners + due
      dates.

## References

- Plan: `specs/036-foundry-rag-grounding/plan.md` §Phasing D
- Quickstart: `specs/036-foundry-rag-grounding/quickstart.md`
- Alerts: `infra/bicep/modules/foundry-rag-cutover-alerts.bicep`
- Canary rollback: `infra/scripts/canary-rollback-drill.ps1`
- Offline-cache verify: `infra/scripts/verify-offline-cache.ps1`
- RAG-OPTOUT lint: `tools/lint/check_rag_optout_bindings.py`
- Persona traceability: `specs/036-foundry-rag-grounding/persona-traceability.md`
- Constitution: `.specify/memory/constitution.md` (Principle I, §IV)
