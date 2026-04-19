"use client";

/**
 * JurisdictionSelector — Fieldset-based multi-select filter panel for jurisdictions.
 *
 * Matches the disaster map FilterPanel layout: fieldset groups with native checkboxes,
 * All/Clear action links in the legend, grouped by level (Commonwealth / States / Territories).
 */

import { useCallback } from "react";

import type { JurisdictionSummary } from "../../lib/api/jurisdictions";

interface JurisdictionSelectorProps {
  jurisdictions: JurisdictionSummary[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}

const LEVEL_LABELS: Record<string, string> = {
  commonwealth: "Commonwealth",
  state: "States",
  territory: "Territories",
};

export function JurisdictionSelector({ jurisdictions, selectedIds, onChange }: JurisdictionSelectorProps) {
  const grouped = groupByLevel(jurisdictions);

  const toggleItem = useCallback(
    (id: string) => {
      const next = selectedIds.includes(id)
        ? selectedIds.filter((sid) => sid !== id)
        : [...selectedIds, id];
      onChange(next);
    },
    [selectedIds, onChange],
  );

  const selectAll = useCallback(() => {
    onChange(jurisdictions.map((j) => j.jurisdiction_id));
  }, [jurisdictions, onChange]);

  const clearAll = useCallback(() => {
    onChange([]);
  }, [onChange]);

  const selectedCount = selectedIds.length;

  return (
    <div
      className="preparedness-filter-panel"
      role="search"
      aria-label="Filter by jurisdiction"
    >
      <div className="preparedness-filter-content">
        {/* Summary status */}
        <p className="preparedness-filter-status" aria-live="polite">
          {selectedCount === 0
            ? "No jurisdictions selected"
            : selectedCount === jurisdictions.length
              ? "All jurisdictions selected"
              : `${selectedCount} of ${jurisdictions.length} selected`}
        </p>

        {/* One fieldset per level group */}
        {grouped.map(({ level, items }) => {
          const levelIds = items.map((j) => j.jurisdiction_id);
          const allSelected = levelIds.every((id) => selectedIds.includes(id));

          const selectGroup = () => {
            const merged = new Set([...selectedIds, ...levelIds]);
            onChange(Array.from(merged));
          };
          const clearGroup = () => {
            onChange(selectedIds.filter((id) => !levelIds.includes(id)));
          };

          return (
            <fieldset key={level} className="preparedness-filter-group">
              <legend>
                {LEVEL_LABELS[level] ?? level}
                <span className="preparedness-filter-actions">
                  <button type="button" onClick={allSelected ? clearGroup : selectGroup}>
                    {allSelected ? "Clear" : "All"}
                  </button>
                </span>
              </legend>
              {items.map((jurisdiction) => {
                const isSelected = selectedIds.includes(jurisdiction.jurisdiction_id);
                return (
                  <label key={jurisdiction.jurisdiction_id} className="preparedness-checkbox">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleItem(jurisdiction.jurisdiction_id)}
                    />
                    {jurisdiction.name}
                  </label>
                );
              })}
            </fieldset>
          );
        })}

        {/* Global actions */}
        <div className="preparedness-filter-global-actions">
          <button type="button" onClick={selectAll} className="preparedness-filter-action-btn">
            Select All
          </button>
          <button type="button" onClick={clearAll} className="preparedness-filter-action-btn preparedness-filter-action-btn--clear">
            Clear All
          </button>
        </div>
      </div>
    </div>
  );
}

function groupByLevel(
  jurisdictions: JurisdictionSummary[],
): { level: string; items: JurisdictionSummary[] }[] {
  const groups = new Map<string, JurisdictionSummary[]>();
  for (const j of jurisdictions) {
    const existing = groups.get(j.level) ?? [];
    existing.push(j);
    groups.set(j.level, existing);
  }
  return Array.from(groups.entries()).map(([level, items]) => ({ level, items }));
}
