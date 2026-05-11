/** spec-038 T-AA110 — staleness banner. */
export function StalenessBanner({ since, downgraded }: { since?: string; downgraded?: boolean }) {
  return (
    <div role="status" className={`rounded border p-2 ${downgraded ? "bg-gray-50 text-gray-700" : "bg-amber-50 text-amber-900 border-amber-400"}`}>
      {downgraded
        ? "This screenshot is older than the grace period; using best available."
        : `Screenshot may be out of date${since ? ` (since ${since})` : ""}.`}
    </div>
  );
}
