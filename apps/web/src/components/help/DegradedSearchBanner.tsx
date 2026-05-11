/** spec-038 T-AA118 — persistent degraded-search banner. */
export function DegradedSearchBanner() {
  return (
    <div role="status" className="rounded border border-amber-400 bg-amber-50 p-2 text-sm">
      Showing cached results only — full search unavailable offline.
    </div>
  );
}
