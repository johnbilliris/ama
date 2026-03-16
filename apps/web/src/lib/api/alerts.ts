const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export async function publishAlert(alertId: string, publishedByPersonaId: string) {
  const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/publish`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ publishedByPersonaId }),
  });

  if (!response.ok) {
    throw new Error("Failed to publish public alert");
  }

  return response.json();
}
