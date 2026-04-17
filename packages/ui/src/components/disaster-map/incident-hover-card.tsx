"use client";

/**
 * IncidentHoverCard — floating preview card shown when hovering over a map marker.
 *
 * Displays incident title, type, region, date, and severity in a compact card
 * positioned on the right side of the map, similar to AIDR's incident preview.
 */

import type { IncidentFeatureProperties } from "./types";
import { IncidentTypeIcon } from "./incident-type-icon";

export interface IncidentHoverCardProps {
  incident: IncidentFeatureProperties;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-AU", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function formatType(type: string): string {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

const SEVERITY_COLOURS: Record<string, string> = {
  advice: "#ffc107",
  watch: "#ff8c00",
  emergency: "#d32f2f",
};

export function IncidentHoverCard({ incident }: IncidentHoverCardProps) {
  const severityColor =
    SEVERITY_COLOURS[incident.severity_tier] ?? "#666";

  return (
    <div className="incident-hover-card" role="tooltip">
      <div className="incident-hover-card__header">
        <IncidentTypeIcon type={incident.incident_type} size={32} />
        <div className="incident-hover-card__title-group">
          <h4 className="incident-hover-card__title">{incident.title}</h4>
          <span className="incident-hover-card__type">
            {formatType(incident.incident_type)}
          </span>
        </div>
      </div>

      <div className="incident-hover-card__details">
        <div className="incident-hover-card__row">
          <span className="incident-hover-card__label">Date</span>
          <span className="incident-hover-card__value">
            {formatDate(incident.started_at)}
          </span>
        </div>
        <div className="incident-hover-card__row">
          <span className="incident-hover-card__label">Severity</span>
          <span
            className="incident-hover-card__severity"
            style={{ color: severityColor }}
          >
            {incident.severity_tier?.replace(/\b\w/g, (c) => c.toUpperCase()) ?? "Unknown"}
          </span>
        </div>
        <div className="incident-hover-card__row">
          <span className="incident-hover-card__label">Status</span>
          <span className="incident-hover-card__value">
            {incident.status?.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) ?? "Unknown"}
          </span>
        </div>
        {incident.pprr_phase && (
          <div className="incident-hover-card__row">
            <span className="incident-hover-card__label">PPRR</span>
            <span className="incident-hover-card__value">
              {incident.pprr_phase.replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
          </div>
        )}
      </div>

      <div className="incident-hover-card__footer">
        Click for details →
      </div>
    </div>
  );
}
