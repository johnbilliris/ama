const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface ApprovalPayload {
  approverPersonaId: string;
  outcome: "approved" | "rejected" | "escalated";
  rationale: string;
  conditions?: string[];
}

export async function approveRecommendation(recommendationId: string, payload: ApprovalPayload) {
  const response = await fetch(`${API_BASE_URL}/recommendations/${recommendationId}/approvals`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to submit approval decision");
  }

  return response.json();
}
