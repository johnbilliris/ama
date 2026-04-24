"use client";

/**
 * SimulationMap — real Azure Maps view for the simulation dashboard.
 *
 * Reuses the shared `DisasterMap` component (Azure Maps + clustered markers)
 * so the simulation looks and behaves identically to the disaster-mapper page.
 * Additional simulation-only chrome (scenario chip, status chip, tenant id)
 * is overlaid on top of the map.
 */

import dynamic from "next/dynamic";
import { useMemo } from "react";

import type { IncidentFeature } from "@/lib/api/incidents-map";

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
}

export function SimulationMap({
  tenantId,
  scenarioType,
  jurisdictions,
  status,
  scenarioCard,
  extraFeatures = [],
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

  const RISK_COLOURS: Record<string, string> = {
    "watch and act": "#f59e0b",
    "advice": "#22c55e",
    "emergency warning": "#dc2626",
    "not applicable": "#6b7280",
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
        <DisasterMap features={features} focus={focus} viewportKey="simulation-map-viewport" />
      </div>
    </div>
  );
}
