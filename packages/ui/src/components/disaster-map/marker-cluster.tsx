"use client";

/**
 * Marker and cluster rendering for the Disaster Mapper.
 *
 * - Registers three custom SVG severity icons via map.imageSprite.add()
 * - Configures a DataSource with clustering (clusterRadius: 60)
 * - Adds a SymbolLayer for individual markers with data-driven icon selection
 * - Adds a BubbleLayer for cluster circles + SymbolLayer for cluster count labels
 * - Handles cluster click-to-expand via getClusterExpansionZoom()
 */

import type { IncidentFeature } from "./types";

/* ── SVG icon data URIs ── */

const SVG_CIRCLE = `data:image/svg+xml;utf8,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="10" fill="#FFC107" stroke="#000" stroke-width="1.5"/>
  </svg>`
)}`;

const SVG_TRIANGLE = `data:image/svg+xml;utf8,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
    <polygon points="12,2 22,22 2,22" fill="#FF8C00" stroke="#000" stroke-width="1.5"/>
  </svg>`
)}`;

const SVG_DIAMOND = `data:image/svg+xml;utf8,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
    <polygon points="12,1 23,12 12,23 1,12" fill="#D32F2F" stroke="#000" stroke-width="1.5"/>
  </svg>`
)}`;

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
 */
export async function setupMarkerCluster(
  atlas: typeof import("azure-maps-control"),
  map: InstanceType<typeof import("azure-maps-control").Map>,
  onMarkerClick?: (feature: IncidentFeature) => void,
) {
  // Register severity icons
  await Promise.all([
    map.imageSprite.add("marker-advice", SVG_CIRCLE),
    map.imageSprite.add("marker-watch", SVG_TRIANGLE),
    map.imageSprite.add("marker-emergency", SVG_DIAMOND),
  ]);

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

  // ── Individual marker layer ──
  const markerLayer = new atlas.layer.SymbolLayer(
    dataSource,
    "incident-markers",
    {
      iconOptions: {
        image: [
          "match",
          ["get", "severityTier"],
          "advice",
          "marker-advice",
          "watch",
          "marker-watch",
          "emergency",
          "marker-emergency",
          "marker-advice", // default fallback
        ] as unknown as string,
        size: 1,
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
