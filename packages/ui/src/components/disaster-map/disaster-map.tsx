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
import { useMapViewport } from "./use-map-viewport";

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
  const [retryKey, setRetryKey] = useState(0);
  const { getSavedViewport, saveViewport } = useMapViewport();

  // Stable callback ref
  const onMarkerClickRef = useRef(onMarkerClick);
  onMarkerClickRef.current = onMarkerClick;
  const onRenderCompleteRef = useRef(onRenderComplete);
  onRenderCompleteRef.current = onRenderComplete;

  // ── Initialise map ──
  useEffect(() => {
    if (!containerRef.current) return;

    let disposed = false;
    setMapError(false);
    setMapReady(false);

    async function initMap() {
      try {
        const atlas = await import("azure-maps-control");
        await import("azure-maps-control/dist/atlas.min.css");
        atlasRef.current = atlas;

        if (disposed || !containerRef.current) return;

        const subscriptionKey =
          process.env.NEXT_PUBLIC_AZURE_MAPS_KEY ?? "";

        // Restore saved viewport or default to Australia bounds
        const savedViewport = getSavedViewport();
        const viewOptions: Record<string, unknown> = savedViewport
          ? { center: savedViewport.center, zoom: savedViewport.zoom }
          : { bounds: [112.0, -45.0, 155.0, -9.0] as unknown as import("azure-maps-control").data.BoundingBox, padding: 20 };

        const map = new atlas.Map(containerRef.current, {
          ...viewOptions,
          language: "en-AU",
          authOptions: subscriptionKey
            ? {
                authType: atlas.AuthenticationType.subscriptionKey as unknown as import("azure-maps-control").AuthenticationType,
                subscriptionKey,
              }
            : undefined,
          style: "road",
          // Touch gesture support for mobile
          dragRotateInteraction: false,
          touchInteraction: true,
        });

        mapRef.current = map;

        map.events.add("ready", async () => {
          if (disposed) return;

          map.controls.add(new atlas.control.ZoomControl(), {
            position: atlas.ControlPosition.TopLeft as unknown as import("azure-maps-control").ControlPosition,
          });

          const ds = await setupMarkerCluster(
            atlas,
            map,
            (f: IncidentFeature) => onMarkerClickRef.current?.(f),
          );

          dataSourceRef.current = ds;
          setMapReady(true);

          // Persist viewport on pan/zoom for restoration after navigation
          map.events.add("moveend", () => {
            const cam = map.getCamera();
            if (cam.center && cam.zoom != null) {
              saveViewport({
                zoom: cam.zoom,
                center: [cam.center[0], cam.center[1]],
              });
            }
          });
        });

        // 15-second timeout — Azure Maps cold-starts can be slow on first load
        const timeout = setTimeout(() => {
          if (!disposed) setMapError(true);
        }, 15000);

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
  }, [retryKey]); // eslint-disable-line react-hooks/exhaustive-deps

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

  // Always render the container div so the map area never collapses.
  // When mapError is true, overlay an inline message instead of returning null —
  // this preserves layout height and lets the user retry without a full page reload.
  return (
    <div
      style={{ position: "relative", width: "100%", height: "100%" }}
    >
      <div
        ref={containerRef}
        className={`disaster-map-container ${className ?? ""}`}
        role="application"
        aria-label="Disaster incident map of Australia"
        style={{ width: "100%", height: "100%" }}
      />
      {mapError && (
        <div className="disaster-map-error-overlay" role="alert">
          <p>Map tiles could not be loaded.</p>
          <button
            className="disaster-map-retry-btn"
            onClick={() => setRetryKey((k) => k + 1)}
          >
            Retry
          </button>
        </div>
      )}
    </div>
  );
}

export default DisasterMap;
