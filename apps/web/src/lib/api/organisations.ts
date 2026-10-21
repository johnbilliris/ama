import { getApiBaseUrl } from "@/lib/api/base-url";
const API_BASE_URL = getApiBaseUrl();

export interface PreparednessOrganisation {
  organisation_id: string;
  name: string;
  abbreviation: string | null;
  category: string;
  jurisdiction_ids: string[];
  operating_role: string;
  authority_level: string;
  status: string;
  aiims_functions: string[];
  lead_agency_for: string[];
  primary_capabilities: string[];
  hazard_types: string[];
  workforce_type: string | null;
  legislative_basis: string | null;
  mutual_aid_partner_ids: string[];
  activation_triggers: string[];
}

export async function listPreparednessOrganisations(
  jurisdictionIds: string[],
  signal?: AbortSignal,
): Promise<PreparednessOrganisation[]> {
  const params = new URLSearchParams();
  for (const id of jurisdictionIds) {
    params.append("jurisdictionId", id);
  }

  const response = await fetch(`${API_BASE_URL}/organisations?${params.toString()}`, {
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new Error("Failed to load organisation catalogue");
  }

  return (await response.json()) as PreparednessOrganisation[];
}
