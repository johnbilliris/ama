/**
 * Shared type re-exports from the web app's API client.
 * This allows packages/ui components to reference the same types
 * without directly importing from apps/web.
 */

export interface GeoJSONPoint {
  type: "Point";
  coordinates: [number, number];
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

export interface MapFilterParams {
  type?: string;
  severity?: string;
  status?: string;
  pprr_phase?: string;
  keyword?: string;
  year_start?: number;
  year_end?: number;
}
