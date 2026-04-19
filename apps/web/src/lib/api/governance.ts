/**
 * Typed API client for governance dashboard endpoints.
 *
 * Provides typed request/response interfaces matching the OpenAPI contract,
 * error handling, continuation token pagination, and Cache-Control support.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

// --- Response Types ---

export interface DimensionScore {
  dimension: string;
  score: number;
  weight: number;
  weighted_score: number;
  input_count: number;
  stale: boolean;
}

export interface GovernanceHealthScore {
  id: string;
  tenant_id: string;
  score: number;
  status: "green" | "amber" | "red";
  dimensions: DimensionScore[];
  calculated_at: string;
  cache_ttl_s: number;
  has_active_incident: boolean;
}

export interface ConstitutionalGateStatus {
  gate_number: number;
  gate_name: string;
  status:
    | "compliant"
    | "non_compliant"
    | "partially_compliant"
    | "assessment_pending";
  severity: "info" | "warning" | "critical" | null;
  last_assessment_date: string | null;
  evidence_count: number;
  detail_url: string;
}

export interface ExecutiveSummaryResponse {
  health_score: GovernanceHealthScore;
  constitutional_gates: ConstitutionalGateStatus[];
  active_incident_count: number;
  resource_utilisation_pct: number;
  risk_summary: Record<string, number>;
  data_freshness: string;
  tenant_id: string;
}

export interface WidgetDefinition {
  widget_id: string;
  widget_type: string;
  display_name: string;
  priority: number;
  data_endpoint: string;
  refresh_group: "active_incident" | "steady_state" | "manual_only";
}

export interface DashboardConfigResponse {
  user_roles: string[];
  primary_role: string | null;
  widget_layout: WidgetDefinition[];
  default_view: string;
  poll_interval_ms: number;
  has_active_incident: boolean;
  cache_ttl_s: number;
  tenant_id: string;
  tenant_display_name: string;
  is_simulation: boolean;
}

export interface ComplianceMatrixEntry {
  data_source_id: string;
  data_source_name: string;
  compliance_status: string;
  last_assessment_date: string | null;
  next_assessment_due_date: string | null;
  governance_gap_count: number;
  grace_period_expiry: string | null;
  grace_period_reason: string | null;
  grace_period_countdown_days: number | null;
  category: string | null;
}

export interface ComplianceMatrixResponse {
  entries: ComplianceMatrixEntry[];
  total_count: number;
  filters_applied: Record<string, string>;
  continuation_token: string | null;
  page_size: number;
}

export interface ComplianceDetailResponse {
  data_source_id: string;
  data_source_name: string;
  compliance_status: string;
  assessment_history: Record<string, unknown>[];
  remediation_actions: Record<string, unknown>[];
  related_audit_urls: string[];
}

export interface AuditEventSummary {
  id: string;
  timestamp: string;
  actor: string;
  action_type: string;
  affected_entity: string;
  outcome: string;
  provenance_reference: string | null;
  has_decision_chain: boolean;
}

export interface AuditTrailResponse {
  events: AuditEventSummary[];
  total_count: number;
  filters_applied: Record<string, string>;
  continuation_token: string | null;
  page_size: number;
}

export interface DecisionChainStep {
  step_order: number;
  event_type: "trigger" | "approval" | "action" | "notification";
  actor: string;
  timestamp: string;
  description: string;
  rationale: string | null;
  evidence_integrity: "verified" | "unverified" | "pending";
}

export interface AuditDecisionChainResponse {
  event_id: string;
  chain: DecisionChainStep[];
  chain_complete: boolean;
}

export interface AuditExportJobResponse {
  id: string;
  status: string;
  download_url: string | null;
  progress: number;
  error_message: string | null;
}

export interface PPRRPhaseStatus {
  phase: "prevention" | "preparedness" | "response" | "recovery";
  is_active: boolean;
  indicator_status: "active" | "inactive" | "elevated";
}

export interface EmergencyPlanSummary {
  lifecycle_state: string;
  count: number;
  overdue_count: number;
}

export interface AIIMSRoleCoverage {
  role: string;
  assigned_count: number;
  required_count: number;
  is_staffed: boolean;
  coverage_pct: number;
}

export interface OperationalReadinessResponse {
  pprr_phases: PPRRPhaseStatus[];
  emergency_plans: EmergencyPlanSummary[];
  total_plans: number;
  overdue_plans_total: number;
  exercise_completion_rate_pct: number;
  exercise_breakdown: Record<string, unknown>[];
  overall_readiness_score: number;
  aiims_role_coverage: AIIMSRoleCoverage[];
  overall_role_coverage_pct: number;
  capability_gap_count: number;
  capability_gaps?: { gap_type: string; description: string; severity: string; affected_roles: string[] }[];
  volunteer_readiness?: {
    total_registered: number;
    currently_available: number;
    active_deployed: number;
    availability_rate_pct: number;
    welfare_check_compliance_pct: number;
  };
}

export interface RecoveryDomainProgress {
  domain: string;
  display_name: string;
  completion_pct: number;
  trend: "improving" | "stable" | "declining";
  target_pct: number;
  variance_from_target: number;
  is_below_target: boolean;
  is_cross_cutting: boolean;
  incident_id: string;
}

export interface RecoveryDomainDetail {
  domain: string;
  outcome_targets: Record<string, unknown>[];
  activity_completion_rates: Record<string, unknown>[];
  community_indicators: Record<string, unknown>[];
  me_evaluation_results: Record<string, unknown>[];
}

export interface RecoveryProgressResponse {
  domains: RecoveryDomainProgress[];
  active_incident_id: string | null;
  available_incidents: Record<string, unknown>[];
  has_active_recovery: boolean;
}

export interface RiskSeverityBreakdown {
  extreme: number;
  high: number;
  medium: number;
  low: number;
  total: number;
}

export interface AWSPrincipleCompliance {
  principle: string;
  display_name: string;
  compliant_count: number;
  total_count: number;
  compliance_rate_pct: number;
  non_compliant_warning_ids: string[];
}

export interface AlertComplianceMetrics {
  avg_approval_latency_s: number;
  acceptable_threshold_s: number;
  exceeds_threshold: boolean;
  alerts_exceeding_threshold: Record<string, unknown>[];
  aws_tier_usage: Record<string, number>;
  broadcast_reach_pct: number;
  principle_compliance: AWSPrincipleCompliance[];
  overall_principle_compliance_pct: number;
}

export interface RiskWarningResponse {
  risk_severity: RiskSeverityBreakdown;
  treatment_closure_rate_pct: number;
  alert_compliance: AlertComplianceMetrics;
  top_risks: Record<string, unknown>[];
}

export interface RiskDetailResponse {
  risk_id: string;
  description: string;
  severity: string;
  likelihood: string;
  consequence: string;
  treatments: Record<string, unknown>[];
  treatment_history: Record<string, unknown>[];
  related_audit_urls: string[];
}

// --- Session ID for audit correlation ---

let _sessionId: string | null = null;

function getSessionId(): string {
  if (!_sessionId) {
    _sessionId = crypto.randomUUID();
  }
  return _sessionId;
}

// --- API Client Functions ---

async function dashboardFetch<T>(
  path: string,
  options: { bypassCache?: boolean; headers?: Record<string, string> } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Session-Id": getSessionId(),
    ...options.headers,
  };

  if (options.bypassCache) {
    headers["Cache-Control"] = "no-cache";
  }

  const response = await fetch(`${API_BASE_URL}/governance/dashboard${path}`, {
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      body.detail || `Dashboard API error: ${response.status}`,
    );
  }

  return (await response.json()) as T;
}

export async function getDashboardConfig(
  roleHeader?: string,
): Promise<DashboardConfigResponse> {
  const headers: Record<string, string> = {};
  if (roleHeader) {
    headers["X-User-Roles"] = roleHeader;
  }
  return dashboardFetch<DashboardConfigResponse>("/config", { headers });
}

export async function getExecutiveSummary(
  bypassCache = false,
): Promise<ExecutiveSummaryResponse> {
  return dashboardFetch<ExecutiveSummaryResponse>("/summary", { bypassCache });
}

export async function getComplianceMatrix(params?: {
  compliance_status?: string;
  category?: string;
  sort_by?: string;
  sort_dir?: string;
  page_size?: number;
  continuation_token?: string;
}): Promise<ComplianceMatrixResponse> {
  const query = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) query.set(k, String(v));
    });
  }
  const qs = query.toString();
  return dashboardFetch<ComplianceMatrixResponse>(
    `/compliance${qs ? `?${qs}` : ""}`,
  );
}

export async function getComplianceDetail(
  dataSourceId: string,
): Promise<ComplianceDetailResponse> {
  return dashboardFetch<ComplianceDetailResponse>(
    `/compliance/${encodeURIComponent(dataSourceId)}`,
  );
}

export async function getAuditTrail(params?: {
  date_from?: string;
  date_to?: string;
  actor?: string;
  action_type?: string;
  affected_entity?: string;
  keyword?: string;
  page_size?: number;
  continuation_token?: string;
}): Promise<AuditTrailResponse> {
  const query = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) query.set(k, String(v));
    });
  }
  const qs = query.toString();
  return dashboardFetch<AuditTrailResponse>(`/audit${qs ? `?${qs}` : ""}`);
}

export async function getDecisionChain(
  eventId: string,
): Promise<AuditDecisionChainResponse> {
  return dashboardFetch<AuditDecisionChainResponse>(
    `/audit/${encodeURIComponent(eventId)}/chain`,
  );
}

export async function createAuditExport(body: {
  format: "pdf" | "csv" | "json";
  filter_params?: Record<string, unknown>;
  record_ids?: string[];
}): Promise<AuditExportJobResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Session-Id": getSessionId(),
  };

  const response = await fetch(
    `${API_BASE_URL}/governance/dashboard/audit/export`,
    {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    },
  );

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `Export error: ${response.status}`);
  }

  return (await response.json()) as AuditExportJobResponse;
}

export async function getExportStatus(
  jobId: string,
): Promise<AuditExportJobResponse> {
  return dashboardFetch<AuditExportJobResponse>(
    `/audit/export/${encodeURIComponent(jobId)}`,
  );
}

export async function getOperationalReadiness(): Promise<OperationalReadinessResponse> {
  return dashboardFetch<OperationalReadinessResponse>("/readiness");
}

export async function getRecoveryProgress(
  incidentId?: string,
): Promise<RecoveryProgressResponse> {
  const qs = incidentId ? `?incident_id=${encodeURIComponent(incidentId)}` : "";
  return dashboardFetch<RecoveryProgressResponse>(`/recovery${qs}`);
}

export async function getRecoveryDomainDetail(
  domain: string,
  incidentId?: string,
): Promise<RecoveryDomainDetail> {
  const qs = incidentId ? `?incident_id=${encodeURIComponent(incidentId)}` : "";
  return dashboardFetch<RecoveryDomainDetail>(
    `/recovery/${encodeURIComponent(domain)}${qs}`,
  );
}

export async function getRiskAndWarning(): Promise<RiskWarningResponse> {
  return dashboardFetch<RiskWarningResponse>("/risk");
}

export async function getRiskDetail(
  riskId: string,
): Promise<RiskDetailResponse> {
  return dashboardFetch<RiskDetailResponse>(
    `/risk/${encodeURIComponent(riskId)}`,
  );
}

// --- Polling Hook ---

import { useCallback, useEffect, useRef, useState } from "react";

export function useGovernancePolling<T>(
  fetcher: (bypassCache: boolean) => Promise<T>,
  pollIntervalMs: number,
  enabled = true,
): {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refresh: () => void;
} {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const doFetch = useCallback(
    async (bypass = false) => {
      try {
        setLoading(true);
        const result = await fetcher(bypass);
        setData(result);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e : new Error(String(e)));
      } finally {
        setLoading(false);
      }
    },
    [fetcher],
  );

  useEffect(() => {
    if (!enabled) return;
    doFetch(false);
    intervalRef.current = setInterval(() => doFetch(false), pollIntervalMs);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [doFetch, pollIntervalMs, enabled]);

  const refresh = useCallback(() => doFetch(true), [doFetch]);

  return { data, error, loading, refresh };
}

// --- Widget Telemetry Hook (T098) ---

export function useWidgetTelemetry(
  viewName: string,
  widgetType: string,
): { markRenderStart: () => void; markRenderEnd: () => void } {
  const startRef = useRef<number>(0);

  const markRenderStart = useCallback(() => {
    startRef.current = performance.now();
  }, []);

  const markRenderEnd = useCallback(() => {
    if (startRef.current > 0) {
      const duration = performance.now() - startRef.current;
      // In production, send to App Insights JS SDK (no PII per FR-035)
      if (typeof window !== "undefined" && process.env.NODE_ENV === "production") {
        console.debug(
          `[telemetry] widget=${widgetType} view=${viewName} render=${duration.toFixed(1)}ms`,
        );
      }
      startRef.current = 0;
    }
  }, [viewName, widgetType]);

  return { markRenderStart, markRenderEnd };
}
