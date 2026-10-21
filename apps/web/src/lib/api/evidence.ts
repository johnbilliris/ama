import { getApiBaseUrl } from "@/lib/api/base-url";
import type {
  AuditTrace,
  BenchmarkEntry,
  CausalChain,
  DeltaScorecard,
  KpiLadderView,
  PublicInformationRender,
} from "@ama/domain";

const API_BASE_URL = getApiBaseUrl();

export class EvidenceApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "EvidenceApiError";
  }
}

interface EvidenceRequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

async function evidenceRequest<T>(
  path: string,
  options: EvidenceRequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "x-ama-correlation-id": crypto.randomUUID(),
    ...options.headers,
  };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(`${API_BASE_URL}/v1/evidence${path}`, {
    method: options.method ?? "GET",
    cache: "no-store",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({}));
    throw new EvidenceApiError(
      response.status,
      String(problem.detail ?? problem.title ?? `Evidence API error ${response.status}`),
    );
  }
  return (await response.json()) as T;
}

export async function getMeasurementMethod(signal?: AbortSignal): Promise<string> {
  const response = await fetch(
    `${API_BASE_URL}/v1/evidence/measurement-method?format=markdown`,
    {
      cache: "no-store",
      headers: {
        Accept: "text/markdown",
        "x-ama-correlation-id": crypto.randomUUID(),
      },
      signal,
    },
  );
  if (!response.ok) {
    throw new EvidenceApiError(response.status, `Measurement method error ${response.status}`);
  }
  return response.text();
}

export function getKpiLadder(
  includeRiskAdjusted: boolean,
  capstoneScId: string | null,
  signal?: AbortSignal,
): Promise<KpiLadderView> {
  const params = new URLSearchParams({
    include_risk_adjusted: String(includeRiskAdjusted),
  });
  if (capstoneScId) params.set("capstone_sc_id", capstoneScId);
  return evidenceRequest<KpiLadderView>(`/kpi-ladder?${params}`, { signal });
}

export function getLatestScorecard(
  scenarioId: string,
  signal?: AbortSignal,
): Promise<DeltaScorecard | null> {
  return evidenceRequest<DeltaScorecard | null>(
    `/scorecards/latest?scenario_id=${encodeURIComponent(scenarioId)}`,
    { signal },
  );
}

export function runReplay(
  scenarioId: string,
  input: {
    seed: string;
    run_pair_id: string;
    repetitions: number;
    allow_degraded_mode: boolean;
  },
  signal?: AbortSignal,
): Promise<DeltaScorecard> {
  return evidenceRequest<DeltaScorecard>(
    `/scenarios/${encodeURIComponent(scenarioId)}/replay`,
    { method: "POST", body: input, signal },
  );
}

export function getCausalChain(
  capabilityId: string,
  signal?: AbortSignal,
): Promise<CausalChain> {
  return evidenceRequest<CausalChain>(
    `/causal-chains/${encodeURIComponent(capabilityId)}`,
    { signal },
  );
}

export function getBenchmarks(
  kpiId: string,
  jurisdiction: string,
  signal?: AbortSignal,
): Promise<BenchmarkEntry[]> {
  return evidenceRequest<BenchmarkEntry[]>(
    `/benchmarks/${encodeURIComponent(kpiId)}?jurisdiction=${encodeURIComponent(jurisdiction)}`,
    { signal },
  );
}

export function getAuditTrace(
  valueId: string,
  signal?: AbortSignal,
): Promise<AuditTrace> {
  return evidenceRequest<AuditTrace>(
    `/audit/${encodeURIComponent(valueId)}`,
    { signal },
  );
}

export function getPublicInformation(
  scenarioId: string,
  language: string,
  signal?: AbortSignal,
): Promise<PublicInformationRender> {
  return evidenceRequest<PublicInformationRender>(
    `/public-information/${encodeURIComponent(scenarioId)}?lang=${encodeURIComponent(language)}`,
    { signal },
  );
}
