"use client";

/**
 * /disasters — Disaster Mapper page
 *
 * Interactive Azure Maps view of incident markers across Australia.
 * Loads data progressively from the incidents/map API endpoint.
 */

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import { AppShell } from "@ama/ui/components/layout/app-shell";
import type {
  IncidentFeature,
  IncidentMapMetadata,
} from "../../lib/api/incidents-map";
import {
  loadIncidentsProgressively,
  type MapFilterParams,
} from "../../lib/api/incidents-map";

/* Dynamic import — SSR disabled for Azure Maps */
const DisasterMap = dynamic(
  () =>
    import("@ama/ui/components/disaster-map/disaster-map").then(
      (mod) => mod.DisasterMap,
    ),
  { ssr: false },
);

export default function DisastersPage() {
  const [features, setFeatures] = useState<IncidentFeature[]>([]);
  const [metadata, setMetadata] = useState<IncidentMapMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingComplete, setLoadingComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIncident, setSelectedIncident] =
    useState<IncidentFeature | null>(null);
  const [mapError, setMapError] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const [filters] = useState<MapFilterParams>({});

  // ── Load data ──
  const loadData = useCallback(
    async (filterParams: MapFilterParams) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setLoadingComplete(false);
      setError(null);

      try {
        await loadIncidentsProgressively(
          filterParams,
          (result) => {
            setFeatures(result.features);
            setMetadata(result.metadata);
            setLoading(false);
            if (result.isComplete) {
              setLoadingComplete(true);
            }
          },
          controller.signal,
        );
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error ? err.message : "Failed to load incidents",
          );
          setLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    loadData(filters);
    return () => abortRef.current?.abort();
  }, [filters, loadData]);

  const handleMarkerClick = useCallback((feature: IncidentFeature) => {
    setSelectedIncident(feature);
  }, []);

  const handleMapRenderComplete = useCallback(() => {
    // Telemetry hook point — T031 will add metrics here
  }, []);

  return (
    <AppShell>
      <div className="disaster-mapper-page">
        {/* Header */}
        <header className="disaster-mapper-header">
          <p className="disaster-mapper-kicker">Situational Awareness</p>
          <h1 className="disaster-mapper-title">Disaster Mapper</h1>
          <p className="disaster-mapper-status">
            {loading
              ? "Loading incidents…"
              : `${features.length} incident${features.length !== 1 ? "s" : ""} displayed`}
            {!loadingComplete && !loading && " (loading more…)"}
          </p>
        </header>

        {/* Error banner */}
        {error && (
          <div className="disaster-mapper-error" role="alert">
            <p>{error}</p>
            <button
              onClick={() => loadData(filters)}
              className="disaster-mapper-retry-btn"
            >
              Retry
            </button>
          </div>
        )}

        {/* Map + sidebar layout */}
        <div className="disaster-mapper-content">
          <div className="disaster-mapper-map-area">
            {!mapError ? (
              <DisasterMap
                features={features}
                onMarkerClick={handleMarkerClick}
                onRenderComplete={handleMapRenderComplete}
              />
            ) : (
              <div className="disaster-mapper-map-unavailable">
                <p>Map service is currently unavailable.</p>
                <button
                  onClick={() => setMapError(false)}
                  className="disaster-mapper-retry-btn"
                >
                  Retry map
                </button>
              </div>
            )}
          </div>

          {/* Sidebar for selected incident */}
          {selectedIncident && (
            <aside className="disaster-mapper-sidebar" role="complementary">
              <div className="disaster-mapper-sidebar-header">
                <h2>{selectedIncident.properties.title}</h2>
                <button
                  onClick={() => setSelectedIncident(null)}
                  className="disaster-mapper-close-btn"
                  aria-label="Close incident details"
                >
                  ×
                </button>
              </div>
              <dl className="disaster-mapper-detail-list">
                <dt>Type</dt>
                <dd>{selectedIncident.properties.incident_type}</dd>
                <dt>Status</dt>
                <dd>{selectedIncident.properties.status}</dd>
                <dt>Severity</dt>
                <dd
                  className={`disaster-mapper-severity disaster-mapper-severity--${selectedIncident.properties.severity_tier}`}
                >
                  {selectedIncident.properties.severity_tier}
                </dd>
                <dt>Start date</dt>
                <dd>{selectedIncident.properties.started_at}</dd>
                {selectedIncident.properties.pprr_phase && (
                  <>
                    <dt>PPRR Phase</dt>
                    <dd>{selectedIncident.properties.pprr_phase}</dd>
                  </>
                )}
                <dt>Incident Level</dt>
                <dd>{selectedIncident.properties.incident_level}</dd>
                <dt>Jurisdictions</dt>
                <dd>
                  {selectedIncident.properties.affected_jurisdiction_ids.join(
                    ", ",
                  ) || "—"}
                </dd>
              </dl>
              <a
                href={`/incidents/${selectedIncident.properties.incident_id}`}
                className="disaster-mapper-workspace-link"
              >
                Open Workspace →
              </a>
            </aside>
          )}
        </div>

        {/* Metadata notices */}
        {metadata && (
          <footer className="disaster-mapper-footer">
            {metadata.unmapped_count > 0 && (
              <p className="disaster-mapper-unmapped-notice">
                {metadata.unmapped_count} incident
                {metadata.unmapped_count !== 1 ? "s" : ""} could not be mapped
                due to missing location data
              </p>
            )}
            <p className="disaster-mapper-timestamp">
              Last updated: {new Date(metadata.fetched_at).toLocaleString()}
            </p>
          </footer>
        )}
      </div>
    </AppShell>
  );
}
