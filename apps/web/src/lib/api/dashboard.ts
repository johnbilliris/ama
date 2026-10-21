import { getApiBaseUrl } from "@/lib/api/base-url";
const API_BASE_URL = getApiBaseUrl();

export interface DashboardPayload {
  incident: {
    incidentId: string;
    title: string;
    incidentType: string;
    status: string;
    severity: string;
    actorPersonaId?: string | null;
    frameworkContext?: Array<{
      frameworkId: string;
      name: string;
      frameworkType: string;
      principles: string[];
      status: string;
    }>;
    geometry?: Record<string, unknown> | null;
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
    approvalAction?: {
      allowed: boolean;
      requiresPersona: boolean;
    };
    requiresManualReview?: boolean;
    degradedSupportingSources?: string[];
  }>;
  activeTasks: Array<{
    task_id: string;
    title: string;
    status: string;
    priority: string;
  }>;
  signalSummary: {
    authoritativeCount: number;
    communityCount: number;
    contradictedCount: number;
    degradedSources?: Array<{
      sourceId: string;
      status: string;
      reason: string;
      since: string;
    }>;
  };
}

export class ApiHttpError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function getIncidentDashboard(incidentId: string, signal?: AbortSignal): Promise<DashboardPayload> {
  const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/dashboard`, {
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new ApiHttpError(404, "Incident not found");
    }
    if (response.status === 401 || response.status === 403) {
      throw new ApiHttpError(response.status, "Unauthorized");
    }
    throw new ApiHttpError(response.status, "Failed to load incident dashboard");
  }

  return (await response.json()) as DashboardPayload;
}
