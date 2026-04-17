const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface DashboardPayload {
  incident: {
    incidentId: string;
    title: string;
    incidentType: string;
    status: string;
    severity: string;
    region?: string;
    startedAt?: string;
    introduction?: string;
    sourceUrl?: string;
    location?: {
      longitude: number | null;
      latitude: number | null;
    };
    impact?: {
      deaths?: number | null;
      injuries?: number | null;
      homesDestroyed?: number | null;
      businessesDestroyed?: number | null;
      insuranceCostAud?: number | null;
      insuranceCostFormatted?: string | null;
    };
  };
  participatingOrganisations: Array<{
    organisationId: string;
    name: string;
    category: string;
    status: string;
  }>;
  activeRecommendations: Array<{
    recommendation_id: string;
    type: string;
    summary: string;
    status: string;
  }>;
  signalSummary: {
    authoritativeCount: number;
    communityCount: number;
    contradictedCount: number;
  };
}

export async function getIncidentDashboard(incidentId: string): Promise<DashboardPayload> {
  const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/dashboard`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to load incident dashboard");
  }

  return (await response.json()) as DashboardPayload;
}
