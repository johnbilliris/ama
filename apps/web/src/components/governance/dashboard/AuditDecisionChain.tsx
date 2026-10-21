"use client";

import type { DecisionChainStep } from "@/lib/api/governance";

interface AuditDecisionChainProps {
  eventId: string;
  chain: DecisionChainStep[];
  chainComplete: boolean;
  onClose: () => void;
}

const STEP_ICONS: Record<string, string> = {
  trigger: "⚡",
  approval: "✓",
  action: "▶",
  notification: "📧",
};

const INTEGRITY_BADGES: Record<string, { icon: string; text: string; className: string }> = {
  verified: { icon: "✓", text: "Verified", className: "bg-green-100 text-green-800" },
  unverified: { icon: "⚠", text: "Unverified", className: "bg-yellow-100 text-yellow-800" },
  pending: { icon: "⏳", text: "Pending", className: "bg-gray-100 text-gray-600" },
};

/**
 * Decision chain timeline visualiser (US3).
 * Shows trigger → intermediate approvals → final action with evidence integrity.
 */
export function AuditDecisionChain({
  eventId,
  chain,
  chainComplete,
  onClose,
}: AuditDecisionChainProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">
          Decision Chain — {eventId}
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
          aria-label="Close decision chain"
        >
          ✕
        </button>
      </div>

      {!chainComplete && (
        <div className="mb-3 rounded bg-yellow-50 px-3 py-2 text-xs text-yellow-700">
          ⚠ Chain incomplete — final action not yet recorded
        </div>
      )}

      {chain.length === 0 ? (
        <p className="text-sm text-gray-500">No decision chain steps found.</p>
      ) : (
        <ol className="relative border-l-2 border-gray-200 pl-6">
          {chain.map((step) => {
            const icon = STEP_ICONS[step.event_type] ?? "•";
            const integrity = INTEGRITY_BADGES[step.evidence_integrity] ?? INTEGRITY_BADGES.pending;
            return (
              <li key={step.step_order} className="mb-6 last:mb-0">
                <span
                  className="absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full bg-white ring-2 ring-gray-300 text-xs"
                  aria-hidden="true"
                >
                  {icon}
                </span>
                <div className="ml-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium uppercase text-gray-500">
                      {step.event_type}
                    </span>
                    <span className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium ${integrity.className}`}>
                      {integrity.icon} {integrity.text}
                    </span>
                  </div>
                  <p className="mt-1 text-sm font-medium text-gray-800">
                    {step.description}
                  </p>
                  <div className="mt-1 text-xs text-gray-500">
                    <span>{step.actor}</span>
                    <span className="mx-2">•</span>
                    <time>{new Date(step.timestamp).toLocaleString()}</time>
                  </div>
                  {step.rationale && (
                    <p className="mt-1 text-xs text-gray-600 italic">
                      &quot;{step.rationale}&quot;
                    </p>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
