/**
 * API client for GET /api/v1/incidents/map
 * Supports progressive loading: fetch page 1 immediately, then background-fetch
 * subsequent pages until features.length < page_size.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

/* ── Response types (matching GeoJSON FeatureCollection schema) ── */

export interface GeoJSONPoint {
  type: "Point";
  coordinates: [number, number]; // [longitude, latitude]
}

export interface IncidentFeatureProperties {
  incident_id: string;
  title: string;
  incident_type: string;
  status: string;
  severity: string;
  severity_tier: "advice" | "watch" | "emergency";
  affected_jurisdiction_ids: string[];
  participating_organisation_ids: string[];
  started_at: string;
  pprr_phase: string | null;
  incident_level: number;
}

export interface IncidentFeature {
  type: "Feature";
  id: string;
  geometry: GeoJSONPoint;
  properties: IncidentFeatureProperties;
}

export interface IncidentMapMetadata {
  total: number;
  unmapped_count: number;
  page: number;
  page_size: number;
  fetched_at: string;
}

export interface IncidentFeatureCollection {
  type: "FeatureCollection";
  features: IncidentFeature[];
  metadata: IncidentMapMetadata;
}

/* ── Filter params ── */

export interface MapFilterParams {
  type?: string;
  severity?: string;
  status?: string;
  pprr_phase?: string;
  keyword?: string;
  year_start?: number;
  year_end?: number;
}

/* ── Fetch a single page ── */

export async function fetchIncidentsMapPage(
  filters: MapFilterParams = {},
  page = 1,
  pageSize = 200,
): Promise<IncidentFeatureCollection> {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));

  if (filters.type) params.set("type", filters.type);
  if (filters.severity) params.set("severity", filters.severity);
  if (filters.status) params.set("status", filters.status);
  if (filters.pprr_phase) params.set("pprr_phase", filters.pprr_phase);
  if (filters.keyword) params.set("keyword", filters.keyword);
  if (filters.year_start != null)
    params.set("year_start", String(filters.year_start));
  if (filters.year_end != null)
    params.set("year_end", String(filters.year_end));

  const url = `${API_BASE_URL}/incidents/map?${params.toString()}`;
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(
      `Incidents map API error ${response.status}: ${body}`,
    );
  }

  return (await response.json()) as IncidentFeatureCollection;
}

/* ── Progressive loader ── */

export interface ProgressiveLoadResult {
  features: IncidentFeature[];
  metadata: IncidentMapMetadata;
  isComplete: boolean;
}

/**
 * Progressively load all pages of incident data.
 * Calls `onProgress` after each page so the UI can render incrementally.
 * Returns when all pages have been fetched or the abort signal fires.
 */
export async function loadIncidentsProgressively(
  filters: MapFilterParams = {},
  onProgress: (result: ProgressiveLoadResult) => void,
  signal?: AbortSignal,
  pageSize = 200,
): Promise<void> {
  let page = 1;
  let allFeatures: IncidentFeature[] = [];
  let latestMetadata: IncidentMapMetadata | null = null;

  while (true) {
    if (signal?.aborted) return;

    const result = await fetchIncidentsMapPage(filters, page, pageSize);
    allFeatures = [...allFeatures, ...result.features];
    latestMetadata = result.metadata;

    const isComplete = result.features.length < pageSize;

    onProgress({
      features: allFeatures,
      metadata: latestMetadata,
      isComplete,
    });

    if (isComplete) break;
    page += 1;
  }
}
