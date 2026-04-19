"use client";

/**
 * IncidentSidebar — Detail panel for a selected incident.
 *
 * Displays full incident information with AWS-coloured severity indicator
 * and a prominent workspace navigation link.
 */

import type { IncidentFeatureProperties } from "./types";
import Link from "next/link";

export interface IncidentSidebarProps {
  /** The selected incident's properties */
  incident: IncidentFeatureProperties;
  /** Called when the user closes the sidebar */
  onClose: () => void;
  /** Return path with filter params for back-navigation */
  returnPath?: string;
  /** Additional CSS class */
  className?: string;
}

/* ── Severity tier display config ── */

const SEVERITY_DISPLAY: Record<
  string,
  { label: string; cssClass: string }
> = {
  advice: { label: "Advice", cssClass: "disaster-mapper-severity--advice" },
  watch: {
    label: "Watch and Act",
    cssClass: "disaster-mapper-severity--watch",
  },
  emergency: {
    label: "Emergency Warning",
    cssClass: "disaster-mapper-severity--emergency",
  },
};

function formatLabel(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-AU", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
    });
  } catch {
    return iso;
  }
}

export function IncidentSidebar({
  incident,
  onClose,
  returnPath,
  className,
}: IncidentSidebarProps) {
  const severityInfo = SEVERITY_DISPLAY[incident.severity_tier] ?? {
    label: incident.severity_tier,
    cssClass: "",
  };

  return (
    <aside
      className={`disaster-mapper-sidebar ${className ?? ""}`}
      role="complementary"
      aria-label={`Details for ${incident.title}`}
    >
      <div className="disaster-mapper-sidebar-header">
        <h2>{incident.title}</h2>
        <button
          onClick={onClose}
          className="disaster-mapper-close-btn"
          aria-label="Close incident details"
        >
          ×
        </button>
      </div>

      {/* Severity badge */}
      <div
        className={`disaster-mapper-severity-badge ${severityInfo.cssClass}`}
      >
        {severityInfo.label}
      </div>

      <dl className="disaster-mapper-detail-list">
        <dt>Type</dt>
        <dd>{formatLabel(incident.incident_type)}</dd>

        <dt>Status</dt>
        <dd>{formatLabel(incident.status)}</dd>

        <dt>Severity</dt>
        <dd className={severityInfo.cssClass}>
          {formatLabel(incident.severity)} → {severityInfo.label}
        </dd>

        <dt>Start Date</dt>
        <dd>{formatDate(incident.started_at)}</dd>

        {incident.pprr_phase && (
          <>
            <dt>PPRR Phase</dt>
            <dd>{formatLabel(incident.pprr_phase)}</dd>
          </>
        )}

        <dt>Incident Level</dt>
        <dd>Level {incident.incident_level}</dd>

        <dt>Affected Jurisdictions</dt>
        <dd>
          {incident.affected_jurisdiction_ids.length > 0
            ? incident.affected_jurisdiction_ids
                .map((id) => id.toUpperCase())
                .join(", ")
            : "—"}
        </dd>

        {incident.participating_organisation_ids.length > 0 && (
          <>
            <dt>Organisations</dt>
            <dd>
              {incident.participating_organisation_ids.join(", ")}
            </dd>
          </>
        )}
      </dl>

      <Link
        href={`/incidents/${incident.incident_id}${returnPath ? `?returnUrl=${encodeURIComponent(returnPath)}` : ""}`}
        className="disaster-mapper-workspace-link"
      >
        Open Workspace →
      </Link>
    </aside>
  );
}

export default IncidentSidebar;
