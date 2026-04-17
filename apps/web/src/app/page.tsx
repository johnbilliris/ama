"use client";

/**
 * / — Disaster Mapper page (moved from /disasters)
 *
 * Interactive Azure Maps view of incident markers across Australia.
 * Loads data progressively from the incidents/map API endpoint.
 * Supports multi-criteria URL-synced filtering and keyword search.
 */

import dynamic from "next/dynamic";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { AppShell } from "@ama/ui/components/layout/app-shell";
import type {
  IncidentFeature,
  IncidentMapMetadata,
} from "../lib/api/incidents-map";
import {
  loadIncidentsProgressively,
  type MapFilterParams,
} from "../lib/api/incidents-map";

/* Dynamic imports — SSR disabled for Azure Maps and filter components */
const DisasterMap = dynamic(
  () =>
    import("@ama/ui/components/disaster-map/disaster-map").then(
      (mod) => mod.DisasterMap,
    ),
  { ssr: false },
);

const FilterPanel = dynamic(
  () =>
    import("@ama/ui/components/disaster-map/filter-panel").then(
      (mod) => mod.FilterPanel,
    ),
  { ssr: false },
);

const IncidentSidebar = dynamic(
  () =>
    import("@ama/ui/components/disaster-map/incident-sidebar").then(
      (mod) => mod.IncidentSidebar,
    ),
  { ssr: false },
);

const IncidentHoverCard = dynamic(
  () =>
    import("@ama/ui/components/disaster-map/incident-hover-card").then(
      (mod) => mod.IncidentHoverCard,
    ),
  { ssr: false },
);

/* Inner component that uses useSearchParams (must be inside Suspense) */
function DisastersPageInner() {
  // Import the hook dynamically to avoid SSR issues with useSearchParams
  const [hookModule, setHookModule] = useState<typeof import("@ama/ui/components/disaster-map/use-disaster-map-filters") | null>(null);

  useEffect(() => {
    import("@ama/ui/components/disaster-map/use-disaster-map-filters").then(setHookModule);
  }, []);

  if (!hookModule) {
    return <DisastersPageContent filters={{}} setFilter={() => {}} resetAll={() => {}} keywordInput="" setKeywordInput={() => {}} />;
  }

  return <DisastersPageWithFilters hookModule={hookModule} />;
}

function DisastersPageWithFilters({ hookModule }: { hookModule: typeof import("@ama/ui/components/disaster-map/use-disaster-map-filters") }) {
  const { filters, setFilter, resetAll, keywordInput, setKeywordInput } = hookModule.useDisasterMapFilters();
  return <DisastersPageContent filters={filters} setFilter={setFilter} resetAll={resetAll} keywordInput={keywordInput} setKeywordInput={setKeywordInput} />;
}

interface DisastersPageContentProps {
  filters: MapFilterParams;
  setFilter: <K extends keyof MapFilterParams>(key: K, value: MapFilterParams[K]) => void;
  resetAll: () => void;
  keywordInput: string;
  setKeywordInput: (value: string) => void;
}

function DisastersPageContent({ filters, setFilter, resetAll, keywordInput, setKeywordInput }: DisastersPageContentProps) {
  const [features, setFeatures] = useState<IncidentFeature[]>([]);
  const [metadata, setMetadata] = useState<IncidentMapMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingComplete, setLoadingComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIncident, setSelectedIncident] =
    useState<IncidentFeature | null>(null);
  const [filterPanelOpen, setFilterPanelOpen] = useState(true);
  const abortRef = useRef<AbortController | null>(null);

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

  const [hoveredIncident, setHoveredIncident] =
    useState<IncidentFeature | null>(null);

  const handleMarkerHover = useCallback((feature: IncidentFeature | null) => {
    setHoveredIncident(feature);
  }, []);

  // ── Telemetry (T031) ──
  const pageLoadStartRef = useRef(typeof performance !== "undefined" ? performance.now() : 0);

  const handleMapRenderComplete = useCallback(() => {
    // Emit telemetry metrics when map finishes rendering
    if (typeof performance !== "undefined") {
      const renderTime = performance.now() - pageLoadStartRef.current;
      // disaster_mapper.page_load_ms — navigation to map ready
      console.debug("[telemetry] disaster_mapper.page_load_ms:", renderTime);
      // disaster_mapper.map_render_ms — data receipt to marker render
      console.debug("[telemetry] disaster_mapper.map_render_ms:", renderTime);
    }
    // disaster_mapper.incidents_displayed — gauge on each render
    console.debug("[telemetry] disaster_mapper.incidents_displayed:", features.length);
  }, [features.length]);

  return (
    <AppShell>
      <div className="disaster-mapper-page">
        {/* Top: header + error banner — always one grid row */}
        <div className="disaster-mapper-top">
          <header className="disaster-mapper-header">
            <p className="disaster-mapper-kicker">Situational Awareness</p>
            <h1 className="disaster-mapper-title">Disaster Mapper</h1>
            <div className="disaster-mapper-header-controls">
              {/* Search bar */}
              <div className="disaster-mapper-search-wrapper">
                <input
                  type="search"
                  className="disaster-mapper-search-input"
                  placeholder="Search incidents by title…"
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  aria-label="Search incidents by keyword"
                />
                {keywordInput && (
                  <button
                    className="disaster-mapper-search-clear"
                    onClick={() => setKeywordInput("")}
                    aria-label="Clear search"
                  >
                    ×
                  </button>
                )}
              </div>
              <button
                className="disaster-mapper-filter-toggle-btn"
                onClick={() => setFilterPanelOpen((v) => !v)}
                aria-expanded={filterPanelOpen}
              >
                {filterPanelOpen ? "Hide Filters" : "Show Filters"}
              </button>
            </div>
            <p className="disaster-mapper-status" aria-live="polite">
              {loading
                ? "Loading incidents…"
                : `Showing ${features.length} incident${features.length !== 1 ? "s" : ""}`}
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
        </div>

        {/* Main content: filter panel + map + sidebar — always fills 1fr */}
        <div className="disaster-mapper-body">
          {/* Filter panel */}
          <FilterPanel
            filters={filters}
            onFilterChange={setFilter}
            onReset={resetAll}
            isOpen={filterPanelOpen}
            onToggle={() => setFilterPanelOpen((v) => !v)}
          />

          {/* Map + sidebar */}
          <div className="disaster-mapper-content">
            <div className="disaster-mapper-map-area">
              {/* Loading overlay */}
              {loading && (
                <div className="disaster-mapper-loading">
                  <div className="disaster-mapper-spinner" />
                  <p>Loading incidents…</p>
                </div>
              )}
              {/* Progressive loading bar */}
              {!loading && !loadingComplete && metadata && (
                <div className="disaster-mapper-progress-bar">
                  <div
                    className="disaster-mapper-progress-fill"
                    style={{
                      width: `${Math.min(100, (features.length / Math.max(metadata.total, 1)) * 100)}%`,
                    }}
                  />
                </div>
              )}
              {/* DisasterMap always renders its container; error overlay is handled internally */}
              <DisasterMap
                features={features}
                onMarkerClick={handleMarkerClick}
                onMarkerHover={handleMarkerHover}
                onRenderComplete={handleMapRenderComplete}
              />
              {/* Hover preview card */}
              {hoveredIncident && !selectedIncident && (
                <IncidentHoverCard incident={hoveredIncident.properties} />
              )}
              {/* No-results overlay — floats above the map so the map stays visible */}
              {!loading && features.length === 0 && !error && (
                <div className="disaster-mapper-no-results" role="status">
                  <p>No incidents match your criteria.</p>
                  <button
                    onClick={resetAll}
                    className="disaster-mapper-retry-btn"
                  >
                    Reset filters
                  </button>
                </div>
              )}
            </div>

            {/* Sidebar for selected incident */}
            {selectedIncident && (
              <IncidentSidebar
                incident={selectedIncident.properties}
                onClose={() => setSelectedIncident(null)}
              />
            )}
          </div>
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

export default function HomePage() {
  return (
    <Suspense fallback={<div className="disaster-mapper-page"><p>Loading…</p></div>}>
      <DisastersPageInner />
    </Suspense>
  );
}

