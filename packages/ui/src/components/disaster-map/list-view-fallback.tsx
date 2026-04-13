"use client";

/**
 * ListViewFallback — Table-based fallback view when Azure Maps is unavailable.
 *
 * Displays incidents in a sortable table with columns: Title, Type, Severity,
 * Status, Date, Location. Shares the same filter controls as the map view.
 */

import { useCallback, useState } from "react";
import type { IncidentFeature } from "./types";

export interface ListViewFallbackProps {
  features: IncidentFeature[];
  onIncidentClick?: (feature: IncidentFeature) => void;
  className?: string;
}

type SortField =
  | "title"
  | "incident_type"
  | "severity"
  | "status"
  | "started_at"
  | "location";
type SortDir = "asc" | "desc";

function formatLabel(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
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

function formatCoords(coords: [number, number]): string {
  return `${coords[1].toFixed(2)}°S, ${Math.abs(coords[0]).toFixed(2)}°E`;
}

export function ListViewFallback({
  features,
  onIncidentClick,
  className,
}: ListViewFallbackProps) {
  const [sortField, setSortField] = useState<SortField>("started_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const toggleSort = useCallback(
    (field: SortField) => {
      if (sortField === field) {
        setSortDir((d) => (d === "asc" ? "desc" : "asc"));
      } else {
        setSortField(field);
        setSortDir("asc");
      }
    },
    [sortField],
  );

  const sorted = [...features].sort((a, b) => {
    const pa = a.properties;
    const pb = b.properties;
    let cmp = 0;

    switch (sortField) {
      case "title":
        cmp = pa.title.localeCompare(pb.title);
        break;
      case "incident_type":
        cmp = pa.incident_type.localeCompare(pb.incident_type);
        break;
      case "severity":
        cmp = pa.severity.localeCompare(pb.severity);
        break;
      case "status":
        cmp = pa.status.localeCompare(pb.status);
        break;
      case "started_at":
        cmp = pa.started_at.localeCompare(pb.started_at);
        break;
      case "location":
        cmp =
          a.geometry.coordinates[1] - b.geometry.coordinates[1];
        break;
    }

    return sortDir === "asc" ? cmp : -cmp;
  });

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return "";
    return sortDir === "asc" ? " ▲" : " ▼";
  };

  return (
    <div
      className={`disaster-mapper-list-view ${className ?? ""}`}
      role="region"
      aria-label="Incident list view"
    >
      <table className="disaster-mapper-table">
        <thead>
          <tr>
            {(
              [
                ["title", "Title"],
                ["incident_type", "Type"],
                ["severity", "Severity"],
                ["status", "Status"],
                ["started_at", "Date"],
                ["location", "Location"],
              ] as [SortField, string][]
            ).map(([field, label]) => (
              <th
                key={field}
                onClick={() => toggleSort(field)}
                className="disaster-mapper-th"
                role="columnheader"
                aria-sort={
                  sortField === field
                    ? sortDir === "asc"
                      ? "ascending"
                      : "descending"
                    : "none"
                }
              >
                {label}
                {sortIndicator(field)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((f) => (
            <tr
              key={f.id}
              onClick={() => onIncidentClick?.(f)}
              className="disaster-mapper-tr"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onIncidentClick?.(f);
                }
              }}
            >
              <td>{f.properties.title}</td>
              <td>{formatLabel(f.properties.incident_type)}</td>
              <td
                className={`disaster-mapper-severity--${f.properties.severity_tier}`}
              >
                {formatLabel(f.properties.severity_tier)}
              </td>
              <td>{formatLabel(f.properties.status)}</td>
              <td>{formatDate(f.properties.started_at)}</td>
              <td>
                {formatCoords(
                  f.geometry.coordinates as [number, number],
                )}
              </td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr>
              <td colSpan={6} className="disaster-mapper-empty-row">
                No incidents to display.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default ListViewFallback;
