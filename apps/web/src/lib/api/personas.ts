const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface PersonaWorkspacePayload {
  persona: {
    persona_id: string;
    display_name: string;
    organisation_id: string;
    role: string;
  };
  tasks: Array<{
    task_id: string;
    title: string;
    status: string;
    priority: string;
  }>;
  dependencies: Array<{
    task_id: string;
    title: string;
    status: string;
  }>;
}

export class PersonaWorkspaceError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "PersonaWorkspaceError";
    this.status = status;
  }
}

export async function getPersonaWorkspace(personaId: string): Promise<PersonaWorkspacePayload> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/personas/${personaId}/workspace`, {
      cache: "no-store",
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
