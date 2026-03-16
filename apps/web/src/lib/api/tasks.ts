const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export async function updateTaskStatus(taskId: string, personaId: string, status: string) {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/status`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ personaId, status }),
  });

  if (!response.ok) {
    throw new Error("Failed to update coordination task status");
  }

  return response.json();
}
