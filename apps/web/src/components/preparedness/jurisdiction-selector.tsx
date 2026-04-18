"use client";

import { useEffect, useRef, useState } from "react";

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
  const [isOpen, setIsOpen] = useState(false);
  const [focusIndex, setFocusIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const actionsRef = useRef<HTMLDivElement>(null);

  const grouped = groupByLevel(jurisdictions);
  const flatItems = jurisdictions;

  const selectedCount = selectedIds.length;
  const buttonLabel =
    selectedCount === 0
      ? "Select jurisdictions…"
      : selectedCount === jurisdictions.length
        ? "All jurisdictions selected"
        : `${selectedCount} jurisdiction${selectedCount > 1 ? "s" : ""} selected`;

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (isOpen && focusIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll('[role="option"]');
      (items[focusIndex] as HTMLElement)?.focus();
    }
  }, [focusIndex, isOpen]);

  function toggleItem(id: string) {
    const next = selectedIds.includes(id)
      ? selectedIds.filter((sid) => sid !== id)
      : [...selectedIds, id];
    onChange(next);
  }

  function selectAll() {
    onChange(jurisdictions.map((j) => j.jurisdiction_id));
  }

  function clearAll() {
    onChange([]);
  }

  function handleKeyDown(event: React.KeyboardEvent) {
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        setFocusIndex((prev) => Math.min(prev + 1, flatItems.length - 1));
        break;
      case "ArrowUp":
        event.preventDefault();
        setFocusIndex((prev) => Math.max(prev - 1, 0));
        break;
      case " ":
      case "Enter":
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusIndex(0);
        } else if (focusIndex >= 0 && focusIndex < flatItems.length) {
          toggleItem(flatItems[focusIndex].jurisdiction_id);
        }
        break;
      case "Escape":
        event.preventDefault();
        setIsOpen(false);
        break;
      case "Home":
        event.preventDefault();
        if (isOpen) selectAll();
        break;
      case "End":
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          if (isOpen) clearAll();
        }
        break;
      case "a":
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          if (isOpen) selectAll();
        }
        break;
    }
  }

  return (
    <div className="preparedness-jurisdiction-selector" ref={containerRef}>
      <button
        type="button"
        className="preparedness-select preparedness-jurisdiction-trigger"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) setFocusIndex(0);
        }}
        onKeyDown={handleKeyDown}
      >
        {buttonLabel}
      </button>

      {isOpen && (
        <div className="preparedness-jurisdiction-dropdown">
          <div className="preparedness-jurisdiction-actions" ref={actionsRef}>
            <button
              type="button"
              className="preparedness-button"
              onClick={selectAll}
              tabIndex={0}
              aria-keyshortcuts="Control+A"
            >
              Select all
            </button>
            <button
              type="button"
              className="preparedness-button"
              onClick={clearAll}
              tabIndex={0}
            >
              Clear all
            </button>
          </div>

          <ul
            ref={listRef}
            role="listbox"
            aria-multiselectable="true"
            aria-label="Jurisdictions"
            className="preparedness-jurisdiction-list"
            onKeyDown={handleKeyDown}
          >
            {grouped.map(({ level, items }) => (
              <li key={level} role="presentation">
                <span className="preparedness-jurisdiction-group-label">
                  {LEVEL_LABELS[level] ?? level}
                </span>
                <ul role="group" aria-label={LEVEL_LABELS[level] ?? level}>
                  {items.map((jurisdiction) => {
                    const globalIndex = flatItems.findIndex(
                      (j) => j.jurisdiction_id === jurisdiction.jurisdiction_id,
                    );
                    const isSelected = selectedIds.includes(jurisdiction.jurisdiction_id);
                    return (
                      <li
                        key={jurisdiction.jurisdiction_id}
                        role="option"
                        aria-selected={isSelected}
                        tabIndex={focusIndex === globalIndex ? 0 : -1}
                        className={`preparedness-jurisdiction-option ${isSelected ? "preparedness-jurisdiction-option--selected" : ""}`}
                        onClick={() => toggleItem(jurisdiction.jurisdiction_id)}
                        onKeyDown={handleKeyDown}
                      >
                        <span
                          className="preparedness-jurisdiction-checkbox"
                          aria-hidden="true"
                        >
                          {isSelected ? "☑" : "☐"}
                        </span>
                        {jurisdiction.name}
                      </li>
                    );
                  })}
                </ul>
              </li>
            ))}
          </ul>
        </div>
      )}
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
