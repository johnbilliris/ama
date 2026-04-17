import type { DashboardPayload } from "../../lib/api/dashboard";
import type { SignalRecord } from "../../lib/api/signals";
import { DegradedModeBanner } from "./degraded-mode-banner";
import { SourceHealthPanel } from "./source-health-panel";

interface SharedOperatingPictureProps {
  dashboard: DashboardPayload;
  signals: SignalRecord[];
}

export function SharedOperatingPicture({ dashboard, signals }: SharedOperatingPictureProps) {
  const safeSignals = Array.isArray(signals) ? signals : [];
  return (
    <section className="sop-layout">
      <header className="sop-header">
        <p className="sop-kicker">
          {dashboard.incident.incidentType} incident
        </p>
        <h1 className="sop-title">{dashboard.incident.title}</h1>
        <p className="sop-status">
          Status: {dashboard.incident.status} · Severity: {dashboard.incident.severity}
        </p>
      </header>

      <DegradedModeBanner contradictedCount={dashboard.signalSummary.contradictedCount} />
      <SourceHealthPanel {...dashboard.signalSummary} />

      <section className="sop-columns">
        <article className="sop-panel">
          <h2 className="sop-panel-title">Live signals</h2>
          <ul className="sop-list">
            {safeSignals.map((signal) => (
              <li key={signal.signal_id} className="sop-list-item">
                <strong>{signal.category}</strong>
                <div className="signal-meta">
                  {signal.data_source_id} · {signal.validation_status} · confidence {signal.confidence_score}
                </div>
              </li>
            ))}
          </ul>
        </article>

        <article className="sop-panel">
          <h2 className="sop-panel-title">Agencies</h2>
          <ul className="sop-list">
            {dashboard.participatingOrganisations.map((organisation) => (
              <li key={organisation.organisationId}>
                <strong>{organisation.name}</strong>
                <div className="agency-status">{organisation.status}</div>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </section>
  );
}
