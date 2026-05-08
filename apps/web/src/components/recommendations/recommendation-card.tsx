/**
 * Spec 036 T086 — Recommendation card with citation grounding.
 *
 * Initial scaffold for the Risk Manager UI's recommendation surface. Wraps a
 * single agent recommendation (from the spec-027 governance event payload)
 * with:
 *
 *   - the recommendation text + agent badge,
 *   - a stacked list of ``<CitationCard />`` instances (FR-RAG-AG-03),
 *   - a ``<DegradedModeBadge />`` when the agent is operating from the
 *     offline cache (FR-RAG-LS-02).
 *
 * Renders nothing visual when ``citations`` is empty AND ``degraded`` is
 * false — i.e. legacy non-grounded responses. The grounded path activates
 * when the agent's per-agent feature flag is on and retrieval returns
 * results.
 */

"use client";

import * as React from "react";
import { CitationCard, type Citation } from "@ama/ui/components/citation/citation-card";
import { DegradedModeBadge } from "@ama/ui/components/citation/degraded-mode-badge";

export interface RecommendationCardProps {
  /** Stable identifier from the governance event */
  id: string;
  agentName: string;
  title: string;
  body: string;
  citations: Citation[];
  /** When true, the offline cache is in use; the badge is rendered. */
  degraded?: boolean;
  cacheBuiltAt?: string;
  degradedReason?: string;
  /** Empty-result note from the simulation SSE channel (FR-RAG-SIM-03). */
  emptyResultNote?: string;
}

export function RecommendationCard({
  id,
  agentName,
  title,
  body,
  citations,
  degraded,
  cacheBuiltAt,
  degradedReason,
  emptyResultNote,
}: RecommendationCardProps) {
  const showCitations = citations.length > 0;
  return (
    <section
      aria-labelledby={`${id}-title`}
      className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
    >
      <header className="flex items-center justify-between gap-2">
        <h3 id={`${id}-title`} className="text-base font-semibold text-slate-900">
          {title}
        </h3>
        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
          {agentName}
        </span>
      </header>

      {degraded ? (
        <DegradedModeBadge
          degraded
          cacheBuiltAt={cacheBuiltAt}
          reason={degradedReason}
        />
      ) : null}

      <p className="text-sm leading-relaxed text-slate-800">{body}</p>

      {showCitations ? (
        <div
          className="mt-1 flex flex-col gap-2"
          role="region"
          aria-label={`Sources cited by ${agentName}`}
        >
          {/* Spec 036 / F-A12 / T241 — fire a polite live-region announcement when
              the grounded recommendation renders so screen readers acknowledge that
              the response is sourced from N citations. */}
          <p className="sr-only" role="status" aria-live="polite">
            {`Grounded recommendation with ${citations.length} citation${citations.length === 1 ? "" : "s"}`}
          </p>
          {citations.map((c, i) => (
            <CitationCard
              key={c.sha256_of_chunk || `${id}-cite-${i}`}
              citation={c}
              idPrefix={`${id}-cite-${i}`}
            />
          ))}
        </div>
      ) : emptyResultNote ? (
        <p
          role="status"
          className="rounded border-l-2 border-amber-400 bg-amber-50 px-3 py-1 text-xs text-amber-900"
        >
          {emptyResultNote}
        </p>
      ) : null}
    </section>
  );
}

export default RecommendationCard;
