/**
 * Spec 038 evidence-harness route stub (T-S07).
 *
 * Mounts the existing PersonaWorkspace shell with six tab slots (KPI Ladder,
 * Measurement Method, Replay Scorecard, Impact Chains, Benchmarks, Audit
 * Trace) — no new chart libraries, no new UI primitives (FR-013 / FR-034).
 */
import KpiLadderTab from "./_tabs/KpiLadderTab";
import MeasurementTab from "./_tabs/MeasurementTab";
import ReplayTab from "./_tabs/ReplayTab";
import ImpactTab from "./_tabs/ImpactTab";
import BenchmarkTab from "./_tabs/BenchmarkTab";
import AuditTab from "./_tabs/AuditTab";

const TABS = [
  { id: "kpi-ladder", label: "KPI Ladder", Component: KpiLadderTab },
  { id: "measurement", label: "Measurement Method", Component: MeasurementTab },
  { id: "replay", label: "Replay Scorecard", Component: ReplayTab },
  { id: "impact", label: "Impact Chains", Component: ImpactTab },
  { id: "benchmarks", label: "Benchmarks", Component: BenchmarkTab },
  { id: "audit", label: "Audit Trace", Component: AuditTab },
] as const;

export default function EvidencePage() {
  return (
    <section className="workspace-shell" aria-label="Evidence Harness">
      <header className="workspace-header">
        <p className="workspace-kicker">Governance · Evidence</p>
        <h1 className="workspace-title">Measurable Success-Criteria Evidence Harness</h1>
        <p className="workspace-org">
          Advisory-only · AU sovereignty · Append-only audit (spec 038)
        </p>
      </header>
      <nav aria-label="Evidence tabs" className="workspace-tabs">
        <ul role="tablist">
          {TABS.map((t) => (
            <li key={t.id} role="presentation">
              <a href={`#${t.id}`} role="tab">
                {t.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <div className="workspace-tabpanels">
        {TABS.map((t) => (
          <section key={t.id} id={t.id} role="tabpanel" aria-labelledby={t.id}>
            <h2>{t.label}</h2>
            <t.Component />
          </section>
        ))}
      </div>
      <p className="workspace-banner" role="note">
        Advisory only — no autonomous action. (FR-030)
      </p>
    </section>
  );
}
