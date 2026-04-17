"use client";

/**
 * useDisasterMapFilters — URL-synced filter state for the Disaster Mapper.
 *
 * Reads/writes URL query params via useSearchParams from next/navigation.
 * Supports multi-value comma-separated params for type, severity, status,
 * and pprr_phase. Keyword changes are debounced at 300ms; all others are
 * immediate.
 */

import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import type { MapFilterParams } from "./types";

export type { MapFilterParams };

/* ── Constants ── */

export const INCIDENT_TYPES = [
  "biosecurity",
  "bushfire",
  "criminal",
  "cyclone",
  "earthquake",
  "environment",
  "extreme_heat",
  "flood",
  "health",
  "industrial",
  "landslide",
  "maritime_coastal",
  "other",
  "pandemic",
  "storm",
  "tornado",
  "transport",
  "tsunami",
  "urban_fire",
] as const;

export const SEVERITY_TIERS = [
  { label: "Advice", values: ["advisory"] },
  { label: "Watch and Act", values: ["watch"] },
  { label: "Emergency Warning", values: ["warning", "emergency"] },
] as const;

export const OPERATIONAL_STATUSES = [
  "monitoring",
  "active",
  "stabilising",
  "recovery",
  "closed",
] as const;

export const PPRR_PHASES = [
  "prevention",
  "preparedness",
  "response",
  "recovery",
] as const;

/* ── Hook ── */

export interface DisasterMapFilters {
  /** Current filter params (ready for API call) */
  filters: MapFilterParams;
  /** Set a specific filter — triggers URL update */
  setFilter: <K extends keyof MapFilterParams>(
    key: K,
    value: MapFilterParams[K],
  ) => void;
  /** Reset all filters to empty */
  resetAll: () => void;
  /** Debounced keyword value from the search input */
  keywordInput: string;
  /** Set the keyword input (debounced before URL update) */
  setKeywordInput: (value: string) => void;
}

function parseCSV(value: string | null): string[] {
  if (!value) return [];
  return value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean);
}

function parseIntOrNull(value: string | null): number | undefined {
  if (!value) return undefined;
  const n = parseInt(value, 10);
  return isNaN(n) ? undefined : n;
}

export function useDisasterMapFilters(): DisasterMapFilters {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // Parse current URL params into filter state
  const filtersFromURL: MapFilterParams = {
    type: searchParams.get("type") || undefined,
    severity: searchParams.get("severity") || undefined,
    status: searchParams.get("status") || undefined,
    pprr_phase: searchParams.get("pprr_phase") || undefined,
    keyword: searchParams.get("keyword") || undefined,
    year_start: parseIntOrNull(searchParams.get("year_start")),
    year_end: parseIntOrNull(searchParams.get("year_end")),
  };

  // Local state for debounced keyword
  const [keywordInput, setKeywordInputState] = useState(
    filtersFromURL.keyword ?? "",
  );
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── URL updater ──
  const updateURL = useCallback(
    (newFilters: MapFilterParams) => {
      const params = new URLSearchParams();
      if (newFilters.type) params.set("type", newFilters.type);
      if (newFilters.severity) params.set("severity", newFilters.severity);
      if (newFilters.status) params.set("status", newFilters.status);
      if (newFilters.pprr_phase)
        params.set("pprr_phase", newFilters.pprr_phase);
      if (newFilters.keyword) params.set("keyword", newFilters.keyword);
      if (newFilters.year_start != null)
        params.set("year_start", String(newFilters.year_start));
      if (newFilters.year_end != null)
        params.set("year_end", String(newFilters.year_end));

      const qs = params.toString();
      router.push(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    },
    [router, pathname],
  );

  const setFilter = useCallback(
    <K extends keyof MapFilterParams>(key: K, value: MapFilterParams[K]) => {
      const updated = { ...filtersFromURL, [key]: value || undefined };
      updateURL(updated);
    },
    [filtersFromURL, updateURL],
  );

  const resetAll = useCallback(() => {
    setKeywordInputState("");
    router.push(pathname, { scroll: false });
  }, [router, pathname]);

  // ── Keyword debounce ──
  const setKeywordInput = useCallback(
    (value: string) => {
      setKeywordInputState(value);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        const updated = { ...filtersFromURL, keyword: value || undefined };
        updateURL(updated);
      }, 300);
    },
    [filtersFromURL, updateURL],
  );

  // Sync keyword state with URL on external navigation
  useEffect(() => {
    const urlKeyword = searchParams.get("keyword") ?? "";
    setKeywordInputState(urlKeyword);
  }, [searchParams]);

  // Cleanup debounce timer
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return {
    filters: filtersFromURL,
    setFilter,
    resetAll,
    keywordInput,
    setKeywordInput,
  };
}

/* ── Helper: toggle a value in a comma-separated param ── */

export function toggleCSVValue(
  current: string | undefined,
  value: string,
): string | undefined {
  const values = current ? parseCSV(current) : [];
  const idx = values.indexOf(value);
  if (idx >= 0) {
    values.splice(idx, 1);
  } else {
    values.push(value);
  }
  return values.length > 0 ? values.join(",") : undefined;
}

/** Check if a value is present in a comma-separated param */
export function csvHasValue(
  current: string | undefined,
  value: string,
): boolean {
  if (!current) return false;
  return parseCSV(current).includes(value);
}
