"use client";

import { useCallback, useEffect, useState } from "react";
import { IncidentTypeIcon } from "@ama/ui/components/disaster-map/incident-type-icon";
import {
  ApiHttpError,
  getIncidentDashboard,
  type DashboardPayload,
} from "../../../lib/api/dashboard";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { SharedOperatingPicture } from "../../../components/dashboard/shared-operating-picture";
import { PublicAlertComposer } from "../../../components/alerts/public-alert-composer";
import { listSignals, type SignalRecord } from "../../../lib/api/signals";
import { ConnectivityBanner } from "../../../components/offline/connectivity-banner";
import { useI18n } from "../../../lib/i18n/runtime";

/* ── Stat card helper ── */
function StatCard({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="incident-stat-card">
      <span className="incident-stat-value">{value}</span>
      <span className="incident-stat-label">{label}</span>
    </div>
  );
}

function formatCost(aud?: number | null, formatted?: string | null, locale = "en-AU"): string | null {
  if (formatted) return formatted;
  if (aud == null) return null;
  if (aud >= 1_000_000_000) return `$${(aud / 1_000_000_000).toFixed(1)} billion`;
  if (aud >= 1_000_000) return `$${(aud / 1_000_000).toFixed(0)} million`;
  if (aud >= 1_000) return `$${(aud / 1_000).toFixed(0)},000`;
  return `$${new Intl.NumberFormat(locale).format(aud)}`;
}

export default function IncidentPage() {
  const { locale, t, formatDateTime, formatNumber } = useI18n();
  const params = useParams<{ incidentId: string }>();
  const searchParams = useSearchParams();
  const incidentId = params.incidentId;
  const returnUrl = searchParams.get("returnUrl") || "/";
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [signals, setSignals] = useState<SignalRecord[]>([]);
  const [viewState, setViewState] = useState<
    "loading" | "stale" | "degraded" | "empty" | "ready" | "error" | "not-found" | "unauthorized"
  >("loading");
  const [refreshNonce, setRefreshNonce] = useState(0);
  const isLiveIncident = dashboard
    ? ["active", "monitoring", "stabilising"].includes(dashboard.incident.status)
    : false;

  const refresh = useCallback(async (signal: AbortSignal) => {
    const [dash, liveSignals] = await Promise.all([
      getIncidentDashboard(incidentId, signal),
      listSignals(incidentId, signal),
    ]);
    setDashboard(dash);
    setSignals(liveSignals);
    if ((dash.signalSummary.degradedSources?.length ?? 0) > 0) {
      setViewState("degraded");
      return;
    }
    const isEmpty =
      dash.participatingOrganisations.length === 0 &&
      dash.activeRecommendations.length === 0 &&
      dash.activeTasks.length === 0 &&
      liveSignals.length === 0;
    setViewState(isEmpty ? "empty" : "ready");
  }, [incidentId]);

  useEffect(() => {
    let disposed = false;
    const controller = new AbortController();

    const load = async () => {
      try {
        await refresh(controller.signal);
      } catch (error) {
        if (disposed || controller.signal.aborted) {
          return;
        }
        if (error instanceof ApiHttpError) {
          if (error.status === 404) {
            setViewState("not-found");
            return;
          }
          if (error.status === 401 || error.status === 403) {
            setViewState("unauthorized");
            return;
          }
        }
        setViewState((current) => current === "loading" ? "error" : "stale");
      }
    };

    load();
    const interval = window.setInterval(load, 10000);
    return () => {
      disposed = true;
      controller.abort();
      window.clearInterval(interval);
    };
  }, [incidentId, refresh, refreshNonce]);

  if (viewState === "not-found") {
    return (
      <div className="incident-detail-page">
        <ConnectivityBanner />
        <div className="incident-error">
          <h1>{t("incident.notFound")}</h1>
          <p>{t("incident.notFoundBody")}</p>
          <Link href={returnUrl} className="incident-back-link">← {t("common.backToMap")}</Link>
        </div>
      </div>
    );
  }

  if (viewState === "unauthorized") {
    return (
      <div className="incident-detail-page">
        <ConnectivityBanner />
        <div className="incident-error">
          <h1>{t("incident.unauthorized")}</h1>
          <p>{t("incident.unauthorizedBody")}</p>
          <Link href={returnUrl} className="incident-back-link">← {t("common.backToMap")}</Link>
        </div>
      </div>
    );
  }

  if (viewState === "loading" || !dashboard) {
    return (
      <div className="incident-detail-page">
        <ConnectivityBanner />
        <div className="incident-loading">{t("incident.loading")}</div>
      </div>
    );
  }

  if (viewState === "error") {
    return (
      <div className="incident-detail-page">
        <ConnectivityBanner />
        <div className="incident-error">
          <h1>{t("incident.error")}</h1>
          <p>{t("incident.errorBody")}</p>
          <Link href={returnUrl} className="incident-back-link">← {t("common.backToMap")}</Link>
        </div>
      </div>
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

  const publicAlertRecommendation = dashboard.activeRecommendations.find(
    (recommendation) => recommendation.type === "public_alert",
  );
  const canApproveAlert = Boolean(publicAlertRecommendation?.approvalAction?.allowed);

  return (
    <div className="incident-detail-page">
        <ConnectivityBanner />
        {viewState === "stale" ? (
          <section className="degraded-banner" role="status">
            <strong>{t("incident.staleTitle")}</strong>
            <p className="degraded-copy">{t("incident.staleBody")}</p>
          </section>
        ) : null}
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
            <Link href={returnUrl} className="incident-back-link">← {t("common.backToMap")}</Link>
            <div className="incident-hero-meta">
              <IncidentTypeIcon type={inc.incidentType} size={36} />
              <span className="incident-hero-type">
                {inc.incidentType.replace(/_/g, " ")}
              </span>
              {inc.region && (
                <span className="incident-hero-region">{inc.region}</span>
              )}
              {inc.startedAt && (
                <span className="incident-hero-date">{formatDateTime(inc.startedAt)}</span>
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
                <StatCard value={formatNumber(impact.deaths)} label="Fatalities" />
              )}
              {impact.injuries != null && (
                <StatCard value={formatNumber(impact.injuries)} label="Injuries" />
              )}
              {impact.homesDestroyed != null && (
                <StatCard value={formatNumber(impact.homesDestroyed)} label="Homes Destroyed" />
              )}
              {impact.businessesDestroyed != null && (
                <StatCard value={formatNumber(impact.businessesDestroyed)} label="Businesses Destroyed" />
              )}
              {(impact.insuranceCostAud != null || impact.insuranceCostFormatted) && (
                <StatCard
                  value={formatCost(impact.insuranceCostAud, impact.insuranceCostFormatted, locale) ?? "N/A"}
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
        {viewState === "empty" ? (
          <section className="incident-operational">
            <h2 className="incident-section-title">{t("incident.operationalData")}</h2>
            <p>{t("incident.noOperational")}</p>
          </section>
        ) : null}

        {isLiveIncident && (
          <section className="incident-operational">
            <SharedOperatingPicture dashboard={dashboard} signals={signals} />
            {publicAlertRecommendation ? (
              <PublicAlertComposer
                recommendationId={publicAlertRecommendation.recommendation_id}
                alertId={`alert-${publicAlertRecommendation.recommendation_id}`}
                languages={["en-AU", "zh-Hans"]}
                actorPersonaId={inc.actorPersonaId}
                onWorkflowComplete={() => setRefreshNonce((value) => value + 1)}
              />
            ) : null}
            {!canApproveAlert ? (
              <p className="incident-source-link" role="status">
                {t("incident.alertUnavailable")}
              </p>
            ) : null}
          </section>
        )}

        {!isLiveIncident && (dashboard.participatingOrganisations.length > 0 ||
          dashboard.activeRecommendations.length > 0 ||
          dashboard.signalSummary.authoritativeCount > 0 ||
          dashboard.signalSummary.communityCount > 0) && (
          <section className="incident-operational">
            <h2 className="incident-section-title">{t("incident.operationalData")}</h2>
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
  );
}
