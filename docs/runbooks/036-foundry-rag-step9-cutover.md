# Spec 036 — Step 9 cutover runbook (T145 + T146 + T147)

> **Owner**: Lead Architect (J.B.)
> **Audience**: SRE on-call rotation, Lead Architect, Comms Owner
> **Trigger**: Phase E final-canary green light (T142 dry-run + T145
> staging dry-run all PASS).

This runbook is the operator-facing procedure for the **final** cutover
step of spec 036 — the live env-var flip + atomic legacy-deletion PR
merge + redeploy. It complements
[`036-foundry-rag-gameday.md`](./036-foundry-rag-gameday.md) which
covers post-cutover game-days.

The actions below run **after** T142–T144 have landed on
`036-foundry-rag-grounding` and **after** the deletion PR for T146 has
been opened on `036-legacy-deletion`.

## 0. Pre-flight checklist

Before entering the change window:

- [ ] `pwsh ./infra/scripts/simulation-final-canary-dry-run.ps1` exits 0.
- [ ] `pwsh ./infra/scripts/canary-rollback-drill.ps1 -Agent simulation`
      exits 0 (rollback path verified).
- [ ] `pytest tests/contract tests/integration tests/unit -q` is green
      on `036-foundry-rag-grounding`.
- [ ] The deletion PR on `036-legacy-deletion` is open as DRAFT (not
      merged yet) and has CI green with the `from openai` lint binding.
- [ ] On-call SRE has access to:
      - Application Insights workbook *Foundry RAG cutover overview*.
      - The four scheduled-query alerts:
        `foundry-rag-gateway-deny`, `foundry-rag-citation-drop`,
        `foundry-rag-equivalence-regression`,
        `foundry-rag-offline-cache-ttl`.
      - The `audit_replay_fidelity.kql` query bound as a 24 h alert.
- [ ] Comms Owner posts a #change-window banner: 60 min planned, 90 min
      hard cap.

## 1. Live env-var flip (T145, FR-RAG-FM-06, FR-RAG-SIM-01..06)

```powershell
# 1a. Ensure the environment is the production target.
azd env select prod

# 1b. Flip the SimulationController flag.
azd env set FOUNDRY_RAG_ENABLED_AGENTS "monitoring,risk,evacuation,resource,communication,simulation"

# 1c. Roll the API + agents revisions.
azd deploy api
azd deploy agents
```

**Expected**: every agent revision resolves
`FOUNDRY_RAG_ENABLED_AGENTS` to all six agents within ≤ 5 min. If any
revision fails the readiness probe, **rollback immediately** with:

```powershell
azd env set FOUNDRY_RAG_ENABLED_AGENTS "monitoring,risk,evacuation,resource,communication"
azd deploy api
azd deploy agents
pwsh ./infra/scripts/canary-rollback-drill.ps1 -Agent simulation
```

## 2. Atomic legacy-deletion PR merge (T146)

After T145 is green for at least 30 minutes (or the canary settles per
spec-029 progressive-delivery guidance) — merge the deletion PR.

```bash
# Reviewer: confirm the PR diff matches the T146 charter:
#   - Removes from openai imports from 3 anchor files.
#   - Collapses _generate_with_fallback to template-only branch.
#   - Moves infra/modules/azure-openai.bicep → legacy/.
#   - Drops LEGACY_AZURE_OPENAI escape hatch.
#   - Unmarks pytest.mark.skip on tests/contract/test_no_openai_imports.py.
#   - main.bicep no longer references azure-openai.bicep.

gh pr merge --squash <PR-NUMBER>
```

**Expected**: the merge to `036-foundry-rag-grounding` (or `main` after
that branch merges) keeps CI green with the `from openai` lint
**binding**. If the lint trips on a residual import, **revert** the
merge commit (`gh pr revert`) and surface the offending file to the
Phase A team for a clean-up patch.

## 3. `azd up` redeploy (T147)

```powershell
# 3a. Staging first.
azd env select staging
azd up

# 3b. Smoke-test staging.
pwsh ./infra/scripts/azd-up-smoke-test.ps1 `
    -BaseUrl "https://staging-ama-api.example.com" `
    -AppInsightsAppId "<staging-appi-id>" `
    -SimulationChatUrl "https://staging-ama-api.example.com/v1/sim/<sim-id>/chat/stream" `
    -Bearer "<staging-token>"

# 3c. Production.
azd env select prod
azd up

# 3d. Smoke-test production.
pwsh ./infra/scripts/azd-up-smoke-test.ps1 `
    -BaseUrl "https://prod-ama-api.example.com" `
    -AppInsightsAppId "<prod-appi-id>" `
    -SimulationChatUrl "https://prod-ama-api.example.com/v1/sim/<sim-id>/chat/stream" `
    -Bearer "<prod-token>"
```

**Expected**: each smoke-test invocation exits 0 and prints the four
verified `/healthz` fields.

If `/healthz` does not yet expose `rag_used` / `corpus_build_sha` /
`embedding_model_id` / `alias_active_index`, the API revision
post-merge has not been redeployed — re-run `azd deploy api` and try
again.

## 4. Post-cutover validation

Within 1 hour of the cutover:

- [ ] `audit_trail_completeness.kql` (T099) returns zero rows missing
      `rag_used`.
- [ ] `audit_replay_fidelity.kql` (T144) shows ≥ 95 % replay fidelity
      for the post-cutover window.
- [ ] No `foundry-rag-citation-drop` alert has fired.
- [ ] No `foundry-rag-equivalence-regression` alert has fired.
- [ ] At least one Simulation chat turn shows an `event: citation`
      SSE line (manual sample).

## 5. Rollback ladder

| Symptom | Severity | Action |
|---------|----------|--------|
| `/healthz` returns 5xx after `azd up` | Sev-1 | Revert API revision; redeploy previous tag. |
| `rag_used=false` on every grounded call | Sev-1 | Toggle `FOUNDRY_RAG_ENABLED_AGENTS` to drop simulation; re-investigate. |
| Citation envelope schema drift detected | Sev-2 | Re-run `pytest tests/contract/test_citation_envelope.py`; rollback if drift confirmed. |
| Replay fidelity < 95 % | Sev-2 | Pause new flips; investigate `replay_key()` regression. |
| Foundry quota 429s sustained | Sev-2 | Spec-014 fallback chain now template-only; raise capacity ticket. |

## References

- T145 dry-run: `infra/scripts/simulation-final-canary-dry-run.ps1`
- T147 smoke-test: `infra/scripts/azd-up-smoke-test.ps1`
- Game-day runbook: `docs/runbooks/036-foundry-rag-gameday.md`
- KQL alerts: `tests/audit/audit_trail_completeness.kql`,
  `tests/audit/audit_replay_fidelity.kql`
- Plan: `specs/036-foundry-rag-grounding/plan.md` §Phasing E
