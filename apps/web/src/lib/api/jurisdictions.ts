import { getApiBaseUrl } from "@/lib/api/base-url";
const API_BASE_URL = getApiBaseUrl();

export interface JurisdictionSummary {
  jurisdiction_id: string;
  name: string;
  level: string;
}

export async function listJurisdictions(): Promise<JurisdictionSummary[]> {
  const response = await fetch(`${API_BASE_URL}/jurisdictions`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to load jurisdictions");
  }

  return (await response.json()) as JurisdictionSummary[];
}
