"use client";

/**
 * SearchBar — Keyword search input for the Disaster Mapper.
 *
 * Text input with placeholder, clear button, and 300ms debounce.
 * Consumes keyword state from the filter hook.
 */

export interface SearchBarProps {
  /** Current input value (controlled) */
  value: string;
  /** Called on every keystroke (debouncing is handled by the filter hook) */
  onChange: (value: string) => void;
  /** Placeholder text */
  placeholder?: string;
  /** Additional CSS class */
  className?: string;
}

export function SearchBar({
  value,
  onChange,
  placeholder = "Search incidents by title…",
  className,
}: SearchBarProps) {
  return (
    <div
      className={`disaster-mapper-search-wrapper ${className ?? ""}`}
      role="search"
      aria-label="Search incidents"
    >
      <input
        type="search"
        className="disaster-mapper-search-input"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="Search incidents by keyword"
      />
      {value && (
        <button
          className="disaster-mapper-search-clear"
          onClick={() => onChange("")}
          aria-label="Clear search"
          type="button"
        >
          ×
        </button>
      )}
    </div>
  );
}

export default SearchBar;
