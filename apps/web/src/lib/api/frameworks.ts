const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface PreparednessFramework {
  framework_id: string;
  name: string;
  abbreviation: string | null;
  description: string;
  framework_type: string;
  applicable_jurisdiction_ids: string[];
  custodian_organisation_id: string | null;
  pprr_phases: string[];
  hazard_types: string[];
  principles: string[];
  control_model: string;
  approval_rules: Record<string, string>[];
  escalation_rules: Record<string, string>[];
  span_of_control_guidance: string;
  activation_triggers: string[];
  legislative_basis: string | null;
  version: string | null;
  source_uri: string | null;
  related_framework_ids: string[];
  status: string;
}

export async function listPreparednessFrameworks(
  jurisdictionIds: string[],
  signal?: AbortSignal,
): Promise<PreparednessFramework[]> {
  const params = new URLSearchParams();
  for (const id of jurisdictionIds) {
    params.append("jurisdictionId", id);
  }

  const response = await fetch(`${API_BASE_URL}/frameworks?${params.toString()}`, {
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new Error("Failed to load framework catalogue");
  }

  return (await response.json()) as PreparednessFramework[];
}
