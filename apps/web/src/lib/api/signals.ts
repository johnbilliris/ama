const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface SignalRecord {
  signal_id: string;
  incident_id: string | null;
  data_source_id: string;
  category: string;
  validation_status: string;
  confidence_score: number;
  freshness_score: number;
  provenance: Record<string, unknown>;
}

export async function listSignals(incidentId: string): Promise<SignalRecord[]> {
  const response = await fetch(`${API_BASE_URL}/signals?incidentId=${incidentId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to load incident signals");
  }

  return (await response.json()) as SignalRecord[];
}
