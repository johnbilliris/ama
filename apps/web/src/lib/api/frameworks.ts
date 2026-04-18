const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface PreparednessFramework {
  framework_id: string;
  name: string;
  framework_type: string;
  span_of_control_guidance: string;
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
    throw new Error("Failed to load framework catalog");
  }

  return (await response.json()) as PreparednessFramework[];
}
