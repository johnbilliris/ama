import { getApiBaseUrl } from "@/lib/api/base-url";
const API_BASE_URL = getApiBaseUrl();

export class SignalsApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

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

export interface SignalPage {
  items: SignalRecord[];
  total: number;
}

export async function listSignals(incidentId: string, signal?: AbortSignal): Promise<SignalRecord[]> {
  const response = await fetch(`${API_BASE_URL}/signals?incidentId=${incidentId}`, {
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new SignalsApiError(response.status, "Failed to load incident signals");
  }

  const body: unknown = await response.json();
  if (
    !body ||
    typeof body !== "object" ||
    !Array.isArray((body as { items?: unknown }).items) ||
    typeof (body as { total?: unknown }).total !== "number"
  ) {
    throw new Error("Signals API returned an unexpected response shape");
  }

  return (body as SignalPage).items;
}
