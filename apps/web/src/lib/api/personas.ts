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

export async function getPersonaWorkspace(personaId: string): Promise<PersonaWorkspacePayload> {
  const response = await fetch(`${API_BASE_URL}/personas/${personaId}/workspace`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to load persona workspace");
  }

  return (await response.json()) as PersonaWorkspacePayload;
}
