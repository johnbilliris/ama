"use client";

/**
 * DisasterMap — Azure Maps wrapper client component.
 *
 * Initialises an atlas.Map centred on Australia, loads severity-coded markers
 * from GeoJSON incident data, and supports marker click events.
 *
 * Must be loaded via next/dynamic with { ssr: false }.
 */

import { useEffect, useRef, useCallback, useState } from "react";
import type { IncidentFeature } from "./types";
import { setupMarkerCluster, featuresToGeoJSON } from "./marker-cluster";

export interface DisasterMapProps {
  /** GeoJSON IncidentFeature array to render as markers */
  features: IncidentFeature[];
  /** Called when a marker (individual, not cluster) is clicked */
  onMarkerClick?: (feature: IncidentFeature) => void;
  /** Called when the map finishes rendering / re-rendering markers */
  onRenderComplete?: () => void;
  /** Additional CSS class for the map container */
  className?: string;
}

export function DisasterMap({
  features,
  onMarkerClick,
  onRenderComplete,
  className,
}: DisasterMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);
  const dataSourceRef = useRef<unknown>(null);
  const atlasRef = useRef<typeof import("azure-maps-control") | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [mapError, setMapError] = useState(false);

  // Stable callback ref
  const onMarkerClickRef = useRef(onMarkerClick);
  onMarkerClickRef.current = onMarkerClick;
  const onRenderCompleteRef = useRef(onRenderComplete);
  onRenderCompleteRef.current = onRenderComplete;

  // ── Initialise map ──
  useEffect(() => {
    if (!containerRef.current) return;

    let disposed = false;

    async function initMap() {
      try {
        const atlas = await import("azure-maps-control");
        await import("azure-maps-control/dist/atlas.min.css");
        atlasRef.current = atlas;

        if (disposed || !containerRef.current) return;

        const subscriptionKey =
          process.env.NEXT_PUBLIC_AZURE_MAPS_KEY ?? "";

        const map = new atlas.Map(containerRef.current, {
          center: [134.0, -25.5], // Centre of Australia
          zoom: 4,
          language: "en-AU",
          authOptions: subscriptionKey
            ? {
                authType: atlas.AuthenticationType.subscriptionKey as unknown as import("azure-maps-control").AuthenticationType,
                subscriptionKey,
              }
            : undefined,
          style: "road",
        });

        mapRef.current = map;

        map.events.add("ready", async () => {
          if (disposed) return;

          const ds = await setupMarkerCluster(
            atlas,
            map,
            (f: IncidentFeature) => onMarkerClickRef.current?.(f),
          );

          dataSourceRef.current = ds;
          setMapReady(true);
        });

        // 5-second timeout for tile load failure detection
        const timeout = setTimeout(() => {
          if (!mapReady && !disposed) {
            setMapError(true);
          }
        }, 5000);

        map.events.add("ready", () => clearTimeout(timeout));
      } catch {
        if (!disposed) setMapError(true);
      }
    }

    initMap();

    return () => {
      disposed = true;
      const map = mapRef.current as { dispose?: () => void } | null;
      if (map?.dispose) map.dispose();
      mapRef.current = null;
      dataSourceRef.current = null;
      atlasRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Update markers when features change ──
  const updateMarkers = useCallback(() => {
    const atlas = atlasRef.current;
    const ds = dataSourceRef.current as {
      clear: () => void;
      add: (shapes: unknown[]) => void;
    } | null;

    if (!atlas || !ds || !mapReady) return;

    ds.clear();
    if (features.length > 0) {
      const shapes = featuresToGeoJSON(atlas, features);
      ds.add(shapes);
    }
    onRenderCompleteRef.current?.();
  }, [features, mapReady]);

  useEffect(() => {
    updateMarkers();
  }, [updateMarkers]);

  if (mapError) {
    return null; // Parent will handle fallback
  }

  return (
    <div
      ref={containerRef}
      className={`disaster-map-container ${className ?? ""}`}
      role="application"
      aria-label="Disaster incident map of Australia"
      style={{ width: "100%", height: "100%" }}
    />
  );
}

export default DisasterMap;
