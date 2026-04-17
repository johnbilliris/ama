"use client";

interface DegradedModeBannerProps {
  /** List of unavailable data sources */
  degradedSources: string[];
  /** Whether the banner should be visible */
  visible?: boolean;
}

/**
 * System-wide degradation alert banner listing unavailable data sources (FR-031).
 */
export function DegradedModeBanner({
  degradedSources,
  visible = true,
}: DegradedModeBannerProps) {
  if (!visible || degradedSources.length === 0) return null;

  return (
    <div
      role="alert"
      aria-live="polite"
      className="rounded-lg border border-orange-300 bg-orange-50 p-4"
    >
      <div className="flex items-start gap-3">
        <span className="text-lg" aria-hidden="true">
          ⚠️
        </span>
        <div>
          <h3 className="text-sm font-semibold text-orange-800">
            Degraded Mode — Some data sources unavailable
          </h3>
          <p className="mt-1 text-xs text-orange-700">
            The following data sources are currently unavailable. Displayed data
            may be stale or incomplete.
          </p>
          <ul className="mt-2 list-inside list-disc text-xs text-orange-700">
            {degradedSources.map((source) => (
              <li key={source}>{source}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
