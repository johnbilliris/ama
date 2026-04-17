"use client";

import { useState, useEffect } from "react";
import { AppShell } from "@ama/ui/components/layout/app-shell";
import { IncidentTypeIcon } from "@ama/ui/components/disaster-map/incident-type-icon";
import { getIncidentDashboard, type DashboardPayload } from "../../../lib/api/dashboard";
import { useParams } from "next/navigation";
import Link from "next/link";

/* ── Stat card helper ── */
function StatCard({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="incident-stat-card">
      <span className="incident-stat-value">{value}</span>
      <span className="incident-stat-label">{label}</span>
    </div>
  );
}

/* ── Format helpers ── */
function formatDate(iso?: string): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("en-AU", { year: "numeric", month: "long", day: "numeric" });
  } catch {
    return iso;
  }
}

function formatCost(aud?: number | null, formatted?: string | null): string | null {
  if (formatted) return formatted;
  if (aud == null) return null;
  if (aud >= 1_000_000_000) return `$${(aud / 1_000_000_000).toFixed(1)} billion`;
  if (aud >= 1_000_000) return `$${(aud / 1_000_000).toFixed(0)} million`;
  if (aud >= 1_000) return `$${(aud / 1_000).toFixed(0)},000`;
  return `$${aud.toLocaleString()}`;
}

export default function IncidentPage() {
  const params = useParams<{ incidentId: string }>();
  const incidentId = params.incidentId;
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getIncidentDashboard(incidentId)
      .then(setDashboard)
      .catch(() => setError(true));
  }, [incidentId]);

  if (error) {
    return (
      <AppShell>
        <div className="incident-detail-page">
          <div className="incident-error">
            <h1>Incident not found</h1>
            <p>The requested incident could not be loaded.</p>
            <Link href="/" className="incident-back-link">← Back to map</Link>
          </div>
        </div>
      </AppShell>
    );
  }

  if (!dashboard) {
    return (
      <AppShell>
        <div className="incident-detail-page">
          <div className="incident-loading">Loading incident details…</div>
        </div>
      </AppShell>
    );
  }

  const inc = dashboard.incident;
  const impact = inc.impact ?? {};
  const loc = inc.location;
  const hasStats =
    impact.deaths != null ||
    impact.injuries != null ||
    impact.homesDestroyed != null ||
    impact.businessesDestroyed != null ||
    impact.insuranceCostAud != null ||
    impact.insuranceCostFormatted != null;

  const mapUrl =
    loc?.latitude != null && loc?.longitude != null
      ? `https://atlas.microsoft.com/map/static/png?api-version=2024-04-01&center=${loc.longitude},${loc.latitude}&zoom=7&width=1200&height=400&layer=basic&style=main&subscription-key=${process.env.NEXT_PUBLIC_AZURE_MAPS_KEY ?? ""}`
      : null;

  return (
    <AppShell>
      <div className="incident-detail-page">
        {/* ── Hero section with map background ── */}
        <section
          className="incident-hero"
          style={
            mapUrl
              ? { backgroundImage: `url(${mapUrl})` }
              : { background: "linear-gradient(135deg, #0d6b79 0%, #134e5e 100%)" }
          }
        >
          <div className="incident-hero-overlay" />
          <div className="incident-hero-content">
            <Link href="/" className="incident-back-link">← Back to map</Link>
            <div className="incident-hero-meta">
              <IncidentTypeIcon type={inc.incidentType} size={36} />
              <span className="incident-hero-type">
                {inc.incidentType.replace(/_/g, " ")}
              </span>
              {inc.region && (
                <span className="incident-hero-region">{inc.region}</span>
              )}
              {inc.startedAt && (
                <span className="incident-hero-date">{formatDate(inc.startedAt)}</span>
              )}
            </div>
            <h1 className="incident-hero-title">{inc.title}</h1>
            <div className="incident-hero-badges">
              <span className={`incident-badge incident-badge--${inc.severity}`}>
                {inc.severity}
              </span>
              <span className={`incident-badge incident-badge--${inc.status}`}>
                {inc.status}
              </span>
            </div>
          </div>
        </section>

        {/* ── Quick statistics ── */}
        {hasStats && (
          <section className="incident-stats">
            <h2 className="incident-section-title">Quick Statistics</h2>
            <div className="incident-stats-grid">
              {impact.deaths != null && (
                <StatCard value={impact.deaths.toLocaleString()} label="Fatalities" />
              )}
              {impact.injuries != null && (
                <StatCard value={impact.injuries.toLocaleString()} label="Injuries" />
              )}
              {impact.homesDestroyed != null && (
                <StatCard value={impact.homesDestroyed.toLocaleString()} label="Homes Destroyed" />
              )}
              {impact.businessesDestroyed != null && (
                <StatCard value={impact.businessesDestroyed.toLocaleString()} label="Businesses Destroyed" />
              )}
              {(impact.insuranceCostAud != null || impact.insuranceCostFormatted) && (
                <StatCard
                  value={formatCost(impact.insuranceCostAud, impact.insuranceCostFormatted) ?? "N/A"}
                  label="Insurance Cost"
                />
              )}
            </div>
          </section>
        )}

        {/* ── Description / historical context ── */}
        {inc.introduction && (
          <section className="incident-description">
            <h2 className="incident-section-title">About this Incident</h2>
            <div className="incident-description-text">
              {inc.introduction.split("\n").map((para, i) => (
                <p key={i}>{para}</p>
              ))}
            </div>
          </section>
        )}

        {/* ── Source attribution ── */}
        {inc.sourceUrl && (
          <section className="incident-sources">
            <h2 className="incident-section-title">Information Sources</h2>
            <p>
              Data sourced from the{" "}
              <a
                href={inc.sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="incident-source-link"
              >
                Australian Disaster Resilience Knowledge Hub (AIDR)
              </a>
            </p>
          </section>
        )}

        {/* ── Operational data (only for active/simulation incidents) ── */}
        {(dashboard.participatingOrganisations.length > 0 ||
          dashboard.activeRecommendations.length > 0 ||
          dashboard.signalSummary.authoritativeCount > 0 ||
          dashboard.signalSummary.communityCount > 0) && (
          <section className="incident-operational">
            <h2 className="incident-section-title">Operational Data</h2>
            {dashboard.participatingOrganisations.length > 0 && (
              <div className="incident-orgs">
                <h3>Participating Organisations</h3>
                <ul>
                  {dashboard.participatingOrganisations.map((org) => (
                    <li key={org.organisationId}>{org.name} ({org.category})</li>
                  ))}
                </ul>
              </div>
            )}
            {(dashboard.signalSummary.authoritativeCount > 0 ||
              dashboard.signalSummary.communityCount > 0) && (
              <div className="incident-signals-summary">
                <h3>Signal Summary</h3>
                <p>
                  Authoritative: {dashboard.signalSummary.authoritativeCount} ·
                  Community: {dashboard.signalSummary.communityCount} ·
                  Contradicted: {dashboard.signalSummary.contradictedCount}
                </p>
              </div>
            )}
          </section>
        )}
      </div>
    </AppShell>
  );
}
