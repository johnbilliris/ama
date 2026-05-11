"use client";

/**
 * SimulationMap — real Azure Maps view for the simulation dashboard.
 *
 * Reuses the shared `DisasterMap` component (Azure Maps + clustered markers)
 * so the simulation looks and behaves identically to the disaster-mapper page.
 * Additional simulation-only chrome (scenario chip, status chip, tenant id)
 * is overlaid on top of the map.
 *
 * Spec-036 T-I04: also accepts an optional stream of `MapOverlayEvent`s
 * (16 closed-set layer types per `contracts/sse-map-overlay.md §2`) and
 * folds them into the rendered feature collection via the typed dispatch
 * in `lib/sse/map-overlay-dispatch.ts` (which uses an `assertNever`
 * exhaustiveness guard).
 */

import dynamic from "next/dynamic";
import { useMemo } from "react";

import type { IncidentFeature } from "@/lib/api/incidents-map";
import { applyMapOverlayEvents } from "@/lib/sse/map-overlay-dispatch";
import type { MapOverlayEvent } from "@/lib/sse/map-overlay-events";

const DisasterMap = dynamic(
  () =>
    import("@ama/ui/components/disaster-map/disaster-map").then(
      (mod) => mod.DisasterMap,
    ),
  { ssr: false },
);

// Approximate capital-city centroids for AU jurisdictions (lng, lat).
// Used to seed an incident marker for each affected jurisdiction until the
// controller flows real geocoded incidents through the simulation.
const JURISDICTION_CENTROIDS: Record<
  string,
  { lng: number; lat: number; name: string }
> = {
  NSW: { lng: 151.2093, lat: -33.8688, name: "NSW" },
  VIC: { lng: 144.9631, lat: -37.8136, name: "VIC" },
  QLD: { lng: 153.0251, lat: -27.4698, name: "QLD" },
  WA: { lng: 115.8605, lat: -31.9505, name: "WA" },
  SA: { lng: 138.6007, lat: -34.9285, name: "SA" },
  TAS: { lng: 147.3272, lat: -42.8821, name: "TAS" },
  NT: { lng: 130.8456, lat: -12.4634, name: "NT" },
  ACT: { lng: 149.13, lat: -35.2809, name: "ACT" },
};

const SCENARIO_ICON: Record<string, string> = {
  bushfire: "🔥",
  flood: "🌊",
  cyclone: "🌀",
  storm: "⛈",
  "severe storm": "⛈",
  earthquake: "🌐",
  heatwave: "🌡",
  heat: "🌡",
  pandemic: "⚕",
  tsunami: "🌊",
};

/**
 * Normalise a scenario/hazard label (e.g. "Bushfire", "Severe Storm", "Heatwave",
 * "heat") to a pin-icon key recognised by the DisasterMap marker layer.
 * Keep in sync with PIN_DEFS in packages/ui/.../marker-cluster.tsx.
 */
function normaliseHazardKey(value: string | null | undefined): string {
  if (!value) return "other";
  const v = value.trim().toLowerCase();
  const direct: Record<string, string> = {
    bushfire: "bushfire",
    fire: "bushfire",
    "urban fire": "urban_fire",
    urban_fire: "urban_fire",
    flood: "flood",
    cyclone: "cyclone",
    storm: "storm",
    "severe storm": "storm",
    tornado: "tornado",
    earthquake: "earthquake",
    tsunami: "tsunami",
    heatwave: "extreme_heat",
    "extreme heat": "extreme_heat",
    heat: "extreme_heat",
    extreme_heat: "extreme_heat",
    pandemic: "pandemic",
    health: "health",
    biosecurity: "biosecurity",
    landslide: "landslide",
    industrial: "industrial",
    transport: "transport",
    criminal: "criminal",
    environment: "environment",
    "maritime coastal": "maritime_coastal",
    maritime: "maritime_coastal",
  };
  return direct[v] ?? "other";
}

export interface ScenarioCard {
  id?: string;
  tenant_id?: string;
  simulation_id?: string;
  hazard?: string;
  location?: {
    name?: string;
    lng?: number | null;
    lat?: number | null;
    zoom?: number | null;
    resolver?: string;
  };
  start_at?: string;
  aws_default_level?: string;
  parameters?: Record<string, unknown>;
}

interface SimulationMapProps {
  tenantId: string;
  scenarioType: string;
  jurisdictions: string[];
  status: string;
  /** Scenario card emitted by the controller — zooms the map to its location. */
  scenarioCard?: ScenarioCard | null;
  /** Optional extra GeoJSON features to render (for future server-supplied markers). */
  extraFeatures?: IncidentFeature[];
  /**
   * Spec-036 T-I04 — closed set of map-overlay SSE events to fold into
   * the feature collection. Each event is dispatched through
   * `applyMapOverlayEvents`, which uses `assertNever` to enforce
   * compile-time exhaustiveness across the 16-entry layer-type union.
   */
  overlayEvents?: MapOverlayEvent[];
}

export function SimulationMap({
  tenantId,
  scenarioType,
  jurisdictions,
  status,
  scenarioCard,
  extraFeatures = [],
  overlayEvents = [],
}: SimulationMapProps) {
  const features = useMemo<IncidentFeature[]>(() => {
    const now = new Date().toISOString();
    const derived: IncidentFeature[] = [];

    // When a scenario card is present, emit a primary marker at its coords.
    const lng = scenarioCard?.location?.lng;
    const lat = scenarioCard?.location?.lat;
    if (typeof lng === "number" && typeof lat === "number") {
      const hazard = scenarioCard?.hazard ?? scenarioType ?? "simulation";
      const locName = scenarioCard?.location?.name ?? "simulation";
      derived.push({
        type: "Feature",
        id: `sim-${tenantId}-scenario`,
        geometry: { type: "Point", coordinates: [lng, lat] },
        properties: {
          incident_id: `sim-${tenantId}-scenario`,
          title: `[SIM] ${hazard} – ${locName}`,
          incident_type: normaliseHazardKey(hazard),
          status: status === "Archived" ? "closed" : "active",
          severity: "critical",
          severity_tier: "emergency",
          affected_jurisdiction_ids: jurisdictions.map((j) => j.toLowerCase()),
          participating_organisation_ids: [],
          started_at: scenarioCard?.start_at ?? now,
          pprr_phase: "response",
          incident_level: 3,
        },
      });
    }

    // Otherwise fall back to jurisdiction centroids so the map isn't empty.
    if (derived.length === 0) {
      for (const j of jurisdictions) {
        const pt = JURISDICTION_CENTROIDS[j.toUpperCase()];
        if (!pt) continue;
        derived.push({
          type: "Feature",
          id: `sim-${tenantId}-${j}`,
          geometry: { type: "Point", coordinates: [pt.lng, pt.lat] },
          properties: {
            incident_id: `sim-${tenantId}-${j}`,
            title: `[SIM] ${scenarioType} – ${pt.name}`,
            incident_type: normaliseHazardKey(scenarioType || "simulation"),
            status: status === "Archived" ? "closed" : "active",
            severity: "critical",
            severity_tier: "emergency",
            affected_jurisdiction_ids: [j.toLowerCase()],
            participating_organisation_ids: [],
            started_at: now,
            pprr_phase: "response",
            incident_level: 3,
          },
        });
      }
    }
    return [...derived, ...extraFeatures];
  }, [tenantId, scenarioType, jurisdictions, status, scenarioCard, extraFeatures]);

  // Spec-036 T-I04 — fold overlay SSE events through the typed dispatcher.
  // Spec-036 T-R04 / T-R07 / T-R08 — Wave 4 amendment: surface
  // non-Point geometries (LineString, Polygon, MultiPolygon) as
  // accessible bullets in the screen-reader live region AND as a
  // visible non-map "overlay summary" panel so coordinators using
  // assistive technology aren't denied the situational awareness that
  // sighted users get from the map. Wind-direction markers (T-R07)
  // emit a structured ``wind-arrow`` row with bearing/speed text so
  // SR users get the canonical example: "wind direction has changed
  // → wind direction markers should appear".
  const overlayResult = useMemo(
    () => applyMapOverlayEvents([], overlayEvents),
    [overlayEvents],
  );
  const overlayPointFeatures = useMemo<IncidentFeature[]>(() => {
    return overlayResult
      .filter((f) => f.geometry.type === "Point")
      .map<IncidentFeature>((f) => ({
        type: "Feature",
        id: f.id,
        geometry: f.geometry as { type: "Point"; coordinates: [number, number] },
        properties: {
          incident_id: f.properties.incident_id,
          title: f.properties.title,
          incident_type: f.properties.incident_type,
          status: f.properties.status,
          severity: f.properties.severity,
          severity_tier: f.properties.severity_tier,
          affected_jurisdiction_ids: [],
          participating_organisation_ids: [],
          started_at: f.properties.started_at,
          pprr_phase: f.properties.pprr_phase,
          incident_level: f.properties.incident_level,
        },
      }));
  }, [overlayResult]);

  // T-R04 — non-Point overlays grouped for the accessible summary panel.
  const overlayNonPointFeatures = useMemo(() => {
    return overlayResult.filter((f) => f.geometry.type !== "Point");
  }, [overlayResult]);

  // T-R07 — wind direction markers (closed-set ``wind-arrow`` layer).
  const windDirectionFeatures = useMemo(() => {
    return overlayResult.filter((f) => f.properties.layer_type === "wind-arrow");
  }, [overlayResult]);

  const renderedFeatures = useMemo(
    () => [...features, ...overlayPointFeatures],
    [features, overlayPointFeatures],
  );

  const focus = useMemo(() => {
    const lng = scenarioCard?.location?.lng;
    const lat = scenarioCard?.location?.lat;
    const zoom = scenarioCard?.location?.zoom ?? 10;
    if (typeof lng === "number" && typeof lat === "number") {
      return { center: [lng, lat] as [number, number], zoom };
    }
    return undefined;
  }, [scenarioCard]);

  const icon = SCENARIO_ICON[(scenarioCard?.hazard ?? scenarioType).toLowerCase()] ?? "⚑";

  // Risk severity badge derived from scenario card's aws_default_level
  const riskLevel = scenarioCard?.aws_default_level
    ? scenarioCard.aws_default_level.replace(/_/g, " ")
    : null;

  // Spec-036 T-R05 — Australian Warning System (AWS) three-tier palette
  // mandated by constitution v1.2.0. The previous draft used green
  // (#22c55e) for "advice", which conflated low-tier alert with
  // all-clear semantics; the canonical mapping below restores the
  // three-tier hue progression (yellow → orange → red) plus an
  // information-class blue.
  const RISK_COLOURS: Record<string, string> = {
    "advice": "#fbbf24",            // yellow
    "watch and act": "#fb923c",     // orange
    "emergency warning": "#dc2626", // red
    "information": "#3b82f6",       // blue
    "not applicable": "#6b7280",    // grey (no AWS tier)
  };
  const riskColour = riskLevel ? (RISK_COLOURS[riskLevel.toLowerCase()] ?? "#ef4444") : null;

  return (
    <div className="sim-map-root" aria-label="Simulation affected area map">
      <div className="sim-map-toolbar">
        <div className="sim-map-toolbar-left">
          <span className="sim-map-chip sim-map-chip--scenario">
            {icon} {scenarioCard?.hazard ?? scenarioType}
          </span>
          <span
            className={`sim-map-chip sim-map-chip--status sim-map-chip--${status}`}
          >
            {status}
          </span>
          {riskLevel && (
            <span
              className="sim-map-chip sim-risk-badge"
              style={{ background: riskColour ?? "#ef4444", color: "#fff" }}
              title={`Risk level: ${riskLevel}`}
            >
              ⚠ {riskLevel}
            </span>
          )}
          <span className="sim-map-chip sim-map-chip--jurisdictions">
            {scenarioCard?.location?.name
              ? scenarioCard.location.name
              : jurisdictions.length > 0
                ? jurisdictions.map((j) => j.toUpperCase()).join(" · ")
                : "No jurisdictions"}
          </span>
        </div>
        <span className="sim-map-toolbar-tenant" title={tenantId}>
          Tenant: {tenantId.slice(0, 14)}…
        </span>
      </div>
      <div className="sim-map-canvas">
        <DisasterMap features={renderedFeatures} focus={focus} viewportKey="simulation-map-viewport" />
      </div>
      {/*
        T-I04 / T-R04 / T-R07 / T-R08 — accessible overlay summary.
        Splits the SR-only digest into:
          1. point-overlay count (rendered on the map already);
          2. non-Point overlay rows (LineString / Polygon — not on the
             map yet; surfaced here so SR users still get them);
          3. wind-direction marker rows with bearing + speed text so
             AT users get the canonical "wind direction changed"
             callout (the visual layer is provisioned but not yet
             rendered by Azure Maps in this milestone).
      */}
      <section
        aria-label="Simulation map overlay summary"
        className="sim-map-overlay-summary"
        data-testid="sim-overlay-summary"
      >
        <div className="sr-only" aria-live="polite" data-testid="sim-overlay-sr-digest">
          {overlayResult.length === 0
            ? "No simulation overlays active."
            : `${overlayResult.length} simulation overlays active: ${Array.from(
                new Set(overlayResult.map((f) => f.properties.layer_type)),
              ).join(", ")}.`}
        </div>
        {overlayNonPointFeatures.length > 0 && (
          <div
            data-testid="sim-overlay-nonpoint-list"
            className="sim-map-overlay-nonpoint"
          >
            <h3 className="sim-map-overlay-heading">
              Geometric overlays ({overlayNonPointFeatures.length})
            </h3>
            <ul aria-label="Non-point geometric overlays">
              {overlayNonPointFeatures.map((f) => (
                <li key={f.id} data-layer-type={f.properties.layer_type}>
                  <span className="sim-map-overlay-kind">
                    {f.geometry.type}
                  </span>
                  {": "}
                  <span className="sim-map-overlay-name">
                    {f.properties.title ?? f.properties.layer_type}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {windDirectionFeatures.length > 0 && (
          <div
            data-testid="sim-overlay-wind-list"
            className="sim-map-overlay-wind"
          >
            <h3 className="sim-map-overlay-heading">
              Wind direction markers ({windDirectionFeatures.length})
            </h3>
            <ul aria-label="Wind direction markers">
              {windDirectionFeatures.map((f) => {
                const bearing =
                  (f.properties as { bearing_deg?: number }).bearing_deg;
                const speed =
                  (f.properties as { speed_kmh?: number }).speed_kmh;
                return (
                  <li key={f.id}>
                    <span className="sim-map-wind-bearing">
                      Bearing {typeof bearing === "number" ? `${bearing}°` : "—"}
                    </span>
                    {", "}
                    <span className="sim-map-wind-speed">
                      Speed {typeof speed === "number" ? `${speed} km/h` : "—"}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}
