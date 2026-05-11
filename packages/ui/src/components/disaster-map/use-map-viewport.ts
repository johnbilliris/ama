"use client";

/**
 * useMapViewport — sessionStorage-backed persistence for Azure Maps viewport.
 *
 * Saves zoom/center on map moveend (debounced 500ms) and restores on mount.
 * Gracefully degrades if sessionStorage is unavailable (privacy mode, etc.).
 */

import { useCallback, useRef } from "react";

const DEFAULT_STORAGE_KEY = "disaster-map-viewport";

export interface MapViewport {
  zoom: number;
  center: [number, number];
}

export function useMapViewport(storageKey: string = DEFAULT_STORAGE_KEY) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const getSavedViewport = useCallback((): MapViewport | null => {
    try {
      const raw = sessionStorage.getItem(storageKey);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (
        typeof parsed.zoom === "number" &&
        Array.isArray(parsed.center) &&
        parsed.center.length === 2 &&
        typeof parsed.center[0] === "number" &&
        typeof parsed.center[1] === "number"
      ) {
        return parsed as MapViewport;
      }
      return null;
    } catch {
      return null;
    }
  }, [storageKey]);

  const saveViewport = useCallback(
    (viewport: MapViewport, options?: { immediate?: boolean }) => {
      if (timerRef.current) clearTimeout(timerRef.current);
      const persist = () => {
        try {
          sessionStorage.setItem(storageKey, JSON.stringify(viewport));
        } catch {
          // Graceful degradation — sessionStorage may be unavailable
        }
      };
      if (options?.immediate) {
        timerRef.current = null;
        persist();
      } else {
        timerRef.current = setTimeout(persist, 500);
      }
    },
    [storageKey],
  );

  return { getSavedViewport, saveViewport };
}
