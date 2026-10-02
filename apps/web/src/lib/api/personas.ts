import { getApiBaseUrl } from "@/lib/api/base-url";
const API_BASE_URL = getApiBaseUrl();

export interface PersonaWorkspacePayload {
  persona: {
    persona_id: string;
    display_name: string;
    organisation_id: string;
    jurisdiction_id: string;
    role: string;
    decision_rights?: string[];
    information_needs?: string[];
    communication_pathways?: string[];
  };
  tasks: Array<{
    task_id: string;
    title: string;
    status: string;
    priority: string;
    version?: number;
  }>;
  dependencies: Array<{
    taskId: string;
    title: string;
    status: string;
    ownerOrganisationId: string;
    expectedCompletion?: string | null;
    blockerReason?: string | null;
  }>;
  incidentId?: string;
  inboundRequests?: Array<Record<string, unknown>>;
  pendingApprovals?: Array<Record<string, unknown>>;
}

export class PersonaWorkspaceError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "PersonaWorkspaceError";
    this.status = status;
  }
}

export async function getPersonaWorkspace(
  personaId: string,
  incidentId: string,
  tenantId?: string,
): Promise<PersonaWorkspacePayload> {
  let response: Response;
  try {
    const params = new URLSearchParams({ incidentId });
    response = await fetch(`${API_BASE_URL}/personas/${personaId}/workspace?${params.toString()}`, {
      cache: "no-store",
      headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
    });
  } catch (cause) {
    throw new PersonaWorkspaceError(
      cause instanceof Error ? cause.message : "Network request failed",
      0,
    );
  }

  if (!response.ok) {
    let message = `Failed to load persona workspace (HTTP ${response.status})`;
    try {
      const body = (await response.json()) as { message?: unknown };
      if (typeof body?.message === "string" && body.message.length > 0) {
        message = body.message;
      }
    } catch {
      // Body was not JSON — keep the default message.
    }
    throw new PersonaWorkspaceError(message, response.status);
  }

  return (await response.json()) as PersonaWorkspacePayload;
}
