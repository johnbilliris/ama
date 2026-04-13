"use client";

/**
 * FilterPanel — Multi-criteria filter panel for the Disaster Mapper.
 *
 * Renders checkboxes for incident type (9), severity tier (3 AWS tiers),
 * status (5 operational), PPRR phase (4), and year range selectors.
 * Supports Select All / Reset per category.
 */

import { useCallback } from "react";
import {
  INCIDENT_TYPES,
  SEVERITY_TIERS,
  OPERATIONAL_STATUSES,
  PPRR_PHASES,
  toggleCSVValue,
  csvHasValue,
  type MapFilterParams,
} from "./use-disaster-map-filters";

export interface FilterPanelProps {
  filters: MapFilterParams;
  onFilterChange: <K extends keyof MapFilterParams>(
    key: K,
    value: MapFilterParams[K],
  ) => void;
  onReset: () => void;
  /** Whether the panel is expanded (for mobile toggle) */
  isOpen?: boolean;
  /** Toggle panel open/closed (mobile) */
  onToggle?: () => void;
  className?: string;
}

/* ── Label formatters ── */

function formatLabel(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ── Component ── */

export function FilterPanel({
  filters,
  onFilterChange,
  onReset,
  isOpen = true,
  onToggle,
  className,
}: FilterPanelProps) {
  // ── Checkbox toggle helpers ──
  const toggleType = useCallback(
    (value: string) => {
      onFilterChange("type", toggleCSVValue(filters.type, value));
    },
    [filters.type, onFilterChange],
  );

  const toggleSeverity = useCallback(
    (values: readonly string[]) => {
      // Severity tiers map to one or more domain values
      let current = filters.severity ? filters.severity.split(",") : [];
      const allPresent = values.every((v) => current.includes(v));
      if (allPresent) {
        current = current.filter((v) => !values.includes(v));
      } else {
        for (const v of values) {
          if (!current.includes(v)) current.push(v);
        }
      }
      onFilterChange(
        "severity",
        current.length > 0 ? current.join(",") : undefined,
      );
    },
    [filters.severity, onFilterChange],
  );

  const toggleStatus = useCallback(
    (value: string) => {
      onFilterChange("status", toggleCSVValue(filters.status, value));
    },
    [filters.status, onFilterChange],
  );

  const togglePhase = useCallback(
    (value: string) => {
      onFilterChange("pprr_phase", toggleCSVValue(filters.pprr_phase, value));
    },
    [filters.pprr_phase, onFilterChange],
  );

  // ── Select All / Clear per category ──
  const selectAllTypes = useCallback(() => {
    onFilterChange("type", INCIDENT_TYPES.join(","));
  }, [onFilterChange]);

  const clearTypes = useCallback(() => {
    onFilterChange("type", undefined);
  }, [onFilterChange]);

  const selectAllStatuses = useCallback(() => {
    onFilterChange("status", OPERATIONAL_STATUSES.join(","));
  }, [onFilterChange]);

  const clearStatuses = useCallback(() => {
    onFilterChange("status", undefined);
  }, [onFilterChange]);

  const selectAllPhases = useCallback(() => {
    onFilterChange("pprr_phase", PPRR_PHASES.join(","));
  }, [onFilterChange]);

  const clearPhases = useCallback(() => {
    onFilterChange("pprr_phase", undefined);
  }, [onFilterChange]);

  // Year range
  const currentYear = new Date().getFullYear();
  const yearOptions = Array.from(
    { length: currentYear - 2000 + 1 },
    (_, i) => 2000 + i,
  );

  return (
    <div
      className={`disaster-mapper-filter-panel ${isOpen ? "disaster-mapper-filter-panel--open" : ""} ${className ?? ""}`}
      role="search"
      aria-label="Filter incidents"
    >
      {/* Mobile toggle header */}
      {onToggle && (
        <button
          className="disaster-mapper-filter-toggle"
          onClick={onToggle}
          aria-expanded={isOpen}
          aria-controls="filter-panel-content"
        >
          Filters {isOpen ? "▾" : "▸"}
        </button>
      )}

      <div
        id="filter-panel-content"
        className="disaster-mapper-filter-content"
        style={{ display: isOpen ? "block" : "none" }}
      >
        {/* ── Date range ── */}
        <fieldset className="disaster-mapper-filter-group">
          <legend>Date Range</legend>
          <div className="disaster-mapper-year-selectors">
            <label>
              From
              <select
                value={filters.year_start ?? ""}
                onChange={(e) =>
                  onFilterChange(
                    "year_start",
                    e.target.value ? parseInt(e.target.value, 10) : undefined,
                  )
                }
              >
                <option value="">Any</option>
                {yearOptions.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </label>
            <label>
              To
              <select
                value={filters.year_end ?? ""}
                onChange={(e) =>
                  onFilterChange(
                    "year_end",
                    e.target.value ? parseInt(e.target.value, 10) : undefined,
                  )
                }
              >
                <option value="">Any</option>
                {yearOptions.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </fieldset>

        {/* ── Incident type ── */}
        <fieldset className="disaster-mapper-filter-group">
          <legend>
            Incident Type
            <span className="disaster-mapper-filter-actions">
              <button type="button" onClick={selectAllTypes}>
                All
              </button>
              <button type="button" onClick={clearTypes}>
                Clear
              </button>
            </span>
          </legend>
          {INCIDENT_TYPES.map((t) => (
            <label key={t} className="disaster-mapper-checkbox">
              <input
                type="checkbox"
                checked={csvHasValue(filters.type, t)}
                onChange={() => toggleType(t)}
              />
              {formatLabel(t)}
            </label>
          ))}
        </fieldset>

        {/* ── Severity tier ── */}
        <fieldset className="disaster-mapper-filter-group">
          <legend>Severity</legend>
          {SEVERITY_TIERS.map((tier) => {
            const checked = tier.values.every((v) =>
              csvHasValue(filters.severity, v),
            );
            return (
              <label key={tier.label} className="disaster-mapper-checkbox">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleSeverity(tier.values)}
                />
                <span
                  className={`disaster-mapper-severity-dot disaster-mapper-severity-dot--${tier.label.toLowerCase().replace(/ /g, "-")}`}
                />
                {tier.label}
              </label>
            );
          })}
        </fieldset>

        {/* ── Status ── */}
        <fieldset className="disaster-mapper-filter-group">
          <legend>
            Status
            <span className="disaster-mapper-filter-actions">
              <button type="button" onClick={selectAllStatuses}>
                All
              </button>
              <button type="button" onClick={clearStatuses}>
                Clear
              </button>
            </span>
          </legend>
          {OPERATIONAL_STATUSES.map((s) => (
            <label key={s} className="disaster-mapper-checkbox">
              <input
                type="checkbox"
                checked={csvHasValue(filters.status, s)}
                onChange={() => toggleStatus(s)}
              />
              {formatLabel(s)}
            </label>
          ))}
        </fieldset>

        {/* ── PPRR Phase ── */}
        <fieldset className="disaster-mapper-filter-group">
          <legend>
            PPRR Phase
            <span className="disaster-mapper-filter-actions">
              <button type="button" onClick={selectAllPhases}>
                All
              </button>
              <button type="button" onClick={clearPhases}>
                Clear
              </button>
            </span>
          </legend>
          {PPRR_PHASES.map((p) => (
            <label key={p} className="disaster-mapper-checkbox">
              <input
                type="checkbox"
                checked={csvHasValue(filters.pprr_phase, p)}
                onChange={() => togglePhase(p)}
              />
              {formatLabel(p)}
            </label>
          ))}
        </fieldset>

        {/* ── Reset all ── */}
        <button
          type="button"
          className="disaster-mapper-filter-reset"
          onClick={onReset}
        >
          Reset All Filters
        </button>
      </div>
    </div>
  );
}

export default FilterPanel;
