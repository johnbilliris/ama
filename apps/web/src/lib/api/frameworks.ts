const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface PreparednessFramework {
  framework_id: string;
  name: string;
  framework_type: string;
  span_of_control_guidance: string;
  status: string;
}

export async function listPreparednessFrameworks(jurisdictionId: string): Promise<PreparednessFramework[]> {
  const response = await fetch(`${API_BASE_URL}/frameworks?jurisdictionId=${jurisdictionId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to load framework catalog");
  }

  return (await response.json()) as PreparednessFramework[];
}
