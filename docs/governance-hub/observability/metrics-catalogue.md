# Metrics catalogue

> Operational metric inventory for the AMA platform. The **executive roll-up**
> view of these metrics is consolidated into the
> [Executive KPI Surface](../executive-kpi/surface.md) (spec-037, FR-022). This
> file retains the operational metric-inventory role per analyser finding I5 +
> the FR-022 amendment ("Deprecation MAY be section-scoped").

## Spec-037 — Capstone Evidence Pack metrics (T048, T065)

| Metric | Type | Dimensions | Owner | Alert threshold | Source-of-truth |
|---|---|---|---|---|---|
| `evidence_pack.publication.duration_seconds` | gauge (seconds) | `artefact_id`, `publication_id`, `environment` | SRE Engineer | p95 > 300s over 24h | `apps/api/app/services/governance/evidence_pack_writer.py` |
| `evidence_pack.manual_row_ratio` | gauge (0..1) | `artefact_id`, `publication_id`, `environment` | Compliance Auditor | ratio > 0.5 without `auditor_signoff` (publication-gate failure) | `apps/api/app/services/governance/manual_row_ratio.py` |
| `evidence_pack.publication_gate.failure_rate` | counter (failures/24h) | `gate_check`, `environment` | SRE Engineer | failure_rate > 5% / 24h | `scripts/evidence_pack_gate/` |

These three metrics emit through the existing OpenTelemetry pipeline configured
by `apps/api/app/main.py` and route to the existing AMA App Insights workspace
in `rg-ama` (AU East). **No new App Insights workspace is provisioned.**

Targets and rationale per `specs/037-capstone-evidence-pack/plan.md` § Performance Goals:

- Publication duration median ≤ 60 s, p95 ≤ 180 s, alert if p95 > 300 s.
- Publication-gate CI job wall-clock ≤ 3 minutes.
- Read-API p95 ≤ 200 ms per artefact retrieval (Cosmos cache hit) with cold-source fallback ≤ 1.5 s.

> **Executive view**: see [`Executive KPI Surface`](../executive-kpi/surface.md)
> for the per-criterion leading + lagging KPI ladder. The metrics above are the
> operational telemetry that powers the surface; they are NOT directly inserted
> as `kpi_row` entries (the `kpi_row.capstone_criterion` enum is restricted to
> the five SC-CAP criteria — see T065 acceptance note).
