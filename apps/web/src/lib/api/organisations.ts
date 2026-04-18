const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface PreparednessOrganisation {
  organisation_id: string;
  name: string;
  category: string;
  jurisdiction_ids: string[];
  operating_role: string;
  authority_level: string;
  status: string;
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
    throw new Error("Failed to load organisation catalog");
  }

  return (await response.json()) as PreparednessOrganisation[];
}
