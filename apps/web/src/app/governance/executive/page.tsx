/**
 * T043 — Executive KPI page (Server Component).
 *
 * Composes the spec-035 governance shell, fetches all 5 artefact summaries
 * + the Executive KPI Surface envelope, and renders:
 *   - ManualRowRatioStrip across the top (FR-021 + FR-037 + NN-3)
 *   - StaleTelemetryBanner when the health endpoint reports `degraded`
 *   - KpiLadder grouped by capstone criterion (FR-019 + FR-020)
 *
 * Citations: FR-021, SC-008, SC-009, RES-03.
 */
import * as React from 'react';
import {
  getArtefact,
  getHealth,
  listArtefacts,
} from '@/lib/governance/evidence-pack/client';
import { ManualRowRatioStrip } from './_components/ManualRowRatioStrip';
import { KpiLadder, type KpiSummary } from './_components/KpiLadder';
import { StaleTelemetryBanner } from './_components/StaleTelemetryBanner';

export const dynamic = 'force-dynamic';

export default async function ExecutiveKpiPage(): Promise<React.ReactElement> {
  const [summaries, health, kpiArtefact] = await Promise.all([
    listArtefacts().catch(() => []),
    getHealth().catch(() => null),
    getArtefact('executive_kpi_surface').catch(() => null),
  ]);

  const ratios = summaries.map((s) => ({
    artefact_id: s.artefact_id,
    manual_row_ratio: s.manual_row_ratio,
  }));

  const stale = health?.overall_status === 'degraded' || health?.overall_status === 'unhealthy';
  const lastObserved =
    health?.artefacts.find((a) => a.artefact_id === 'executive_kpi_surface')?.last_publication_utc ??
    null;

  const kpis: KpiSummary[] = (kpiArtefact?.rows ?? []) as unknown as KpiSummary[];

  return (
    <main className="governance-executive">
      <h1>Executive KPI Surface</h1>
      <p>
        Single-page roll-up against the five capstone success criteria. Reads from the
        in-repo evidence-pack artefacts published via the
        <code>evidence-pack-publication-gate</code> CI job (spec-037).
      </p>

      <ManualRowRatioStrip ratios={ratios} />
      <StaleTelemetryBanner stale={stale} lastObservedUtc={lastObserved} />
      <KpiLadder kpis={kpis} />
    </main>
  );
}
