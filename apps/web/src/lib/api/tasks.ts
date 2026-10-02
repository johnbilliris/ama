import { getApiBaseUrl } from "@/lib/api/base-url";
const API_BASE_URL = getApiBaseUrl();

export type TaskStatus = "queued" | "in_progress" | "blocked" | "completed";

interface UpdateTaskInput {
  taskId: string;
  personaId: string;
  status: TaskStatus;
  blockerReason?: string;
  expectedCompletion?: string;
  ifMatch?: number;
}

export async function updateTaskStatus(input: UpdateTaskInput) {
  const payload: Record<string, unknown> = {
    personaId: input.personaId,
    status: input.status,
  };
  if (input.blockerReason) payload.blockerReason = input.blockerReason;
  if (input.expectedCompletion) payload.expectedCompletion = input.expectedCompletion;
  if (typeof input.ifMatch === "number") payload.ifMatch = input.ifMatch;

  const response = await fetch(`${API_BASE_URL}/tasks/${input.taskId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let message = "Failed to update coordination task status";
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body?.detail === "string" && body.detail.length > 0) {
        message = body.detail;
      }
    } catch {
      // keep default message
    }
    throw new Error(`${message} (HTTP ${response.status})`);
  }

  return response.json();
}
