import { getApiBaseUrl } from "@/lib/api/base-url";
const API_BASE_URL = getApiBaseUrl();

export interface ApprovalPayload {
  approverPersonaId: string;
  outcome: "approved" | "rejected" | "escalated" | "timed_out";
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
