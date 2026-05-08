/**
 * Spec 036 T084 — Citation card component (FR-RAG-AG-03, R-14, WCAG 2.2 AA).
 *
 * Renders a single grounding citation:
 *   - jurisdiction badge (full state name for screen readers)
 *   - topic + page anchor
 *   - confidence indicator (badge + numeric, never colour-only)
 *   - link to ``rendered_url`` (Markdown handbook page)
 *   - link to ``source_url`` (PDF) — opens in new tab with noopener
 *   - collapsible snippet (full-text licences only)
 *
 * Accessibility:
 *   - Whole card is a region with aria-label; expand/collapse is a button
 *     with aria-expanded; the panel itself has aria-controls / id pairing.
 *   - Jurisdiction codes are expanded for screen readers
 *     ("New South Wales" not "NSW") per Accessibility memo §51–54.
 *   - Confidence does NOT rely on colour alone; we always show the value.
 */

import * as React from "react";

export type CitationLicenceMode = "full-text" | "metadata-only";

export interface Citation {
  jurisdiction: string;
  topic: string;
  page: number;
  source_url: string;
  rendered_url: string;
  sha256_of_chunk: string;
  licence_mode: CitationLicenceMode;
  confidence: number;
  /** Present iff licence_mode === "full-text" */
  snippet?: string;
}

export interface CitationCardProps {
  citation: Citation;
  /** Optional outer className for layout integration */
  className?: string;
  /** Optional id used as the prefix for collapsible section ids */
  idPrefix?: string;
}

const JURISDICTION_LABELS: Record<string, string> = {
  nsw: "New South Wales",
  vic: "Victoria",
  qld: "Queensland",
  sa: "South Australia",
  wa: "Western Australia",
  tas: "Tasmania",
  nt: "Northern Territory",
  act: "Australian Capital Territory",
  national: "Australian National",
  aidr: "Australian Institute for Disaster Resilience",
};

function describeConfidence(c: number): { label: string; tone: "low" | "medium" | "high" } {
  if (c >= 0.75) return { label: "High", tone: "high" };
  if (c >= 0.5) return { label: "Medium", tone: "medium" };
  return { label: "Low", tone: "low" };
}

const CONFIDENCE_STYLE: Record<"low" | "medium" | "high", { bg: string; fg: string; icon: string }> = {
  low: { bg: "bg-red-100", fg: "text-red-800", icon: "✗" },
  medium: { bg: "bg-yellow-100", fg: "text-yellow-800", icon: "⚠" },
  high: { bg: "bg-green-100", fg: "text-green-800", icon: "✓" },
};

export function CitationCard({ citation, className, idPrefix }: CitationCardProps) {
  const [open, setOpen] = React.useState(false);
  const baseId = idPrefix ?? `citation-${citation.sha256_of_chunk.slice(0, 8)}`;
  const panelId = `${baseId}-panel`;
  const headerId = `${baseId}-header`;

  const jurisdictionLabel = JURISDICTION_LABELS[citation.jurisdiction.toLowerCase()] ?? citation.jurisdiction;
  const confidence = describeConfidence(citation.confidence);
  const cs = CONFIDENCE_STYLE[confidence.tone];
  const hasSnippet = citation.licence_mode === "full-text" && Boolean(citation.snippet);

  return (
    <article
      className={`rounded-md border border-slate-200 bg-white shadow-sm ${className ?? ""}`}
      aria-labelledby={headerId}
    >
      <header className="flex flex-wrap items-center gap-2 px-3 py-2 text-sm" id={headerId}>
        <span
          className="inline-flex items-center rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-800"
          aria-label={`Jurisdiction: ${jurisdictionLabel}`}
        >
          {jurisdictionLabel}
        </span>
        <span className="font-medium text-slate-900">{citation.topic}</span>
        <span className="text-slate-500">page {citation.page}</span>
        <span
          className={`ml-auto inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${cs.bg} ${cs.fg}`}
          aria-label={`Confidence: ${confidence.label} (${(citation.confidence * 100).toFixed(0)} percent)`}
          role="status"
        >
          <span aria-hidden="true">{cs.icon}</span>
          {confidence.label} ({(citation.confidence * 100).toFixed(0)}%)
        </span>
      </header>

      <div className="flex flex-wrap items-center gap-3 px-3 pb-2 text-sm">
        <a
          className="text-blue-700 underline underline-offset-2 hover:text-blue-900"
          href={citation.rendered_url}
        >
          Open handbook
        </a>
        <a
          className="text-blue-700 underline underline-offset-2 hover:text-blue-900"
          href={citation.source_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Source PDF (opens in new tab)
        </a>
        {hasSnippet ? (
          <button
            type="button"
            className="ml-auto rounded border border-slate-300 px-2 py-0.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
            aria-expanded={open}
            aria-controls={panelId}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? "Hide quote" : "Show quote"}
          </button>
        ) : (
          <span className="ml-auto rounded bg-slate-50 px-2 py-0.5 text-xs text-slate-600">
            Metadata only — open the handbook for the full passage
          </span>
        )}
      </div>

      {hasSnippet && open ? (
        <blockquote
          id={panelId}
          className="border-t border-slate-200 bg-slate-50 px-3 py-2 text-sm italic text-slate-800"
        >
          {citation.snippet}
        </blockquote>
      ) : null}
    </article>
  );
}

export default CitationCard;
