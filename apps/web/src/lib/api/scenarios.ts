const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface ScenarioRunPayload {
  scenario_run_id: string;
  scenario_name: string;
  scenario_type: string;
  jurisdiction_ids: string[];
  organisation_ids: string[];
  framework_ids: string[];
  coordination_gap_summary: string[];
  generated_findings: string[];
}

export async function replayPreparednessScenario(scenarioName: string, scenarioType: string, jurisdictionIds: string[]) {
  const response = await fetch(`${API_BASE_URL}/scenarios/replay`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ scenarioName, scenarioType, jurisdictionIds }),
  });

  if (!response.ok) {
    throw new Error("Failed to replay preparedness scenario");
  }

  return (await response.json()) as ScenarioRunPayload;
}
