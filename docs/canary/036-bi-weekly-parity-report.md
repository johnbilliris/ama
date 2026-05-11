# Spec 036 — Bi-weekly parity report (FR-RAG-FM-06, Risk R11)

> **Purpose**: every two weeks, the per-agent canary gate is re-run against
> the latest production fixture and a parity report is opened against the
> grounded-vs-legacy decision pair. This is the **post-cutover monitor**
> for FR-023 / spec-033 — the bar that says "Foundry-grounded path still
> behaves like the legacy path within tolerance".

## What gets measured

For each grounded agent (Monitoring, Risk Assessment, Evacuation, Resource
Allocation, Communication, plus Simulation Controller):

* **Decision equivalence** ≥ 95% — same `decision` value across both runners.
* **Schema equivalence** == 100% — same set of top-level keys.
* **Citation fidelity** ≥ 0.7 — fraction of citations that resolve to a
  retrieved chunk; binding gate lands in Phase E3.
* **Hallucinated-citation count** == 0 across the full fixture.

## When it runs

A scheduled GitHub Actions workflow runs `per_agent_canary_gate.py` against
each agent's spec036 fixture every 14 days. Failures open an issue tagged
`036/parity-report`. The CI logs include the report JSON for archival.

## Where the artefact lives

* The CI log → uploaded to Application Insights as a custom event
  (`spec036_parity_report`).
* A summary issue is opened automatically when any of the four metrics
  regresses below threshold.
* The GitHub Actions workflow is wired in Phase E2 alongside the broader
  parity-test review thread (T127).

## Phase C deliverable

This document is the **specification** of the bi-weekly review; the actual
GitHub Actions schedule + custom-event emission is Phase E2 work
(`/.github/workflows/036-parity-report.yml`). The canary-gate harness +
citation-fidelity signal are already authored (T100,
`apps/eval-runner/src/ama_eval/citation_fidelity.py`).
