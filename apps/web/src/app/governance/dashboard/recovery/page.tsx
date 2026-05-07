"use client";

import { useEffect, useState } from "react";
import { RecoveryDomainTracker } from "@/components/governance/dashboard/RecoveryDomainTracker";
import { WidgetErrorBoundary } from "@/components/governance/dashboard/WidgetErrorBoundary";
import {
  getRecoveryProgress,
  getRecoveryDomainDetail,
  type RecoveryProgressResponse,
  type RecoveryDomainDetail,
} from "@/lib/api/governance";
import {
  ClaimsVelocityDashboard,
  type ClaimsVelocitySnapshot,
} from "@/components/claims-velocity";

const FR_024_BUILT_SUBDOMAINS = [
  "housing-restoration",
  "infrastructure-rebuild",
] as const;

const FR_024_ECONOMIC_SUBDOMAINS = [
  "insurance-recovery",
  "small-business-grants",
  "supply-chain-restoration",
  "tourism-reactivation",
] as const;

const PLACEHOLDER_CLAIMS_VELOCITY: ClaimsVelocitySnapshot = {
  as_at: new Date().toISOString(),
  claims_lodged: 0,
  claims_closed: 0,
  dollars_lodged: 0,
  dollars_paid: 0,
  lga_breakdown: [],
};

interface SendaiCounterfactual {
  baseline_loss: number;
  projected_loss: number;
  ratio: number;
  threshold: number;
  status: "satisfied" | "blocked";
}

/**
 * Recovery progress view page (US5).
 * 5 domains with progress, trends, incident selector, and domain detail.
 */
export default function RecoveryPage() {
  const [data, setData] = useState<RecoveryProgressResponse | null>(null);
  const [detail, setDetail] = useState<RecoveryDomainDetail | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [claimsVelocity, setClaimsVelocity] = useState<ClaimsVelocitySnapshot>(
    PLACEHOLDER_CLAIMS_VELOCITY,
  );
  const [sendai, setSendai] = useState<SendaiCounterfactual | null>(null);
  const [sendaiError, setSendaiError] = useState<string | null>(null);

  const fetchData = async (incidentId?: string) => {
    try {
      setLoading(true);
      const result = await getRecoveryProgress(incidentId);
      setData(result);
    } catch {
      // handled by boundary
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    fetch("/api/recovery/claims-velocity", { signal: ctrl.signal })
      .then(async (res) => {
        if (!res.ok) return;
        const body = (await res.json()) as ClaimsVelocitySnapshot;
        setClaimsVelocity(body);
      })
      .catch(() => {
        /* keep placeholder */
      });
    return () => ctrl.abort();
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    fetch("/api/recovery/sendai-counterfactual", { signal: ctrl.signal })
      .then(async (res) => {
        if (res.status === 422) {
          const body = await res.json().catch(() => ({}));
          setSendaiError(
            (body as { detail?: string }).detail ?? "Sendai counterfactual blocked.",
          );
          return;
        }
        if (!res.ok) return;
        const body = (await res.json()) as SendaiCounterfactual;
        setSendai(body);
      })
      .catch(() => {
        /* silent */
      });
    return () => ctrl.abort();
  }, []);

  const handleDomainClick = async (domain: string) => {
    try {
      const d = await getRecoveryDomainDetail(domain, selectedIncident);
      setDetail(d);
    } catch {
      // silently fail
    }
  };

  if (loading && !data) {
    return <div className="h-64 animate-pulse rounded-lg bg-gray-200" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Recovery Progress</h2>
        {data && data.available_incidents.length > 0 && (
          <select
            value={selectedIncident ?? ""}
            onChange={(e) => {
              const val = e.target.value || undefined;
              setSelectedIncident(val);
              fetchData(val);
            }}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            aria-label="Select incident for recovery view"
          >
            <option value="">Latest incident</option>
            {data.available_incidents.map((inc: Record<string, unknown>) => (
              <option key={String(inc.incident_id)} value={String(inc.incident_id)}>
                {String(inc.name)}
              </option>
            ))}
          </select>
        )}
      </div>

      {data && !data.has_active_recovery ? (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
          <p className="text-lg text-gray-600">No active recovery programme</p>
          <p className="mt-2 text-sm text-gray-500">
            Recovery tracking will appear here when a recovery programme is initiated.
          </p>
          <a
            href="/recovery/catalogue"
            className="mt-4 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            View Recovery Catalogue
          </a>
        </div>
      ) : (
        <WidgetErrorBoundary widgetName="Recovery Domains">
          {data && (
            <RecoveryDomainTracker
              domains={data.domains}
              onDomainClick={handleDomainClick}
            />
          )}
        </WidgetErrorBoundary>
      )}

      {/* Domain detail slide-out */}
      {detail && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900 capitalize">
              {detail.domain.replace(/_/g, " ")} Recovery Detail
            </h3>
            <button
              onClick={() => setDetail(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <h4 className="text-xs font-semibold text-gray-700">Outcome Targets</h4>
              {detail.outcome_targets.map((t, i) => (
                <p key={i} className="text-xs text-gray-600">
                  {String(t.target_name)}: {String(t.current_value)}/{String(t.target_value)}
                </p>
              ))}
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-700">Activity Completion</h4>
              {detail.activity_completion_rates.map((a, i) => (
                <p key={i} className="text-xs text-gray-600">
                  {String(a.activity)}: {String(a.rate_pct)}%
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      <section
        className="grid gap-3 lg:grid-cols-2"
        data-testid="fr-024-recovery-environments"
      >
        <article
          className="rounded-lg border border-slate-200 bg-white p-4"
          data-testid="recovery-env-built"
        >
          <h3 className="text-sm font-semibold">Built environment (FR-024)</h3>
          <ul className="mt-2 list-disc pl-5 text-xs text-slate-600">
            {FR_024_BUILT_SUBDOMAINS.map((sub) => (
              <li key={sub} data-testid={`fr-024-${sub}`}>
                {sub}
              </li>
            ))}
          </ul>
        </article>
        <article
          className="rounded-lg border border-slate-200 bg-white p-4"
          data-testid="recovery-env-economic"
        >
          <h3 className="text-sm font-semibold">Economic environment (FR-024)</h3>
          <ul className="mt-2 list-disc pl-5 text-xs text-slate-600">
            {FR_024_ECONOMIC_SUBDOMAINS.map((sub) => (
              <li key={sub} data-testid={`fr-024-${sub}`}>
                {sub}
              </li>
            ))}
          </ul>
          {sendai ? (
            <dl className="mt-3 grid grid-cols-3 gap-2 text-xs">
              <div>
                <dt className="text-slate-500">Baseline loss</dt>
                <dd className="font-mono">${sendai.baseline_loss.toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Projected loss</dt>
                <dd className="font-mono">${sendai.projected_loss.toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Sendai ratio</dt>
                <dd
                  className={`font-mono ${
                    sendai.status === "blocked" ? "text-rose-700" : "text-emerald-700"
                  }`}
                  data-testid="sendai-ratio"
                >
                  {sendai.ratio.toFixed(1)}
                </dd>
              </div>
            </dl>
          ) : null}
          {sendaiError ? (
            <p
              className="mt-2 rounded-md bg-rose-50 p-2 text-xs text-rose-900"
              role="alert"
              data-testid="sendai-threshold-warning"
            >
              {sendaiError}
            </p>
          ) : null}
        </article>
      </section>

      <section data-testid="recovery-claims-velocity">
        <ClaimsVelocityDashboard snapshot={claimsVelocity} />
      </section>
    </div>
  );
}
