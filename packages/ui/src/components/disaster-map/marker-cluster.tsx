"use client";

/**
 * Marker and cluster rendering for the Disaster Mapper.
 *
 * - Generates teardrop-shaped SVG pin icons per incident type
 *   (colour + pictogram inspired by AIDR Knowledge Hub pins)
 * - Configures a DataSource with clustering (clusterRadius: 60)
 * - Adds a SymbolLayer for individual markers with data-driven icon selection
 * - Adds a BubbleLayer for cluster circles + SymbolLayer for cluster count labels
 * - Handles cluster click-to-expand via getClusterExpansionZoom()
 */

import type { IncidentFeature } from "./types";

/* ── Teardrop pin SVG generator ── */

interface PinDef {
  bg: string;
  /** SVG path(s) for the symbol drawn inside the white circle, viewBox 0 0 16 16 */
  paths: string;
}

const PIN_DEFS: Record<string, PinDef> = {
  biosecurity: {
    bg: "#6A1B9A",
    paths: `<path d="M8 3v10M3 8h10M5.2 5.2l5.6 5.6M10.8 5.2l-5.6 5.6" stroke="#6A1B9A" stroke-width="1.5" fill="none" stroke-linecap="round"/>`,
  },
  bushfire: {
    bg: "#D84315",
    paths: `<path d="M8 2c0 3-3 4-3 7a3.5 3.5 0 0 0 6.5.7c-1 .1-2-.6-2-1.7 0-1.5 2-2.5 1.5-4.5C10 5 9 4 8 2z" fill="#D84315"/>`,
  },
  criminal: {
    bg: "#37474F",
    paths: `<circle cx="8" cy="5.5" r="2.5" fill="none" stroke="#37474F" stroke-width="1.5"/><path d="M8 8v3M6 13h4" stroke="#37474F" stroke-width="1.5" stroke-linecap="round"/>`,
  },
  cyclone: {
    bg: "#0277BD",
    paths: `<path d="M8 5.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM8 3c3.5 0 4.5 2 4 3.5M8 13c-3.5 0-4.5-2-4-3.5" fill="none" stroke="#0277BD" stroke-width="1.3" stroke-linecap="round"/>`,
  },
  earthquake: {
    bg: "#795548",
    paths: `<path d="M2 9l3-2 1.5 3L8 5l1.5 5L11 7l3 2" fill="none" stroke="#795548" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>`,
  },
  environment: {
    bg: "#2E7D32",
    paths: `<path d="M8 13V7M8 7c-3-3-6 0-6 0s3 0 6 3M8 7c3-3 6 0 6 0s-3 0-6 3" fill="none" stroke="#2E7D32" stroke-width="1.3" stroke-linecap="round"/>`,
  },
  extreme_heat: {
    bg: "#E65100",
    paths: `<circle cx="8" cy="8" r="2.5" fill="#E65100"/><path d="M8 3v1.5M8 11.5V13M3 8h1.5M11.5 8H13M4.8 4.8l1 1M10.2 10.2l1 1M11.2 4.8l-1 1M4.8 11.2l1-1" stroke="#E65100" stroke-width="1.2" stroke-linecap="round"/>`,
  },
  flood: {
    bg: "#1565C0",
    paths: `<path d="M2 7c1.5-1.5 3-1.5 4 0s2.5 1.5 4 0 2.5-1.5 4 0M2 11c1.5-1.5 3-1.5 4 0s2.5 1.5 4 0 2.5-1.5 4 0" fill="none" stroke="#1565C0" stroke-width="1.5" stroke-linecap="round"/>`,
  },
  health: {
    bg: "#C62828",
    paths: `<path d="M6.5 4h3v3h3v3h-3v3h-3v-3h-3V7h3z" fill="#C62828"/>`,
  },
  industrial: {
    bg: "#455A64",
    paths: `<path d="M4 13V7l3 2V7l3 2V5h2v8z" fill="none" stroke="#455A64" stroke-width="1.3" stroke-linejoin="round"/>`,
  },
  landslide: {
    bg: "#8D6E63",
    paths: `<path d="M2 13l5-8 3 4 4-6" fill="none" stroke="#8D6E63" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 13h12" stroke="#8D6E63" stroke-width="1.5" stroke-linecap="round"/>`,
  },
  maritime_coastal: {
    bg: "#00838F",
    paths: `<path d="M8 3v7M5 12c1-1.5 2-1.5 3 0s2 1.5 3 0" fill="none" stroke="#00838F" stroke-width="1.3" stroke-linecap="round"/><path d="M5 7l3 3 3-3" fill="none" stroke="#00838F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>`,
  },
  other: {
    bg: "#757575",
    paths: `<circle cx="8" cy="11" r="1" fill="#757575"/><path d="M6.5 5.5a1.5 1.5 0 0 1 3 0c0 1-1.5 1.2-1.5 2.5v.5" fill="none" stroke="#757575" stroke-width="1.4" stroke-linecap="round"/>`,
  },
  pandemic: {
    bg: "#AD1457",
    paths: `<circle cx="8" cy="8" r="2" fill="#AD1457"/><path d="M8 3v2M8 11v2M3 8h2M11 8h2M4.8 4.8l1.5 1.5M9.7 9.7l1.5 1.5M11.2 4.8l-1.5 1.5M6.3 9.7l-1.5 1.5" stroke="#AD1457" stroke-width="1.2" stroke-linecap="round"/>`,
  },
  storm: {
    bg: "#4527A0",
    paths: `<path d="M9 2L5 9h4l-2 5 6-7H9l2-5z" fill="#4527A0"/>`,
  },
  tornado: {
    bg: "#283593",
    paths: `<path d="M4 4h8M5 6.5h6M6 9h4M7 11.5h2" fill="none" stroke="#283593" stroke-width="1.5" stroke-linecap="round"/>`,
  },
  transport: {
    bg: "#EF6C00",
    paths: `<rect x="3.5" y="6" width="9" height="5" rx="1" fill="none" stroke="#EF6C00" stroke-width="1.3"/><circle cx="5.5" cy="12" r="1" fill="#EF6C00"/><circle cx="10.5" cy="12" r="1" fill="#EF6C00"/><path d="M6 6V4h4v2" fill="none" stroke="#EF6C00" stroke-width="1.2"/>`,
  },
  tsunami: {
    bg: "#006064",
    paths: `<path d="M2 10c2-4 4-4 6 0s4 4 6 0" fill="none" stroke="#006064" stroke-width="1.8" stroke-linecap="round"/><path d="M5 5l1 2.5L7 5" fill="none" stroke="#006064" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>`,
  },
  urban_fire: {
    bg: "#BF360C",
    paths: `<rect x="4" y="6" width="8" height="7" fill="none" stroke="#BF360C" stroke-width="1.2"/><rect x="6" y="9" width="4" height="4" fill="#BF360C"/><path d="M3 6l5-3 5 3" fill="none" stroke="#BF360C" stroke-width="1.3" stroke-linejoin="round"/>`,
  },
};

const FALLBACK_PIN: PinDef = { bg: "#9E9E9E", paths: `<circle cx="8" cy="8" r="3" fill="#9E9E9E"/>` };

/** Build an SVG data URI for a teardrop map pin. */
function makeTeardropSvg(def: PinDef): string {
  // Teardrop: 30 × 42, pin tip at bottom
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="42" viewBox="0 0 30 42">
  <defs><filter id="s"><feDropShadow dx="0" dy="1" stdDeviation="1" flood-opacity="0.3"/></filter></defs>
  <path d="M15 41C15 41 1 25 1 14.5C1 6.8 7.3 0.5 15 0.5C22.7 0.5 29 6.8 29 14.5C29 25 15 41 15 41Z"
        fill="${def.bg}" stroke="#fff" stroke-width="1" filter="url(#s)"/>
  <circle cx="15" cy="14" r="9" fill="#fff"/>
  <svg x="7" y="6" width="16" height="16" viewBox="0 0 16 16">${def.paths}</svg>
</svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

/* ── Types re-exported for convenience ── */

export type { IncidentFeature };

/* ── Setup function ── */

/**
 * Initialise marker layers on the given Azure Maps instance.
 * Returns the DataSource so the parent component can update its data.
 *
 * @param atlas  The `atlas` module (imported dynamically to avoid SSR)
 * @param map    The atlas.Map instance
 * @param onMarkerClick  Callback when an individual marker is clicked
 * @param onMarkerHover  Callback when hovering over / leaving a marker
 */
export async function setupMarkerCluster(
  atlas: typeof import("azure-maps-control"),
  map: InstanceType<typeof import("azure-maps-control").Map>,
  onMarkerClick?: (feature: IncidentFeature) => void,
  onMarkerHover?: (feature: IncidentFeature | null) => void,
) {
  // Register teardrop pin icons for each incident type
  const allTypes = Object.keys(PIN_DEFS);
  await Promise.all(
    allTypes.map((type) =>
      map.imageSprite.add(`pin-${type}`, makeTeardropSvg(PIN_DEFS[type])),
    ),
  );
  // Fallback icon for unknown types
  await map.imageSprite.add("pin-unknown", makeTeardropSvg(FALLBACK_PIN));

  // Create clustered DataSource
  const dataSource = new atlas.source.DataSource(undefined, {
    cluster: true,
    clusterRadius: 60,
    clusterMaxZoom: 14,
  });
  map.sources.add(dataSource);

  // ── Cluster bubble layer ──
  const clusterBubbleLayer = new atlas.layer.BubbleLayer(
    dataSource,
    "cluster-bubbles",
    {
      radius: [
        "step",
        ["get", "point_count"],
        18, // default radius
        10,
        24, // 10+ points
        50,
        32, // 50+ points
      ] as unknown as number,
      color: "rgba(13, 107, 121, 0.7)",
      strokeColor: "rgba(13, 107, 121, 1)",
      strokeWidth: 2,
      filter: ["has", "point_count"],
    },
  );

  // ── Cluster count label layer ──
  const clusterLabelLayer = new atlas.layer.SymbolLayer(
    dataSource,
    "cluster-labels",
    {
      iconOptions: { image: "none" },
      textOptions: {
        textField: ["get", "point_count_abbreviated"],
        offset: [0, 0.4],
        size: 14,
        color: "#FFFFFF",
        font: ["StandardFont-Bold"],
      },
      filter: ["has", "point_count"],
    },
  );

  // ── Individual marker layer (teardrop pins by incident type) ──
  const iconMatch: unknown[] = [
    "match",
    ["get", "incidentType"],
  ];
  for (const type of allTypes) {
    (iconMatch as string[]).push(type, `pin-${type}`);
  }
  (iconMatch as string[]).push("pin-unknown"); // fallback

  const markerLayer = new atlas.layer.SymbolLayer(
    dataSource,
    "incident-markers",
    {
      iconOptions: {
        image: iconMatch as unknown as string,
        size: 0.85,
        anchor: "bottom",
        allowOverlap: false,
      },
      filter: ["!", ["has", "point_count"]],
    },
  );

  map.layers.add([clusterBubbleLayer, clusterLabelLayer, markerLayer]);

  // ── Cluster click-to-expand ──
  map.events.add("click", clusterBubbleLayer, (e: { shapes?: unknown[] }) => {
    if (!e.shapes || e.shapes.length === 0) return;
    const shape = e.shapes[0] as { getProperties?: () => Record<string, unknown> };
    if (!shape.getProperties) return;
    const props = shape.getProperties();
    const clusterId = props.cluster_id as number;
    if (clusterId == null) return;

    dataSource.getClusterExpansionZoom(clusterId).then((zoom: number) => {
      const geom = (shape as { getCoordinates?: () => unknown }).getCoordinates?.();
      if (geom) {
        map.setCamera({
          center: geom as [number, number],
          zoom,
          type: "ease",
          duration: 300,
        });
      }
    });
  });

  // ── Individual marker click ──
  if (onMarkerClick) {
    map.events.add("click", markerLayer, (e: { shapes?: unknown[] }) => {
      if (!e.shapes || e.shapes.length === 0) return;
      const shape = e.shapes[0] as { getProperties?: () => Record<string, unknown> };
      if (!shape.getProperties) return;
      const props = shape.getProperties();
      // Reconstruct an IncidentFeature-like object from the shape properties
      onMarkerClick({
        type: "Feature",
        id: props.incidentId as string,
        geometry: {
          type: "Point",
          coordinates: ((shape as { getCoordinates?: () => unknown }).getCoordinates?.() as [number, number]) ?? [0, 0],
        },
        properties: {
          incident_id: props.incidentId as string,
          title: props.title as string,
          incident_type: props.incidentType as string,
          status: props.status as string,
          severity: props.severity as string,
          severity_tier: props.severityTier as "advice" | "watch" | "emergency",
          affected_jurisdiction_ids: (props.affectedJurisdictionIds as string[]) ?? [],
          participating_organisation_ids: (props.participatingOrganisationIds as string[]) ?? [],
          started_at: props.startedAt as string,
          pprr_phase: (props.pprrPhase as string) ?? null,
          incident_level: (props.incidentLevel as number) ?? 1,
        },
      });
    });
  }

  // ── Individual marker hover (preview card) ──
  if (onMarkerHover) {
    map.events.add("mouseover", markerLayer, (e: { shapes?: unknown[] }) => {
      if (!e.shapes || e.shapes.length === 0) return;
      const shape = e.shapes[0] as { getProperties?: () => Record<string, unknown>; getCoordinates?: () => unknown };
      if (!shape.getProperties) return;
      const props = shape.getProperties();
      map.getCanvasContainer().style.cursor = "pointer";
      onMarkerHover({
        type: "Feature",
        id: props.incidentId as string,
        geometry: {
          type: "Point",
          coordinates: (shape.getCoordinates?.() as [number, number]) ?? [0, 0],
        },
        properties: {
          incident_id: props.incidentId as string,
          title: props.title as string,
          incident_type: props.incidentType as string,
          status: props.status as string,
          severity: props.severity as string,
          severity_tier: props.severityTier as "advice" | "watch" | "emergency",
          affected_jurisdiction_ids: (props.affectedJurisdictionIds as string[]) ?? [],
          participating_organisation_ids: (props.participatingOrganisationIds as string[]) ?? [],
          started_at: props.startedAt as string,
          pprr_phase: (props.pprrPhase as string) ?? null,
          incident_level: (props.incidentLevel as number) ?? 1,
        },
      });
    });
    map.events.add("mouseout", markerLayer, () => {
      map.getCanvasContainer().style.cursor = "";
      onMarkerHover(null);
    });
  }

  return dataSource;
}

/**
 * Convert IncidentFeature[] to atlas-compatible GeoJSON features
 * with flattened properties for SymbolLayer expressions.
 */
export function featuresToGeoJSON(
  atlas: typeof import("azure-maps-control"),
  features: IncidentFeature[],
) {
  return features.map((f) =>
    new atlas.data.Feature(
      new atlas.data.Point(f.geometry.coordinates as [number, number]),
      {
        incidentId: f.properties.incident_id,
        title: f.properties.title,
        incidentType: f.properties.incident_type,
        status: f.properties.status,
        severity: f.properties.severity,
        severityTier: f.properties.severity_tier,
        affectedJurisdictionIds: f.properties.affected_jurisdiction_ids,
        participatingOrganisationIds: f.properties.participating_organisation_ids,
        startedAt: f.properties.started_at,
        pprrPhase: f.properties.pprr_phase,
        incidentLevel: f.properties.incident_level,
      },
    ),
  );
}
